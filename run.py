"""Arranque de la aplicación: ``python run.py`` y abrir http://127.0.0.1:5000"""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host=os.environ.get("CAFETERIA_HOST", "127.0.0.1"),
            port=int(os.environ.get("CAFETERIA_PUERTO", "5000")),
            debug=False)
