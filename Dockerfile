# Imagen de Rakim Bot. Dos etapas: compila con todas las dependencias y la
# imagen final solo lleva las de producción y el código compilado.
#
# Node 24 (LTS con soporte hasta abril de 2028). Se construye con `--pull` para
# traer siempre el último parche de la línea; .npmrc activa `engine-strict`, así
# que `npm ci` falla si la imagen base trae una versión sin el parche de
# seguridad de octubre de 2026 (ver `engines` en package.json).

FROM node:24-bookworm-slim AS build
WORKDIR /app

COPY package.json package-lock.json .npmrc ./
RUN npm ci

COPY tsconfig.json tsconfig.build.json ./
COPY src ./src
RUN npm run build && npm prune --omit=dev


FROM node:24-bookworm-slim
ENV NODE_ENV=production
WORKDIR /app

COPY --from=build --chown=node:node /app/package.json ./
COPY --from=build --chown=node:node /app/node_modules ./node_modules
COPY --from=build --chown=node:node /app/dist ./dist

# Aquí vive el estado (el aviso de bump pendiente). En producción es un volumen.
RUN mkdir -p /app/data && chown node:node /app/data

# Sin privilegios de root. La configuración llega por variables de entorno.
USER node
CMD ["node", "dist/index.js"]
