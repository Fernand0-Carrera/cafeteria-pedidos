"""Entidades del dominio: Producto, Cliente, Pedido y Detalle del pedido.

Los importes se manejan siempre en **centavos** (enteros) para evitar
errores de redondeo propios de los números de punto flotante.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Categoria(str, Enum):
    """Tipo de producto ofrecido en el menú."""

    ALIMENTO = "ALIMENTO"
    BEBIDA = "BEBIDA"

    @property
    def etiqueta(self) -> str:
        """Nombre legible de la categoría."""
        return "Alimento" if self is Categoria.ALIMENTO else "Bebida"


class EstadoPedido(str, Enum):
    """Etapas de atención de un pedido (RN-NEG-06).

    El orden de declaración es el único orden permitido de avance:
    Pendiente → En preparación → Listo para retirar → Entregado.
    """

    PENDIENTE = "PENDIENTE"
    EN_PREPARACION = "EN_PREPARACION"
    LISTO_PARA_RETIRAR = "LISTO_PARA_RETIRAR"
    ENTREGADO = "ENTREGADO"

    @property
    def etiqueta(self) -> str:
        """Nombre legible del estado, tal como aparece en la especificación."""
        return _ETIQUETAS_ESTADO[self]

    def siguiente(self) -> Optional["EstadoPedido"]:
        """Devuelve el estado inmediatamente posterior, o ``None`` si es el último."""
        orden = list(EstadoPedido)
        posicion = orden.index(self)
        return orden[posicion + 1] if posicion + 1 < len(orden) else None


_ETIQUETAS_ESTADO = {
    EstadoPedido.PENDIENTE: "Pendiente",
    EstadoPedido.EN_PREPARACION: "En preparación",
    EstadoPedido.LISTO_PARA_RETIRAR: "Listo para retirar",
    EstadoPedido.ENTREGADO: "Entregado",
}


@dataclass
class Producto:
    """Artículo del menú identificado por un código único."""

    codigo: str
    nombre: str
    categoria: Categoria
    precio_centavos: int
    disponible: bool = True
    id: Optional[int] = None


@dataclass
class Cliente:
    """Estudiante o docente que registra pedidos."""

    nombre: str
    apellido: str
    cedula: str
    celular: str
    correo: str
    codigo: Optional[str] = None
    id: Optional[int] = None

    @property
    def nombre_completo(self) -> str:
        """Nombre y apellido del cliente."""
        return f"{self.nombre} {self.apellido}"


@dataclass
class DetallePedido:
    """Producto incluido en un pedido con su cantidad y el precio congelado (RN-NEG-04)."""

    producto_id: int
    codigo_producto: str
    nombre_producto: str
    cantidad: int
    precio_unitario_centavos: int

    @property
    def subtotal_centavos(self) -> int:
        """Precio unitario multiplicado por la cantidad."""
        return self.precio_unitario_centavos * self.cantidad


@dataclass
class CambioEstado:
    """Registro histórico de un cambio de estado de un pedido."""

    estado: EstadoPedido
    fecha: str
    usuario: str


@dataclass
class Pedido:  # pylint: disable=too-many-instance-attributes
    """Solicitud confirmada por un cliente.

    Reúne los atributos que la especificación (sección 7) exige para un pedido;
    dividirlo solo para satisfacer el umbral de pylint empeoraría la legibilidad.
    """

    codigo_retiro: str
    cliente_id: int
    estado: EstadoPedido
    fecha_registro: str
    total_centavos: int
    detalles: list[DetallePedido] = field(default_factory=list)
    id: Optional[int] = None
    cliente_nombre: Optional[str] = None


@dataclass
class ResumenPedido:
    """Selección revisada por el cliente antes de confirmar (RU-03)."""

    detalles: list[DetallePedido]

    @property
    def total_centavos(self) -> int:
        """Suma de precio vigente × cantidad de cada línea (RN-NEG-03)."""
        return sum(detalle.subtotal_centavos for detalle in self.detalles)
