#!/usr/bin/env bash
# Prepara un Droplet nuevo de Ubuntu 24.04 para correr Rakim Bot. Se ejecuta UNA vez, como root:
#
#   DEPLOY_PUBKEY="$(cat rakim-deploy.pub)" bash setup-droplet.sh
#
# Qué hace: swap de 1 GB (el Droplet de US$4 tiene 512 MiB), Docker, firewall que solo
# deja entrar SSH, actualizaciones de seguridad automáticas, un usuario `deploy` sin sudo
# para el CD y SSH solo con llave. Se puede volver a ejecutar sin romper nada.
set -euo pipefail

DEPLOY_USER="deploy"
APP_DIR="/opt/rakim-bot"

if [ "$(id -u)" -ne 0 ]; then
    echo "Ejecútalo como root." >&2
    exit 1
fi
if [ -z "${DEPLOY_PUBKEY:-}" ]; then
    echo "Falta DEPLOY_PUBKEY: la llave PÚBLICA que usará el CD (rakim-deploy.pub)." >&2
    exit 1
fi

echo "==> Swap de 1 GB"
if ! swapon --show=NAME --noheadings | grep -q '^/swapfile$'; then
    fallocate -l 1G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "==> Paquetes: Docker, firewall y actualizaciones automáticas"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y docker.io docker-compose-v2 ufw unattended-upgrades
systemctl enable --now docker
dpkg-reconfigure -f noninteractive unattended-upgrades

echo "==> Firewall: solo SSH de entrada"
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw --force enable

echo "==> Usuario ${DEPLOY_USER}"
if ! id "${DEPLOY_USER}" >/dev/null 2>&1; then
    adduser --disabled-password --gecos "" "${DEPLOY_USER}"
fi
# Pertenecer al grupo docker equivale a tener root en esta máquina: por eso este usuario
# solo se usa con la llave del CD y la tuya, y no tiene sudo.
usermod -aG docker "${DEPLOY_USER}"
install -d -m 700 -o "${DEPLOY_USER}" -g "${DEPLOY_USER}" "/home/${DEPLOY_USER}/.ssh"
AUTH="/home/${DEPLOY_USER}/.ssh/authorized_keys"
touch "${AUTH}"
# Tu llave de administración (la que pusiste al crear el Droplet) también entra como deploy.
if [ -f /root/.ssh/authorized_keys ]; then
    cat /root/.ssh/authorized_keys >> "${AUTH}"
fi
echo "${DEPLOY_PUBKEY}" >> "${AUTH}"
sort -u "${AUTH}" -o "${AUTH}"
chown "${DEPLOY_USER}:${DEPLOY_USER}" "${AUTH}"
chmod 600 "${AUTH}"

echo "==> Directorio de la aplicación"
install -d -m 750 -o "${DEPLOY_USER}" -g "${DEPLOY_USER}" "${APP_DIR}"

echo "==> SSH solo con llave"
cat > /etc/ssh/sshd_config.d/99-rakim-hardening.conf <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
EOF
sshd -t
systemctl reload ssh

echo
echo "Listo. Siguiente paso: crear ${APP_DIR}/.env (ver docs/deployment.md)."
