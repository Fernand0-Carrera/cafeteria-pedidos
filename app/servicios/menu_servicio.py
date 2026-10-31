"""Casos de uso del menú: consulta (RU-01) y mantenimiento por el personal (RU-06)."""

from __future__ import annotations

import sqlite3

from app.dominio.excepciones import ProductoDuplicadoError, ProductoNoEncontradoError, ValidacionError
from app.dominio.modelos import Categoria, Producto
from app.dominio.validaciones import convertir_precio_a_centavos, validar_codigo_producto
from app.persistencia.repositorios import ProductoRepositorio


class MenuServicio:
    """Consulta y mantenimiento de los productos del menú."""

    def __init__(self, conexion: sqlite3.Connection):
        self._con = conexion
        self._productos = ProductoRepositorio(conexion)

    def listar_menu(self) -> list[Producto]:
        """Productos disponibles con sus precios, tal como los ve el cliente (RU-01)."""
        return self._productos.listar(solo_disponibles=True)

    def listar_todos(self) -> list[Producto]:
        """Todos los productos, incluidos los no disponibles (vista del personal)."""
        return self._productos.listar()

    def obtener(self, codigo: str) -> Producto:
        """Devuelve un producto por su código.

        Raises:
            ProductoNoEncontradoError: Si el código no existe.
        """
        producto = self._productos.obtener_por_codigo((codigo or "").strip().upper())
        if producto is None:
            raise ProductoNoEncontradoError(f"No existe un producto con código {codigo}.")
        return producto

    def registrar_producto(self, codigo: str, nombre: str, categoria: str,
                           precio: str, disponible: bool) -> Producto:
        """Registra un producto nuevo en el menú (RU-06).

        Raises:
            ValidacionError: Si algún dato no es válido.
            ProductoDuplicadoError: Si el código ya existe.
        """
        producto = Producto(
            codigo=validar_codigo_producto(codigo),
            nombre=self._validar_nombre(nombre),
            categoria=self._validar_categoria(categoria),
            precio_centavos=convertir_precio_a_centavos(precio),
            disponible=bool(disponible),
        )
        if self._productos.obtener_por_codigo(producto.codigo):
            raise ProductoDuplicadoError(f"Ya existe un producto con código {producto.codigo}.")
        with self._con:
            return self._productos.crear(producto)

    def actualizar_producto(self, codigo: str, nombre: str, categoria: str,
                            precio: str, disponible: bool) -> Producto:
        """Actualiza nombre, categoría, precio y disponibilidad (RU-06).

        El cambio de precio no afecta a pedidos ya registrados (RN-NEG-04),
        porque cada detalle de pedido guarda su propio precio unitario.
        """
        producto = self.obtener(codigo)
        producto.nombre = self._validar_nombre(nombre)
        producto.categoria = self._validar_categoria(categoria)
        producto.precio_centavos = convertir_precio_a_centavos(precio)
        producto.disponible = bool(disponible)
        with self._con:
            self._productos.actualizar(producto)
        return producto

    def cambiar_disponibilidad(self, codigo: str, disponible: bool) -> Producto:
        """Marca un producto como disponible o no disponible (RU-06, RN-NEG-02)."""
        producto = self.obtener(codigo)
        producto.disponible = bool(disponible)
        with self._con:
            self._productos.actualizar(producto)
        return producto

    @staticmethod
    def _validar_nombre(nombre: str) -> str:
        nombre = " ".join((nombre or "").split())
        if not 2 <= len(nombre) <= 80:
            raise ValidacionError("El nombre del producto debe tener entre 2 y 80 caracteres.")
        return nombre

    @staticmethod
    def _validar_categoria(categoria: str) -> Categoria:
        try:
            return Categoria((categoria or "").upper())
        except ValueError as error:
            raise ValidacionError("La categoría debe ser Alimento o Bebida.") from error
