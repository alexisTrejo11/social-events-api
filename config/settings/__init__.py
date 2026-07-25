"""
Settings initialization - auto-detects environment.

Priority:
1. DJANGO_SETTINGS_MODULE environment variable
2. If not set, defaults to 'development'
"""

import os

# Get the settings module from environment
# Default to development if not specified
settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "").split(".")[-1]

if settings_module == "production":
    from .production import *
elif settings_module == "test":
    from .test import *
elif settings_module == "development":
    from .development import *
else:
    # Default to development
    from .development import *
