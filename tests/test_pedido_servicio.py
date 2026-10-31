"""Pruebas de registro (PN-01) y de preparación y entrega (PN-02) de pedidos (CP-14 a CP-35)."""

import pytest

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
from app.dominio.modelos import EstadoPedido
from app.persistencia.repositorios import PedidoRepositorio
from app.servicios.generador_codigo import ALFABETO, generar_codigo_retiro
from app.servicios.pedido_servicio import PedidoServicio

# ----------------------------------------------------------------- PN-01


def test_cp14_total_es_suma_de_precio_por_cantidad(pedidos):
    """CP-14 (RU-03, RN-NEG-03): A01 $2.50×2 + B02 $1.75×1 + B04 $0.75×3 = $8.00."""
    resumen = pedidos.calcular_resumen({"A01": 2, "B02": 1, "B04": 3})
    assert [d.subtotal_centavos for d in resumen.detalles] == [500, 175, 225]
    assert resumen.total_centavos == 900


def test_cp15_pedido_sin_productos_es_rechazado(pedidos, cliente):
    """CP-15 (RN-NEG-01): un pedido debe incluir al menos un producto."""
    with pytest.raises(PedidoVacioError):
        pedidos.calcular_resumen({})
    with pytest.raises(PedidoVacioError):
        pedidos.confirmar_pedido(cliente.id, {})
    with pytest.raises(PedidoVacioError):
        pedidos.calcular_resumen(pedidos.interpretar_cantidades({"A01": "", "B01": "0"}))


@pytest.mark.parametrize("texto", ["-1", "1.5", "abc", "2e1", "²", " - 3"])
def test_cp16a_cantidad_escrita_no_entera_positiva_es_rechazada(pedidos, texto):
    """CP-16 (RN-NEG-01): el formulario solo admite enteros positivos."""
    with pytest.raises(CantidadInvalidaError):
        pedidos.interpretar_cantidades({"A01": texto})


@pytest.mark.parametrize("cantidad", [0, -2, 1.5, True, "3"])
def test_cp16b_cantidad_no_entera_positiva_es_rechazada_en_servicio(pedidos, cantidad):
    """CP-16 (RN-NEG-01): el servicio rechaza cantidades que no son int > 0."""
    with pytest.raises(CantidadInvalidaError):
        pedidos.calcular_resumen({"A01": cantidad})


def test_cp17_cantidad_mayor_al_maximo_es_rechazada(conexion):
    """CP-17: la cantidad por producto no supera el máximo configurado."""
    servicio = PedidoServicio(conexion, cantidad_maxima=5)
    assert servicio.calcular_resumen({"A01": 5}).total_centavos == 1250
    with pytest.raises(CantidadInvalidaError, match="máxima"):
        servicio.calcular_resumen({"A01": 6})


def test_cp18_producto_no_disponible_es_rechazado(pedidos, cliente):
    """CP-18 (RN-NEG-02): A05 (Almuerzo del día) no está disponible."""
    with pytest.raises(ProductoNoDisponibleError):
        pedidos.confirmar_pedido(cliente.id, {"A01": 1, "A05": 1})
    assert not pedidos.consultar_pedidos_cliente(cliente.id)


def test_cp19_producto_inexistente_es_rechazado(pedidos):
    """CP-19: un código que no está en el menú no se puede pedir."""
    with pytest.raises(ProductoNoEncontradoError):
        pedidos.calcular_resumen({"Z99": 1})


def test_cp20_confirmar_registra_pedido_pendiente_con_codigo(conexion, cliente):
    """CP-20 (RU-04, RN-NEG-05, RN-NEG-06): el pedido nace Pendiente, con código, fecha y total."""
    servicio = PedidoServicio(conexion, reloj=lambda: "2026-11-03 10:15:00")
    pedido = servicio.confirmar_pedido(cliente.id, {"A01": 2, "B01": 1}, total_mostrado_centavos=600)
    assert pedido.id is not None
    assert pedido.estado is EstadoPedido.PENDIENTE
    assert len(pedido.codigo_retiro) == 6 and set(pedido.codigo_retiro) <= set(ALFABETO)
    assert pedido.fecha_registro == "2026-11-03 10:15:00"
    assert pedido.total_centavos == 600
    assert [(d.codigo_producto, d.cantidad, d.precio_unitario_centavos) for d in pedido.detalles] == \
        [("A01", 2, 250), ("B01", 1, 100)]
    assert pedido.cliente_nombre == "Ana Pérez"


def test_cp21a_codigos_de_retiro_son_unicos(pedidos, cliente):
    """CP-21 (RN-NEG-05): 300 pedidos consecutivos reciben códigos distintos."""
    codigos = {pedidos.confirmar_pedido(cliente.id, {"B01": 1}).codigo_retiro for _ in range(300)}
    assert len(codigos) == 300


def test_cp21b_colision_de_codigo_genera_otro(conexion, cliente):
    """CP-21 (RN-NEG-05): si el generador repite un código existente se genera uno nuevo."""
    secuencia = iter(["AAAAAA", "AAAAAA", "BBBBBB"])
    servicio = PedidoServicio(conexion, generador_codigo=lambda: next(secuencia))
    primero = servicio.confirmar_pedido(cliente.id, {"B01": 1})
    segundo = servicio.confirmar_pedido(cliente.id, {"B01": 1})
    assert (primero.codigo_retiro, segundo.codigo_retiro) == ("AAAAAA", "BBBBBB")


def test_cp21c_generador_falla_si_no_encuentra_codigo_libre(conexion, cliente):
    """CP-21 (RN-NEG-05): nunca se registra un código repetido aunque el generador falle."""
    servicio = PedidoServicio(conexion, generador_codigo=lambda: "AAAAAA")
    servicio.confirmar_pedido(cliente.id, {"B01": 1})
    with pytest.raises(RuntimeError):
        servicio.confirmar_pedido(cliente.id, {"B01": 1})
    assert len(generar_codigo_retiro()) == 6


def test_cp22_precio_del_pedido_no_cambia_si_cambia_el_menu(pedidos, menu, cliente):
    """CP-22 (RN-NEG-04): el detalle conserva el precio vigente al confirmar."""
    pedido = pedidos.confirmar_pedido(cliente.id, {"A01": 2})
    menu.actualizar_producto("A01", "Sánduche de pollo", "ALIMENTO", "3.00", True)
    guardado = pedidos.consultar_pedido_cliente(cliente.id, pedido.id)
    assert guardado.detalles[0].precio_unitario_centavos == 250
    assert guardado.total_centavos == 500
    assert pedidos.calcular_resumen({"A01": 2}).total_centavos == 600  # nuevos pedidos: precio nuevo


def test_cp23_total_desactualizado_no_confirma(pedidos, menu, cliente):
    """CP-23 (RN-NEG-03): si el precio cambia entre revisar y confirmar, se pide revisar otra vez."""
    total_visto = pedidos.calcular_resumen({"A01": 1}).total_centavos
    menu.actualizar_producto("A01", "Sánduche de pollo", "ALIMENTO", "2.75", True)
    with pytest.raises(TotalDesactualizadoError, match=r"\$2\.75"):
        pedidos.confirmar_pedido(cliente.id, {"A01": 1}, total_mostrado_centavos=total_visto)
    assert not pedidos.consultar_pedidos_cliente(cliente.id)


def test_cp24_producto_agotado_entre_revision_y_confirmacion(pedidos, menu, cliente):
    """CP-24 (RN-NEG-02, PN-01 paso 7): no se confirma y no queda ningún registro parcial."""
    total_visto = pedidos.calcular_resumen({"A01": 1, "B01": 1}).total_centavos
    menu.cambiar_disponibilidad("B01", False)
    with pytest.raises(ProductoNoDisponibleError):
        pedidos.confirmar_pedido(cliente.id, {"A01": 1, "B01": 1}, total_visto)
    assert not pedidos.consultar_pedidos_cliente(cliente.id)


def test_cp25_cliente_solo_consulta_sus_pedidos(pedidos, cliente, otro_cliente):
    """CP-25 (RU-05): el cliente ve sus pedidos con estado; no puede ver pedidos ajenos."""
    propio = pedidos.confirmar_pedido(cliente.id, {"A01": 1})
    ajeno = pedidos.confirmar_pedido(otro_cliente.id, {"B01": 1})
    lista = pedidos.consultar_pedidos_cliente(cliente.id)
    assert [p.id for p in lista] == [propio.id] and lista[0].estado is EstadoPedido.PENDIENTE
    with pytest.raises(PedidoNoEncontradoError):
        pedidos.consultar_pedido_cliente(cliente.id, ajeno.id)
    with pytest.raises(PedidoNoEncontradoError):
        pedidos.consultar_pedido_cliente(cliente.id, 9999)

# ----------------------------------------------------------------- PN-02


def test_cp26_avance_de_estados_en_orden(pedidos, cliente):
    """CP-26 (RU-07, RN-NEG-06): Pendiente → En preparación → Listo para retirar."""
    pedido = pedidos.confirmar_pedido(cliente.id, {"A01": 1})
    assert [p.id for p in pedidos.listar_pedidos(EstadoPedido.PENDIENTE)] == [pedido.id]
    pedido = pedidos.avanzar_estado(pedido.id, EstadoPedido.EN_PREPARACION, "admin")
    assert pedido.estado is EstadoPedido.EN_PREPARACION
    pedido = pedidos.avanzar_estado(pedido.id, EstadoPedido.LISTO_PARA_RETIRAR, "admin")
    assert pedido.estado is EstadoPedido.LISTO_PARA_RETIRAR
    assert pedidos.contar_por_estado()[EstadoPedido.LISTO_PARA_RETIRAR] == 1


def test_cp27_no_se_puede_saltar_estados(pedidos, cliente):
    """CP-27 (RN-NEG-06): Pendiente no pasa directo a Listo para retirar."""
    pedido = pedidos.confirmar_pedido(cliente.id, {"A01": 1})
    with pytest.raises(TransicionEstadoInvalidaError):
        pedidos.avanzar_estado(pedido.id, EstadoPedido.LISTO_PARA_RETIRAR, "admin")
    assert pedidos.obtener(pedido.id).estado is EstadoPedido.PENDIENTE


def test_cp28_no_se_puede_retroceder_ni_repetir(pedidos, pedido_listo):
    """CP-28 (RN-NEG-06): no se retrocede ni se repite un estado (doble clic)."""
    for estado in (EstadoPedido.EN_PREPARACION, EstadoPedido.PENDIENTE, EstadoPedido.LISTO_PARA_RETIRAR):
        with pytest.raises(TransicionEstadoInvalidaError):
            pedidos.avanzar_estado(pedido_listo.id, estado, "admin")


def test_cp29_entregado_exige_codigo(pedidos, pedido_listo):
    """CP-29 (RN-NEG-07): avanzar a Entregado sin código está prohibido."""
    with pytest.raises(TransicionEstadoInvalidaError, match="código"):
        pedidos.avanzar_estado(pedido_listo.id, EstadoPedido.ENTREGADO, "admin")


@pytest.mark.parametrize("transformar", [
    str, str.lower, lambda c: f"  {c[:3]} {c[3:]} ", lambda c: c[:3] + "-" + c[3:]])
def test_cp30_entrega_con_codigo_correcto(pedidos, pedido_listo, transformar):
    """CP-30 (RN-NEG-07): con código correcto y estado Listo se registra Entregado.

    El código se acepta en minúsculas, con espacios o con guion.
    """
    encontrado = pedidos.buscar_por_codigo(transformar(pedido_listo.codigo_retiro))
    assert encontrado.id == pedido_listo.id
    entregado = pedidos.entregar_pedido(pedido_listo.id, transformar(pedido_listo.codigo_retiro), "admin")
    assert entregado.estado is EstadoPedido.ENTREGADO


def test_cp31_entrega_con_codigo_incorrecto(pedidos, pedido_listo, cliente):
    """CP-31 (RN-04, RN-NEG-07): el código de otro pedido o uno inventado no sirve."""
    otro = pedidos.confirmar_pedido(cliente.id, {"B01": 1})
    with pytest.raises(EntregaInvalidaError, match="no corresponde"):
        pedidos.entregar_pedido(pedido_listo.id, otro.codigo_retiro, "admin")
    with pytest.raises(PedidoNoEncontradoError):
        pedidos.buscar_por_codigo("ZZZZZZ")
    assert pedidos.obtener(pedido_listo.id).estado is EstadoPedido.LISTO_PARA_RETIRAR


def test_cp32_no_se_entrega_si_no_esta_listo(pedidos, cliente):
    """CP-32 (RN-NEG-07): Pendiente o En preparación no se entregan, aunque el código sea correcto."""
    pedido = pedidos.confirmar_pedido(cliente.id, {"A01": 1})
    with pytest.raises(EntregaInvalidaError, match="Pendiente"):
        pedidos.entregar_pedido(pedido.id, pedido.codigo_retiro, "admin")
    pedidos.avanzar_estado(pedido.id, EstadoPedido.EN_PREPARACION, "admin")
    with pytest.raises(EntregaInvalidaError, match="En preparación"):
        pedidos.entregar_pedido(pedido.id, pedido.codigo_retiro, "admin")


def test_cp33_no_se_entrega_dos_veces(pedidos, pedido_listo):
    """CP-33 (RN-04): un pedido Entregado no puede entregarse de nuevo."""
    pedidos.entregar_pedido(pedido_listo.id, pedido_listo.codigo_retiro, "admin")
    with pytest.raises(EntregaInvalidaError, match="Entregado"):
        pedidos.entregar_pedido(pedido_listo.id, pedido_listo.codigo_retiro, "admin")


def test_cp34_historial_registra_cada_cambio(pedidos, pedido_listo):
    """CP-34 (RN-03): queda registro de estado, fecha y usuario de cada cambio."""
    pedidos.entregar_pedido(pedido_listo.id, pedido_listo.codigo_retiro, "maria")
    historial = pedidos.historial(pedido_listo.id)
    assert [h.estado for h in historial] == list(EstadoPedido)
    assert [h.usuario for h in historial] == ["cliente", "admin", "admin", "maria"]
    assert all(h.fecha for h in historial)


def test_cp35_concurrencia_optimista(conexion, pedidos, cliente):
    """CP-35: si dos empleados avanzan el mismo pedido a la vez, solo uno lo consigue."""
    pedido = pedidos.confirmar_pedido(cliente.id, {"A01": 1})
    repositorio = PedidoRepositorio(conexion)
    assert repositorio.actualizar_estado(pedido.id, EstadoPedido.PENDIENTE, EstadoPedido.EN_PREPARACION)
    assert not repositorio.actualizar_estado(pedido.id, EstadoPedido.PENDIENTE, EstadoPedido.EN_PREPARACION)
    # El servicio detecta el conflicto cuando el estado leído ya no es el vigente.
    obsoleto = pedidos.obtener(pedido.id)
    obsoleto.estado = EstadoPedido.PENDIENTE
    with pytest.raises(TransicionEstadoInvalidaError, match="otro usuario"):
        pedidos._cambiar_estado(obsoleto, EstadoPedido.EN_PREPARACION, "admin")  # pylint: disable=protected-access


def test_estado_siguiente_y_etiquetas():
    """Apoyo a CP-26: orden y nombres de los estados según la especificación."""
    assert EstadoPedido.PENDIENTE.siguiente() is EstadoPedido.EN_PREPARACION
    assert EstadoPedido.ENTREGADO.siguiente() is None
    assert [e.etiqueta for e in EstadoPedido] == ["Pendiente", "En preparación", "Listo para retirar", "Entregado"]
