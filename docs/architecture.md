# Arquitectura

Un solo proceso de Node.js mantiene una conexión permanente (_gateway_) con Discord y reacciona a eventos. No hay servidor HTTP ni base de datos. El código se organiza por **evento de Discord**: cada archivo de `src/events/` atiende uno y delega el trabajo en un servicio.

```text
Discord gateway
      │
  discord.js Client
      │  registerEvents (events/index.ts): un error dentro de un evento se registra y no tumba el proceso
      ▼
  events/                         services/                lib/
  clientReady          ───────►   memberLog.init, bump.start
  guildMemberAdd       ───────►   memberLog.logJoin ─────►  invites.ts, embeds.ts
                                  welcome.greet (si no está pending)
  guildMemberUpdate    ───────►   welcome.greet (pending: true → false)
  guildMemberRemove    ───────►   memberLog.logLeave
  messageCreate        ───────►   bump.handleMessage ─────► bump.ts ── state.ts (data/state.json)
```

| Carpeta/archivo | Qué hay                                                                                                          |
| :-------------- | :--------------------------------------------------------------------------------------------------------------- |
| `index.ts`      | Arranque: configuración, cliente con sus intents, registro de eventos                                            |
| `config.ts`     | Variables de entorno validadas con `zod`                                                                         |
| `context.ts`    | `Context`: la configuración y los tres servicios, que reciben todos los eventos                                  |
| `messages.ts`   | Todo lo que Rakim escribe en Discord                                                                             |
| `events/`       | Un archivo por evento. Cada uno filtra el servidor y llama al servicio                                           |
| `services/`     | La lógica de cada función con acceso a Discord: `welcome`, `memberLog`, `bump`                                   |
| `lib/`          | Piezas que no dependen de Discord y se prueban solas: `invites`, `bump`, `state`, `embeds`, `channels`, `logger` |

Sumar un evento: crear su archivo en `events/` con `defineEvent` y agregarlo a la lista de `events/index.ts`.

## Intents

Un intent le dice a Discord qué eventos enviar al bot. Se pide solo lo que las tres funciones necesitan:

| Intent           | Privilegiado | Qué habilita                                            | Qué se rompe sin él                                                                                          |
| :--------------- | :----------- | :------------------------------------------------------ | :----------------------------------------------------------------------------------------------------------- |
| `Guilds`         | No           | Que el bot conozca el servidor, sus canales y sus roles | Todo: no puede resolver canales ni roles                                                                     |
| `GuildMembers`   | **Sí**       | Entradas, salidas y cambios de miembro                  | Log de entradas y salidas y saludo (el fin de la pantalla de reglas llega como cambio de miembro, `pending`) |
| `GuildMessages`  | No           | Mensajes de los canales del servidor                    | Recordatorio de bump: no vería la respuesta de Disboard                                                      |
| `MessageContent` | **Sí**       | El texto y los embeds de mensajes de otros bots         | Recordatorio de bump: Discord los entrega vacíos y no se distingue un bump exitoso del aviso de espera       |

Los dos privilegiados se activan en el portal de desarrolladores (Bot > Privileged Gateway Intents) y no requieren verificación mientras el bot esté en menos de 100 servidores.

**Descartados a propósito**: `GuildInvites` (solo sirve para escuchar cuándo se crea una invitación; Rakim lee las invitaciones por la API en cada entrada, así que no lo necesita), `DirectMessages` (no hay mensajes directos), `GuildPresences` y `GuildVoiceStates` (no se usan).

## Permisos del bot en el servidor

Se invita con `permissions=19488`:

| Permiso            | Para qué                                                                                        |
| :----------------- | :---------------------------------------------------------------------------------------------- |
| Ver canales        | Llegar a los canales de bienvenida, logs y bump, y recibir los mensajes de Disboard             |
| Enviar mensajes    | Saludar, registrar y recordar                                                                   |
| Insertar enlaces   | Los embeds del log                                                                              |
| Gestionar servidor | Leer las invitaciones y sus usos (no hay otra forma). Es sensible: dárselo solo al rol de Rakim |

El canal de logs es privado: el rol de Rakim necesita acceso explícito. Si `BUMP_ROLE_ID` está definido, ese rol debe ser mencionable. No se pide "Leer el historial de mensajes" porque el bot solo reacciona a eventos nuevos (a confirmar al probar en un servidor de pruebas).

## Bienvenida

`services/welcome.ts`, disparada por `guildMemberAdd` y `guildMemberUpdate`.

- Mientras la persona no acepta las reglas, Discord la marca como `pending`. Al aceptarlas llega un `guildMemberUpdate` con `pending` pasando de `true` a `false`: ese es el momento del saludo.
- Si la persona entra sin `pending` (el servidor no exige reglas), se saluda en `guildMemberAdd`.
- Se ignoran los bots y los servidores distintos de `GUILD_ID`. Un conjunto en memoria evita el saludo doble si Discord repite el evento; tras un reinicio, un evento repetido podría saludar otra vez (es raro y inofensivo).
- El mensaje menciona solo a la persona (`allowedMentions`). El texto está en `messages.ts`.

## Log de entradas y salidas

`services/memberLog.ts`. Publica un embed en el canal de logs.

- **Entrada**: miembro, ID, antigüedad de la cuenta e invitación usada.
- **Salida**: miembro, ID, desde cuándo estaba y roles.
- **Invitación usada**: Discord no la informa al entrar. Rakim guarda en memoria los usos de cada invitación y, en cada entrada, vuelve a leerlos y compara (`lib/invites.ts`):
    - Si el contador de una invitación subió, esa es (también una creada y usada entre las dos lecturas).
    - Si una invitación desapareció y estaba a un uso de su límite, también (Discord borra las que se agotan).
    - Si subieron varias, o ninguna, el log lo dice ("no se pudo determinar") en vez de adivinar.
- Las entradas se procesan en cola, de una en una, para que cada comparación parta de la anterior.
- `INVITE_LABELS` asigna nombres legibles a los códigos (por ejemplo, la invitación oficial del sitio y la que gestiona Disboard).

### Límites conocidos

- Con la invitación vanity, flujos de OAuth o dos entradas casi simultáneas, el resultado puede ser "no se pudo determinar".
- Si el bot estuvo apagado, las entradas de ese período no se registran.
- El log no distingue entre salida voluntaria, expulsión y ban.

## Recordatorio de bump

`services/bump.ts` y `lib/bump.ts`. Rakim no ejecuta `/bump` (un bot no puede invocar los comandos de otro, y automatizarlo con una cuenta de usuario incumple los términos de Discord): solo recuerda.

1. Llega un mensaje del bot de Disboard (`DISBOARD_BOT_ID`) cuyo texto o embed coincide con `BUMP_SUCCESS_PATTERN`. La respuesta de "espera X minutos" no coincide, así que no reinicia el temporizador.
2. `BumpReminder` guarda `dueAt = ahora + enfriamiento` en `data/state.json` y arma un temporizador.
3. Al vencer, borra `dueAt` y publica el aviso en el canal de bump, mencionando `BUMP_ROLE_ID` si existe.
4. Al arrancar, retoma un aviso pendiente. Si venció con el bot apagado, avisa de inmediato (una sola vez).

Un bump nuevo reemplaza al aviso pendiente. Si el envío falla, el aviso no se reintenta (se registra el error).

## Estado

`lib/state.ts`. Un archivo JSON con el aviso de bump pendiente. Los cambios se aplican en memoria al instante y se escriben en disco con un archivo temporal y un renombrado, encolados para no pisarse; un fallo al guardar se registra y no frena las escrituras siguientes. Solo lo usa un proceso. El directorio `data/` no se sube al repo; en producción debe ser un volumen persistente.

## Configuración y textos

- **Entorno** (`config.ts`): token, IDs de servidor, canales y rol, y parámetros del bump. Se validan con `zod` al arrancar: si falta algo o está mal, el proceso termina con todos los errores a la vez. `.env.example` las lista con su explicación; `.env` no se sube al repo.
- **Textos** (`messages.ts`): el mensaje de bienvenida, el aviso de bump y los textos de los embeds del log. Cambiar el tono no toca la lógica.
