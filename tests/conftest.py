"""Fixtures compartidas por las pruebas.

pylint W0621 (redefined-outer-name) se desactiva en este módulo porque pytest inyecta
las fixtures como parámetros con el mismo nombre de la función que las define.
"""
# pylint: disable=redefined-outer-name

import re

import pytest

from app import create_app
from app.datos_demo import cargar_datos_demo
from app.dominio.modelos import EstadoPedido
from app.persistencia.db import conectar, crear_esquema
from app.servicios.cliente_servicio import ClienteServicio
from app.servicios.menu_servicio import MenuServicio
from app.servicios.pedido_servicio import PedidoServicio

DOMINIO = "epn.edu.ec"


def cedula_valida(prefijo: str) -> str:
    """Completa 9 dígitos con el dígito verificador de módulo 10."""
    suma = 0
    for i, c in enumerate(prefijo):
        v = int(c) * (2 if i % 2 == 0 else 1)
        suma += v - 9 if v > 9 else v
    return prefijo + str((10 - suma % 10) % 10)


@pytest.fixture
def conexion():
    """Base de datos en memoria con el menú de ejemplo."""
    con = conectar(":memory:")
    crear_esquema(con)
    cargar_datos_demo(con)
    yield con
    con.close()


@pytest.fixture
def menu(conexion):
    """Servicio de menú sobre la base en memoria."""
    return MenuServicio(conexion)


@pytest.fixture
def clientes(conexion):
    """Servicio de clientes con el dominio de prueba."""
    return ClienteServicio(conexion, DOMINIO)


@pytest.fixture
def pedidos(conexion):
    """Servicio de pedidos con cantidad máxima 50."""
    return PedidoServicio(conexion, cantidad_maxima=50)


@pytest.fixture
def cliente(clientes):
    """Cliente Ana Pérez ya registrado."""
    return clientes.registrar("Ana", "Pérez", cedula_valida("171003406"), "0991234567",
                              "ana@epn.edu.ec")


@pytest.fixture
def otro_cliente(clientes):
    """Segundo cliente, Luis Mora."""
    return clientes.registrar("Luis", "Mora", cedula_valida("090123456"), "0987654321",
                              "luis@epn.edu.ec")


@pytest.fixture
def pedido_listo(pedidos, cliente):
    """Pedido que ya pasó por En preparación y está Listo para retirar."""
    pedido = pedidos.confirmar_pedido(cliente.id, {"A01": 1})
    pedidos.avanzar_estado(pedido.id, EstadoPedido.EN_PREPARACION, "admin")
    return pedidos.avanzar_estado(pedido.id, EstadoPedido.LISTO_PARA_RETIRAR, "admin")


@pytest.fixture
def app(tmp_path):
    """Aplicación Flask con base temporal y CSRF desactivado."""
    return create_app({
        "DATABASE": str(tmp_path / "prueba.db"),
        "SECRET_KEY": "prueba",
        "CSRF_HABILITADO": False,
        "TESTING": True,
        "DOMINIO_CORREO": DOMINIO,
    })


@pytest.fixture
def web(app):
    """Cliente HTTP de prueba."""
    return app.test_client()


def registrar_web(cliente_http, cedula_prefijo="171003406", correo="ana@epn.edu.ec"):
    """Registra a un cliente desde el formulario web."""
    return cliente_http.post("/registro", data={
        "nombre": "Ana", "apellido": "Pérez", "cedula": cedula_valida(cedula_prefijo),
        "celular": "0991234567", "correo": correo})


def ingresar_personal(cliente_http, clave="cafeteria2026"):
    """Inicia sesión como el usuario inicial del personal."""
    return cliente_http.post("/personal/ingresar", data={"usuario": "admin", "clave": clave})


def extraer_codigo(html: str) -> str:
    """Obtiene el código de retiro mostrado en el ticket."""
    return re.search(r'id="codigo-retiro">(\w+)<', html).group(1)
