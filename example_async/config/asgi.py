"""ASGI entrypoint for the async blog.

Serve this with an ASGI server to run async views concurrently:

    uv run uvicorn config.asgi:application --app-dir example_async
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
