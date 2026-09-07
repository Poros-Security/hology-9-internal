FROM node:18-slim

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-sandbox \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV BASE_URL=http://localhost:7777

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 7777

CMD ["npm", "start"]
