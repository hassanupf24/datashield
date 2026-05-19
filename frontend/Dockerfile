FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --ignore-scripts
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -g 1001 -S datashield && adduser -S datashield -u 1001
COPY --from=builder /app/public ./public
COPY --from=builder --chown=datashield:datashield /app/.next/standalone ./
COPY --from=builder --chown=datashield:datashield /app/.next/static ./.next/static
USER datashield
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
