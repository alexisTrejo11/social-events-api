# OAuth2 Quick Start

## 🎯 Configuración Rápida

### Paso 1: Instalar Dependencias
```bash
pip install -r requirements.txt
```

### Paso 2: Ejecutar Migraciones
```bash
python manage.py migrate
```

### Paso 3: Crear Superusuario
```bash
python manage.py createsuperuser
```

### Paso 4: Obtener Credenciales OAuth

#### Google:
1. Ve a: https://console.cloud.google.com/
2. Crea un proyecto → APIs & Services → Credentials
3. Crea OAuth 2.0 Client ID
4. Añade redirect URI: `http://localhost:8000/accounts/google/login/callback/`
5. Copia Client ID y Client Secret

#### GitHub:
1. Ve a: https://github.com/settings/developers
2. New OAuth App
3. Callback URL: `http://localhost:8000/accounts/github/login/callback/`
4. Copia Client ID y Client Secret

### Paso 5: Configurar en Django Admin

1. Inicia el servidor:
   ```bash
   python manage.py runserver
   ```

2. Ve a: http://localhost:8000/admin/

3. **Sites** → Edita `example.com`:
   - Domain: `localhost:8000`
   - Display name: `Social Events`
   - Save

4. **Social applications** → Add:
   
   **Google:**
   - Provider: `Google`
   - Name: `Google OAuth`
   - Client id: [Tu Google Client ID]
   - Secret key: [Tu Google Client Secret]
   - Sites: Selecciona `localhost:8000`
   - Save
   
   **GitHub:**
   - Provider: `GitHub`
   - Name: `GitHub OAuth`
   - Client id: [Tu GitHub Client ID]
   - Secret key: [Tu GitHub Client Secret]
   - Sites: Selecciona `localhost:8000`
   - Save

### Paso 6: Probar

Los endpoints están disponibles en:
- `POST /api/v2/auth/oauth/google/` - Login con Google
- `POST /api/v2/auth/oauth/github/` - Login con GitHub
- `GET /api/v2/auth/oauth/accounts/` - Ver cuentas conectadas
- `POST /api/v2/auth/oauth/disconnect/` - Desconectar cuenta

Documentación completa: Ver `docs/OAUTH_SETUP.md`

API Docs: http://localhost:8000/api/docs/

---

## 📝 Notas Importantes

1. ⚠️ Las credenciales se configuran en el **Admin de Django**, NO en el archivo .env (aunque también es posible)
2. ✅ Las credenciales se guardan en la base de datos de forma segura
3. 🔒 Nunca expongas tus Client Secrets en el frontend
4. 🌐 Para producción, actualiza las URLs de callback en Google/GitHub
