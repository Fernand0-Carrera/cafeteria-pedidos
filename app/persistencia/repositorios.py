"""Repositorios: traducen entre filas de SQLite y entidades del dominio.

Los repositorios no aplican reglas de negocio; solo leen y escriben datos.
Las transacciones las controla la capa de servicios.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Iterable, Optional

from app.dominio.modelos import (
    CambioEstado,
    Categoria,
    Cliente,
    DetallePedido,
    EstadoPedido,
    Pedido,
    Producto,
)


def _a_producto(fila: sqlite3.Row) -> Producto:
    return Producto(
        id=fila["id"],
        codigo=fila["codigo"],
        nombre=fila["nombre"],
        categoria=Categoria(fila["categoria"]),
        precio_centavos=fila["precio_centavos"],
        disponible=bool(fila["disponible"]),
    )


def _a_cliente(fila: sqlite3.Row) -> Cliente:
    return Cliente(
        id=fila["id"],
        codigo=fila["codigo"],
        nombre=fila["nombre"],
        apellido=fila["apellido"],
        cedula=fila["cedula"],
        celular=fila["celular"],
        correo=fila["correo"],
    )


class ProductoRepositorio:
    """Acceso a la tabla ``producto``."""

    def __init__(self, conexion: sqlite3.Connection):
        self._con = conexion

    def listar(self, solo_disponibles: bool = False) -> list[Producto]:
        """Lista productos ordenados por categoría y nombre."""
        sql = "SELECT * FROM producto"
        if solo_disponibles:
            sql += " WHERE disponible = 1"
        sql += " ORDER BY categoria, nombre"
        return [_a_producto(f) for f in self._con.execute(sql)]

    def obtener_por_codigo(self, codigo: str) -> Optional[Producto]:
        """Devuelve el producto con el código indicado o ``None``."""
        fila = self._con.execute("SELECT * FROM producto WHERE codigo = ?", (codigo,)).fetchone()
        return _a_producto(fila) if fila else None

    def obtener_por_codigos(self, codigos: Iterable[str]) -> dict[str, Producto]:
        """Devuelve un diccionario código → producto para los códigos existentes."""
        codigos = list(codigos)
        if not codigos:
            return {}
        # La lista viaja como un único parámetro JSON: la sentencia SQL es fija y no
        # se construye concatenando texto (evita el aviso B608 de inyección SQL).
        filas = self._con.execute(
            "SELECT * FROM producto WHERE codigo IN (SELECT value FROM json_each(?))",
            (json.dumps(codigos),),
        )
        return {f["codigo"]: _a_producto(f) for f in filas}

    def crear(self, producto: Producto) -> Producto:
        """Inserta un producto y devuelve la entidad con su ``id``."""
        cursor = self._con.execute(
            "INSERT INTO producto (codigo, nombre, categoria, precio_centavos, disponible) "
            "VALUES (?, ?, ?, ?, ?)",
            (producto.codigo, producto.nombre, producto.categoria.value,
             producto.precio_centavos, int(producto.disponible)),
        )
        producto.id = cursor.lastrowid
        return producto

    def actualizar(self, producto: Producto) -> None:
        """Actualiza nombre, categoría, precio y disponibilidad de un producto."""
        self._con.execute(
            "UPDATE producto SET nombre = ?, categoria = ?, precio_centavos = ?, disponible = ? "
            "WHERE codigo = ?",
            (producto.nombre, producto.categoria.value, producto.precio_centavos,
             int(producto.disponible), producto.codigo),
        )

    def contar(self) -> int:
        """Número total de productos registrados."""
        return self._con.execute("SELECT COUNT(*) FROM producto").fetchone()[0]


class ClienteRepositorio:
    """Acceso a la tabla ``cliente``."""

    def __init__(self, conexion: sqlite3.Connection):
        self._con = conexion

    def crear(self, cliente: Cliente) -> Cliente:
        """Inserta el cliente y le asigna un código con formato ``CLI-00001``."""
        cursor = self._con.execute(
            "INSERT INTO cliente (nombre, apellido, cedula, celular, correo) VALUES (?, ?, ?, ?, ?)",
            (cliente.nombre, cliente.apellido, cliente.cedula, cliente.celular, cliente.correo),
        )
        cliente.id = cursor.lastrowid
        cliente.codigo = f"CLI-{cliente.id:05d}"
        self._con.execute("UPDATE cliente SET codigo = ? WHERE id = ?", (cliente.codigo, cliente.id))
        return cliente

    def obtener_por_id(self, cliente_id: int) -> Optional[Cliente]:
        """Devuelve el cliente con el ``id`` indicado o ``None``."""
        fila = self._con.execute("SELECT * FROM cliente WHERE id = ?", (cliente_id,)).fetchone()
        return _a_cliente(fila) if fila else None

    def obtener_por_cedula(self, cedula: str) -> Optional[Cliente]:
        """Devuelve el cliente con la cédula indicada o ``None``."""
        fila = self._con.execute("SELECT * FROM cliente WHERE cedula = ?", (cedula,)).fetchone()
        return _a_cliente(fila) if fila else None

    def existe_correo(self, correo: str) -> bool:
        """Indica si el correo ya está registrado."""
        return self._con.execute("SELECT 1 FROM cliente WHERE correo = ?", (correo,)).fetchone() is not None


class PedidoRepositorio:
    """Acceso a las tablas ``pedido``, ``detalle_pedido`` e ``historial_estado``."""

    _SELECT_PEDIDO = (
        "SELECT p.*, c.nombre || ' ' || c.apellido AS cliente_nombre "
        "FROM pedido p JOIN cliente c ON c.id = p.cliente_id"
    )

    def __init__(self, conexion: sqlite3.Connection):
        self._con = conexion

    def existe_codigo(self, codigo_retiro: str) -> bool:
        """Indica si ya existe un pedido con ese código de retiro."""
        return self._con.execute(
            "SELECT 1 FROM pedido WHERE codigo_retiro = ?", (codigo_retiro,)
        ).fetchone() is not None

    def crear(self, pedido: Pedido, usuario: str) -> Pedido:
        """Inserta el pedido, sus detalles y el primer registro del historial."""
        cursor = self._con.execute(
            "INSERT INTO pedido (codigo_retiro, cliente_id, estado, fecha_registro, total_centavos) "
            "VALUES (?, ?, ?, ?, ?)",
            (pedido.codigo_retiro, pedido.cliente_id, pedido.estado.value,
             pedido.fecha_registro, pedido.total_centavos),
        )
        pedido.id = cursor.lastrowid
        self._con.executemany(
            "INSERT INTO detalle_pedido (pedido_id, producto_id, codigo_producto, nombre_producto, "
            "cantidad, precio_unitario_centavos) VALUES (?, ?, ?, ?, ?, ?)",
            [(pedido.id, d.producto_id, d.codigo_producto, d.nombre_producto, d.cantidad,
              d.precio_unitario_centavos) for d in pedido.detalles],
        )
        self.registrar_historial(pedido.id, pedido.estado, pedido.fecha_registro, usuario)
        return pedido

    def registrar_historial(self, pedido_id: int, estado: EstadoPedido, fecha: str, usuario: str) -> None:
        """Agrega una fila al historial de estados del pedido."""
        self._con.execute(
            "INSERT INTO historial_estado (pedido_id, estado, fecha, usuario) VALUES (?, ?, ?, ?)",
            (pedido_id, estado.value, fecha, usuario),
        )

    def actualizar_estado(self, pedido_id: int, estado_actual: EstadoPedido,
                          estado_nuevo: EstadoPedido) -> bool:
        """Cambia el estado solo si el pedido sigue en ``estado_actual``.

        Returns:
            ``True`` si se actualizó; ``False`` si otro usuario lo cambió antes
            (control de concurrencia optimista).
        """
        cursor = self._con.execute(
            "UPDATE pedido SET estado = ? WHERE id = ? AND estado = ?",
            (estado_nuevo.value, pedido_id, estado_actual.value),
        )
        return cursor.rowcount == 1

    def obtener(self, pedido_id: int) -> Optional[Pedido]:
        """Devuelve el pedido con sus detalles o ``None``."""
        fila = self._con.execute(f"{self._SELECT_PEDIDO} WHERE p.id = ?", (pedido_id,)).fetchone()
        return self._con_detalles(fila) if fila else None

    def obtener_por_codigo(self, codigo_retiro: str) -> Optional[Pedido]:
        """Devuelve el pedido con el código de retiro indicado o ``None``."""
        fila = self._con.execute(
            f"{self._SELECT_PEDIDO} WHERE p.codigo_retiro = ?", (codigo_retiro,)
        ).fetchone()
        return self._con_detalles(fila) if fila else None

    def listar_por_cliente(self, cliente_id: int) -> list[Pedido]:
        """Pedidos del cliente, del más reciente al más antiguo."""
        filas = self._con.execute(
            f"{self._SELECT_PEDIDO} WHERE p.cliente_id = ? ORDER BY p.id DESC", (cliente_id,)
        )
        return [self._con_detalles(f) for f in filas]

    def listar(self, estado: Optional[EstadoPedido] = None) -> list[Pedido]:
        """Pedidos filtrados por estado, del más antiguo al más reciente (orden de atención)."""
        if estado is None:
            filas = self._con.execute(f"{self._SELECT_PEDIDO} ORDER BY p.id")
        else:
            filas = self._con.execute(
                f"{self._SELECT_PEDIDO} WHERE p.estado = ? ORDER BY p.id", (estado.value,)
            )
        return [self._con_detalles(f) for f in filas]

    def contar_por_estado(self) -> dict[EstadoPedido, int]:
        """Cantidad de pedidos en cada estado."""
        conteo = {estado: 0 for estado in EstadoPedido}
        for fila in self._con.execute("SELECT estado, COUNT(*) AS n FROM pedido GROUP BY estado"):
            conteo[EstadoPedido(fila["estado"])] = fila["n"]
        return conteo

    def historial(self, pedido_id: int) -> list[CambioEstado]:
        """Cambios de estado del pedido en orden cronológico."""
        filas = self._con.execute(
            "SELECT estado, fecha, usuario FROM historial_estado WHERE pedido_id = ? ORDER BY id",
            (pedido_id,),
        )
        return [CambioEstado(EstadoPedido(f["estado"]), f["fecha"], f["usuario"]) for f in filas]

    def _con_detalles(self, fila: sqlite3.Row) -> Pedido:
        detalles = [
            DetallePedido(
                producto_id=d["producto_id"],
                codigo_producto=d["codigo_producto"],
                nombre_producto=d["nombre_producto"],
                cantidad=d["cantidad"],
                precio_unitario_centavos=d["precio_unitario_centavos"],
            )
            for d in self._con.execute(
                "SELECT * FROM detalle_pedido WHERE pedido_id = ? ORDER BY id", (fila["id"],)
            )
        ]
        return Pedido(
            id=fila["id"],
            codigo_retiro=fila["codigo_retiro"],
            cliente_id=fila["cliente_id"],
            estado=EstadoPedido(fila["estado"]),
            fecha_registro=fila["fecha_registro"],
            total_centavos=fila["total_centavos"],
            detalles=detalles,
            cliente_nombre=fila["cliente_nombre"],
        )


class PersonalRepositorio:
    """Acceso a la tabla ``personal`` (usuarios del personal de cafetería)."""

    def __init__(self, conexion: sqlite3.Connection):
        self._con = conexion

    def crear(self, usuario: str, nombre: str, hash_clave: str) -> None:
        """Registra un usuario del personal."""
        self._con.execute(
            "INSERT INTO personal (usuario, nombre, hash_clave) VALUES (?, ?, ?)",
            (usuario, nombre, hash_clave),
        )

    def obtener(self, usuario: str) -> Optional[sqlite3.Row]:
        """Devuelve la fila del usuario o ``None``."""
        return self._con.execute("SELECT * FROM personal WHERE usuario = ?", (usuario,)).fetchone()

    def contar(self) -> int:
        """Número de usuarios del personal."""
        return self._con.execute("SELECT COUNT(*) FROM personal").fetchone()[0]
