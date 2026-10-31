"""Generación de códigos de retiro aleatorios y fáciles de leer en voz alta."""

from __future__ import annotations

import secrets

# Se excluyen caracteres que se confunden al leerlos o dictarlos: 0/O, 1/I/L.
ALFABETO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
LONGITUD = 6


def generar_codigo_retiro(longitud: int = LONGITUD) -> str:
    """Genera un código aleatorio criptográficamente seguro, por ejemplo ``K7Q2MX``.

    La unicidad (RN-NEG-05) la garantiza ``PedidoServicio`` consultando la base
    de datos y la restricción ``UNIQUE`` de la tabla ``pedido``.
    """
    return "".join(secrets.choice(ALFABETO) for _ in range(longitud))


def normalizar_codigo(codigo: str) -> str:
    """Quita espacios y guiones y pasa a mayúsculas el código que presenta el cliente."""
    return (codigo or "").strip().upper().replace(" ", "").replace("-", "")
