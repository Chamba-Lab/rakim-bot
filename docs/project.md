# Proyecto

## Propósito

Rakim Bot es el bot de Discord de [Chamba Lab](https://chambalab.org). El servidor es pequeño, crece de forma orgánica y tiene pocos moderadores, así que a veces alguien nuevo espera sin respuesta. El bot quita esa fricción de entrada y automatiza tareas repetitivas. Rakim es la mascota de la comunidad (un mapache con taza de café y expresión _grumpy_) y es la primera voz del servidor.

El contexto de la comunidad (misión, perfiles, estructura del servidor) está en la documentación del equipo en Notion; aquí solo lo que condiciona al bot.

## Alcance de la v0

| Función                   | Qué hace                                                                                                      | Estado       |
| :------------------------ | :------------------------------------------------------------------------------------------------------------ | :----------- |
| Bienvenida                | Saluda en el canal general a quien termina la pantalla de reglas, con primeros pasos y qué ofrece el servidor | Implementada |
| Log de entradas y salidas | Publica en un canal privado cada entrada (con la invitación usada) y cada salida                              | Implementada |
| Recordatorio de bump      | Detecta el bump de Disboard y avisa a las 2 horas                                                             | Implementada |

"Implementada" significa con código y pruebas unitarias; falta probarla contra el servidor real (ver "Pendiente de verificar").

## Fuera de alcance (por ahora)

- Moderación avanzada, niveles o karma, gamificación.
- Integración con Chamba Board.
- Mensaje directo de bienvenida: se descartó por parecer invasivo y se puede evaluar más adelante.
- Detectar si una salida fue expulsión o ban (exige leer el registro de auditoría).

## Voz de Rakim

Breve, seca y algo gruñona, pero cálida. Frases cortas, español neutro, tuteo, sin jerga local y como máximo un emoji por mensaje. Sin promesas de empleo ni de resultados. Hacia afuera se dice "equipo".

## El mensaje de bienvenida

El texto vigente es un **borrador** y vive en `src/messages.ts`. Cubre, en este orden:

1. Bienvenida y lo esencial de la comunidad: un espacio tranquilo para conectar, inspirarse y crecer.
2. Invitación a presentarse en el canal de presentación, de forma casual: nombre, de dónde es, a qué se dedica o qué estudia, hobbies e intereses.
3. Recordatorio de que puede pedir feedback de su portafolio, GitHub, LinkedIn o CV en `ask-feedback`.
4. Que el canal general es donde se conversa día a día.
5. Dónde dar feedback sobre el servidor (`server-feedback`).
6. Dónde están las redes y la descripción completa del servidor (el canal de enlaces).

El texto final se define con el equipo antes de ponerlo en producción.

## Pendiente de verificar

- **Texto exacto de la confirmación de Disboard.** El patrón por defecto (`bump done`) es una suposición; se verifica en el servidor de pruebas o en el real y, si hace falta, se ajusta `BUMP_SUCCESS_PATTERN` sin tocar código.
- **Comportamiento de `pending`.** Que el saludo salga al terminar la pantalla de reglas depende de que el servidor tenga la pantalla de reglas obligatoria activa, como indica la documentación del equipo.
- **Permisos reales del rol de Rakim** en el canal de logs y en el servidor.

## Roadmap

1. **Hecho**: estructura del repo, documentación y las tres funciones de la v0 con pruebas.
2. **Siguiente**: probar contra un servidor de pruebas, verificar los puntos de arriba y cerrar el texto de bienvenida con el equipo.
3. **Después**: elegir hosting y definir el CI/CD del bot (ver `docs/decisions.md`), y desplegar.
4. **Horizonte**: lo que pida la comunidad; cada función nueva se evalúa contra el principio de "quitar fricción, no sumar ruido".
