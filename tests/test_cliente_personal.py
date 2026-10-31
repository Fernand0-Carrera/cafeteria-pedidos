"""Pruebas de clientes, personal y persistencia (CP-36 a CP-40)."""

import pytest

from app import create_app
from app.dominio.excepciones import ClienteDuplicadoError, CredencialesInvalidasError, ValidacionError
from app.persistencia.db import conectar
from app.servicios.pedido_servicio import PedidoServicio
from app.servicios.personal_servicio import PersonalServicio
from tests.conftest import cedula_valida


def test_cp36_registro_de_cliente(clientes):
    """CP-36: el cliente se registra con sus datos y recibe un código CLI-xxxxx."""
    cliente = clientes.registrar(" Ana ", "Pérez", cedula_valida("171003406"), "0991234567",
                                 "ANA@universidad.edu.ec")
    assert cliente.codigo == "CLI-00001"
    assert cliente.nombre_completo == "Ana Pérez" and cliente.correo == "ana@universidad.edu.ec"
    assert clientes.obtener(cliente.id).cedula == cedula_valida("171003406")


def test_cp37_cliente_duplicado_o_datos_invalidos(clientes, cliente):
    """CP-37: no se repiten cédula ni correo; los datos inválidos se informan."""
    with pytest.raises(ClienteDuplicadoError, match="cédula"):
        clientes.registrar("Otra", "Persona", cliente.cedula, "0990000000", "otra@universidad.edu.ec")
    with pytest.raises(ClienteDuplicadoError, match="correo"):
        clientes.registrar("Otra", "Persona", cedula_valida("010101010"), "0990000000", cliente.correo)
    with pytest.raises(ValidacionError):
        clientes.registrar("Otra", "Persona", "1234567890", "0990000000", "otra@universidad.edu.ec")


def test_cp38_identificacion_de_cliente(clientes, cliente):
    """CP-38: el cliente se identifica con cédula y correo; otras combinaciones se rechazan."""
    assert clientes.identificar(cliente.cedula, " ANA@universidad.edu.ec ").id == cliente.id
    for cedula, correo in [(cliente.cedula, "otro@universidad.edu.ec"),
                           (cedula_valida("090123456"), cliente.correo), ("", "")]:
        with pytest.raises(CredencialesInvalidasError):
            clientes.identificar(cedula, correo)


def test_cp39_autenticacion_del_personal(conexion):
    """CP-39: el personal ingresa con usuario y clave; la clave se guarda como hash."""
    servicio = PersonalServicio(conexion)
    assert not servicio.hay_usuarios()
    servicio.registrar("Maria", "María López", "clave-segura")
    assert servicio.autenticar(" maria ", "clave-segura") == "María López"
    fila = conexion.execute("SELECT hash_clave FROM personal").fetchone()
    assert "clave-segura" not in fila[0]
    with pytest.raises(CredencialesInvalidasError):
        servicio.autenticar("maria", "otra-clave")
    with pytest.raises(CredencialesInvalidasError):
        servicio.autenticar("nadie", "clave-segura")
    with pytest.raises(ValidacionError):
        servicio.registrar("maria", "Duplicada", "clave-segura")
    with pytest.raises(ValidacionError):
        servicio.registrar("pedro", "Pedro", "corta")
    with pytest.raises(ValidacionError):
        servicio.registrar("", "", "clave-segura")


def test_cp40_la_informacion_persiste_entre_ejecuciones(tmp_path):
    """CP-40 (sección 8): productos, clientes y pedidos siguen disponibles al reiniciar."""
    ruta = str(tmp_path / "persistencia.db")
    configuracion = {"DATABASE": ruta, "SECRET_KEY": "x", "DOMINIO_CORREO": "universidad.edu.ec"}
    create_app(configuracion)                           # primera ejecución
    con = conectar(ruta)
    from app.servicios.cliente_servicio import ClienteServicio  # pylint: disable=import-outside-toplevel
    cliente = ClienteServicio(con, "universidad.edu.ec").registrar(
        "Ana", "Pérez", cedula_valida("171003406"), "0991234567", "ana@universidad.edu.ec")
    codigo = PedidoServicio(con).confirmar_pedido(cliente.id, {"A01": 1}).codigo_retiro
    con.close()

    create_app(configuracion)                           # segunda ejecución sobre el mismo archivo
    con = conectar(ruta)
    pedido = PedidoServicio(con).buscar_por_codigo(codigo)
    productos = con.execute("SELECT COUNT(*) FROM producto").fetchone()[0]
    usuarios = con.execute("SELECT COUNT(*) FROM personal").fetchone()[0]
    con.close()
    assert pedido.cliente_nombre == "Ana Pérez"
    assert productos == 9 and usuarios == 1             # no se duplican datos iniciales
