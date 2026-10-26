# Arquitectura

Un solo proceso de Python mantiene una conexión permanente (_gateway_) con Discord y reacciona a eventos. No hay servidor HTTP ni base de datos. Cada módulo de `rakim/events/` atiende un evento; la lógica con reglas vive en módulos que se prueban sin Discord.

```text
Discord gateway ── RakimBot (bot.py) ── events/
                                         ├─ ready          → lee invitaciones, retoma el aviso de bump
                                         ├─ member_join    → log de entrada (invites.py) y saludo (welcome.py)
                                         ├─ member_update  → saludo cuando termina la pantalla de reglas
                                         ├─ member_remove  → log de salida
                                         └─ message        → detecta el bump (bump.py) ── state.py
```

## Intents

Un intent le dice a Discord qué eventos enviar. Se piden solo los que las tres funciones necesitan:

| Intent            | Privilegiado | Para qué                                                    | Sin él                                                                              |
| :---------------- | :----------- | :---------------------------------------------------------- | :---------------------------------------------------------------------------------- |
| `guilds`          | No           | Conocer el servidor, sus canales y roles                    | Todo falla                                                                          |
| `members`         | **Sí**       | Entradas, salidas y fin de la pantalla de reglas (`pending`) | No hay log ni saludo                                                                |
| `guild_messages`  | No           | Ver los mensajes de los canales                             | No ve la respuesta de Disboard                                                      |
| `message_content` | **Sí**       | Leer el texto y los embeds de mensajes de otros bots        | Discord los entrega vacíos: no se distingue un bump exitoso del aviso de «espera»   |

Los dos privilegiados se activan en el portal de desarrolladores (Bot > Privileged Gateway Intents) y no exigen verificación con menos de 100 servidores.

**Descartados**: `guild_invites` (solo avisa cuando se crea una invitación; Rakim lee las invitaciones por la API en cada entrada), mensajes directos, presencias y voz.

## Permisos en el servidor

Se invita con `permissions=19488`:

| Permiso            | Para qué                                                                                 |
| :----------------- | :--------------------------------------------------------------------------------------- |
| Ver canales        | Llegar a los canales de bienvenida, logs y bump, y recibir los mensajes de Disboard      |
| Enviar mensajes    | Saludar, registrar y recordar                                                            |
| Insertar enlaces   | Los embeds del log                                                                       |
| Gestionar servidor | Leer las invitaciones y sus usos (no hay otra forma). Sensible: solo para el rol de Rakim |

El canal de logs es privado: el rol de Rakim necesita acceso explícito. Si hay `BUMP_ROLE_ID`, ese rol debe ser mencionable (así no hace falta el permiso de mencionar todos los roles). No se pide «Leer el historial» porque el bot solo reacciona a eventos nuevos (a confirmar en un servidor de pruebas).

## Bienvenida

`welcome.py`, desde `member_join` y `member_update`. Mientras la persona no acepta las reglas, Discord la marca `pending`; al aceptarlas llega un `member_update` con `pending` pasando de `True` a `False`, y ese es el momento del saludo. Si el servidor no exige reglas, se saluda al entrar. Se ignoran los bots, y un conjunto en memoria evita el saludo doble. El mensaje menciona solo a la persona.

## Log de entradas y salidas

Un embed en el canal de logs. La entrada muestra miembro, ID, antigüedad de la cuenta e **invitación usada**; la salida, desde cuándo estaba y sus roles.

Discord no informa la invitación usada, así que `invites.py` la deduce: en cada entrada Rakim vuelve a leer los usos y compara con la lectura anterior. Si el contador de una subió (también una creada y usada entre las dos lecturas), esa es; si una desapareció y estaba a un uso de su límite (Discord borra las que se agotan), también. Con varias candidatas o ninguna, el log dice «no se pudo determinar» en vez de adivinar. Las entradas se procesan de una en una. `INVITE_LABELS` da nombres legibles a los códigos.

**Límites**: con la invitación vanity, flujos de OAuth o dos entradas casi simultáneas puede no determinarse; las entradas con el bot apagado no se registran; el log no distingue salida voluntaria, expulsión y ban.

## Recordatorio de bump

`bump.py`. Llega un mensaje del bot de Disboard (`DISBOARD_BOT_ID`) cuyo texto o embed coincide con `BUMP_SUCCESS_PATTERN`; la respuesta de «espera X minutos» no coincide, así que no reinicia nada. `BumpReminder` guarda `bump_due_at` en el estado y arma una tarea que, al vencer, borra el estado y publica el aviso en el canal de bump (mencionando `BUMP_ROLE_ID`, si existe). Un bump nuevo reemplaza al pendiente. Al arrancar retoma un aviso pendiente; si venció con el bot apagado, avisa al instante, una sola vez. Si el envío falla, no se reintenta (se registra el error).

## Estado y configuración

- **Estado** (`state.py`): un JSON con `bump_due_at`, escrito a un archivo aparte y renombrado para que un corte no lo deje a medias. `data/` no se sube al repo; en producción es un volumen.
- **Configuración** (`config.py`): variables de entorno (o `.env`) validadas al arrancar; si falta algo, el proceso termina listando todos los problemas. `.env.example` explica cada una.
- **Textos** (`messages.py`): bienvenida, aviso de bump y embeds del log.
