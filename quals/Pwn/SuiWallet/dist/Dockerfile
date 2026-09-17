FROM debian:bookworm-slim

RUN printf 'Acquire::Retries "5";\nAcquire::http::Timeout "30";\nAcquire::https::Timeout "30";\n' \
    > /etc/apt/apt.conf.d/80suiwallet-retries

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential ca-certificates cmake curl file git gdb \
    libelf-dev libfuse-dev libssl-dev ninja-build pkg-config python3 python3-pip python3-pwntools uuid-dev wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp
RUN wget -q https://github.com/ARMmbed/mbedtls/archive/refs/tags/v3.1.0.tar.gz && \
    tar -xf v3.1.0.tar.gz && \
    cd mbedtls-3.1.0 && \
    cmake -DUSE_SHARED_MBEDTLS_LIBRARY=On . && \
    make -j"$(nproc)" && \
    make install && \
    mkdir -p /usr/local/lib/pkgconfig && \
    printf '%s\n' \
        'prefix=/usr/local' \
        'exec_prefix=${prefix}' \
        'libdir=${exec_prefix}/lib' \
        'includedir=${prefix}/include' \
        '' \
        'Name: mbedcrypto' \
        'Description: Mbed TLS cryptography library' \
        'Version: 3.1.0' \
        'Libs: -L${libdir} -lmbedcrypto' \
        'Cflags: -I${includedir}' \
        > /usr/local/lib/pkgconfig/mbedcrypto.pc && \
    ldconfig

RUN git clone --depth 1 https://github.com/Open-TEE/Open-TEE.git /src/opentee && \
    cmake -S /src/opentee -B /src/opentee/build -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/opt/OpenTee && \
    cmake --build /src/opentee/build && \
    cmake --install /src/opentee/build && \
    printf '/opt/OpenTee/lib\n' > /etc/ld.so.conf.d/opentee.conf && \
    ldconfig

WORKDIR /opt/suiwallet
COPY suiwallet_ta.so suiwallet_ca.c suiwallet_ca.h run.sh runtime.conf libc.so.6 ./
RUN flag='CTF{local_test_flag}'; \
    flag_hash=$(printf '%s\n' "$flag" | sha256sum | cut -d' ' -f1); \
    rm -f /flag /flag-*.txt; \
    printf '%s\n' "$flag" > "/flag-${flag_hash}.txt"; \
    chmod 0444 "/flag-${flag_hash}.txt"; \
    chmod 0555 /opt/suiwallet/run.sh

ENV OPEN_TEE_PREFIX=/opt/OpenTee
ENV PKG_CONFIG_PATH=/opt/OpenTee/lib/pkgconfig:/usr/local/lib/pkgconfig:/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/share/pkgconfig
CMD ["./run.sh"]
