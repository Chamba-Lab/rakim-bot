# Crear el bot, probarlo y diagnosticarlo

Para probar usa **un bot y un servidor de pruebas propios**, no los de la comunidad.

## 1. Crear la aplicación y el bot

1. En el [portal de desarrolladores](https://discord.com/developers/applications) crea una aplicación (por ejemplo, "Rakim (pruebas)").
2. En **Bot**, restablece el token y cópialo a `DISCORD_TOKEN`. Es un secreto: quien lo tenga controla el bot. Si se filtra, restablécelo.
3. En **Bot > Privileged Gateway Intents**, activa **Server Members Intent** y **Message Content Intent**.

## 2. Invitarlo al servidor

Con el `client_id` de tu aplicación (en **General Information**):

```text
https://discord.com/oauth2/authorize?client_id=<CLIENT_ID>&scope=bot%20applications.commands&permissions=19488
```

El alcance `applications.commands` habilita `/invitaciones`; sin él solo funciona la mención. `19488` son los cuatro permisos mínimos (la tabla con el porqué está en [`architecture.md`](./architecture.md#permisos-en-el-servidor)). Después, en el servidor: da al rol de Rakim acceso al **canal de logs** (es privado), a los canales de bienvenida y bump, y al canal donde Disboard responde a `/bump`. Si usas el tema del día con un rol, da además al rol de Rakim **Mencionar @everyone, @here y todos los roles** solo en el canal general (permisos del canal), no en el servidor ni en el enlace de invitación.

## 3. Configurar el entorno

Activa el _Modo desarrollador_ en Discord (Ajustes > Avanzado) para copiar IDs con clic derecho > _Copiar ID_. Copia `.env.example` a `.env` y completa:

| Variable                                                                                        | De dónde sale                                            |
| :---------------------------------------------------------------------------------------------- | :------------------------------------------------------- |
| `DISCORD_TOKEN`                                                                                 | Portal de desarrolladores > Bot                          |
| `GUILD_ID`                                                                                      | Clic derecho sobre el servidor                           |
| `WELCOME_CHANNEL_ID`                                                                            | Canal general                                            |
| `INTRO_CHANNEL_ID`, `ASK_FEEDBACK_CHANNEL_ID`, `LINKS_CHANNEL_ID` | Canales que menciona el saludo                           |
| `LOG_CHANNEL_ID`                                                                                | Canal privado de logs                                    |
| `BUMP_CHANNEL_ID`, `BUMP_ROLE_ID` y `BUMP_USER_ID` (opcionales)                                 | Canal del aviso, y rol (debe ser mencionable) y/o persona a mencionar |
| `INVITE_LABELS`                                                                                 | JSON `{"codigo":"nombre"}` para nombrar las invitaciones |
| `DAILY_TOPIC_TIMES` y `DAILY_TOPIC_ROLE_ID` (opcionales)                                         | Horas del tema del día (Lima, `HH:MM`; vacío lo apaga) y rol a mencionar |
| `COUNTRY_ROLE_IDS`, `STAGE_ROLE_IDS` y `NOTIFICATION_ROLE_IDS` (opcionales)                      | Roles de país, de etapa y de notificación (Avisos, Eventos, Actividades) del Onboarding, separados por coma, para `/miembros` |

`DISBOARD_BOT_ID`, `BUMP_SUCCESS_PATTERN`, `BUMP_COOLDOWN_MINUTES`, `WELCOME_WAIT_SYSTEM_MESSAGE`, `DAILY_TOPIC_PRESETS` y `STATE_PATH` tienen valores por defecto.

## 4. Ejecutar y probar

```bash
uv run python -m rakim
```

Verás `Rakim conectado como <nombre>`. Si la configuración es inválida, termina listando todos los errores.

| Función    | Cómo probarla                                                                                                                                                                                                 |
| :--------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Log        | Entra y sal con una cuenta secundaria usando una invitación; debe aparecer un embed por evento, con la invitación identificada. Repite con dos invitaciones distintas.                                          |
| Bienvenida | Entra con una cuenta secundaria y acepta la pantalla de reglas: el saludo debe salir al aceptarlas, no al entrar. Sin reglas obligatorias, sale al entrar. El saludo debe salir después del mensaje nativo «ha entrado» (el canal de mensajes del sistema debe ser `WELCOME_CHANNEL_ID`); con `WELCOME_WAIT_SYSTEM_MESSAGE=false`, tras unos 5 s.                                                        |
| Comandos   | En el canal de logs: `/estado` (debe salir todo con ✔), `/invitaciones` y `/invitaciones alcance:todas`. En cualquier canal: `/ruleta` y `/ruleta tema:…`, y dos veces seguidas en menos de 15 s (la segunda debe pedir calma). `/miembros` debe mostrar las tablas por país, por etapa y de notificaciones (prueba con una cuenta secundaria con un rol de país y otra sin ninguno: debe contar en «Sin responder»). Con una cuenta sin Gestionar servidor, `/estado` debe negarse. Para ver el aviso de arranque, quita el permiso de enviar mensajes en el canal de bump y reinicia el bot. |
| Tema del día | Pon `DAILY_TOPIC_TIMES` un par de minutos por delante de la hora de Lima y reinicia: a esa hora debe salir el tema en el canal general, mencionando el rol si hay `DAILY_TOPIC_ROLE_ID` (y la mención debe notificar). En la consola aparece `Tema del día publicado`. Con dos horas cercanas (`HH:MM,HH:MM`), el segundo tema no repite el primero, tampoco tras reiniciar. `/estado` debe marcar «Rol del tema del día» con ✘ si quitas el permiso de mencionar en general. `/tema` en el canal de logs debe publicar uno en el general al instante y confirmarlo solo a ti; en otro canal o sin Gestionar servidor, debe negarse. |
| Bump       | Ejecuta `/bump` con Disboard. Debe aparecer `Bump detectado; aviso programado`. Para una prueba rápida usa `BUMP_COOLDOWN_MINUTES=1` y reinicia el bot durante la espera: el aviso debe llegar igualmente.       |

## 5. Si algo falla

| Síntoma                                           | Causa probable                                                                                              |
| :------------------------------------------------ | :---------------------------------------------------------------------------------------------------------- |
| `PrivilegedIntentsRequired` al arrancar           | Falta activar _Server Members_ o _Message Content_ en el portal                                             |
| `Configuración inválida: …`                       | Falta o está mal una variable; el mensaje lista cuáles                                                      |
| El log dice «No se pudo determinar» siempre       | Falta _Gestionar servidor_ (busca `No se pudieron leer las invitaciones` en la consola)                     |
| No sale el saludo                                 | El rol de Rakim no puede escribir en el canal general, o la persona aún no acepta las reglas                |
| No se detecta el bump                             | El texto real de Disboard no coincide con `BUMP_SUCCESS_PATTERN`: cópialo y ajusta la variable              |
| El aviso de bump no llega tras reiniciar          | `STATE_PATH` apunta a un lugar no persistente; en producción debe ser un volumen                            |
| No sale el tema del día                           | `DAILY_TOPIC_TIMES` vacío (la consola dice `Tema del día apagado`), la hora es de Lima y no la tuya, o falta insertar enlaces en el canal general |
| El tema sale pero la mención no notifica          | Falta «Mencionar @everyone, @here y todos los roles» en el canal general (lo marca `/estado`)               |
| `Forbidden` / `Missing Access` al publicar        | El rol de Rakim no tiene acceso al canal de logs, de bump o general                                         |

Al activar el bot en producción, desactiva el mensaje automático de llegada de Discord (Ajustes del servidor > Resumen > Canal de mensajes del sistema) para que no se duplique con el saludo de Rakim. Para rotar el token: restablécelo en el portal, actualiza `DISCORD_TOKEN` y reinicia.
