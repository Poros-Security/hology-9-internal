FROM composer:2 AS vendor
WORKDIR /app
COPY backend/composer.json backend/composer.lock ./
RUN composer install --no-dev --no-interaction --optimize-autoloader --no-scripts

FROM node:22-alpine AS modules
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --omit=dev

FROM php:8.4-fpm-alpine

RUN apk add --no-cache nginx nodejs supervisor

WORKDIR /app
ENV DB_PATH=/var/lib/mekanik/mt.sqlite
ENV BACKEND_URL=http://127.0.0.1:8080

COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/supervisord.conf /etc/supervisord.conf
COPY docker/php.ini /usr/local/etc/php/conf.d/app.ini
COPY docker/php-fpm-pool.conf /usr/local/etc/php-fpm.d/zz-app.conf
COPY docker/entrypoint.sh /usr/local/bin/entrypoint

COPY backend ./backend
COPY frontend ./frontend
COPY --from=vendor /app/vendor ./backend/vendor
COPY --from=modules /app/node_modules ./frontend/node_modules

RUN chmod +x /usr/local/bin/entrypoint && mkdir -p /var/lib/mekanik

EXPOSE 80
ENTRYPOINT ["entrypoint"]
