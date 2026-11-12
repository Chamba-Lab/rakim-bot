# Arquitectura

Un solo proceso de Python mantiene una conexión permanente (_gateway_) con Discord y reacciona a eventos. No hay servidor HTTP ni base de datos. Cada módulo de `rakim/events/` atiende un evento; la lógica con reglas vive en módulos que se prueban sin Discord.

```text
Discord gateway ── RakimBot (bot.py) ── events/
                                         ├─ ready          → lee invitaciones, comprueba permisos (health.py), retoma el aviso de bump
                                         ├─ member_join    → log de entrada (invites.py) y saludo (welcome.py)
                                         ├─ member_update  → saludo cuando termina la pantalla de reglas
                                         ├─ member_remove  → log de salida
                                         ├─ stats          → `/invitaciones`: entradas por invitación
                                         ├─ members        → `/miembros`: miembros por país, etapa y notificaciones (members.py)
                                         ├─ status         → `/estado`: permisos, canales e invitaciones
                                         ├─ roulette       → `/ruleta`: un tema al azar (roulette.py)
                                         ├─ daily_topic    → el tema del día en general y `/tema` (daily_topic.py) ── state.py
                                         ├─ command_error  → registra los fallos de comandos
                                         └─ message        → detecta el bump (bump.py) ── state.py
                                                            y el mensaje nativo de entrada (welcome.py)
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

**Mencionar @everyone, @here y todos los roles**, solo como permiso del canal general y solo si el tema del día menciona un rol (`DAILY_TOPIC_ROLE_ID`): Discord no tiene un permiso para mencionar un rol concreto. No va en `19488` ni a nivel de servidor. El código igual limita cada envío con `AllowedMentions` al rol configurado, así que nunca sale un `@everyone`.

El canal de logs es privado: el rol de Rakim necesita acceso explícito. Si hay `BUMP_ROLE_ID` (o `BUMP_USER_ID`, para mencionar a una persona), ese rol debe ser mencionable (así no hace falta el permiso de mencionar todos los roles). No se pide «Leer el historial» porque el bot solo reacciona a eventos nuevos (a confirmar en un servidor de pruebas).

## Bienvenida

`welcome.py`, desde `member_join` y `member_update`. Mientras la persona no acepta las reglas, Discord la marca `pending`; al aceptarlas llega un `member_update` con `pending` pasando de `True` a `False`, y ese es el momento del saludo. Si el servidor no exige reglas, se saluda al entrar. Se ignoran los bots, y un conjunto en memoria evita el saludo doble. El mensaje menciona solo a la persona.

**Orden con el mensaje nativo.** Discord publica su mensaje de entrada («X ha entrado») unos segundos después de `member_update`; si el bot saludara al instante, su saludo saldría antes y la mención podría no resolverse en el cliente de quien entra. Con `WELCOME_WAIT_SYSTEM_MESSAGE=true` (por defecto), `greet_in_order` espera ese mensaje (`MessageType.new_member` en el canal de `WELCOME_CHANNEL_ID`, que debe ser también el canal de mensajes del sistema del servidor) hasta 10 s y, tras él (o al vencer el plazo), deja una pausa de 2,5 s antes de saludar: así quien entra termina de cargar el servidor y la notificación le llega bien. Con `false` (mensajes nativos desactivados) no hay nada que esperar y se aplica una pausa fija de 5 s. El saludo es un mensaje normal, no una respuesta.

## Log de entradas y salidas

Un embed en el canal de logs. La entrada muestra miembro, ID, antigüedad de la cuenta e **invitación usada**; la salida, desde cuándo estaba y sus roles.

Discord no informa la invitación usada, así que `invites.py` la deduce: en cada entrada Rakim vuelve a leer los usos y compara con la lectura anterior. Si el contador de una subió (también una creada y usada entre las dos lecturas), esa es; si una desapareció y estaba a un uso de su límite (Discord borra las que se agotan), también. Con varias candidatas o ninguna, el log dice «no se pudo determinar» en vez de adivinar. Las entradas se procesan de una en una. `INVITE_LABELS` da nombres legibles a los códigos.

**Entradas por invitación.** `@Rakim invitaciones` o `/invitaciones` (un comando híbrido, módulo `stats`) lee los usos de las invitaciones en ese momento y los suma por nombre de `INVITE_LABELS` (varios códigos con el mismo nombre se agrupan). La respuesta es un embed con una tabla de barras (conteo y porcentaje por fuente, total y alcance). Por defecto cuenta solo las registradas en `INVITE_LABELS`; con `todas` (o `all`) cuenta también las demás, por su código. Solo responde en `LOG_CHANNEL_ID` o `BUMP_CHANNEL_ID` (así no ensucia el canal de logs) y solo a quien tiene Gestionar servidor, en las dos formas; en otro canal o sin el permiso, con `/` avisa solo a quien lo usó y con mención no responde. El contador es el de Discord: acumulado, incluye a quienes ya salieron, y no guarda historial propio. La forma con mención usa el prefijo y el intent `message_content` ya existentes. La forma `/` exige el alcance `applications.commands` al invitar al bot (no pide permisos nuevos en el servidor) y se publica solo en `GUILD_ID` al arrancar; si falla, se registra y la mención sigue funcionando.

**Límites**: con la invitación vanity, flujos de OAuth o dos entradas casi simultáneas puede no determinarse; las entradas con el bot apagado no se registran; el log no distingue salida voluntaria, expulsión y ban.

## Miembros por país, etapa y notificaciones

`@Rakim miembros` o `/miembros` (módulo `members`) cuenta a los miembros actuales según los roles de las preguntas del Onboarding: país (`COUNTRY_ROLE_IDS`, pregunta opcional) y etapa (`STAGE_ROLE_IDS`, obligatoria) y notificaciones (`NOTIFICATION_ROLE_IDS`: Avisos, Eventos y Actividades; opcional y de selección múltiple). Responde un embed con una tabla de barras por cada uno, de mayor a menor, con los roles en 0 y una fila para quien no tiene ninguno: «Sin responder» (quien saltó la pregunta o entró antes de que existiera) o, en notificaciones, «Ninguna». El porcentaje es sobre el total de miembros contados, no sobre la suma de filas: en notificaciones alguien puede tener varios roles y las filas pueden sumar más que el total (el título de la sección lo aclara). No cuenta bots ni a quien aún no acepta las reglas (`pending`). El nombre de cada fila es el del rol en Discord.

Lee la lista de miembros que el intent `members` ya mantiene en memoria: no hace llamadas a la API ni pide permisos nuevos, y no guarda historial. Mismas restricciones que `/invitaciones` (canal de logs o de bump, Gestionar servidor). Es un comando aparte de `/invitaciones` porque cuentan cosas distintas: miembros actuales frente al acumulado de Discord. Una sección sin roles configurados dice «Sin configurar»; un ID que no existe se omite y lo señalan la comprobación inicial y `/estado`. El cálculo (`members.py`) se prueba sin Discord.

## Estado y comprobación inicial

`health.py` revisa, sin hablar con Discord, lo que Rakim necesita: el permiso Gestionar servidor; en cada canal configurado, ver el canal y, donde escribe, enviar mensajes e insertar enlaces; que cada rol de `COUNTRY_ROLE_IDS`, `STAGE_ROLE_IDS` y `NOTIFICATION_ROLE_IDS` exista, y que cada código de `INVITE_LABELS` coincida con una invitación existente (un código mal escrito es el fallo más fácil de pasar por alto). Se usa en dos sitios:

- **Al arrancar** (`ready`): si algo falla, lo registra en el log y publica el resultado en el canal de logs. Si todo está en orden, solo una línea en el log.
- **`/estado`** (o `@Rakim estado`): la misma comprobación con datos frescos, más la latencia, desde cuándo está activo y el próximo bump. Mismas restricciones que `/invitaciones`; con `/` la respuesta es efímera.

## Ruleta

`roulette.py` y el comando `/ruleta [tema]`. Los temas están en `rakim/roulette.json`, una copia de los `presets` de `src/content/roulette.json` de `Chamba-Lab/home` (8 grupos, 108 temas). Sin `tema` sale uno de todos; con `tema`, del grupo elegido (con `/` el menú ofrece los grupos; con mención se acepta el id o parte del nombre). No repite el último tema que salió en ese canal. Funciona en cualquier canal y para cualquiera, con un enfriamiento de 15 s por canal. No usa permisos ni intents nuevos.

## Tema del día

`daily_topic.py` y el módulo `events/daily_topic`. A las horas de `DAILY_TOPIC_TIMES` (de Lima, UTC-5 fijo: Perú no tiene horario de verano; en la comunidad, una vez al día a las 18:00), Rakim publica en el canal general (`WELCOME_CHANNEL_ID`) una línea con la mención al rol de `DAILY_TOPIC_ROLE_ID` (si existe) y el tema como título de un embed amarillo, con el grupo en el pie (el título no repite «Tema del día», que ya dice la línea). Los temas salen de los grupos de `DAILY_TOPIC_PRESETS` (por defecto Empleabilidad, Rompehielos y Día a día: 36 temas).

- **Ciclo propio**: no repite un tema hasta haber usado todos, y al empezar otra vuelta no repite el último. Es independiente de `/ruleta`. Los temas usados se guardan por texto en el estado, así que sobreviven a un reinicio; al copiar un `roulette.json` nuevo, los temas nuevos entran al ciclo y los borrados se olvidan.
- **A mano con `/tema`** (o `@Rakim tema`): publica ya el siguiente tema del mismo ciclo. Mismas restricciones que `/estado` (canal de logs o de bump, Gestionar servidor); el tema sale en el general y, con `/`, la confirmación es efímera. No reemplaza ni mueve el automático: solo gasta un tema, y el de la hora programada trae otro. Un candado evita que, si coinciden, los dos elijan el mismo tema. Funciona aunque `DAILY_TOPIC_TIMES` esté vacío.
- **Sale siempre a su hora**: no se mira si hubo conversación. Si el bot está apagado a esa hora, ese día no hay tema (no se envía tarde). Un envío fallido se registra y no gasta el tema.
- Con `DAILY_TOPIC_TIMES` vacío la función está apagada. Una hora o un grupo mal escritos hacen fallar el arranque, como el resto de la configuración.
- La comprobación inicial y `/estado` revisan, si la función está activa, que Rakim pueda insertar enlaces en general y que el rol exista y se pueda mencionar ahí.
- Usa `discord.ext.tasks` (el loop atrapa sus errores: uno sin capturar lo detendría hasta el próximo reinicio). Sin intents nuevos.

## Recordatorio de bump

`bump.py`. Llega un mensaje del bot de Disboard (`DISBOARD_BOT_ID`) cuyo texto o embed coincide con `BUMP_SUCCESS_PATTERN`; la respuesta de «espera X minutos» no coincide, así que no reinicia nada. `BumpReminder` guarda `bump_due_at` en el estado y arma una tarea que, al vencer, borra el estado y publica el aviso en el canal de bump (mencionando `BUMP_ROLE_ID`, si existe). Un bump nuevo reemplaza al pendiente. Al arrancar retoma un aviso pendiente; si venció con el bot apagado, avisa al instante, una sola vez. Si el envío falla, no se reintenta (se registra el error).

## Estado y configuración

- **Estado** (`state.py`): un JSON con `bump_due_at` y `used_topics` (los temas del día del ciclo actual), escrito a un archivo aparte y renombrado para que un corte no lo deje a medias. `data/` no se sube al repo; en producción es un volumen.
- **Configuración** (`config.py`): variables de entorno (o `.env`) validadas al arrancar; si falta algo, el proceso termina listando todos los problemas. `.env.example` explica cada una.
- **Textos** (`messages.py`): bienvenida, aviso de bump, tema del día, embeds del log y de los comandos.
