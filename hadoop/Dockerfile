# ---------------------------------------------------------------
# Imagen de Hadoop en modo STANDALONE + OpenSSH Server
# ---------------------------------------------------------------
# 1) Imagen base Debian ligera
FROM debian:bookworm-slim

# 2) Version de Hadoop (se puede cambiar al construir con --build-arg)
ARG HADOOP_VERSION=3.3.6
ARG HADOOP_URL=https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz

# 3) Variables de entorno que Hadoop necesita
ENV DEBIAN_FRONTEND=noninteractive \
    JAVA_HOME=/usr/lib/jvm/default-java \
    HADOOP_HOME=/opt/hadoop
ENV HADOOP_CONF_DIR=${HADOOP_HOME}/etc/hadoop \
    PATH=${PATH}:${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin

# 4) Java (OpenJDK 17), Python 3, servidor y cliente SSH, curl para descargar Hadoop
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      default-jre-headless python3 openssh-server openssh-client \
      curl ca-certificates procps \
 && rm -rf /var/lib/apt/lists/* \
 && [ -e "$JAVA_HOME" ] || ln -s "$(dirname "$(dirname "$(readlink -f "$(which java)")")")" "$JAVA_HOME"

# 5) Descargar y descomprimir Hadoop en /opt/hadoop
RUN curl -fSL "$HADOOP_URL" -o /tmp/hadoop.tar.gz \
 && tar -xzf /tmp/hadoop.tar.gz -C /opt \
 && mv /opt/hadoop-${HADOOP_VERSION} ${HADOOP_HOME} \
 && rm -rf /tmp/hadoop.tar.gz ${HADOOP_HOME}/share/doc \
 && echo "export JAVA_HOME=${JAVA_HOME}" >> ${HADOOP_CONF_DIR}/hadoop-env.sh

# 6) Las sesiones SSH no heredan las ENV de Docker: las dejamos en un perfil
RUN { echo "export JAVA_HOME=${JAVA_HOME}"; \
      echo "export HADOOP_HOME=${HADOOP_HOME}"; \
      echo "export HADOOP_CONF_DIR=${HADOOP_CONF_DIR}"; \
      echo "export PATH=\$PATH:${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin"; \
    } > /etc/profile.d/hadoop.sh

# 7) SSH: usuario "hadoop" SIN contrasena (solo entra con llave) y sshd endurecido
RUN useradd -m -s /bin/bash hadoop \
 && usermod -p '*' hadoop \
 && mkdir -p /run/sshd \
 && ssh-keygen -A \
 && printf 'PasswordAuthentication no\nPermitRootLogin no\nPubkeyAuthentication yes\n' \
      > /etc/ssh/sshd_config.d/examen.conf

# 8) Llaves para "ssh localhost" sin contrasena (ssh-keygen + authorized_keys)
USER hadoop
RUN mkdir -p /home/hadoop/.ssh && chmod 700 /home/hadoop/.ssh \
 && ssh-keygen -t ed25519 -N "" -q -f /home/hadoop/.ssh/id_ed25519 \
 && cat /home/hadoop/.ssh/id_ed25519.pub >> /home/hadoop/.ssh/authorized_keys \
 && chmod 600 /home/hadoop/.ssh/authorized_keys \
 && printf 'Host localhost 127.0.0.1 hadoop\n  StrictHostKeyChecking accept-new\n' > /home/hadoop/.ssh/config \
 && chmod 600 /home/hadoop/.ssh/config \
 && { cat /etc/profile.d/hadoop.sh; cat /etc/skel/.bashrc; } > /home/hadoop/.bashrc
USER root

# 9) Script de arranque: autoriza la llave del contenedor api y levanta sshd
COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

# 10) Verificacion al construir: si Hadoop no quedo bien instalado, el build falla
RUN hadoop version

EXPOSE 22
CMD ["/entrypoint.sh"]
