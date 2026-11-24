# syntax=docker/dockerfile:1
FROM node:20-bookworm-slim AS deps
WORKDIR /srv
RUN corepack enable && corepack prepare pnpm@12.4.2 --activate
COPY package.json pnpm-lock.yaml ./
RUN --mount=type=cache,id=testmind-web-pnpm,target=/pnpm/store \
    pnpm install --frozen-lockfile --store-dir=/pnpm/store

FROM deps AS build
ENV NEXT_TELEMETRY_DISABLED=1
COPY . .
RUN --mount=type=cache,id=testmind-web-next,target=/srv/.next/cache \
    pnpm build

FROM node:20-bookworm-slim AS runner
WORKDIR /srv
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
COPY --from=build /srv/public ./public
COPY --from=build /srv/.next/standalone ./
COPY --from=build /srv/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
