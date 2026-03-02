# 🚀 Pasos Rápidos para Activar HTTPS

## ⚡ Resumen de lo implementado

Se ha configurado tu proyecto con:
- ✅ Nginx como reverse proxy con soporte SSL/TLS
- ✅ Certbot para certificados Let's Encrypt (renovación automática)
- ✅ Configuraciones de seguridad Django para HTTPS
- ✅ Variables de entorno en `.env.docker`

## 📝 Pasos para Activar HTTPS

### 1️⃣ Editar `.env.docker`

Abre el archivo `.env.docker` y actualiza estas variables:

```bash
# Cambia esto por tu dominio real
DOMAIN_NAME=midominio.com

# Agrega tu dominio a ALLOWED_HOSTS
ALLOWED_HOSTS=localhost,127.0.0.1,midominio.com,www.midominio.com

# Cambia tu SECRET_KEY (genera una nueva)
SECRET_KEY=tu-secret-key-super-segura-aqui

# Configura tu base de datos
POSTGRES_PASSWORD=una-password-segura

# Mantén estos en False hasta que SSL esté funcionando
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

### 2️⃣ Asegúrate que tu dominio apunte a tu servidor

```bash
# Verifica que tu dominio apunte correctamente
nslookup midominio.com

# O con dig
dig midominio.com
```

### 3️⃣ Abre los puertos en tu firewall

```bash
# Si usas UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status

# Si usas firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 4️⃣ Ejecuta el script de inicialización SSL

```bash
# Desde la raíz del proyecto
cd /root/Documents/python/social-events-api

# IMPORTANTE: Primero prueba con staging (evita límites de Let's Encrypt)
./scripts/init-letsencrypt.sh midominio.com tu-email@example.com 1

# Si todo funciona bien, ejecuta con producción (último parámetro = 0)
./scripts/init-letsencrypt.sh midominio.com tu-email@example.com 0
```

⚠️ **Nota**: El parámetro `1` usa el servidor de staging de Let's Encrypt (para pruebas). El `0` usa producción.

### 5️⃣ Activa las configuraciones de seguridad HTTPS

Una vez que los certificados estén instalados correctamente, edita `.env.docker`:

```bash
# Cambia estos a True
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 6️⃣ Reinicia los servicios

```bash
cd docker
docker-compose down
docker-compose up -d

# Verifica que todo esté corriendo (Nginx estará en HTTP)
docker-compose ps
```

**Nota**: En este punto, tu aplicación estará corriendo en HTTP (puerto 80), no HTTPS aún.

### 7️⃣ Verifica que HTTP funcione

```bash
# Prueba HTTP (antes de SSL)
curl -I http://midominio.com

# Deberías ver: HTTP/1.1 200 OK
```

### 8️⃣ Ejecuta el script para obtener certificados SSL

```bash
# El script obtendrá los certificados y actualizará la configuración automáticamente
./scripts/init-letsencrypt.sh midominio.com tu-email@example.com 0
```

### 9️⃣ Activa las configuraciones de seguridad HTTPS

Una vez que el script termine exitosamente, edita `.env.docker`:

### Ver logs:
```bash
# Logs de Nginx
docker-compose -f docker/docker-compose.yml logs -f nginx

# Logs de Django
docker-compose -f docker/docker-compose.yml logs -f web

# Logs de Certbot
docker-compose -f docker/docker-compose.yml logs certbot
```

### Ver certificados:
```bash
docker-compose -f docker/docker-compose.yml run --rm certbot certificates
```

### Probar SSL en navegador:
Abre tu navegador y visita:
- `https://midominio.com`
- Verifica el candado verde en la barra de direcciones

### Probar calidad SSL:
- SSL Labs: https://www.ssllabs.com/ssltest/analyze.html?d=midominio.com

## 🎯 Estructura de archivos creados

```
📁 docker/
├── docker-compose.yml              ← Actualizado con nginx y certbot
└── nginx/
    ├── nginx.conf                  ← Configuración principal Nginx
    └── app.conf.template           ← Configuración de tu app

📁 scripts/
└── init-letsencrypt.sh             ← Script para obtener certificados

📁 config/settings/
└── production.py                   ← Settings Django con HTTPS

📁 docs/
├── HTTPS_SETUP.md                  ← Documentación completa
└── QUICK_START_HTTPS.md            ← Este archivo

📄 .env.docker                       ← Actualizado con DOMAIN_NAME y SSL vars
```

## ❓ Solución rápida de problemas

### Error: "502 Bad Gateway"
```bash
# Reinicia Django
docker-compose -f docker/docker-compose.yml restart web
```

### Error: "SSL certificate not found"
```bash
# Vuelve a ejecutar el script
./scripts/init-letsencrypt.sh midominio.com tu-email@example.com 0
```

### Error: "Too many certificates"
```bash
# Usa staging primero (límite de Let's Encrypt)
./scripts/init-letsencrypt.sh midominio.com tu-email@example.com 1
```

### Redirección infinita
```bash
# En .env.docker, verifica:
SECURE_SSL_REDIRECT=True  # debe estar en True
# Y que Nginx esté corriendo correctamente
```

## 📚 Documentación completa

Para información detallada, consulta: [docs/HTTPS_SETUP.md](HTTPS_SETUP.md)

## ✅ Checklist

- [ ] `DOMAIN_NAME` configurado en `.env.docker`
- [ ] Dominio apunta a la IP del servidor
- [ ] Puertos 80 y 443 abiertos
- [ ] Script `init-letsencrypt.sh` ejecutado
- [ ] Certificados SSL obtenidos
- [ ] `SECURE_SSL_REDIRECT=True` activado
- [ ] Servicios Docker corriendo
- [ ] HTTPS funcionando en navegador

---

**¿Todo listo?** Tu API ahora corre en HTTPS con certificados SSL automáticos 🔒✨
