FROM ubuntu:22.04

RUN apt-get update && apt-get install -y curl git python3 python-is-python3

RUN curl -sSf https://raw.githubusercontent.com/WasmEdge/WasmEdge/master/utils/install.sh | bash
ENV PATH="/root/.wasmedge/bin:$PATH"

WORKDIR /app

RUN mkdir public 
COPY image.png public/logo.png

COPY server.wasm /app/server.wasm

EXPOSE 8080

CMD ["wasmedge", "--dir", "/:/", "/app/server.wasm"]