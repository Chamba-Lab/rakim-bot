# Puesta en marcha

Cómo crear el bot en Discord, configurarlo, ejecutarlo y diagnosticarlo. Para probar usa **un bot y un servidor de pruebas propios**, no los de la comunidad.

## 1. Crear la aplicación y el bot

1. Entra al [portal de desarrolladores](https://discord.com/developers/applications) y crea una aplicación (por ejemplo, "Rakim (pruebas)").
2. En **Bot**, pulsa _Reset Token_ y copia el token a `DISCORD_TOKEN`. Guárdalo como un secreto: quien lo tenga controla el bot. Si se filtra, restablécelo.
3. En **Bot > Privileged Gateway Intents**, activa **Server Members Intent** y **Message Content Intent**. Los demás intents no necesitan activación.

## 2. Invitar el bot al servidor

Usa esta URL con el `client_id` de tu aplicación (en **General Information**):

```text
https://discord.com/oauth2/authorize?client_id=<CLIENT_ID>&scope=bot&permissions=19488
```

`19488` suma los cuatro permisos que necesita: Ver canales, Enviar mensajes, Insertar enlaces y Gestionar servidor (para leer las invitaciones). La tabla con el porqué de cada uno está en [`architecture.md`](./architecture.md#permisos-del-bot-en-el-servidor).

Después, en el servidor:

- Da al rol de Rakim acceso al **canal de logs** (es privado) y a los canales de bienvenida y bump.
- El rol de Rakim debe poder ver el canal donde Disboard responde a `/bump`.

## 3. Configurar el entorno

1. Activa el _Modo desarrollador_ en Discord (Ajustes > Avanzado) para copiar IDs con clic derecho > _Copiar ID_.
2. Copia `.env.example` a `.env` y completa:

| Variable                                                                                        | De dónde sale                                            |
| :---------------------------------------------------------------------------------------------- | :------------------------------------------------------- |
| `DISCORD_TOKEN`                                                                                 | Portal de desarrolladores > Bot                          |
| `GUILD_ID`                                                                                      | Clic derecho sobre el servidor                           |
| `WELCOME_CHANNEL_ID`                                                                            | Canal general                                            |
| `INTRO_CHANNEL_ID`, `ASK_FEEDBACK_CHANNEL_ID`, `SERVER_FEEDBACK_CHANNEL_ID`, `LINKS_CHANNEL_ID` | Canales que menciona el mensaje de bienvenida            |
| `LOG_CHANNEL_ID`                                                                                | Canal privado de logs                                    |
| `BUMP_CHANNEL_ID`, `BUMP_ROLE_ID` (opcional)                                                    | Canal del aviso y rol a mencionar                        |
| `INVITE_LABELS`                                                                                 | JSON `{"codigo":"nombre"}` para nombrar las invitaciones |

`DISBOARD_BOT_ID`, `BUMP_SUCCESS_PATTERN`, `BUMP_COOLDOWN_MINUTES` y `STATE_PATH` tienen valores por defecto razonables.

## 4. Ejecutar

```bash
npm install
npm run dev        # desarrollo, reinicia al guardar
# o, en producción:
npm run build
npm start
```

Al conectar verás `Rakim conectado como <nombre>` en la consola. Si la configuración es inválida, el proceso termina listando todos los errores.

## 5. Probar cada función

| Función    | Cómo probarla                                                                                                                                                                                                                                     |
| :--------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Log        | Entra y sal con una cuenta secundaria usando una invitación. Debe aparecer un embed por cada evento, con la invitación identificada. Prueba también con dos invitaciones distintas.                                                               |
| Bienvenida | Entra con una cuenta secundaria y acepta la pantalla de reglas. El saludo debe salir al aceptarlas, no al entrar. Si el servidor de pruebas no tiene reglas obligatorias, saldrá al entrar.                                                       |
| Bump       | Ejecuta `/bump` con Disboard en el servidor de pruebas. Deben aparecer `Bump detectado; aviso programado` en la consola y, para una prueba rápida, `BUMP_COOLDOWN_MINUTES=1`. Reinicia el bot durante la espera: el aviso debe llegar igualmente. |

## 6. Diagnóstico

| Síntoma                                              | Causa probable                                                                                              |
| :--------------------------------------------------- | :---------------------------------------------------------------------------------------------------------- |
| `Used disallowed intents` al arrancar                | Falta activar _Server Members_ o _Message Content_ en el portal                                             |
| `Configuración inválida: …`                          | Falta o está mal una variable; el mensaje lista cuáles                                                      |
| El log dice "No se pudo determinar" siempre          | Falta el permiso _Gestionar servidor_ (busca el aviso `No se pudieron leer las invitaciones` en la consola) |
| No sale el saludo                                    | El rol de Rakim no ve o no puede escribir en el canal general; o la persona aún no acepta las reglas        |
| No se detecta el bump                                | El texto de Disboard no coincide con `BUMP_SUCCESS_PATTERN`; copia el texto real y ajusta la variable       |
| El aviso de bump no llega tras reiniciar             | `STATE_PATH` apunta a un lugar no persistente; en producción debe ser un volumen                            |
| `Missing Access` / `Missing Permissions` al publicar | El rol de Rakim no tiene acceso al canal de logs, de bump o general                                         |

## 7. Operación

- **Reiniciar**: es seguro. El aviso de bump pendiente se retoma; las entradas ocurridas con el bot apagado no se registran.
- **Rotar el token**: restablécelo en el portal, actualiza `DISCORD_TOKEN` y reinicia.
- **Desactivar el mensaje automático de llegada de Discord**: cuando el bot esté en producción, en Ajustes del servidor > Resumen > Canal de mensajes del sistema (desactiva los avisos de bienvenida), para que no se duplique con el saludo de Rakim.
