"""Pruebas de integración de la interfaz web (CP-41 a CP-47)."""

import re

from app import create_app
from tests.conftest import extraer_codigo, ingresar_personal, registrar_web


def test_cp41_flujo_completo_registro_de_pedido(web):
    """CP-41 (PN-01): registro → menú → revisión con total → confirmación con código."""
    anonimo = web.get("/menu").get_data(as_text=True)
    assert "$2.50" in anonimo and "para hacer un pedido" in anonimo and "cant_A01" not in anonimo
    respuesta = registrar_web(web)
    assert respuesta.status_code == 302
    menu = web.get("/menu").get_data(as_text=True)
    assert "Sánduche de pollo" in menu and "$2.50" in menu and "Almuerzo del día" not in menu
    revision = web.post("/pedido/revisar", data={"cant_A01": "2", "cant_B02": "1", "cant_B01": ""})
    html = revision.get_data(as_text=True)
    assert revision.status_code == 200 and 'id="total">$6.75' in html
    confirmacion = web.post("/pedido/confirmar", data={"total_mostrado": "675"})
    assert confirmacion.status_code == 302
    detalle = web.get(confirmacion.headers["Location"]).get_data(as_text=True)
    assert "Pedido confirmado" in detalle and "Pendiente" in detalle
    assert re.fullmatch(r"[A-Z2-9]{6}", extraer_codigo(detalle))
    assert "Pendiente" in web.get("/mis-pedidos").get_data(as_text=True)


def test_cp42_flujo_completo_preparacion_y_entrega(app):
    """CP-42 (PN-02): el personal prepara, marca listo y entrega con el código."""
    cliente, personal = app.test_client(), app.test_client()
    registrar_web(cliente)
    cliente.post("/pedido/revisar", data={"cant_A01": "1"})
    detalle = cliente.get(cliente.post("/pedido/confirmar", data={"total_mostrado": "250"})
                          .headers["Location"]).get_data(as_text=True)
    codigo = extraer_codigo(detalle)

    assert ingresar_personal(personal).status_code == 302
    pendientes = personal.get("/personal/pedidos").get_data(as_text=True)
    assert "Pedido #1" in pendientes and codigo not in pendientes   # el personal no ve el código
    personal.post("/personal/pedidos/1/avanzar", data={"estado_nuevo": "EN_PREPARACION"})
    personal.post("/personal/pedidos/1/avanzar", data={"estado_nuevo": "LISTO_PARA_RETIRAR"})
    assert "Listo para retirar" in cliente.get("/mis-pedidos").get_data(as_text=True)

    erroneo = personal.post("/personal/entrega/confirmar", data={"pedido_id": "1", "codigo": "AAAAAA"},
                            follow_redirects=True).get_data(as_text=True)
    assert "no corresponde" in erroneo
    busqueda = personal.post("/personal/entrega", data={"codigo": codigo.lower()}).get_data(as_text=True)
    assert "Registrar entrega" in busqueda
    final = personal.post("/personal/entrega/confirmar", data={"pedido_id": "1", "codigo": codigo},
                          follow_redirects=True).get_data(as_text=True)
    assert "registrado como Entregado" in final
    assert 'class="actual">\n      Entregado' in cliente.get("/mis-pedidos/1").get_data(as_text=True)


def test_cp43_control_de_acceso(app):
    """CP-43: las páginas del personal y del cliente exigen sesión; el cliente no ve pedidos ajenos."""
    anonimo = app.test_client()
    for ruta in ("/personal/pedidos", "/personal/productos", "/personal/entrega"):
        assert anonimo.get(ruta).headers["Location"].endswith("/personal/ingresar")
    assert "/ingresar" in anonimo.get("/mis-pedidos").headers["Location"]
    assert "/ingresar" in anonimo.post("/pedido/revisar", data={"cant_A01": "1"}).headers["Location"]
    assert ingresar_personal(anonimo, clave="incorrecta").status_code == 401

    ana, luis = app.test_client(), app.test_client()
    registrar_web(ana)
    ana.post("/pedido/revisar", data={"cant_A01": "1"})
    ana.post("/pedido/confirmar", data={"total_mostrado": "250"})
    registrar_web(luis, cedula_prefijo="090123456", correo="luis@universidad.edu.ec")
    assert luis.get("/mis-pedidos/1").status_code == 400


def test_cp44_proteccion_csrf(tmp_path):
    """CP-44: un formulario enviado sin el token de la sesión se rechaza."""
    app = create_app({"DATABASE": str(tmp_path / "csrf.db"), "SECRET_KEY": "x", "TESTING": True})
    cliente = app.test_client()
    respuesta = cliente.post("/personal/ingresar", data={"usuario": "admin", "clave": "cafeteria2026"})
    assert respuesta.status_code == 400 and "expiró" in respuesta.get_data(as_text=True)
    pagina = cliente.get("/personal/ingresar").get_data(as_text=True)
    token = re.search(r'name="csrf" value="([^"]+)"', pagina).group(1)
    respuesta = cliente.post("/personal/ingresar",
                             data={"usuario": "admin", "clave": "cafeteria2026", "csrf": token})
    assert respuesta.status_code == 302


def test_cp45_mensajes_de_error_en_el_pedido(web):
    """CP-45 (PN-01 paso 7): una selección inválida informa el motivo y no se confirma."""
    registrar_web(web)
    vacia = web.post("/pedido/revisar", data={"cant_A01": "", "cant_B01": "0"})
    assert vacia.status_code == 422 and "al menos un producto" in vacia.get_data(as_text=True)
    decimal = web.post("/pedido/revisar", data={"cant_A01": "1.5"})
    assert decimal.status_code == 422 and "entero positivo" in decimal.get_data(as_text=True)
    agotado = web.post("/pedido/revisar", data={"cant_A05": "1"})
    assert agotado.status_code == 422 and "no está disponible" in agotado.get_data(as_text=True)
    sin_carrito = web.post("/pedido/confirmar", data={"total_mostrado": "0"}, follow_redirects=True)
    assert "no se confirmó" in sin_carrito.get_data(as_text=True)
    assert "Aún no tienes pedidos" in web.get("/mis-pedidos").get_data(as_text=True)


def test_cp46_precio_cambiado_antes_de_confirmar_web(app):
    """CP-46 (RN-NEG-03): el cliente ve el nuevo total y debe confirmar otra vez."""
    cliente, personal = app.test_client(), app.test_client()
    registrar_web(cliente)
    cliente.post("/pedido/revisar", data={"cant_A01": "2"})
    ingresar_personal(personal)
    personal.post("/personal/productos/A01/editar",
                  data={"nombre": "Sánduche de pollo", "categoria": "ALIMENTO", "precio": "3.00", "disponible": "1"})
    conflicto = cliente.post("/pedido/confirmar", data={"total_mostrado": "500"})
    html = conflicto.get_data(as_text=True)
    assert conflicto.status_code == 409 and "Los precios cambiaron" in html and 'id="total">$6.00' in html
    assert cliente.post("/pedido/confirmar", data={"total_mostrado": "600"}).status_code == 302


def test_cp47_mantenimiento_del_menu_web(app):
    """CP-47 (RU-06): alta, edición, validación y cambio de disponibilidad desde la web."""
    personal = app.test_client()
    ingresar_personal(personal)
    alta = personal.post("/personal/productos/nuevo", data={
        "codigo": "b05", "nombre": "Té de hierbas", "categoria": "BEBIDA", "precio": "0,90", "disponible": "1"},
        follow_redirects=True).get_data(as_text=True)
    assert "Té de hierbas" in alta and "$0.90" in alta
    invalido = personal.post("/personal/productos/nuevo", data={
        "codigo": "B06", "nombre": "Malo", "categoria": "BEBIDA", "precio": "0"})
    assert invalido.status_code == 422 and "mayor que cero" in invalido.get_data(as_text=True)
    personal.post("/personal/productos/B05/disponibilidad", data={"disponible": "0"})
    assert "Té de hierbas" not in app.test_client().get("/menu").get_data(as_text=True)
    assert personal.get("/personal/productos/NOEXISTE/editar").status_code == 400


def test_paginas_publicas_y_errores(web):
    """Apoyo: páginas públicas, 404 y redirección abierta bloqueada."""
    assert web.get("/").status_code == 200
    assert web.get("/no-existe").status_code == 404
    registrar_web(web)
    web.post("/salir")
    respuesta = web.post("/ingresar", data={"cedula": "1710034065", "correo": "ana@universidad.edu.ec",
                                            "siguiente": "//sitio-malicioso.com"})
    assert respuesta.headers["Location"] == "/menu"
