"""Casos de uso de registro e identificación de clientes."""

from __future__ import annotations

import sqlite3

from app.dominio.excepciones import ClienteDuplicadoError, CredencialesInvalidasError
from app.dominio.modelos import Cliente
from app.dominio.validaciones import (
    validar_cedula,
    validar_celular,
    validar_correo_institucional,
    validar_nombre,
)
from app.persistencia.repositorios import ClienteRepositorio


class ClienteServicio:
    """Registro de clientes e identificación para consultar sus pedidos."""

    def __init__(self, conexion: sqlite3.Connection, dominio_correo: str):
        self._con = conexion
        self._clientes = ClienteRepositorio(conexion)
        self._dominio = dominio_correo

    def registrar(self, nombre: str, apellido: str, cedula: str,
                  celular: str, correo: str) -> Cliente:
        """Valida y registra un cliente; le asigna un código ``CLI-xxxxx``.

        Raises:
            ValidacionError: Si algún dato no es válido.
            ClienteDuplicadoError: Si la cédula o el correo ya están registrados.
        """
        cliente = Cliente(
            nombre=validar_nombre(nombre, "nombre"),
            apellido=validar_nombre(apellido, "apellido"),
            cedula=validar_cedula(cedula),
            celular=validar_celular(celular),
            correo=validar_correo_institucional(correo, self._dominio),
        )
        if self._clientes.obtener_por_cedula(cliente.cedula):
            raise ClienteDuplicadoError("Ya existe un cliente registrado con esa cédula.")
        if self._clientes.existe_correo(cliente.correo):
            raise ClienteDuplicadoError("Ya existe un cliente registrado con ese correo.")
        with self._con:
            return self._clientes.crear(cliente)

    def identificar(self, cedula: str, correo: str) -> Cliente:
        """Identifica a un cliente registrado por su cédula y correo institucional.

        Raises:
            CredencialesInvalidasError: Si no existe un cliente con esa combinación.
        """
        cliente = self._clientes.obtener_por_cedula((cedula or "").strip())
        if cliente is None or cliente.correo != (correo or "").strip().lower():
            raise CredencialesInvalidasError("La cédula y el correo no corresponden a un cliente registrado.")
        return cliente

    def obtener(self, cliente_id: int) -> Cliente | None:
        """Devuelve el cliente por su identificador interno."""
        return self._clientes.obtener_por_id(cliente_id)
