"""Configuración de la aplicación a partir de variables de entorno."""

from __future__ import annotations

import os


class Config:  # pylint: disable=too-few-public-methods
    """Valores por defecto; cada uno puede sobrescribirse con una variable de entorno."""

    SECRET_KEY = os.environ.get("CAFETERIA_SECRET_KEY")
    DATABASE = os.environ.get("CAFETERIA_DB")  # por defecto: instance/cafeteria.db
    DOMINIO_CORREO = os.environ.get("CAFETERIA_DOMINIO_CORREO", "universidad.edu.ec")
    CANTIDAD_MAXIMA = int(os.environ.get("CAFETERIA_CANTIDAD_MAXIMA", "50"))
    CARGAR_DATOS_DEMO = os.environ.get("CAFETERIA_DATOS_DEMO", "1") == "1"
    PERSONAL_INICIAL_USUARIO = os.environ.get("CAFETERIA_ADMIN_USUARIO", "admin")
    PERSONAL_INICIAL_CLAVE = os.environ.get("CAFETERIA_ADMIN_CLAVE", "cafeteria2026")
    CSRF_HABILITADO = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
