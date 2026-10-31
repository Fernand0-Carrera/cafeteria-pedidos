"""Funciones de validación y conversión de datos de entrada."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from app.dominio.excepciones import ValidacionError

PRECIO_MAXIMO_CENTAVOS = 100_000  # 1 000,00 USD
_PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]{2,60}$")
_PATRON_CELULAR = re.compile(r"^09\d{8}$")
_PATRON_CODIGO_PRODUCTO = re.compile(r"^[A-Z0-9-]{2,10}$")
_PATRON_USUARIO_CORREO = re.compile(r"^[A-Za-z0-9._%+-]+$")


def _digito_verificador_cedula(nueve_digitos: str) -> int:
    """Calcula el dígito verificador (módulo 10, coeficientes 2-1-2-1...)."""
    suma = 0
    for posicion, caracter in enumerate(nueve_digitos):
        valor = int(caracter) * (2 if posicion % 2 == 0 else 1)
        suma += valor - 9 if valor > 9 else valor
    return (10 - suma % 10) % 10


def _provincia_valida(codigo: int) -> bool:
    """Provincias 01 a 24, más 30 para ecuatorianos registrados en el exterior."""
    return 1 <= codigo <= 24 or codigo == 30


def validar_cedula(cedula: str) -> str:
    """Valida una cédula ecuatoriana con el algoritmo de módulo 10.

    Args:
        cedula: Texto ingresado por el usuario.

    Returns:
        La cédula sin espacios.

    Raises:
        ValidacionError: Si la cédula no tiene 10 dígitos, la provincia o el
            tercer dígito no son válidos, o el dígito verificador no coincide.
    """
    cedula = (cedula or "").strip()
    if not (len(cedula) == 10 and cedula.isascii() and cedula.isdigit()):
        raise ValidacionError("La cédula debe tener exactamente 10 dígitos.")
    if not _provincia_valida(int(cedula[:2])):
        raise ValidacionError("Los dos primeros dígitos de la cédula no corresponden a una provincia.")
    if int(cedula[2]) >= 6:
        raise ValidacionError("El tercer dígito de la cédula no es válido para personas naturales.")
    if _digito_verificador_cedula(cedula[:9]) != int(cedula[9]):
        raise ValidacionError("La cédula ingresada no es válida (dígito verificador incorrecto).")
    return cedula


def validar_nombre(valor: str, campo: str) -> str:
    """Valida nombres y apellidos: solo letras, espacios, apóstrofo o guion (2-60 caracteres)."""
    valor = " ".join((valor or "").split())
    if not _PATRON_NOMBRE.match(valor):
        raise ValidacionError(f"El {campo} debe tener entre 2 y 60 letras.")
    return valor


def validar_celular(celular: str) -> str:
    """Valida un celular ecuatoriano de 10 dígitos que empieza con 09."""
    celular = (celular or "").strip().replace(" ", "")
    if not _PATRON_CELULAR.match(celular):
        raise ValidacionError("El celular debe tener 10 dígitos y empezar con 09.")
    return celular


def validar_correo_institucional(correo: str, dominio: str) -> str:
    """Valida que el correo pertenezca al dominio institucional o a un subdominio suyo.

    Args:
        correo: Correo ingresado.
        dominio: Dominio institucional configurado, por ejemplo ``universidad.edu.ec``.

    Returns:
        El correo normalizado en minúsculas.
    """
    correo = (correo or "").strip().lower()
    dominio = dominio.lower().lstrip("@")
    usuario, separador, dominio_correo = correo.partition("@")
    dominio_valido = dominio_correo == dominio or dominio_correo.endswith("." + dominio)
    if not (separador and _PATRON_USUARIO_CORREO.match(usuario) and dominio_valido):
        raise ValidacionError(f"Use su correo institucional (terminado en @{dominio}).")
    return correo


def validar_codigo_producto(codigo: str) -> str:
    """Normaliza a mayúsculas y valida el código de producto (2-10 letras, números o guion)."""
    codigo = (codigo or "").strip().upper()
    if not _PATRON_CODIGO_PRODUCTO.match(codigo):
        raise ValidacionError("El código del producto debe tener de 2 a 10 letras, números o guiones.")
    return codigo


def convertir_precio_a_centavos(texto: str) -> int:
    """Convierte un precio escrito por el usuario (``1.50`` o ``1,50``) a centavos.

    Raises:
        ValidacionError: Si no es un número, tiene más de dos decimales,
            es menor o igual a cero o supera el máximo permitido.
    """
    texto = (texto or "").strip().replace(",", ".")
    try:
        valor = Decimal(texto)
    except InvalidOperation as error:
        raise ValidacionError("El precio debe ser un número, por ejemplo 1.50.") from error
    if not valor.is_finite() or valor.as_tuple().exponent < -2:
        raise ValidacionError("El precio admite como máximo dos decimales.")
    centavos = int(valor * 100)
    if centavos <= 0:
        raise ValidacionError("El precio debe ser mayor que cero.")
    if centavos > PRECIO_MAXIMO_CENTAVOS:
        raise ValidacionError("El precio no puede superar 1000.00.")
    return centavos


def formatear_centavos(centavos: int) -> str:
    """Representa un importe en dólares, por ejemplo ``$2.75``."""
    return f"${centavos // 100}.{centavos % 100:02d}"
