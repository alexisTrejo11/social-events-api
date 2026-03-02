# 🔐 Configuración de HTTPS con Let's Encrypt y Docker

Esta guía te ayudará a configurar HTTPS en tu aplicación Django usando Nginx, Let's Encrypt y Docker.

## 📋 Requisitos Previos

1. **Dominio apuntando a tu servidor**: Tu dominio (ej: `midominio.com`) debe estar configurado en DNS apuntando a la IP de tu servidor.
2. **Puertos abiertos**: Los puertos 80 (HTTP) y 443 (HTTPS) deben estar abiertos en tu firewall.
3. **Docker y Docker Compose** instalados en tu servidor.

## 🏗️ Arquitectura

```
Internet → Nginx (HTTPS:443) → Django (HTTP:8000)
                ↓
         Let's Encrypt (Certbot)
```

- **Nginx**: Maneja SSL/TLS y actúa como reverse proxy
- **Django**: Corre internamente en HTTP (puerto 8000)
- **Certbot**: Renueva certificados SSL automáticamente

## 🚀 Instalación y Configuración

### Paso 1: Configurar Variables de Entorno

Crea o edita tu archivo `.env.docker` en la raíz del proyecto:

```bash
# Dominio (¡MUY IMPORTANTE!)
DOMAIN_NAME=midominio.com

# Base de datos
DB_USER=postgres
DB_PASSWORD=tu_password_seguro
DB_NAME=social_events_db

# Hosts permitidos (separados por coma)
ALLOWED_HOSTS=localhost,midominio.com,www.midominio.com

# Seguridad HTTPS (dejar en False hasta que SSL esté configurado)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Otros (opcional para primera instalación)
SECRET_KEY=tu_secret_key_aqui
DEBUG=False
```

### Paso 2: Preparar Certificados SSL

Ejecuta el script de inicialización para obtener certificados SSL de Let's Encrypt:

```bash
# Desde la raíz del proyecto
./scripts/init-letsencrypt.sh midominio.com admin@midominio.com 0
```

**Parámetros:**
- `midominio.com`: Tu dominio
- `admin@midominio.com`: Tu email (para notificaciones de Let's Encrypt)
- `0`: Producción (usa `1` para pruebas/staging)

⚠️ **IMPORTANTE**: Para pruebas iniciales, usa `1` (staging) para evitar límites de tasa de Let's Encrypt:
```bash
./scripts/init-letsencrypt.sh midominio.com admin@midominio.com 1
```

### Paso 3: Activar Seguridad HTTPS en Django

Una vez que los certificados estén instalados correctamente, actualiza `.env.docker`:

```bash
# Activar redirección y cookies seguras
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Paso 4: Reiniciar Servicios

```bash
cd docker
docker-compose down
docker-compose up -d
```

## 🔍 Verificación

### 1. Verificar que los contenedores estén corriendo:
```bash
docker-compose -f docker/docker-compose.yml ps
```

Deberías ver:
- `social_events_api` (Django)
- `social_events_nginx` (Nginx)
- `social_events_certbot` (Certbot)
- `social_events_postgres`
- `social_events_redis`

### 2. Probar HTTPS:
```bash
curl -I https://midominio.com
```

Deberías ver `HTTP/2 200` o `301/302` (redirección).

### 3. Verificar certificado:
```bash
openssl s_client -connect midominio.com:443 -servername midominio.com
```

### 4. Verificar logs:
```bash
# Logs de Nginx
docker-compose -f docker/docker-compose.yml logs nginx

# Logs de Django
docker-compose -f docker/docker-compose.yml logs web
```

## 🔄 Renovación Automática

Los certificados SSL se renuevan automáticamente cada 12 horas por el contenedor `certbot`. Let's Encrypt emite certificados válidos por 90 días.

Para forzar una renovación manual:
```bash
docker-compose -f docker/docker-compose.yml run --rm certbot renew
docker-compose -f docker/docker-compose.yml exec nginx nginx -s reload
```

## 🛠️ Comandos Útiles

### Recargar configuración de Nginx (sin downtime):
```bash
docker-compose -f docker/docker-compose.yml exec nginx nginx -s reload
```

### Ver certificados instalados:
```bash
docker-compose -f docker/docker-compose.yml run --rm certbot certificates
```

### Reiniciar solo Nginx:
```bash
docker-compose -f docker/docker-compose.yml restart nginx
```

### Ver logs en tiempo real:
```bash
docker-compose -f docker/docker-compose.yml logs -f nginx
```

### Acceder al shell de un contenedor:
```bash
docker-compose -f docker/docker-compose.yml exec web bash
```

## ❌ Solución de Problemas

### Error: "Connection refused" o 502 Bad Gateway

**Problema**: Nginx no puede conectarse a Django.

**Solución**:
```bash
# Verificar que Django esté corriendo
docker-compose -f docker/docker-compose.yml logs web

# Reiniciar el contenedor web
docker-compose -f docker/docker-compose.yml restart web
```

### Error: "SSL certificate problem"

**Problema**: Certificado no válido o no encontrado.

**Solución**:
```bash
# Verificar que los certificados existan
docker-compose -f docker/docker-compose.yml run --rm certbot certificates

# Si no existen, volver a ejecutar init-letsencrypt.sh
./scripts/init-letsencrypt.sh midominio.com admin@midominio.com 0
```

### Error: "Too many certificates already issued"

**Problema**: Límite de tasa de Let's Encrypt alcanzado.

**Solución**:
- Usa el servidor de staging para pruebas: `./scripts/init-letsencrypt.sh midominio.com email@example.com 1`
- Espera 1 semana para que se reinicie el límite
- Límites: 50 certificados por dominio por semana

### Error: "Challenge failed"

**Problema**: Let's Encrypt no puede verificar tu dominio.

**Solución**:
1. Verifica que tu dominio apunte a la IP correcta: `nslookup midominio.com`
2. Verifica que el puerto 80 esté abierto: `sudo ufw status`
3. Verifica logs de Nginx: `docker-compose logs nginx`

### Redirección infinita o CSRF errors

**Problema**: Configuración incorrecta de proxy headers.

**Solución**:
Verifica en `.env.docker`:
```bash
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
```

## 📁 Estructura de Archivos

```
docker/
├── docker-compose.yml          # Configuración de servicios
├── dockerfile                  # Imagen de Django
└── nginx/
    ├── nginx.conf              # Configuración principal de Nginx
    └── app.conf.template       # Configuración de la app (con variables)

scripts/
└── init-letsencrypt.sh         # Script de inicialización SSL

config/settings/
└── production.py               # Settings de Django con HTTPS habilitado
```

## 🔒 Configuraciones de Seguridad Django

El archivo `config/settings/production.py` incluye:

```python
# Redirigir todo a HTTPS
SECURE_SSL_REDIRECT = True

# Cookies solo en HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Header de proxy para HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

## 📊 Monitoreo

### Health Check:
```bash
curl https://midominio.com/health/
```

### SSL Labs Test:
Prueba la calidad de tu configuración SSL:
[https://www.ssllabs.com/ssltest/](https://www.ssllabs.com/ssltest/)

## 🔧 Configuración Adicional (Opcional)

### Agregar más dominios al certificado:

Edita `scripts/init-letsencrypt.sh` y agrega `-d otrodominio.com` al comando certbot.

### Cambiar el tamaño de la clave RSA:

En `init-letsencrypt.sh`, cambia:
```bash
RSA_KEY_SIZE=4096  # o 2048 para mejor performance
```

### Configurar CORS para HTTPS:

Si tu frontend está en otro dominio, actualiza en `config/settings/production.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "https://mifrontend.com",
    "https://www.mifrontend.com",
]
```

## 📚 Referencias

- [Let's Encrypt](https://letsencrypt.org/)
- [Certbot Documentation](https://certbot.eff.org/)
- [Nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [Django Security Settings](https://docs.djangoproject.com/en/stable/topics/security/)

## ✅ Checklist de Despliegue

- [ ] Dominio apunta a la IP del servidor
- [ ] Puertos 80 y 443 abiertos en firewall
- [ ] `.env.docker` configurado con `DOMAIN_NAME`
- [ ] Ejecutado `init-letsencrypt.sh` exitosamente
- [ ] Certificados SSL obtenidos
- [ ] `SECURE_SSL_REDIRECT=True` activado
- [ ] Servicios corriendo: `docker-compose ps`
- [ ] HTTPS funcionando: `curl -I https://midominio.com`
- [ ] Certificado válido verificado en navegador
- [ ] SSL Labs score A o superior

---

**¿Problemas?** Revisa los logs con `docker-compose logs -f nginx web`
