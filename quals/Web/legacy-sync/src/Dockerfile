FROM node:18-alpine

WORKDIR /app

COPY package.json ./
COPY package-lock.json ./
COPY vite.config.js ./
COPY src ./src
COPY dist ./dist

RUN npm install --omit=dev --quiet

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PORT=6767
EXPOSE 6767

ENTRYPOINT ["/entrypoint.sh"]
