import os
from . import base, dev, production

from dotenv import load_dotenv

load_dotenv()

SETTINGS = base.SETTINGS

if os.getenv('FLASK_ENV') == 'dev':
    SETTINGS.update(dev.SETTINGS)

if os.getenv('FLASK_ENV') == 'production':
    SETTINGS.update(production.SETTINGS)
