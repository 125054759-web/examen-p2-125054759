#!/bin/bash
# Arranque del contenedor hadoop.
set -e

# El contenedor api necesita entrar por SSH sin contrasena.
# Generamos (una sola vez) una llave para "api" en el volumen compartido
# y agregamos su llave publica a authorized_keys del usuario hadoop.
DIR=/ssh-compartido
AUTH=/home/hadoop/.ssh/authorized_keys
if [ -d "$DIR" ]; then
  if [ ! -f "$DIR/id_api" ]; then
    ssh-keygen -t ed25519 -N "" -q -C "api@datamart" -f "$DIR/id_api"
  fi
  chmod 600 "$DIR/id_api"
  grep -qxF "$(cat "$DIR/id_api.pub")" "$AUTH" || cat "$DIR/id_api.pub" >> "$AUTH"
fi

hadoop version | head -n 1
echo "Contenedor hadoop listo. Iniciando servidor SSH..."

# sshd en primer plano mantiene vivo el contenedor
exec /usr/sbin/sshd -D -e
