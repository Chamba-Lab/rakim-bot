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

El alcance `applications.commands` habilita `/invitaciones`; sin él solo funciona la mención. `19488` son los cuatro permisos mínimos (la tabla con el porqué está en [`architecture.md`](./architecture.md#permisos-en-el-servidor)). Después, en el servidor: da al rol de Rakim acceso al **canal de logs** (es privado), a los canales de bienvenida y bump, y al canal donde Disboard responde a `/bump`.

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

`DISBOARD_BOT_ID`, `BUMP_SUCCESS_PATTERN`, `BUMP_COOLDOWN_MINUTES`, `WELCOME_WAIT_SYSTEM_MESSAGE` y `STATE_PATH` tienen valores por defecto.

## 4. Ejecutar y probar

```bash
uv run python -m rakim
```

Verás `Rakim conectado como <nombre>`. Si la configuración es inválida, termina listando todos los errores.

| Función    | Cómo probarla                                                                                                                                                                                                 |
| :--------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Log        | Entra y sal con una cuenta secundaria usando una invitación; debe aparecer un embed por evento, con la invitación identificada. Repite con dos invitaciones distintas.                                          |
| Bienvenida | Entra con una cuenta secundaria y acepta la pantalla de reglas: el saludo debe salir al aceptarlas, no al entrar. Sin reglas obligatorias, sale al entrar. El saludo debe salir después del mensaje nativo «ha entrado» (el canal de mensajes del sistema debe ser `WELCOME_CHANNEL_ID`); con `WELCOME_WAIT_SYSTEM_MESSAGE=false`, tras unos 5 s.                                                        |
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
| `Forbidden` / `Missing Access` al publicar        | El rol de Rakim no tiene acceso al canal de logs, de bump o general                                         |

Al activar el bot en producción, desactiva el mensaje automático de llegada de Discord (Ajustes del servidor > Resumen > Canal de mensajes del sistema) para que no se duplique con el saludo de Rakim. Para rotar el token: restablécelo en el portal, actualiza `DISCORD_TOKEN` y reinicia.
