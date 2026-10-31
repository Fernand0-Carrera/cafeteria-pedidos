"""Autenticación del personal de cafetería."""

from __future__ import annotations

import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from app.dominio.excepciones import CredencialesInvalidasError, ValidacionError
from app.persistencia.repositorios import PersonalRepositorio

LONGITUD_MINIMA_CLAVE = 8


class PersonalServicio:
    """Registro y autenticación de usuarios del personal."""

    def __init__(self, conexion: sqlite3.Connection):
        self._con = conexion
        self._personal = PersonalRepositorio(conexion)

    def registrar(self, usuario: str, nombre: str, clave: str) -> None:
        """Crea un usuario del personal con la clave almacenada como hash.

        Raises:
            ValidacionError: Si los datos son incompletos, la clave es corta o el usuario existe.
        """
        usuario = (usuario or "").strip().lower()
        nombre = " ".join((nombre or "").split())
        if not usuario or not nombre:
            raise ValidacionError("El usuario y el nombre son obligatorios.")
        if len(clave or "") < LONGITUD_MINIMA_CLAVE:
            raise ValidacionError(f"La clave debe tener al menos {LONGITUD_MINIMA_CLAVE} caracteres.")
        if self._personal.obtener(usuario):
            raise ValidacionError(f"El usuario {usuario} ya existe.")
        with self._con:
            self._personal.crear(usuario, nombre, generate_password_hash(clave))

    def autenticar(self, usuario: str, clave: str) -> str:
        """Verifica las credenciales y devuelve el nombre del usuario.

        Raises:
            CredencialesInvalidasError: Si el usuario no existe o la clave no coincide.
        """
        fila = self._personal.obtener((usuario or "").strip().lower())
        if fila is None or not check_password_hash(fila["hash_clave"], clave or ""):
            raise CredencialesInvalidasError("Usuario o clave incorrectos.")
        return fila["nombre"]

    def hay_usuarios(self) -> bool:
        """Indica si existe al menos un usuario del personal."""
        return self._personal.contar() > 0
