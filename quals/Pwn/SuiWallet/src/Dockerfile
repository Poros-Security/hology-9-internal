FROM debian:bookworm-slim

RUN printf 'Acquire::Retries "5";\nAcquire::http::Timeout "30";\nAcquire::https::Timeout "30";\n' \
    > /etc/apt/apt.conf.d/80suiwallet-retries

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential ca-certificates cmake coreutils curl git libelf-dev \
    libfuse-dev libssl-dev netcat-openbsd ninja-build pkg-config python3 uuid-dev wget xinetd \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --system --home /nonexistent --shell /usr/sbin/nologin suiwallet

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

RUN mkdir -p /etc/suiwallet /var/run/xinetd /opt/suiwallet
COPY suiwallet_ta.so suiwallet /opt/suiwallet/
COPY xinetd.conf /etc/xinetd.conf
COPY runtime.conf /etc/suiwallet/runtime.conf
COPY service.sh run_engine.sh start.sh healthcheck.sh /usr/local/bin/

RUN chmod 0555 /usr/local/bin/service.sh /usr/local/bin/run_engine.sh \
        /usr/local/bin/start.sh /usr/local/bin/healthcheck.sh && \
    chmod 0555 /opt/suiwallet/suiwallet && \
    chmod 0444 /opt/suiwallet/suiwallet_ta.so

EXPOSE 9999
ENV PKG_CONFIG_PATH=/opt/OpenTee/lib/pkgconfig:/usr/local/lib/pkgconfig:/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/share/pkgconfig
HEALTHCHECK --interval=30s --timeout=12s --start-period=20s CMD /usr/local/bin/healthcheck.sh
CMD ["/usr/local/bin/start.sh"]
