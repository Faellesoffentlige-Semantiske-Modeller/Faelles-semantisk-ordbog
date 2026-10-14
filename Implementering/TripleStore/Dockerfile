FROM maven:3.9-eclipse-temurin-21-alpine AS fetch

ENV LANG=C.UTF-8

RUN set -eux; \
    apk -U upgrade; \
    apk add --no-cache curl ca-certificates coreutils tar; \
    rm -rf /var/cache/apk/*

ENV FUSEKI_SHA512=8b14dcefade409bb4efd94e05291ea46d50508bf175f6f163f328d1d80183559a4c5b75806802283802a2879405a132b9b311e2277f784a784fa66ce4a9d8722
ENV FUSEKI_VERSION=6.0.0
ENV SHIRO_HASHER_VERSION=2.1.0
ENV ASF_MIRROR=https://www.apache.org/dyn/mirrors/mirrors.cgi?action=download&filename=
ENV ASF_ARCHIVE=https://downloads.apache.org/

ENV FUSEKI_HOME=/jena-fuseki

WORKDIR /tmp

# Download/check/unpack/move in one go
RUN set -eux; \
    echo "$FUSEKI_SHA512  fuseki.tar.gz" > fuseki.tar.gz.sha512; \
    (curl --location --silent --show-error --fail --retry-connrefused --retry 3 --output fuseki.tar.gz "${ASF_MIRROR}jena/binaries/apache-jena-fuseki-${FUSEKI_VERSION}.tar.gz" \
    || curl --fail --silent --show-error --retry-connrefused --retry 3 --output fuseki.tar.gz "${ASF_ARCHIVE}jena/binaries/apache-jena-fuseki-${FUSEKI_VERSION}.tar.gz"); \
    sha512sum -c fuseki.tar.gz.sha512; \
    tar zxf fuseki.tar.gz; \
    mv apache-jena-fuseki* "${FUSEKI_HOME}"; \
    rm -f fuseki.tar.gz fuseki.tar.gz.sha512; \
    cd "${FUSEKI_HOME}"; \
    rm -rf fuseki.war; \
    chmod 755 fuseki-server; \
    mvn dependency:get -DgroupId=org.apache.shiro.tools -DartifactId=shiro-tools-hasher -Dclassifier=cli -Dversion=${SHIRO_HASHER_VERSION}; \
    cp /root/.m2/repository/org/apache/shiro/tools/shiro-tools-hasher/${SHIRO_HASHER_VERSION}/shiro-tools-hasher-${SHIRO_HASHER_VERSION}-cli.jar shiro-tools-hasher.jar

FROM eclipse-temurin:21-jre-alpine AS runtime

ENV LANG=C.UTF-8

RUN set -eux; \
    apk -U upgrade; \
    apk add --no-cache bash curl ca-certificates findutils coreutils gettext pwgen procps tini; \
    rm -rf /var/cache/apk/*

ENV FUSEKI_VERSION=5.5.0
ENV FUSEKI_BASE=/fuseki
ENV FUSEKI_HOME=/jena-fuseki

LABEL org.opencontainers.image.documentation="https://jena.apache.org/documentation/fuseki2/"
LABEL org.opencontainers.image.title="Apache Jena Fuseki"
LABEL org.opencontainers.image.description="Fuseki is a SPARQL 1.1 server with a web interface, backed by the Apache Jena TDB RDF triple store."
LABEL org.opencontainers.image.version="${FUSEKI_VERSION}"
LABEL org.opencontainers.image.licenses="(Apache-2.0 AND (GPL-2.0 WITH Classpath-exception-2.0) AND GPL-3.0)"
LABEL org.opencontainers.image.authors="Apache Jena Fuseki by https://jena.apache.org/; this image by https://orcid.org/0000-0001-9842-9718"

COPY --from=fetch /jena-fuseki ${FUSEKI_HOME}

# enable basic-auth (shiro.ini) and entrypoint
COPY shiro.ini ${FUSEKI_HOME}/shiro.ini
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod 755 /docker-entrypoint.sh

# Create non-root user/group
RUN addgroup -S fuseki && adduser -G fuseki -S -D -H fuseki

# Where we start our server from
WORKDIR ${FUSEKI_HOME}
RUN chown -R fuseki:fuseki ${FUSEKI_HOME}

# Ensure /fuseki exists, is empty, and owned by fuseki
RUN set -eux; \
    mkdir -p ${FUSEKI_BASE}; \
    rm -rf ${FUSEKI_BASE}/*; \
    chown -R fuseki:fuseki ${FUSEKI_BASE}

VOLUME ${FUSEKI_BASE}

EXPOSE 3030
USER fuseki

ENTRYPOINT ["/sbin/tini", "--", "/docker-entrypoint.sh"]
CMD ["/jena-fuseki/fuseki-server"]
