"""Excepciones de negocio de la cafetería.

Cada excepción indica, cuando aplica, la regla de negocio (``RN-NEG-xx``)
que la origina, para facilitar la trazabilidad entre requisitos, código y pruebas.
"""


class ErrorNegocio(Exception):
    """Error base de todas las violaciones de reglas o validaciones del dominio.

    Attributes:
        mensaje: Texto comprensible para el usuario final.
        regla: Identificador de la regla de negocio relacionada (puede ser ``None``).
    """

    regla = None

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


class ValidacionError(ErrorNegocio):
    """Un dato ingresado no cumple el formato o rango esperado."""


class PedidoVacioError(ErrorNegocio):
    """El pedido no contiene productos (RN-NEG-01)."""

    regla = "RN-NEG-01"


class CantidadInvalidaError(ErrorNegocio):
    """La cantidad de un producto no es un entero positivo (RN-NEG-01)."""

    regla = "RN-NEG-01"


class ProductoNoDisponibleError(ErrorNegocio):
    """Se intentó pedir un producto no disponible (RN-NEG-02)."""

    regla = "RN-NEG-02"


class ProductoNoEncontradoError(ErrorNegocio):
    """El código de producto no existe en el menú."""


class ProductoDuplicadoError(ErrorNegocio):
    """Ya existe un producto con el mismo código."""


class TotalDesactualizadoError(ErrorNegocio):
    """El total mostrado al cliente ya no coincide con los precios vigentes (RN-NEG-03)."""

    regla = "RN-NEG-03"


class TransicionEstadoInvalidaError(ErrorNegocio):
    """El cambio de estado solicitado no respeta el orden permitido (RN-NEG-06)."""

    regla = "RN-NEG-06"


class EntregaInvalidaError(ErrorNegocio):
    """El pedido no puede entregarse: estado incorrecto o código no coincide (RN-NEG-07)."""

    regla = "RN-NEG-07"


class PedidoNoEncontradoError(ErrorNegocio):
    """No existe un pedido con el identificador o código indicado."""


class ClienteDuplicadoError(ErrorNegocio):
    """Ya existe un cliente con la misma cédula o correo."""


class CredencialesInvalidasError(ErrorNegocio):
    """Los datos de acceso no corresponden a un usuario registrado."""
