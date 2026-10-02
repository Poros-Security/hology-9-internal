FROM ghcr.io/cirruslabs/flutter:stable AS web
WORKDIR /src
COPY frontend/pubspec.yaml frontend/pubspec.lock* ./
RUN flutter pub get
COPY frontend ./
RUN flutter build web --release --pwa-strategy=none

FROM dart:stable AS api
WORKDIR /src
COPY backend/pubspec.yaml ./
RUN dart pub get
COPY backend ./
RUN dart pub get --offline && dart compile exe bin/server.dart -o /src/slopter-api

FROM debian:stable-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends nginx supervisor ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PORT=8080

COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/supervisord.conf /etc/supervisord.conf
COPY docker/entrypoint.sh /usr/local/bin/entrypoint

COPY --from=api /src/slopter-api /app/slopter-api
COPY --from=web /src/build/web /app/web

RUN chmod +x /usr/local/bin/entrypoint /app/slopter-api

EXPOSE 80
ENTRYPOINT ["entrypoint"]
