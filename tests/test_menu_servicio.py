"""Pruebas del mantenimiento y consulta del menú (CP-09 a CP-13)."""

import pytest

from app.dominio.excepciones import ProductoDuplicadoError, ProductoNoEncontradoError, ValidacionError
from app.dominio.modelos import Categoria


def test_cp09_menu_del_cliente_muestra_solo_disponibles(menu):
    """CP-09 (RU-01): el menú del cliente lista solo productos disponibles con su precio."""
    productos = menu.listar_menu()
    assert productos and all(p.disponible for p in productos)
    assert "A05" not in {p.codigo for p in productos}          # Almuerzo del día: no disponible
    assert "A05" in {p.codigo for p in menu.listar_todos()}   # el personal sí lo ve
    assert all(p.precio_centavos > 0 for p in productos)


def test_cp10_registrar_producto_valido(menu):
    """CP-10 (RU-06): el personal registra un producto nuevo."""
    producto = menu.registrar_producto("b05", "Té de hierbas", "BEBIDA", "0.90", True)
    assert producto.id is not None
    guardado = menu.obtener("B05")
    assert (guardado.nombre, guardado.categoria, guardado.precio_centavos, guardado.disponible) == \
        ("Té de hierbas", Categoria.BEBIDA, 90, True)


def test_cp11_registrar_producto_duplicado_o_invalido(menu):
    """CP-11 (RU-06): no se admiten códigos repetidos ni datos inválidos."""
    with pytest.raises(ProductoDuplicadoError):
        menu.registrar_producto("A01", "Otro", "ALIMENTO", "1", True)
    with pytest.raises(ValidacionError):
        menu.registrar_producto("X1", "Otro", "POSTRE", "1", True)
    with pytest.raises(ValidacionError):
        menu.registrar_producto("X1", "", "ALIMENTO", "1", True)
    with pytest.raises(ValidacionError):
        menu.registrar_producto("X1", "Otro", "ALIMENTO", "-2", True)


def test_cp12_actualizar_producto(menu):
    """CP-12 (RU-06): se actualizan nombre, categoría, precio y disponibilidad."""
    menu.actualizar_producto("A01", "Sánduche de pollo grande", "ALIMENTO", "3.10", False)
    producto = menu.obtener("a01")
    assert (producto.nombre, producto.precio_centavos, producto.disponible) == \
        ("Sánduche de pollo grande", 310, False)
    with pytest.raises(ProductoNoEncontradoError):
        menu.actualizar_producto("NOEXISTE", "X", "ALIMENTO", "1", True)


def test_cp13_cambiar_disponibilidad(menu):
    """CP-13 (RU-06, RN-NEG-02): desactivar un producto lo retira del menú del cliente."""
    menu.cambiar_disponibilidad("B01", False)
    assert "B01" not in {p.codigo for p in menu.listar_menu()}
    menu.cambiar_disponibilidad("B01", True)
    assert "B01" in {p.codigo for p in menu.listar_menu()}
