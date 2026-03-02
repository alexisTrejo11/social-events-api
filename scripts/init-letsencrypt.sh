#!/bin/bash

# init-letsencrypt.sh
# Este script prepara los certificados SSL de Let's Encrypt para primera vez

set -e

# Configuración
DOMAIN_NAME="${1:-example.com}"
EMAIL="${2:-admin@example.com}"
STAGING="${3:-0}" # Set to 1 for staging (testing)
DATA_PATH="./certbot"
RSA_KEY_SIZE=4096

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Inicializando certificados SSL Let's Encrypt ${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "Dominio: ${YELLOW}${DOMAIN_NAME}${NC}"
echo -e "Email: ${YELLOW}${EMAIL}${NC}"
echo -e "Staging: ${YELLOW}${STAGING}${NC}"
echo ""

# Verificar que se proporcionaron argumentos
if [ "$DOMAIN_NAME" = "example.com" ]; then
    echo -e "${RED}Error: Debes proporcionar un nombre de dominio válido${NC}"
    echo -e "Uso: $0 <dominio> <email> [staging]"
    echo -e "Ejemplo: $0 midominio.com admin@midominio.com 0"
    exit 1
fi

if [ "$EMAIL" = "admin@example.com" ]; then
    echo -e "${RED}Error: Debes proporcionar un email válido${NC}"
    echo -e "Uso: $0 <dominio> <email> [staging]"
    echo -e "Ejemplo: $0 midominio.com admin@midominio.com 0"
    exit 1
fi

# Crear estructura de directorios
echo -e "${YELLOW}[1/6] Creando estructura de directorios...${NC}"
mkdir -p "${DATA_PATH}/www"
mkdir -p "${DATA_PATH}/conf/live/${DOMAIN_NAME}"

# Descargar parámetros TLS recomendados
echo -e "${YELLOW}[2/6] Descargando parámetros TLS recomendados...${NC}"
if [ ! -e "${DATA_PATH}/conf/options-ssl-nginx.conf" ] || [ ! -e "${DATA_PATH}/conf/ssl-dhparams.pem" ]; then
    echo "Descargando opciones SSL de Certbot..."
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "${DATA_PATH}/conf/options-ssl-nginx.conf"
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "${DATA_PATH}/conf/ssl-dhparams.pem"
    echo -e "${GREEN}✓ Parámetros TLS descargados${NC}"
else
    echo -e "${GREEN}✓ Parámetros TLS ya existen${NC}"
fi

# Crear certificado dummy para iniciar nginx
echo -e "${YELLOW}[3/6] Creando certificado temporal (dummy) para iniciar Nginx...${NC}"
CERT_PATH="${DATA_PATH}/conf/live/${DOMAIN_NAME}"
mkdir -p "${CERT_PATH}"
if [ ! -e "${CERT_PATH}/privkey.pem" ]; then
    docker-compose -f docker/docker-compose.yml run --rm --entrypoint "\
        openssl req -x509 -nodes -newkey rsa:${RSA_KEY_SIZE} -days 1 \
        -keyout '/etc/letsencrypt/live/${DOMAIN_NAME}/privkey.pem' \
        -out '/etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem' \
        -subj '/CN=localhost'" certbot
    echo -e "${GREEN}✓ Certificado temporal creado${NC}"
else
    echo -e "${GREEN}✓ Certificado temporal ya existe${NC}"
fi

# Crear chain.pem temporal (necesario para OCSP stapling)
if [ ! -e "${CERT_PATH}/chain.pem" ]; then
    cp "${CERT_PATH}/fullchain.pem" "${CERT_PATH}/chain.pem"
fi

# Iniciar nginx
echo -e "${YELLOW}[4/6] Iniciando Nginx...${NC}"
docker-compose -f docker/docker-compose.yml up -d nginx
echo -e "${GREEN}✓ Nginx iniciado${NC}"

# Borrar certificado dummy
echo -e "${YELLOW}[5/6] Eliminando certificado temporal...${NC}"
docker-compose -f docker/docker-compose.yml run --rm --entrypoint "\
    rm -rf /etc/letsencrypt/live/${DOMAIN_NAME} && \
    rm -rf /etc/letsencrypt/archive/${DOMAIN_NAME} && \
    rm -rf /etc/letsencrypt/renewal/${DOMAIN_NAME}.conf" certbot
echo -e "${GREEN}✓ Certificado temporal eliminado${NC}"

# Solicitar certificado real de Let's Encrypt
echo -e "${YELLOW}[6/6] Solicitando certificado SSL de Let's Encrypt...${NC}"

# Seleccionar servidor (staging o producción)
if [ "$STAGING" != "0" ]; then
    STAGING_ARG="--staging"
    echo -e "${YELLOW}⚠ Usando servidor de STAGING (pruebas)${NC}"
else
    STAGING_ARG=""
    echo -e "${GREEN}Usando servidor de PRODUCCIÓN${NC}"
fi

# Solicitar certificado
docker-compose -f docker/docker-compose.yml run --rm --entrypoint "\
    certbot certonly --webroot -w /var/www/certbot \
    ${STAGING_ARG} \
    --email ${EMAIL} \
    -d ${DOMAIN_NAME} \
    -d www.${DOMAIN_NAME} \
    --rsa-key-size ${RSA_KEY_SIZE} \
    --agree-tos \
    --force-renewal \
    --non-interactive" certbot

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  ✓ ¡Certificado SSL obtenido exitosamente!    ${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

# Cambiar configuración de Nginx a HTTPS
echo -e "${YELLOW}Cambiando configuración de Nginx a HTTPS...${NC}"
sed -i 's|app-http-only.conf.template|app.conf.template|g' docker/docker-compose.yml
echo -e "${GREEN}✓ Configuración actualizada${NC}"

echo ""
echo -e "Ahora puedes:"
echo -e "1. Actualizar .env.docker con seguridad HTTPS:"
echo -e "   ${YELLOW}SECURE_SSL_REDIRECT=True${NC}"
echo -e "   ${YELLOW}SESSION_COOKIE_SECURE=True${NC}"
echo -e "   ${YELLOW}CSRF_COOKIE_SECURE=True${NC}"
echo -e ""
echo -e "2. Reiniciar servicios: ${YELLOW}docker-compose -f docker/docker-compose.yml restart nginx${NC}"
echo -e "   O reiniciar todo: ${YELLOW}docker-compose -f docker/docker-compose.yml down && docker-compose -f docker/docker-compose.yml up -d${NC}"
echo ""
echo -e "Los certificados se renovarán automáticamente cada 12 horas."
echo ""
