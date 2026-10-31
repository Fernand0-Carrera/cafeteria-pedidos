"""Creación de conexiones y del esquema de la base de datos SQLite.

La información de productos, clientes y pedidos persiste entre ejecuciones
en un archivo ``.db`` (requisito de la sección 8 de la especificación).
"""

from __future__ import annotations

import sqlite3

ESQUEMA = """
CREATE TABLE IF NOT EXISTS producto (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo          TEXT    NOT NULL UNIQUE,
    nombre          TEXT    NOT NULL,
    categoria       TEXT    NOT NULL CHECK (categoria IN ('ALIMENTO', 'BEBIDA')),
    precio_centavos INTEGER NOT NULL CHECK (precio_centavos > 0),
    disponible      INTEGER NOT NULL DEFAULT 1 CHECK (disponible IN (0, 1))
);

CREATE TABLE IF NOT EXISTS cliente (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo   TEXT UNIQUE,
    nombre   TEXT NOT NULL,
    apellido TEXT NOT NULL,
    cedula   TEXT NOT NULL UNIQUE,
    celular  TEXT NOT NULL,
    correo   TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS pedido (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_retiro  TEXT    NOT NULL UNIQUE,
    cliente_id     INTEGER NOT NULL REFERENCES cliente (id),
    estado         TEXT    NOT NULL CHECK (estado IN
                   ('PENDIENTE', 'EN_PREPARACION', 'LISTO_PARA_RETIRAR', 'ENTREGADO')),
    fecha_registro TEXT    NOT NULL,
    total_centavos INTEGER NOT NULL CHECK (total_centavos > 0)
);

CREATE TABLE IF NOT EXISTS detalle_pedido (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id                INTEGER NOT NULL REFERENCES pedido (id) ON DELETE CASCADE,
    producto_id              INTEGER NOT NULL REFERENCES producto (id),
    codigo_producto          TEXT    NOT NULL,
    nombre_producto          TEXT    NOT NULL,
    cantidad                 INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario_centavos INTEGER NOT NULL CHECK (precio_unitario_centavos > 0),
    UNIQUE (pedido_id, producto_id)
);

CREATE TABLE IF NOT EXISTS historial_estado (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL REFERENCES pedido (id) ON DELETE CASCADE,
    estado    TEXT    NOT NULL,
    fecha     TEXT    NOT NULL,
    usuario   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS personal (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario    TEXT NOT NULL UNIQUE,
    nombre     TEXT NOT NULL,
    hash_clave TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pedido_estado  ON pedido (estado);
CREATE INDEX IF NOT EXISTS idx_pedido_cliente ON pedido (cliente_id);
"""


def conectar(ruta: str) -> sqlite3.Connection:
    """Abre una conexión con claves foráneas activas y filas accesibles por nombre.

    Args:
        ruta: Ruta del archivo de base de datos o ``":memory:"``.
    """
    conexion = sqlite3.connect(ruta)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def crear_esquema(conexion: sqlite3.Connection) -> None:
    """Crea las tablas e índices si todavía no existen (operación idempotente)."""
    conexion.executescript(ESQUEMA)
    conexion.commit()
