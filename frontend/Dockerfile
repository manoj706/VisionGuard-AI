FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Copy built assets to shared volume
FROM alpine:3.19
COPY --from=builder /app/dist /srv/frontend
