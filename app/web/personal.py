"""Rutas del personal: pedidos (RU-07), entrega con código (RN-NEG-07) y menú (RU-06)."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.dominio.excepciones import ErrorNegocio
from app.dominio.modelos import EstadoPedido
from app.servicios.personal_servicio import PersonalServicio
from app.web.comun import obtener_conexion, personal_requerido, servicio_menu, servicio_pedidos

bp = Blueprint("personal", __name__, url_prefix="/personal")

ACCION_POR_ESTADO = {
    EstadoPedido.PENDIENTE: "Iniciar preparación",
    EstadoPedido.EN_PREPARACION: "Marcar listo para retirar",
}


@bp.route("/ingresar", methods=["GET", "POST"])
def ingresar():
    """Inicio de sesión del personal."""
    if request.method == "POST":
        try:
            nombre = PersonalServicio(obtener_conexion()).autenticar(
                request.form.get("usuario", ""), request.form.get("clave", ""))
        except ErrorNegocio as error:
            flash(error.mensaje, "error")
            return render_template("personal/ingresar.html", usuario=request.form.get("usuario", "")), 401
        session["personal_usuario"] = request.form["usuario"].strip().lower()
        session["personal_nombre"] = nombre
        return redirect(url_for("personal.pedidos"))
    return render_template("personal/ingresar.html", usuario="")


@bp.route("/salir", methods=["POST"])
def salir():
    """Cierra la sesión del personal."""
    session.pop("personal_usuario", None)
    session.pop("personal_nombre", None)
    return redirect(url_for("inicio"))


@bp.route("/pedidos")
@personal_requerido
def pedidos():
    """Pedidos agrupados por estado, en orden de llegada (RU-07, PN-02 paso 1)."""
    try:
        estado = EstadoPedido(request.args.get("estado", EstadoPedido.PENDIENTE.value))
    except ValueError:
        estado = EstadoPedido.PENDIENTE
    servicio = servicio_pedidos()
    return render_template("personal/pedidos.html", estado=estado, estados=list(EstadoPedido),
                           pedidos=servicio.listar_pedidos(estado), conteo=servicio.contar_por_estado(),
                           acciones=ACCION_POR_ESTADO)


@bp.route("/pedidos/<int:pedido_id>/avanzar", methods=["POST"])
@personal_requerido
def avanzar(pedido_id: int):
    """Registra el avance de estado de un pedido (PN-02 pasos 2 y 3)."""
    estado_origen = request.form.get("estado_origen", EstadoPedido.PENDIENTE.value)
    try:
        nuevo = EstadoPedido(request.form.get("estado_nuevo", ""))
        pedido = servicio_pedidos().avanzar_estado(pedido_id, nuevo, session["personal_usuario"])
        flash(f"Pedido #{pedido.id} ahora está «{pedido.estado.etiqueta}».", "exito")
    except ValueError:
        flash("Estado no reconocido.", "error")
    except ErrorNegocio as error:
        flash(error.mensaje, "error")
    return redirect(url_for("personal.pedidos", estado=estado_origen))


@bp.route("/entrega", methods=["GET", "POST"])
@personal_requerido
def entrega():
    """Busca el pedido que corresponde al código que presenta el cliente (PN-02 paso 4)."""
    pedido = None
    codigo = request.form.get("codigo", "")
    if request.method == "POST":
        try:
            pedido = servicio_pedidos().buscar_por_codigo(codigo)
        except ErrorNegocio as error:
            flash(error.mensaje, "error")
    return render_template("personal/entrega.html", pedido=pedido, codigo=codigo)


@bp.route("/entrega/confirmar", methods=["POST"])
@personal_requerido
def confirmar_entrega():
    """Registra el pedido como Entregado tras verificar el código (PN-02 paso 5, RN-NEG-07)."""
    try:
        pedido = servicio_pedidos().entregar_pedido(
            int(request.form.get("pedido_id", "0")), request.form.get("codigo", ""),
            session["personal_usuario"])
    except ErrorNegocio as error:
        flash(error.mensaje, "error")
        return redirect(url_for("personal.entrega"))
    flash(f"Pedido #{pedido.id} de {pedido.cliente_nombre} registrado como Entregado.", "exito")
    return redirect(url_for("personal.entrega"))


@bp.route("/productos")
@personal_requerido
def productos():
    """Listado completo del menú para su mantenimiento (RU-06)."""
    return render_template("personal/productos.html", productos=servicio_menu().listar_todos())


@bp.route("/productos/nuevo", methods=["GET", "POST"])
@personal_requerido
def nuevo_producto():
    """Registro de un producto nuevo (RU-06)."""
    datos = _datos_producto()
    if request.method == "POST":
        try:
            producto = servicio_menu().registrar_producto(**datos)
        except ErrorNegocio as error:
            flash(error.mensaje, "error")
            return render_template("personal/producto_form.html", datos=datos, nuevo=True), 422
        flash(f"Producto «{producto.nombre}» registrado.", "exito")
        return redirect(url_for("personal.productos"))
    datos["disponible"] = True
    return render_template("personal/producto_form.html", datos=datos, nuevo=True)


@bp.route("/productos/<codigo>/editar", methods=["GET", "POST"])
@personal_requerido
def editar_producto(codigo: str):
    """Actualización de nombre, categoría, precio y disponibilidad (RU-06)."""
    servicio = servicio_menu()
    producto = servicio.obtener(codigo)
    if request.method == "POST":
        datos = _datos_producto()
        datos["codigo"] = producto.codigo
        try:
            producto = servicio.actualizar_producto(**datos)
        except ErrorNegocio as error:
            flash(error.mensaje, "error")
            return render_template("personal/producto_form.html", datos=datos, nuevo=False), 422
        flash(f"Producto «{producto.nombre}» actualizado.", "exito")
        return redirect(url_for("personal.productos"))
    datos = {
        "codigo": producto.codigo, "nombre": producto.nombre, "categoria": producto.categoria.value,
        "precio": f"{producto.precio_centavos / 100:.2f}", "disponible": producto.disponible,
    }
    return render_template("personal/producto_form.html", datos=datos, nuevo=False)


@bp.route("/productos/<codigo>/disponibilidad", methods=["POST"])
@personal_requerido
def disponibilidad(codigo: str):
    """Activa o desactiva un producto con un solo clic (RU-06, RN-NEG-02)."""
    producto = servicio_menu().cambiar_disponibilidad(codigo, request.form.get("disponible") == "1")
    estado = "disponible" if producto.disponible else "no disponible"
    flash(f"«{producto.nombre}» ahora está {estado}.", "exito")
    return redirect(url_for("personal.productos"))


def _datos_producto() -> dict:
    return {
        "codigo": request.form.get("codigo", ""),
        "nombre": request.form.get("nombre", ""),
        "categoria": request.form.get("categoria", "ALIMENTO"),
        "precio": request.form.get("precio", ""),
        "disponible": request.form.get("disponible") == "1",
    }
