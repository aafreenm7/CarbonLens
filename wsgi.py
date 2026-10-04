"""CarbonLens WSGI Production Entry Point.

Use with Gunicorn, Waitress, or any WSGI-compliant application server:
    gunicorn "wsgi:application"
    waitress-serve --port=5000 wsgi:application
"""

import os
from app import create_app

env_mode = os.environ.get("FLASK_ENV", "production")
application = create_app(env_mode)
app = application

if __name__ == "__main__":
    application.run()
