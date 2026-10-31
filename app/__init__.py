"""Sistema de gestión de pedidos de la cafetería universitaria.

Punto de entrada: :func:`create_app` construye la aplicación Flask.

Arquitectura en capas::

    web (Flask, plantillas)  →  servicios (reglas de negocio)
                             →  persistencia (repositorios SQLite)
                             →  dominio (entidades, validaciones, excepciones)
"""

from __future__ import annotations

import os
import secrets
from typing import Any, Optional

from flask import Flask

from app.config import Config
from app.datos_demo import cargar_datos_demo
from app.persistencia.db import conectar, crear_esquema
from app.servicios.personal_servicio import PersonalServicio

__version__ = "1.0.0"


def create_app(configuracion: Optional[dict[str, Any]] = None) -> Flask:
    """Crea y configura la aplicación Flask.

    Args:
        configuracion: Valores que sobrescriben :class:`app.config.Config`
            (se usa en las pruebas, por ejemplo para indicar otra base de datos).
    """
    aplicacion = Flask(__name__, instance_relative_config=True,
                       template_folder="web/templates", static_folder="web/static")
    aplicacion.config.from_object(Config)
    if configuracion:
        aplicacion.config.update(configuracion)
    os.makedirs(aplicacion.instance_path, exist_ok=True)
    if not aplicacion.config.get("DATABASE"):
        aplicacion.config["DATABASE"] = os.path.join(aplicacion.instance_path, "cafeteria.db")
    if not aplicacion.config.get("SECRET_KEY"):
        aplicacion.config["SECRET_KEY"] = _clave_secreta_persistente(aplicacion.instance_path)

    _inicializar_base(aplicacion)

    # pylint: disable=import-outside-toplevel
    from app.web import cliente, comun, personal
    comun.registrar(aplicacion)
    aplicacion.register_blueprint(cliente.bp)
    aplicacion.register_blueprint(personal.bp)
    return aplicacion


def _clave_secreta_persistente(carpeta: str) -> str:
    """Lee o genera la clave que firma las cookies de sesión."""
    ruta = os.path.join(carpeta, "secret_key")
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as archivo:
            return archivo.read().strip()
    clave = secrets.token_hex(32)
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(clave)
    return clave


def _inicializar_base(aplicacion: Flask) -> None:
    """Crea el esquema, el usuario inicial del personal y, si se pide, el menú de ejemplo."""
    conexion = conectar(aplicacion.config["DATABASE"])
    try:
        crear_esquema(conexion)
        personal = PersonalServicio(conexion)
        if not personal.hay_usuarios():
            personal.registrar(aplicacion.config["PERSONAL_INICIAL_USUARIO"], "Administrador",
                               aplicacion.config["PERSONAL_INICIAL_CLAVE"])
        if aplicacion.config["CARGAR_DATOS_DEMO"]:
            cargar_datos_demo(conexion)
    finally:
        conexion.close()
