"""Productos de ejemplo para demostrar los procesos en la primera ejecución."""

from __future__ import annotations

import sqlite3

from app.dominio.modelos import Categoria, Producto
from app.persistencia.repositorios import ProductoRepositorio

PRODUCTOS_DEMO = [
    Producto("A01", "Sánduche de pollo", Categoria.ALIMENTO, 250),
    Producto("A02", "Empanada de queso", Categoria.ALIMENTO, 125),
    Producto("A03", "Bolón de verde", Categoria.ALIMENTO, 200),
    Producto("A04", "Ensalada de frutas", Categoria.ALIMENTO, 175),
    Producto("A05", "Almuerzo del día", Categoria.ALIMENTO, 350, disponible=False),
    Producto("B01", "Café pasado", Categoria.BEBIDA, 100),
    Producto("B02", "Capuchino", Categoria.BEBIDA, 175),
    Producto("B03", "Jugo natural de naranja", Categoria.BEBIDA, 150),
    Producto("B04", "Agua sin gas 500 ml", Categoria.BEBIDA, 75),
]


def cargar_datos_demo(conexion: sqlite3.Connection) -> int:
    """Carga los productos de ejemplo solo si el menú está vacío.

    Returns:
        Número de productos insertados.
    """
    repositorio = ProductoRepositorio(conexion)
    if repositorio.contar() > 0:
        return 0
    with conexion:
        for producto in PRODUCTOS_DEMO:
            repositorio.crear(Producto(producto.codigo, producto.nombre, producto.categoria,
                                       producto.precio_centavos, producto.disponible))
    return len(PRODUCTOS_DEMO)
