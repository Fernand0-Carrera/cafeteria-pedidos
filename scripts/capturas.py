"""Genera las capturas de pantalla del manual de usuario recorriendo los procesos PN-01 y PN-02.

Uso:  python scripts/capturas.py [carpeta_destino]
Requiere: pip install playwright && playwright install chromium
(o la variable de entorno CHROMIUM con la ruta de un Chromium ya instalado).
"""

import os
import sys
import tempfile
import threading

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app  # noqa: E402  pylint: disable=wrong-import-position

DESTINO = sys.argv[1] if len(sys.argv) > 1 else "docs/img"
PUERTO = 5055
BASE = f"http://127.0.0.1:{PUERTO}"
VENTANA = {"width": 1100, "height": 760}


def foto(pagina, nombre, completa=False):
    """Guarda una captura de la página en la carpeta de destino."""
    pagina.screenshot(path=os.path.join(DESTINO, nombre), full_page=completa)


def flujo_registro_de_pedido(cliente):
    """PN-01: registro del cliente, menú, revisión y confirmación. Devuelve el código de retiro."""
    cliente.goto(BASE + "/")
    foto(cliente, "01_inicio.png")
    cliente.goto(BASE + "/registro")
    for campo, valor in (("#nombre", "Ana"), ("#apellido", "Pérez"), ("#cedula", "1710034065"),
                         ("#celular", "0991234567"), ("#correo", "ana.perez@epn.edu.ec")):
        cliente.fill(campo, valor)
    foto(cliente, "02_registro.png")
    cliente.click("text=Crear mi cuenta >> nth=-1")
    cliente.fill("#cant_A01", "2")
    cliente.fill("#cant_B02", "1")
    foto(cliente, "03_menu.png", completa=True)
    cliente.click("text=Revisar pedido")
    foto(cliente, "04_revisar.png")
    cliente.click("text=Confirmar pedido")
    cliente.wait_for_timeout(800)
    foto(cliente, "05_confirmado.png", completa=True)
    codigo = cliente.inner_text("#codigo-retiro")
    cliente.goto(BASE + "/menu")
    cliente.evaluate("document.querySelector('#cant_A02').type='text'")
    cliente.fill("#cant_A02", "1.5")
    cliente.click("text=Revisar pedido")
    foto(cliente, "06_error_cantidad.png")
    return codigo


def flujo_preparacion(personal, cliente):
    """PN-02 pasos 1-3: ingreso del personal y avance de estados."""
    personal.goto(BASE + "/personal/ingresar")
    personal.fill("#usuario", "admin")
    personal.fill("#clave", "cafeteria2026")
    foto(personal, "07_personal_ingreso.png")
    personal.click("button:has-text('Ingresar')")
    foto(personal, "08_pedidos_pendientes.png")
    personal.click("text=Iniciar preparación")
    personal.goto(BASE + "/personal/pedidos?estado=EN_PREPARACION")
    foto(personal, "09_en_preparacion.png")
    personal.click("text=Marcar listo para retirar")
    cliente.goto(BASE + "/mis-pedidos")
    foto(cliente, "10_mis_pedidos.png")


def flujo_entrega(personal, cliente, codigo):
    """PN-02 pasos 4-5: verificación del código y registro de la entrega."""
    personal.goto(BASE + "/personal/entrega")
    personal.fill("#codigo", codigo)
    personal.click("text=Buscar pedido")
    foto(personal, "11_entrega_busqueda.png", completa=True)
    personal.click("text=Registrar entrega")
    foto(personal, "12_entrega_registrada.png")
    cliente.goto(BASE + "/mis-pedidos/1")
    foto(cliente, "13_seguimiento_entregado.png", completa=True)


def flujo_menu(personal):
    """RU-06: mantenimiento de productos."""
    personal.goto(BASE + "/personal/productos")
    foto(personal, "14_productos.png", completa=True)
    personal.click("text=Agregar producto")
    personal.fill("#codigo", "B05")
    personal.fill("#nombre", "Té de hierbas")
    personal.select_option("#categoria", "BEBIDA")
    personal.fill("#precio", "0.90")
    foto(personal, "15_nuevo_producto.png")


def main():
    """Levanta un servidor temporal y recorre todos los flujos."""
    os.makedirs(DESTINO, exist_ok=True)
    app = create_app({"DATABASE": os.path.join(tempfile.mkdtemp(), "demo.db"), "SECRET_KEY": "capturas"})
    servidor = make_server("127.0.0.1", PUERTO, app)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    ruta_chromium = os.environ.get("CHROMIUM")
    with sync_playwright() as pw:
        navegador = pw.chromium.launch(executable_path=ruta_chromium) if ruta_chromium else pw.chromium.launch()
        cliente = navegador.new_page(viewport=VENTANA)
        personal = navegador.new_page(viewport=VENTANA)
        codigo = flujo_registro_de_pedido(cliente)
        flujo_preparacion(personal, cliente)
        flujo_entrega(personal, cliente, codigo)
        flujo_menu(personal)
        movil = navegador.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        movil.goto(BASE + "/menu")
        foto(movil, "16_menu_movil.png")
        navegador.close()
    servidor.shutdown()
    print(f"Capturas guardadas en {DESTINO}")


if __name__ == "__main__":
    main()
