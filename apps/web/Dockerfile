FROM node:20-bookworm-slim AS deps
WORKDIR /srv
RUN corepack enable
COPY package.json pnpm-lock.yaml ./
RUN corepack prepare pnpm@12.4.2 --activate && pnpm install --frozen-lockfile

FROM node:20-bookworm-slim AS build
WORKDIR /srv
RUN corepack enable && corepack prepare pnpm@12.4.2 --activate
COPY --from=deps /srv/node_modules ./node_modules
COPY . .
RUN pnpm build

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
