"""Rutas del cliente: registro, menú, pedido y consulta de estado (RU-01 a RU-05)."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.dominio.excepciones import ErrorNegocio, TotalDesactualizadoError
from app.web.comun import cliente_requerido, ruta_local, servicio_clientes, servicio_menu, servicio_pedidos

bp = Blueprint("cliente", __name__)

CAMPOS_REGISTRO = ("nombre", "apellido", "cedula", "celular", "correo")


@bp.route("/registro", methods=["GET", "POST"])
def registro():
    """Formulario de registro de un cliente nuevo."""
    datos = {campo: request.form.get(campo, "") for campo in CAMPOS_REGISTRO}
    if request.method == "POST":
        try:
            cliente = servicio_clientes().registrar(**datos)
        except ErrorNegocio as error:
            flash(error.mensaje, "error")
            return render_template("cliente/registro.html", datos=datos), 422
        _iniciar_sesion(cliente)
        flash(f"Registro completo. Su código de cliente es {cliente.codigo}.", "exito")
        return redirect(url_for("cliente.menu"))
    return render_template("cliente/registro.html", datos=datos)


@bp.route("/ingresar", methods=["GET", "POST"])
def ingresar():
    """Identificación del cliente con cédula y correo institucional."""
    siguiente = ruta_local(request.values.get("siguiente"), url_for("cliente.menu"))
    if request.method == "POST":
        try:
            cliente = servicio_clientes().identificar(request.form.get("cedula", ""),
                                                      request.form.get("correo", ""))
        except ErrorNegocio as error:
            flash(error.mensaje, "error")
            return render_template("cliente/ingresar.html", siguiente=siguiente,
                                   cedula=request.form.get("cedula", "")), 401
        _iniciar_sesion(cliente)
        return redirect(siguiente)
    return render_template("cliente/ingresar.html", siguiente=siguiente, cedula="")


@bp.route("/salir", methods=["POST"])
def salir():
    """Cierra la sesión del cliente."""
    for clave in ("cliente_id", "cliente_nombre", "cliente_codigo", "carrito"):
        session.pop(clave, None)
    return redirect(url_for("inicio"))


@bp.route("/menu")
def menu():
    """Menú con productos disponibles y precios (RU-01) y selección de cantidades (RU-02)."""
    return render_template("cliente/menu.html", productos=servicio_menu().listar_menu(),
                           cantidades=session.get("carrito", {}))


@bp.route("/pedido/revisar", methods=["POST"])
@cliente_requerido
def revisar():
    """Valida la selección y muestra el importe total antes de confirmar (RU-03)."""
    entradas = {clave[5:]: valor for clave, valor in request.form.items() if clave.startswith("cant_")}
    servicio = servicio_pedidos()
    try:
        items = servicio.interpretar_cantidades(entradas)
        resumen = servicio.calcular_resumen(items)
    except ErrorNegocio as error:
        flash(error.mensaje, "error")
        return render_template("cliente/menu.html", productos=servicio_menu().listar_menu(),
                               cantidades=entradas), 422
    session["carrito"] = items
    return render_template("cliente/revisar.html", resumen=resumen)


@bp.route("/pedido/confirmar", methods=["POST"])
@cliente_requerido
def confirmar():
    """Confirma el pedido y muestra el código de retiro (RU-04)."""
    items = session.get("carrito") or {}
    servicio = servicio_pedidos()
    try:
        total_mostrado = int(request.form.get("total_mostrado", ""))
    except ValueError:
        total_mostrado = None
    try:
        pedido = servicio.confirmar_pedido(session["cliente_id"], items, total_mostrado)
    except TotalDesactualizadoError as error:
        flash(error.mensaje, "error")
        return render_template("cliente/revisar.html", resumen=servicio.calcular_resumen(items)), 409
    except ErrorNegocio as error:
        flash(error.mensaje + " El pedido no se confirmó.", "error")
        return redirect(url_for("cliente.menu"))
    session.pop("carrito", None)
    return redirect(url_for("cliente.detalle_pedido", pedido_id=pedido.id, nuevo=1))


@bp.route("/mis-pedidos")
@cliente_requerido
def mis_pedidos():
    """Lista de pedidos del cliente con su estado (RU-05)."""
    pedidos = servicio_pedidos().consultar_pedidos_cliente(session["cliente_id"])
    return render_template("cliente/mis_pedidos.html", pedidos=pedidos)


@bp.route("/mis-pedidos/<int:pedido_id>")
@cliente_requerido
def detalle_pedido(pedido_id: int):
    """Resumen, código de retiro y seguimiento de un pedido (RU-04, RU-05)."""
    servicio = servicio_pedidos()
    pedido = servicio.consultar_pedido_cliente(session["cliente_id"], pedido_id)
    return render_template("cliente/detalle_pedido.html", pedido=pedido,
                           historial=servicio.historial(pedido_id),
                           nuevo=request.args.get("nuevo") == "1")


def _iniciar_sesion(cliente) -> None:
    session["cliente_id"] = cliente.id
    session["cliente_nombre"] = cliente.nombre_completo
    session["cliente_codigo"] = cliente.codigo
