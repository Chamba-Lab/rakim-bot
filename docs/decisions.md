# Decisiones clave

Solo las que un contribuidor o agente podría deshacer sin saberlo. Si cambias una, actualiza la entrada en el mismo PR.

## Producto

- **Recordar el bump, no ejecutarlo.** Un bot no puede invocar los comandos de otro, y hacerlo con una cuenta de usuario (_self-bot_) incumple los términos de Discord y arriesga la cuenta. Rakim detecta el bump de Disboard y avisa a las 2 horas.
- **Saludo en el canal general, no por mensaje directo.** El mensaje directo parece invasivo y falla con los DM cerrados. Se puede reevaluar.
- **El saludo sale al terminar la pantalla de reglas, no al entrar.** Antes la persona no puede escribir (`pending`). El Onboarding ya cubre la guía de los primeros días (no hay canal de bienvenida aparte), así que el saludo la complementa.
- **El saludo espera al mensaje nativo de entrada de Discord, con plazo.** Sin la espera, el saludo salía antes del «X ha entrado» y la mención no se mostraba bien a la persona. Se espera ese mensaje hasta 10 s y se saluda aunque no llegue, para no perder nunca el saludo. Tras el mensaje nativo hay una pausa de 2,5 s: saludando justo después, la notificación llegaba mientras la persona aún cargaba el servidor. `WELCOME_WAIT_SYSTEM_MESSAGE=false` es para cuando se desactiven los mensajes nativos: en vez de esperarlos, una pausa fija de 5 s evita el mismo adelanto. No quitar la espera ni la pausa sin verificarlo en Discord.
- **La invitación usada va solo en el log privado.** Hay dos invitaciones: la que Disboard gestiona y la oficial del sitio y las redes (`chambalab.org/discord`). Distinguirlas ya indica de dónde llega la gente.
- **Copy neutro en español**, con la voz de Rakim (ver `AGENTS.md`).
- **Tema del día: una vez al día, a las 12:00 de Lima, todos los días** (12 nov 2026; antes, 18:00). Empezó como dos al día y se bajó a uno para no llenar de notificaciones a una comunidad pequeña que también recibirá otras actividades. Se movió de 18:00 a 12:00 porque la noche ya es la hora con más conversación, y el tema sirve más para animar el canal cuando está quieto: así sigue vivo toda la tarde y quien entra en la noche lo encuentra con respuestas. El horario laboral pesa poco, porque la mayoría es de perfil Early Career (estudiantes, o gente que trabaja en remoto con Discord abierto de día). A las 12:00 es buena hora en todos los países (11:00 en México, 14:00 en Argentina, 18:00 en España, 19:00 en su verano); a las 18:00 a España le llegaba a medianoche. Se revisa hacia el 26 nov comparando respuestas. La hora vive en `DAILY_TOPIC_TIMES`.
- **El tema sale siempre, sin mirar si hubo conversación.** Vigilar la actividad del canal se descartó por innecesario: con un tema al día no interrumpe, y alguien del equipo ve en el canal cuándo salió y cuándo no.
- **Grupos del tema del día: Empleabilidad, Rompehielos y Día a día & Aprendizaje.** Preguntas que cualquiera responde, sin importar su nivel. Quedan fuera IA & Futuro (de nicho), Debates, Dilemas y Mid & Senior (piden experiencia o temas avanzados) y «Qué Aprender (Early Career)», que son títulos y no preguntas. Día a día se creó para esto en el sitio (`Chamba-Lab/home#126`).
- **`/tema` para lanzarlo a mano, sin tocar el programado.** Lo usa quien tiene Gestionar servidor, como los demás comandos del equipo (no una persona concreta: así no hay que cambiar la configuración si cambia quién lo usa). Comparte el ciclo del automático, pero no lo reemplaza ni lo mueve: gasta un tema y el de las 12:00 sale igual, con otro. Que el manual reemplazara al del día exigía guardar la fecha del último envío, y no hacía falta.
- **Ciclo del tema del día independiente de `/ruleta`.** Lo que sale con `/ruleta` no gasta temas del ciclo diario, y `/ruleta` sigue evitando solo repetir el último.

## Stack

- **Python 3.14, no 3.13.** El 25 oct 2026 salieron las versiones de seguridad 3.14.10, 3.13.18 y 3.12.16 (tarfile, zipfile, ssl, Expat y desconfianza de una CA intermedia, entre otros CVE). Rakim no extrae archivos ni procesa XML, así que la exposición es baja, pero se parchea igual. 3.13 ya solo recibe correcciones de seguridad (sin instaladores) y 3.14 tiene soporte completo, así que un proyecto nuevo arranca en 3.14. Se probó con las dependencias: todas tienen ruedas para 3.14 y los 31 tests y `mypy --strict` pasan. La imagen de producción (`python:3.14-slim`) trae 3.14.10 y el Dockerfile falla si trae menos (ver `deployment.md`). `discord.py` no declara oficialmente 3.13 ni 3.14, pero funciona.
- **Buenas prácticas aplicadas (2026):** secretos como `SecretStr` (no salen en logs ni en `repr`); `uv.lock` con hashes, instalado con `--frozen`; `pip-audit` de las dependencias en cada PR; `ruff` con reglas de seguridad (bandit) y `mypy --strict`; permisos y menciones mínimos; contenedor sin root, de solo lectura y sin capacidades extra; acciones de GitHub fijadas por SHA con permisos de solo lectura.
- **Python con `discord.py`** (cambio del 26 oct 2026; la primera versión estaba en TypeScript). El bot rehecho tiene ~520 líneas frente a ~910, menos archivos de configuración y una imagen Docker de una sola etapa. El costo del cambio fue bajo porque el bot aún no se había fusionado. Aunque `home` usa Node, el bot es otro proyecto con otro ciclo de vida.
- **Estructura por evento** (`rakim/events/`), con la extensión `setup(bot)` de `discord.py`. Sin capas intermedias: un evento llama a la función que necesita.
- **Todos los textos en `messages.py`.** Ajustar el tono no debe exigir tocar la lógica.
- **Config por entorno con `pydantic-settings`.** Un error se descubre al arrancar, con todos los problemas listados. Los IDs y el token son del despliegue, no del repo.
- **El estado es un JSON, no SQLite.** Debe sobrevivir a un reinicio el momento del aviso de bump y, desde el tema del día, la lista de temas usados del ciclo (como mucho, unos cien textos). Sigue siendo pequeño y se escribe una vez al día; se cambia por SQLite si el bot llega a guardar bastante más.
- **Hora de Lima como UTC-5 fijo**, no con `zoneinfo`: Perú no tiene horario de verano, y así no se depende de que la imagen traiga la base de zonas horarias.
- **Comandos híbridos desde la versión 1** (`/comando` y `@Rakim comando`). La v0 solo reaccionaba a eventos. Se agregaron comandos de consulta y de ambiente, no de moderación. Se ejecutan por el gateway que ya usa el bot, no por el endpoint HTTP de interacciones (el del ejemplo de Supabase no entrega entradas, salidas ni mensajes). Los `/` se publican solo en `GUILD_ID` al arrancar y requieren el alcance `applications.commands` al invitar al bot.
- **Los comandos del equipo (`invitaciones`, `miembros`, `estado`, `tema`) responden solo en el canal de logs y el de bump, y solo a quien tiene Gestionar servidor**, en las dos formas. El canal de bump es más visible que el de logs: por eso el permiso se comprueba también con mención y no solo con el filtro del `/`.
- **`/ruleta` sin restricción de canal ni de rol**, con un enfriamiento de 15 s por canal. Es contenido público pensado para animar cualquier conversación; el enfriamiento evita que llene un canal. Los temas son una copia de `src/content/roulette.json` del sitio, dentro del bot (`rakim/roulette.json`): sin consultar el sitio en línea no hay dependencia de red ni de un tercero al responder. Al cambiar los temas en el sitio, se vuelve a copiar.
- **`/miembros` es un comando aparte de `/invitaciones`** (11 nov 2026). Cuenta a los miembros actuales por los roles del Onboarding, mientras que `invitaciones` usa el acumulado de Discord (incluye a quienes salieron): juntos confundirían qué significa cada número. Muestra una tabla por pregunta en un solo embed, sin bots ni quien aún no acepta las reglas, y el porcentaje va sobre el total de miembros.
- **`/miembros` lee el Onboarding de Discord, sin configuración** (11 nov 2026). La primera versión pedía copiar a mano los IDs de los roles a variables de entorno: 14 IDs, tedioso y fácil de desactualizar. Leyendo las preguntas en cada uso, el comando sigue al Onboarding solo, y cada opción se cuenta por su rol propio (sin el que dan todas, como Member). La duda inicial (atarse al texto de la pregunta) no aplica: se recorren todas las preguntas que dan roles, sin buscar ninguna por su texto. `todos` agrega cada rol del servidor para lo que no viene del Onboarding.
- **`/estado` es efímero con `/`** y la comprobación inicial solo escribe en el canal de logs si hay algo que corregir: un arranque sano no genera ruido.
- **Sin comando `help`**: el de discord.py respondería a cualquiera que mencione al bot y listaría los comandos del equipo.

## Discord

- **Cuatro intents, dos privilegiados** (`architecture.md`). No se pide `guild_invites`: Rakim lee las invitaciones por la API en cada entrada.
- **`message_content`**: sin él, Discord entrega vacíos el texto y los embeds de otros bots y no se distingue un bump exitoso del aviso de «espera».
- **El patrón de bump es configurable** (`BUMP_SUCCESS_PATTERN`, por defecto `bump done`). Verificado el 26 oct 2026 con una captura real: Disboard responde al `/bump` con un embed titulado «DISBOARD: The Public Server List» cuya descripción empieza con «Bump done! 👍». Es configurable porque Disboard puede cambiar el texto o responder en otro idioma.
- **Permisos mínimos `19488`**: Ver canales, Enviar mensajes, Insertar enlaces y Gestionar servidor. Nada de Administrador ni Leer el historial.
- **«Mencionar @everyone, @here y todos los roles» solo en el canal general** (11 nov 2026, para el tema del día). Discord no permite mencionar un rol concreto sin ese permiso, salvo que el rol sea mencionable por cualquiera, y eso dejaría a cualquiera notificar a todo el rol de Actividades. Se da por canal y no en el servidor, y deja la puerta abierta a otras funciones que mencionen roles. El riesgo de un `@everyone` lo cubre el código: el bot no menciona a nadie por defecto y cada envío permite solo el rol que necesita. El aviso de bump sigue con su rol mencionable.
- **El bot opera solo en `GUILD_ID`** e ignora cualquier otro servidor.

## Hosting y CI/CD

- **Host: un Droplet de DigitalOcean de US$4/mes (US$48 al año).** Criterios: costo anual bajo y una marca conocida. El bot necesita una conexión permanente, así que se descartó todo lo _serverless_ o que se duerme. Evaluado el 26 oct 2026 con los precios oficiales (cambian a menudo: confirmarlos al contratar):
    - **Supabase** (funciones de 150 a 400 s; los proyectos gratis se pausan) y **Cloudflare Workers**: no sirven. Cloudflare Containers cobra por uso (~US$9.5/mes estimados) y su `sleepAfter` desconecta el bot.
    - **Render** (~US$7/mes el worker) y **Railway** (US$5/mes): funcionan, cuestan más o igual.
    - **Fly.io** (~US$28/año): el más barato de los gestionados; descartado por falta de confianza en la marca.
    - **Hostinger** (US$6.49 el primer plazo de 24 meses, renueva a ~US$11.99): más caro y con contrato largo.
    - **Google Cloud e2-micro «gratis»**: la IPv4 externa (US$0.005/h, ~US$44 al año, según fuentes secundarias) lo iguala a DigitalOcean con una VM más débil.
    - **Oracle Always Free**: reclama las VM con menos del 20 % de uso, justo el caso de este bot.
    - **Autohostear**: viable (el bot solo abre conexiones de salida) pero depende de la disponibilidad de una casa y de una persona.
- **Droplet y no App Platform** (~US$5/mes): no pude confirmar si ofrece disco persistente y cuesta más.
- **512 MiB con swap y Docker.** El bot ocupa unos 100 MB; el contenedor se limita a 256 MB y el servidor lleva 1 GB de swap. Si aparecen reinicios por memoria, se amplía a US$6 (1 GiB) sin reconstruir nada.
- **La imagen viaja por SSH (`docker save | docker load`), sin registro de imágenes.** Un registro obligaría a guardar credenciales en el servidor; para un solo servidor, enviarla directo es más simple. Si hay varios servidores, se cambia por un registro.
- **Llave de despliegue dedicada, con la huella del servidor fijada** (`StrictHostKeyChecking yes`): si cambia, el despliegue falla en vez de confiar a ciegas. El usuario `deploy` está en el grupo `docker` (equivale a root): por eso solo entra con llave y sin `sudo`.
- **`docker build --pull` en cada despliegue** trae el último parche de Python. Las dependencias salen del `uv.lock`, y el job `Dependency audit` avisa de vulnerabilidades conocidas.
- **El CI/CD del bot es propio, no el del sitio** (el sitio es estático en GitHub Pages; el bot es un proceso permanente). Comparten convenciones: Conventional Commits, PR a `master`, acciones fijadas por SHA.
- **El despliegue nace apagado.** `deploy.yml` solo corre si la variable de GitHub `DEPLOY_ENABLED` vale `true` (ambos jobs lo comprueban). Permite fusionar el PR del despliegue antes de tener el servidor, los secretos y el `.env`, y activarlo con un solo comando cuando todo esté listo, sin tocar código.
- **El despliegue se conserva aunque hoy el bot corra autoalojado.** Hoy se ejecuta a mano en un equipo propio (`compose`); `deploy.yml`, `deploy/` y `deployment.md` se mantienen apagados para cuando pase a un VPS, sin rehacer nada.
- **Un cambio solo de documentación no despliega** (`paths-ignore`).
- **El Dockerfile exige Python 3.14.10 o posterior** (`assert sys.version_info`) y uv no descarga otro Python (`UV_PYTHON_DOWNLOADS=never`): la imagen siempre usa el de la base, que `--pull` mantiene al día. Lo mismo en el CI con `setup-python`, porque los Python que descarga uv pueden ir días atrás de un parche. Al salir un parche de seguridad, se sube el mínimo del Dockerfile en el mismo PR.
- **Dependabot espera 7 días antes de proponer una versión nueva** (`cooldown`): la mayoría de los paquetes maliciosos se retiran en ese plazo. Las alertas de seguridad no esperan.
- **Sin alertas ni entorno de pruebas desplegado, por ahora.** `restart: unless-stopped` reinicia ante caídas y un despliegue fallido sale en rojo en Actions.

## Pendiente

- Crear el Droplet y hacer el primer despliegue (`deployment.md`). El script del servidor y los workflows están escritos pero sin probar contra un servidor real.
- Proteger `master` (`deployment.md`, sección 8); depende del plan de la organización.
- Verificar en un servidor de pruebas: el comportamiento de `pending`, los permisos y que el saludo salga después del mensaje nativo (también con `WELCOME_WAIT_SYSTEM_MESSAGE=false`).
- Texto final del mensaje de bienvenida y licencia del repositorio.
