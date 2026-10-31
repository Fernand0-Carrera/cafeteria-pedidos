"""Pruebas unitarias de validaciones de datos (CP-01 a CP-08)."""

import pytest

from app.dominio.excepciones import ValidacionError
from app.dominio.validaciones import (
    convertir_precio_a_centavos,
    formatear_centavos,
    validar_cedula,
    validar_celular,
    validar_codigo_producto,
    validar_correo_institucional,
    validar_nombre,
)
from tests.conftest import cedula_valida


def test_cp01_cedula_valida_es_aceptada():
    """CP-01: una cédula con dígito verificador correcto se acepta."""
    assert validar_cedula(" 1710034065 ") == "1710034065"
    assert validar_cedula(cedula_valida("300000000")) == cedula_valida("300000000")


def test_cp02_cedula_con_verificador_incorrecto_es_rechazada():
    """CP-02: cambiar el último dígito invalida la cédula."""
    with pytest.raises(ValidacionError, match="verificador"):
        validar_cedula("1710034064")


@pytest.mark.parametrize("cedula, motivo", [
    ("", "10 dígitos"), ("171003406", "10 dígitos"), ("17100340651", "10 dígitos"),
    ("17A0034065", "10 dígitos"), ("2510034065", "provincia"), ("0010034065", "provincia"),
    ("1760034065", "tercer dígito"),
])
def test_cp03_cedula_con_formato_invalido_es_rechazada(cedula, motivo):
    """CP-03: longitud, caracteres, provincia y tercer dígito se validan."""
    with pytest.raises(ValidacionError, match=motivo):
        validar_cedula(cedula)


@pytest.mark.parametrize("correo", ["Ana@Universidad.edu.ec", "a.b-c@estud.universidad.edu.ec"])
def test_cp04_correo_institucional_valido(correo):
    """CP-04: se acepta el dominio institucional y sus subdominios; se normaliza a minúsculas."""
    assert validar_correo_institucional(correo, "universidad.edu.ec") == correo.lower()


@pytest.mark.parametrize("correo", ["ana@gmail.com", "ana@universidad.edu.ec.com",
                                    "ana@fakeuniversidad.edu.ec", "ana", "@universidad.edu.ec",
                                    "a na@universidad.edu.ec"])
def test_cp05_correo_no_institucional_es_rechazado(correo):
    """CP-05: correos de otros dominios o mal formados se rechazan."""
    with pytest.raises(ValidacionError, match="institucional"):
        validar_correo_institucional(correo, "universidad.edu.ec")


def test_cp06_celular_y_nombre():
    """CP-06: celular ecuatoriano de 10 dígitos que empieza con 09; nombres solo con letras."""
    assert validar_celular("099 123 4567") == "0991234567"
    for invalido in ("0891234567", "099123456", "09912345678", "abc"):
        with pytest.raises(ValidacionError):
            validar_celular(invalido)
    assert validar_nombre("  María   José ", "nombre") == "María José"
    with pytest.raises(ValidacionError):
        validar_nombre("R2D2", "nombre")


@pytest.mark.parametrize("texto, centavos", [("1.50", 150), ("1,5", 150), ("2", 200),
                                             (" 0.05 ", 5), ("1000", 100000)])
def test_cp07_precio_se_convierte_a_centavos(texto, centavos):
    """CP-07: el precio se interpreta con punto o coma decimal."""
    assert convertir_precio_a_centavos(texto) == centavos


@pytest.mark.parametrize("texto", ["0", "-1", "1.505", "abc", "", "1000.01", "NaN", "Infinity"])
def test_cp08_precio_invalido_es_rechazado(texto):
    """CP-08: precio no positivo, con más de 2 decimales, no numérico o excesivo."""
    with pytest.raises(ValidacionError):
        convertir_precio_a_centavos(texto)


def test_formato_de_dinero_y_codigo_de_producto():
    """Apoyo a CP-09: formato de importes y normalización del código de producto."""
    assert formatear_centavos(5) == "$0.05"
    assert formatear_centavos(1250) == "$12.50"
    assert validar_codigo_producto(" b01 ") == "B01"
    with pytest.raises(ValidacionError):
        validar_codigo_producto("CODIGO-DEMASIADO-LARGO")
