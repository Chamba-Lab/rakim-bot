# Decisiones clave

Registro corto de las decisiones que condicionan el proyecto y el porqué. Solo entran las que un contribuidor o agente podría deshacer sin saberlo. Si cambias una, actualiza la entrada en el mismo PR.

## Producto

- **El bot recuerda el bump, no lo ejecuta.** Un bot no puede invocar los comandos de otro, y hacerlo con una cuenta de usuario (_self-bot_) incumple los términos de Discord y arriesga la cuenta. Rakim detecta el bump de Disboard y avisa a las 2 horas para que una persona ejecute `/bump`.
- **Bienvenida en el canal general, no por mensaje directo.** El mensaje directo se descartó por parecer invasivo y puede fallar si la persona tiene los DM cerrados. Se puede reevaluar más adelante.
- **El saludo sale al terminar la pantalla de reglas, no al entrar.** Mientras la persona está `pending` aún no puede escribir; saludarla antes sería hablarle a alguien que no puede responder. La documentación del equipo ya descartó un canal de bienvenida aparte (la Server Guide del Onboarding cubre la guía de los primeros días), así que el saludo la complementa y no la duplica. Quien administra desactiva el mensaje automático de llegada de Discord cuando el bot esté en producción.
- **La invitación usada va solo en el log privado, no en la bienvenida.** Hay dos invitaciones: la que Disboard crea y gestiona, y la oficial del sitio y las redes (`chambalab.org/discord`). Distinguir esas dos ya indica de dónde llega la gente; no hace falta más observabilidad por fuente.
- **Copy neutro en español, con la voz de Rakim.** Misma regla que el resto de la comunidad: sin jerga local ("Chamba" es la única excepción), tuteo y un solo emoji por mensaje. Rakim: breve, seca y algo gruñona, pero cálida.

## Stack

- **TypeScript con `discord.js`.** Es el stack del resto de la organización (Node y TypeScript) y `discord.js` es la biblioteca más usada. No es oficial: Discord no mantiene SDKs. Python con `discord.py` también servía, pero partía el tooling en dos.
- **El CI/CD del bot es propio, no el del sitio.** El sitio es una web estática que se compila y se publica en GitHub Pages; el bot es un proceso permanente que se despliega en un servidor. Los dos comparten convenciones (Conventional Commits, PR a `master`, lint y tests, acciones fijadas por SHA), no el pipeline.
- **Zod valida la configuración.** Un error de configuración se descubre al arrancar, con todos los problemas listados, no cuando un evento llega a un canal que no existe.
- **Sin comandos slash en la v0.** El bot solo reacciona a eventos, así que no necesita registrar comandos ni el intent de interacciones.
- **El código se organiza por evento de Discord (`src/events/`).** Es la convención de la guía de `discord.js` y encaja con un bot que solo reacciona. Una organización por función habría obligado a que dos funciones escucharan el mismo evento (`guildMemberAdd` lo usan el log y el saludo; `clientReady`, el log y el bump). Ahora cada evento es un archivo corto que filtra el servidor y llama a un servicio; la lógica con reglas vive en `lib/`, sin Discord, para probarla sola.
- **Todos los textos del bot en `src/messages.ts`.** Ajustar el tono o la redacción no debe exigir tocar la lógica ni buscar cadenas repartidas. Los IDs y el token, en cambio, son del despliegue y vienen del entorno, no de un archivo del repo.
- **Los errores de un evento no tumban el proceso.** `registerEvents` envuelve cada evento en un `try/catch` que registra el fallo. Los servicios dejan subir el error en vez de tragarlo, para que haya un solo lugar donde se registra.

## Hosting y CI/CD

- **Host: un Droplet de DigitalOcean de US$4/mes (US$48 al año).** Criterios: costo anual bajo y una marca que el equipo reconoce. El bot necesita una conexión permanente con Discord, así que se descartó todo lo _serverless_ o que se duerme. Evaluado el 26 oct 2026 con los precios de las páginas oficiales (varios cambian con frecuencia: confirmarlos al contratar):
    - **Supabase** (funciones de 150 a 400 s; los proyectos gratis se pausan) y **Cloudflare Workers** (sin conexión de gateway fiable): no sirven. Cloudflare Containers cobra por uso (~US$9.5/mes estimados) y su `sleepAfter` desconecta el bot.
    - **Render** (~US$7/mes el worker, sin plan gratis para workers) y **Railway** (US$5/mes): funcionan, cuestan más o igual.
    - **Fly.io** (~US$28/año): el más barato de los gestionados, descartado por falta de confianza en la marca.
    - **Hostinger** (US$6.49 el primer plazo de 24 meses y renueva a ~US$11.99): más caro y con contrato largo.
    - **Google Cloud e2-micro «gratis»**: la IPv4 externa (US$0.005/h, ~US$44 al año, según fuentes secundarias) lo iguala a DigitalOcean con una VM más débil.
    - **Oracle Always Free**: reclama las VM con menos del 20 % de uso, justo el caso de un bot liviano.
    - **Autohostear**: viable técnicamente (el bot solo abre conexiones de salida) pero se descartó por disponibilidad y por atar el bot a la conexión de una persona.
- **Droplet y no App Platform.** App Platform (~US$5/mes) simplificaba el despliegue, pero no pude confirmar si ofrece disco persistente y cuesta más que el Droplet. El estado del bot cabe en un volumen de Docker.
- **512 MiB con swap y Docker.** El bot ocupa ~100–130 MB; el contenedor se limita a 256 MB y el servidor lleva 1 GB de swap. Si aparecen reinicios por memoria, se amplía el Droplet a US$6 (1 GiB) sin reconstruir nada.
- **La imagen viaja por SSH (`docker save | docker load`), sin registro de imágenes.** Un registro (GitHub Container Registry o DigitalOcean) obligaría a guardar credenciales en el servidor o a usar un token con permisos de lectura; para una imagen de un solo servidor, enviarla directamente es más simple y no suma superficie de ataque. Si algún día hay varios servidores, se cambia por un registro.
- **Llave de despliegue dedicada con la huella del servidor fijada.** `DEPLOY_KNOWN_HOSTS` se verifica contra la consola web del Droplet, y `StrictHostKeyChecking yes` hace fallar el despliegue si la huella cambia, en vez de confiar a ciegas. El usuario `deploy` pertenece al grupo `docker` (equivale a root en el servidor): por eso solo entra con llave y sin `sudo`.
- **Node 24 en el contenedor.** Es la línea con soporte hasta abril de 2028. `docker build --pull` en cada despliegue trae el último parche de la imagen base, y `engine-strict` en `.npmrc` hace fallar `npm ci` si la imagen trae una versión sin el parche de octubre de 2026.
- **Un cambio solo de documentación no despliega.** Evita reiniciar el bot sin motivo (`paths-ignore` en `deploy.yml`).
- **Sin alertas ni entorno de pruebas desplegado, por ahora.** `restart: unless-stopped` reinicia ante caídas y un despliegue fallido sale en rojo en Actions. Se suma monitoreo cuando haya un motivo.

## Entorno

- **Node.js: solo versiones con el parche de octubre de 2026.** El 21 de octubre de 2026 Node publicó 22.23.4, 24.22.1 y 26.12.1, que corrigen 10 CVE; el más grave es un fallo en el decodificador Brotli de `node:zlib` (CVE-2026-111497) que permite ejecución remota de código. `engines` exige esas versiones o posteriores (`^22.23.4 || ^24.22.1 || >=26.12.1`), así que una instalación con 24.22.0, por ejemplo, avisa. Rakim no descomprime datos de terceros con `zlib`, pero el `fetch` integrado sí decodifica Brotli, y el fallo vive en Node, no en `discord.js`: se actualiza el runtime, no una dependencia. Una versión nueva de seguridad sube el mínimo en `package.json`, `README.md`, `AGENTS.md`, `CONTRIBUTING.md` y `PROJECT.yaml` en el mismo PR.
- **Líneas de Node soportadas** (calendario oficial de nodejs/Release, consultado el 26 oct 2026): 22 en mantenimiento hasta el 30 abr 2027; 24 en mantenimiento desde el 20 oct 2026 hasta el 30 abr 2028; 26 pasa a LTS el 28 oct 2026 y llega hasta el 30 abr 2029.

## Estado y datos

- **El estado vive en un archivo JSON, no en SQLite.** El único dato que debe sobrevivir a un reinicio es el momento del próximo aviso de bump. Un archivo evita una dependencia nativa y alcanza para un solo proceso. Se reemplaza por SQLite cuando haya más estado (por ejemplo, para deduplicar saludos entre reinicios o guardar historial); `StateStore` es el único punto que habría que tocar.
- **El caché de invitaciones solo vive en memoria.** Se reconstruye al arrancar leyendo las invitaciones del servidor. Las entradas ocurridas con el bot apagado no se registran.

## Discord

- **Cuatro intents, dos de ellos privilegiados.** `Guilds`, `GuildMembers`, `GuildMessages` y `MessageContent`; la tabla con el porqué de cada uno está en `architecture.md`. No se pide `GuildInvites`: solo sirve para escuchar la creación de invitaciones, y Rakim lee las invitaciones por la API en cada entrada (una invitación creada y usada entre dos lecturas se detecta igual). Quitarlo evita un evento más y un intent más que explicar.
- **Se pide `MessageContent`.** Sin él, Discord entrega vacíos el texto y los embeds de los mensajes de otros bots, y no se podría distinguir un bump exitoso de la respuesta de "espera X minutos". Es un intent privilegiado, pero no exige verificación mientras el bot esté en menos de 100 servidores.
- **El patrón de bump es configurable.** El texto exacto de la confirmación de Disboard depende de su versión e idioma y no está documentado oficialmente. `BUMP_SUCCESS_PATTERN` permite ajustarlo sin desplegar código nuevo.
- **El bot solo opera en `GUILD_ID`.** Ignora cualquier otro servidor al que lo inviten por error.
- **Permiso "Gestionar servidor".** Es la única forma de leer los usos de las invitaciones. Se le da solo al rol de Rakim y se revisa en la tarea de seguridad del servidor.
- **Permisos mínimos: `19488`.** Ver canales, Enviar mensajes, Insertar enlaces y Gestionar servidor. No se pide Administrador, Leer el historial (el bot solo reacciona a mensajes nuevos) ni Mencionar a todos: el rol del bump se marca como mencionable.

## Pendiente

- Crear el Droplet y el primer despliegue (ver `deployment.md`); el script del servidor y el flujo de GitHub Actions están escritos pero sin probar contra un servidor real.
- Proteger `master` con las reglas de `deployment.md` (depende del plan de la organización).
- Licencia del repositorio (hoy privado y sin licencia).
- Texto final del mensaje de bienvenida.
