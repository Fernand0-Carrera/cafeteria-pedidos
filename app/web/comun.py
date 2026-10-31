"""Elementos compartidos de la capa web: conexión por petición, CSRF, filtros y errores."""

from __future__ import annotations

import functools
import secrets
import sqlite3

import click
from flask import Flask, abort, current_app, g, redirect, render_template, request, session, url_for

from app.dominio.excepciones import ErrorNegocio
from app.dominio.validaciones import formatear_centavos
from app.persistencia.db import conectar
from app.servicios.cliente_servicio import ClienteServicio
from app.servicios.menu_servicio import MenuServicio
from app.servicios.pedido_servicio import PedidoServicio
from app.servicios.personal_servicio import PersonalServicio


def obtener_conexion() -> sqlite3.Connection:
    """Conexión SQLite asociada a la petición actual (se cierra al terminarla)."""
    if "db" not in g:
        g.db = conectar(current_app.config["DATABASE"])
    return g.db


def servicio_menu() -> MenuServicio:
    """Servicio de menú para la petición actual."""
    return MenuServicio(obtener_conexion())


def servicio_pedidos() -> PedidoServicio:
    """Servicio de pedidos para la petición actual."""
    return PedidoServicio(obtener_conexion(), cantidad_maxima=current_app.config["CANTIDAD_MAXIMA"])


def servicio_clientes() -> ClienteServicio:
    """Servicio de clientes para la petición actual."""
    return ClienteServicio(obtener_conexion(), current_app.config["DOMINIO_CORREO"])


def cliente_requerido(vista):
    """Decorador: exige que el cliente se haya identificado."""
    @functools.wraps(vista)
    def envoltura(*args, **kwargs):
        if "cliente_id" not in session:
            return redirect(url_for("cliente.ingresar", siguiente=request.path))
        return vista(*args, **kwargs)
    return envoltura


def personal_requerido(vista):
    """Decorador: exige una sesión del personal de cafetería."""
    @functools.wraps(vista)
    def envoltura(*args, **kwargs):
        if "personal_usuario" not in session:
            return redirect(url_for("personal.ingresar"))
        return vista(*args, **kwargs)
    return envoltura


def ruta_local(destino: str | None, por_defecto: str) -> str:
    """Acepta solo rutas internas para evitar redirecciones abiertas."""
    if destino and destino.startswith("/") and not destino.startswith("//"):
        return destino
    return por_defecto


def _token_csrf() -> str:
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def registrar(aplicacion: Flask) -> None:
    """Registra en la aplicación los elementos comunes."""

    @aplicacion.teardown_appcontext
    def cerrar_conexion(_error=None):
        conexion = g.pop("db", None)
        if conexion is not None:
            conexion.close()

    @aplicacion.before_request
    def verificar_csrf():
        if request.method == "POST" and aplicacion.config["CSRF_HABILITADO"]:
            esperado = session.get("csrf")
            enviado = request.form.get("csrf", "")
            # Sin token en la sesión no hay nada con qué comparar: se rechaza
            # (antes "" == "" permitía el envío; ver CP-44 en la documentación de pruebas).
            if not esperado or not secrets.compare_digest(enviado, esperado):
                abort(400, "El formulario expiró. Vuelva a cargar la página e inténtelo de nuevo.")

    @aplicacion.context_processor
    def variables_globales():
        return {"csrf_token": _token_csrf, "version": "1.0.0"}

    aplicacion.add_template_filter(formatear_centavos, "dinero")

    @aplicacion.route("/")
    def inicio():
        return render_template("inicio.html")

    @aplicacion.errorhandler(ErrorNegocio)
    def error_negocio(error: ErrorNegocio):
        return render_template("error.html", codigo=400, mensaje=error.mensaje), 400

    for codigo in (400, 403, 404, 405):
        aplicacion.register_error_handler(codigo, _manejador_http(codigo))

    @aplicacion.cli.command("crear-personal")
    @click.argument("usuario")
    @click.argument("nombre")
    @click.password_option("--clave", prompt="Clave")
    def crear_personal(usuario, nombre, clave):
        """Crea un usuario del personal de cafetería."""
        PersonalServicio(obtener_conexion()).registrar(usuario, nombre, clave)
        click.echo(f"Usuario {usuario} creado.")


def _manejador_http(codigo: int):
    mensajes = {
        400: "La solicitud no es válida.",
        403: "No tiene permiso para realizar esta acción.",
        404: "La página que busca no existe.",
        405: "Esta acción no está permitida desde aquí.",
    }

    def manejar(error):
        descripcion = getattr(error, "description", None)
        personalizado = descripcion and descripcion != type(error).description
        mensaje = descripcion if codigo == 400 and personalizado else mensajes[codigo]
        return render_template("error.html", codigo=codigo, mensaje=mensaje), codigo
    return manejar
