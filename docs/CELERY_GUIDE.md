# 🔥 Celery Async Tasks - Guía Completa

## 📋 Índice

1. [Configuración](#configuración)
2. [Ejecutar Celery](#ejecutar-celery)
3. [Testing](#testing)
4. [Monitoring](#monitoring)
5. [Ejemplos de Uso](#ejemplos-de-uso)
6. [Troubleshooting](#troubleshooting)

---

## ⚙️ Configuración

### Verificar Redis

Celery usa Redis como broker. Verifica que esté corriendo:

```bash
redis-cli ping
# Debe responder: PONG
```

Si no está instalado:
```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# Docker
docker run -d -p 6379:6379 redis:alpine
```

### Variables de Entorno

Asegúrate de tener en tu `.env`:

```env
REDIS_URL=redis://localhost:6379/1
CELERY_BROKER_URL=redis://localhost:6379/0
```

---

## 🚀 Ejecutar Celery

### Opción 1: Scripts Incluidos (Recomendado)

```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery Worker
./start_celery.sh

# Terminal 3: Celery Beat (opcional, para tareas periódicas)
./start_celery_beat.sh
```

### Opción 2: Comandos Manuales

```bash
# Worker básico
celery -A config worker -l info

# Worker con más opciones
celery -A config worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=1000

# Beat scheduler (tareas periódicas)
celery -A config beat -l info
```

### Detener Celery

```bash
./stop_celery.sh

# O manualmente:
pkill -f 'celery worker'
pkill -f 'celery beat'
```

---

## 🧪 Testing

### 1. Verificar health de Celery

```bash
curl http://localhost:8000/api/celery-health/
```

**Respuesta esperada (workers corriendo):**
```json
{
  "status": "healthy",
  "message": "1 worker(s) running",
  "workers": [
    {
      "name": "celery@hostname",
      "status": "active",
      "pool": "prefork",
      "max_concurrency": 4
    }
  ],
  "active_tasks": 0,
  "registered_tasks_count": 10
}
```

**Respuesta si no hay workers:**
```json
{
  "status": "error",
  "message": "No Celery workers are running",
  "workers": [],
  "recommendation": "Start a worker with: celery -A config worker -l info"
}
```

### 2. Ejecutar tarea síncrona (sin Celery)

```bash
curl http://localhost:8000/api/test/
```

Verás los logs en consola inmediatamente.

### 3. Ejecutar tarea asíncrona (con Celery worker)

```bash
curl "http://localhost:8000/api/test/?mode=async"
```

**Respuesta:**
```json
{
  "message": "Task enqueued successfully!",
  "task_id": "abc-123-def-456",
  "status_url": "/api/task-status/abc-123-def-456/",
  "mode": "async",
  "note": "Check logs to see task execution"
}
```

### 4. Verificar estado de la tarea

```bash
curl http://localhost:8000/api/task-status/abc-123-def-456/
```

**Estados posibles:**

- **PENDING**: Esperando ejecución
- **PROGRESS**: En progreso
- **SUCCESS**: Completada
- **FAILURE**: Falló
- **RETRY**: Reintentando

---

## 📊 Monitoring

### Logs en Consola

Con la configuración actual, verás logs detallados:

```
[INFO] common.view test - 🔥 Test API endpoint hit!
[INFO] celery.worker.strategy - 📋 Task Started: common.test_task [ID: abc-123]
[INFO] common.view test_task - ⏳ Starting test task... [Task ID: abc-123]
[INFO] common.view test_task - 🔄 Progress: 1/5 (20% per step)
[INFO] common.view test_task - 🔄 Progress: 2/5 (20% per step)
...
[INFO] common.view test_task - ✅ Test task completed! [Task ID: abc-123]
[INFO] celery.worker.strategy - ✅ Task Finished: common.test_task
[INFO] celery.worker.strategy - 🎉 Task Success: common.test_task
```

### Logs en Archivo

Los logs también se guardan en:

- `logs/django.log` - Logs de Django y la aplicación
- `logs/celery_worker.log` - Logs del worker de Celery
- `logs/celery_beat.log` - Logs del scheduler

### Flower (UI de Monitoring - Opcional)

```bash
pip install flower

celery -A config flower
# Visita: http://localhost:5555
```

---

## 💡 Ejemplos de Uso

### Crear una Tarea Simple

```python
# apps/myapp/tasks.py
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="myapp.send_email")
def send_email(self, user_id, subject, message):
    logger.info(f"📧 Sending email to user {user_id}")
    
    try:
        # Tu lógica aquí
        # send_mail(...)
        
        logger.info(f"✅ Email sent to user {user_id}")
        return {"status": "sent", "user_id": user_id}
        
    except Exception as exc:
        logger.error(f"❌ Email failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
```

### Ejecutar la Tarea

```python
# Desde una vista o cualquier parte del código
from apps.myapp.tasks import send_email

# Asíncrono
task = send_email.delay(user_id=123, subject="Hello", message="World")
print(f"Task ID: {task.id}")

# Especificar countdown (delay)
send_email.apply_async(
    args=[123, "Hello", "World"],
    countdown=60  # Ejecutar en 60 segundos
)

# Con ETA específica
from datetime import datetime, timedelta
send_email.apply_async(
    args=[123, "Hello", "World"],
    eta=datetime.now() + timedelta(hours=1)
)
```

### Tarea con Progreso

```python
@shared_task(bind=True)
def process_large_file(self, file_id):
    logger.info(f"Processing file {file_id}")
    
    total_items = 100
    for i in range(total_items):
        # Procesar item
        
        # Actualizar progreso
        self.update_state(
            state='PROGRESS',
            meta={
                'current': i + 1,
                'total': total_items,
                'percent': ((i + 1) / total_items) * 100
            }
        )
    
    return {'status': 'completed', 'processed': total_items}
```

### Tareas Periódicas con Celery Beat

```python
# config/settings/base.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'send-daily-digest': {
        'task': 'apps.notifications.tasks.send_daily_digest',
        'schedule': crontab(hour=8, minute=0),  # Diario a las 8:00 AM
    },
    'cleanup-old-sessions': {
        'task': 'apps.users.tasks.cleanup_sessions',
        'schedule': crontab(hour=2, minute=0),  # Diario a las 2:00 AM
    },
    'check-upcoming-events': {
        'task': 'apps.events.tasks.send_reminders',
        'schedule': 300.0,  # Cada 5 minutos (300 segundos)
    },
}
```

---

## 🔧 Troubleshooting

### Error: "No module named 'config.celery'"

**Solución:**
```bash
# Asegúrate de estar en el directorio correcto
cd /path/to/project

# Verifica que config/__init__.py importe celery
cat config/__init__.py
# Debe tener: from .celery import app as celery_app
```

### Error: "ConnectionError: Error 111 connecting to localhost:6379"

**Problema:** Redis no está corriendo

**Solución:**
```bash
# Verificar
redis-cli ping

# Iniciar
sudo systemctl start redis  # Linux
brew services start redis   # macOS
```

### Las tareas no se ejecutan

**Checklist:**

1. ✅ Redis está corriendo: `redis-cli ping`
2. ✅ Worker está corriendo: `curl http://localhost:8000/api/celery-health/`
3. ✅ Tarea está registrada: Verifica logs del worker al iniciar
4. ✅ Broker URL correcto en `.env`

### Los logs no aparecen

**Solución:**
```python
# Verifica que tengas en settings/base.py la configuración LOGGING
# Y que tu tarea tenga:
import logging
logger = logging.getLogger(__name__)

# NO:
logger = logging.getLogger('celery')  # ❌

# SÍ:
logger = logging.getLogger(__name__)  # ✅
```

### Tarea stuck en PENDING

**Causas posibles:**

1. Worker no está corriendo
2. Tarea no está registrada (typo en el nombre)
3. Worker se crasheó

**Solución:**
```bash
# Reiniciar worker
./stop_celery.sh
./start_celery.sh

# Verificar logs
tail -f logs/celery_worker.log
```

---

## 📚 Recursos Adicionales

- [Celery Docs](https://docs.celeryproject.org/)
- [Django-Celery Integration](https://docs.celeryproject.org/en/stable/django/)
- [Redis Docs](https://redis.io/documentation)
- [Flower Docs](https://flower.readthedocs.io/)

---

## 🎯 Quick Commands Cheat Sheet

```bash
# Iniciar todo
python manage.py runserver        # Terminal 1
./start_celery.sh                 # Terminal 2

# Testing
curl http://localhost:8000/api/celery-health/
curl http://localhost:8000/api/test/
curl "http://localhost:8000/api/test/?mode=async"

# Monitoring
tail -f logs/celery_worker.log
tail -f logs/django.log

# Detener
./stop_celery.sh
```
