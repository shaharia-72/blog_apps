"""Environment-aware Django settings loader.

Default behavior uses development settings so local commands like
`python manage.py migrate` work out of the box.
Set DJANGO_ENV=production to switch to production settings.
"""

import os

DJANGO_ENV = os.getenv("DJANGO_ENV", "development").lower()

if DJANGO_ENV == "production":
    from .production import *  # noqa: F401,F403
else:
    from .development import *  # noqa: F401,F403
