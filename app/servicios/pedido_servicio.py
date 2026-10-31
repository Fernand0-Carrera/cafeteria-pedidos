"""Casos de uso de pedidos: registro (PN-01) y preparación y entrega (PN-02)."""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from typing import Callable, Mapping, Optional

from app.dominio.excepciones import (
    CantidadInvalidaError,
    EntregaInvalidaError,
    PedidoNoEncontradoError,
    PedidoVacioError,
    ProductoNoDisponibleError,
    ProductoNoEncontradoError,
    TotalDesactualizadoError,
    TransicionEstadoInvalidaError,
)
from app.dominio.modelos import CambioEstado, DetallePedido, EstadoPedido, Pedido, ResumenPedido
from app.dominio.validaciones import formatear_centavos
from app.persistencia.repositorios import PedidoRepositorio, ProductoRepositorio
from app.servicios.generador_codigo import generar_codigo_retiro, normalizar_codigo

INTENTOS_CODIGO = 20


def _ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class PedidoServicio:
    """Aplica las reglas RN-NEG-01 a RN-NEG-07 sobre los pedidos.

    Args:
        conexion: Conexión SQLite abierta.
        cantidad_maxima: Cantidad máxima por producto en un pedido.
        generador_codigo: Función que produce códigos de retiro (inyectable en pruebas).
        reloj: Función que devuelve la fecha y hora actual como texto (inyectable en pruebas).
    """

    def __init__(self, conexion: sqlite3.Connection, cantidad_maxima: int = 50,
                 generador_codigo: Callable[[], str] = generar_codigo_retiro,
                 reloj: Callable[[], str] = _ahora):
        self._con = conexion
        self._productos = ProductoRepositorio(conexion)
        self._pedidos = PedidoRepositorio(conexion)
        self._cantidad_maxima = cantidad_maxima
        self._generar_codigo = generador_codigo
        self._reloj = reloj

    # ------------------------------------------------------------------ PN-01
    def interpretar_cantidades(self, entradas: Mapping[str, str]) -> dict[str, int]:
        """Convierte las cantidades escritas en el formulario a enteros.

        Los campos vacíos o con ``0`` se interpretan como «producto no seleccionado».

        Raises:
            CantidadInvalidaError: Si alguna cantidad no es un número entero positivo.
        """
        cantidades: dict[str, int] = {}
        for codigo, texto in entradas.items():
            texto = (texto or "").strip()
            if texto in ("", "0"):
                continue
            if not re.fullmatch(r"[0-9]+", texto):
                raise CantidadInvalidaError(
                    f"La cantidad de {codigo} debe ser un número entero positivo (recibido: «{texto}»)."
                )
            cantidades[codigo] = int(texto)
        return cantidades

    def calcular_resumen(self, items: Mapping[str, int]) -> ResumenPedido:
        """Valida la selección y calcula el importe con los precios vigentes (RU-02, RU-03).

        Args:
            items: Diccionario código de producto → cantidad.

        Raises:
            PedidoVacioError: Si no hay productos (RN-NEG-01).
            CantidadInvalidaError: Si una cantidad no es entero positivo o supera el máximo (RN-NEG-01).
            ProductoNoEncontradoError: Si un código no existe.
            ProductoNoDisponibleError: Si un producto no está disponible (RN-NEG-02).
        """
        if not items:
            raise PedidoVacioError("Seleccione al menos un producto para registrar el pedido.")
        productos = self._productos.obtener_por_codigos(items.keys())
        detalles = []
        for codigo, cantidad in items.items():
            self._validar_cantidad(codigo, cantidad)
            producto = productos.get(codigo)
            if producto is None:
                raise ProductoNoEncontradoError(f"El producto {codigo} no existe en el menú.")
            if not producto.disponible:
                raise ProductoNoDisponibleError(f"«{producto.nombre}» ya no está disponible.")
            detalles.append(DetallePedido(
                producto_id=producto.id,
                codigo_producto=producto.codigo,
                nombre_producto=producto.nombre,
                cantidad=cantidad,
                precio_unitario_centavos=producto.precio_centavos,
            ))
        return ResumenPedido(detalles)

    def confirmar_pedido(self, cliente_id: int, items: Mapping[str, int],
                         total_mostrado_centavos: Optional[int] = None) -> Pedido:
        """Registra el pedido en estado Pendiente con un código de retiro único (RU-04).

        Se vuelven a validar las reglas al confirmar porque el menú pudo cambiar
        mientras el cliente revisaba su selección.

        Args:
            cliente_id: Cliente que confirma.
            items: Código de producto → cantidad.
            total_mostrado_centavos: Total que vio el cliente; si los precios cambiaron
                y el total es distinto, el pedido no se confirma.

        Raises:
            TotalDesactualizadoError: Si el total vigente difiere del mostrado (RN-NEG-03).
            ErrorNegocio: Cualquier error de :meth:`calcular_resumen`.
        """
        resumen = self.calcular_resumen(items)
        if total_mostrado_centavos is not None and resumen.total_centavos != total_mostrado_centavos:
            raise TotalDesactualizadoError(
                "Los precios cambiaron mientras revisaba su pedido. "
                f"El nuevo total es {formatear_centavos(resumen.total_centavos)}; revíselo y confirme otra vez."
            )
        pedido = Pedido(
            codigo_retiro=self._codigo_unico(),
            cliente_id=cliente_id,
            estado=EstadoPedido.PENDIENTE,
            fecha_registro=self._reloj(),
            total_centavos=resumen.total_centavos,
            detalles=resumen.detalles,
        )
        with self._con:
            self._pedidos.crear(pedido, usuario="cliente")
        return self._pedidos.obtener(pedido.id)

    def consultar_pedidos_cliente(self, cliente_id: int) -> list[Pedido]:
        """Pedidos del cliente con su estado actual (RU-05)."""
        return self._pedidos.listar_por_cliente(cliente_id)

    def consultar_pedido_cliente(self, cliente_id: int, pedido_id: int) -> Pedido:
        """Un pedido del cliente; impide consultar pedidos de otros clientes.

        Raises:
            PedidoNoEncontradoError: Si el pedido no existe o pertenece a otro cliente.
        """
        pedido = self._pedidos.obtener(pedido_id)
        if pedido is None or pedido.cliente_id != cliente_id:
            raise PedidoNoEncontradoError("No se encontró el pedido solicitado.")
        return pedido

    # ------------------------------------------------------------------ PN-02
    def listar_pedidos(self, estado: Optional[EstadoPedido] = None) -> list[Pedido]:
        """Pedidos para el personal, en orden de llegada (RU-07)."""
        return self._pedidos.listar(estado)

    def contar_por_estado(self) -> dict[EstadoPedido, int]:
        """Cantidad de pedidos en cada estado."""
        return self._pedidos.contar_por_estado()

    def obtener(self, pedido_id: int) -> Pedido:
        """Devuelve un pedido por su identificador.

        Raises:
            PedidoNoEncontradoError: Si no existe.
        """
        pedido = self._pedidos.obtener(pedido_id)
        if pedido is None:
            raise PedidoNoEncontradoError(f"No existe el pedido #{pedido_id}.")
        return pedido

    def historial(self, pedido_id: int) -> list[CambioEstado]:
        """Cambios de estado registrados para el pedido (seguimiento, RN-03)."""
        return self._pedidos.historial(pedido_id)

    def avanzar_estado(self, pedido_id: int, estado_nuevo: EstadoPedido, usuario: str) -> Pedido:
        """Pasa el pedido al estado siguiente: Pendiente → En preparación → Listo para retirar.

        La transición a Entregado no se permite aquí porque exige verificar el
        código de retiro; use :meth:`entregar_pedido`.

        Raises:
            TransicionEstadoInvalidaError: Si ``estado_nuevo`` no es el inmediato
                siguiente (RN-NEG-06) o si es Entregado (RN-NEG-07).
        """
        pedido = self.obtener(pedido_id)
        if estado_nuevo is EstadoPedido.ENTREGADO:
            raise TransicionEstadoInvalidaError(
                "Para marcar un pedido como Entregado debe verificar el código de retiro."
            )
        if pedido.estado.siguiente() is not estado_nuevo:
            raise TransicionEstadoInvalidaError(
                f"El pedido #{pedido_id} está «{pedido.estado.etiqueta}» y no puede pasar a "
                f"«{estado_nuevo.etiqueta}»."
            )
        self._cambiar_estado(pedido, estado_nuevo, usuario)
        return self.obtener(pedido_id)

    def buscar_por_codigo(self, codigo_presentado: str) -> Pedido:
        """Localiza el pedido que corresponde al código que presenta el cliente.

        Raises:
            PedidoNoEncontradoError: Si ningún pedido tiene ese código.
        """
        pedido = self._pedidos.obtener_por_codigo(normalizar_codigo(codigo_presentado))
        if pedido is None:
            raise PedidoNoEncontradoError("No existe ningún pedido con ese código de retiro.")
        return pedido

    def entregar_pedido(self, pedido_id: int, codigo_presentado: str, usuario: str) -> Pedido:
        """Registra la entrega de un pedido (RN-NEG-07).

        Raises:
            EntregaInvalidaError: Si el código no corresponde al pedido o si el
                pedido no está en estado Listo para retirar.
        """
        pedido = self.obtener(pedido_id)
        if normalizar_codigo(codigo_presentado) != pedido.codigo_retiro:
            raise EntregaInvalidaError("El código presentado no corresponde a este pedido.")
        if pedido.estado is not EstadoPedido.LISTO_PARA_RETIRAR:
            raise EntregaInvalidaError(
                f"El pedido está «{pedido.estado.etiqueta}»; solo se entregan pedidos Listos para retirar."
            )
        self._cambiar_estado(pedido, EstadoPedido.ENTREGADO, usuario)
        return self.obtener(pedido_id)

    # ------------------------------------------------------------- auxiliares
    def _validar_cantidad(self, codigo: str, cantidad: int) -> None:
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
            raise CantidadInvalidaError(f"La cantidad de {codigo} debe ser un número entero positivo.")
        if cantidad > self._cantidad_maxima:
            raise CantidadInvalidaError(
                f"La cantidad máxima por producto es {self._cantidad_maxima}."
            )

    def _codigo_unico(self) -> str:
        for _ in range(INTENTOS_CODIGO):
            codigo = self._generar_codigo()
            if not self._pedidos.existe_codigo(codigo):
                return codigo
        raise RuntimeError("No se pudo generar un código de retiro único.")

    def _cambiar_estado(self, pedido: Pedido, estado_nuevo: EstadoPedido, usuario: str) -> None:
        with self._con:
            if not self._pedidos.actualizar_estado(pedido.id, pedido.estado, estado_nuevo):
                raise TransicionEstadoInvalidaError(
                    f"El pedido #{pedido.id} fue modificado por otro usuario. Actualice la página."
                )
            self._pedidos.registrar_historial(pedido.id, estado_nuevo, self._reloj(), usuario)
