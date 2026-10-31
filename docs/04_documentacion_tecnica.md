# 4. Documentación Técnica del Código Fuente

## 4.1 Convención de documentación

El código está escrito en Python, por lo que en lugar de JavaDoc se usan **docstrings** con el estilo de Google, la convención equivalente más extendida. Cada módulo, clase y función pública tiene un *docstring* que indica qué hace, sus argumentos (`Args`), su resultado (`Returns`) y las excepciones de negocio que puede lanzar (`Raises`), además de la regla o requisito que implementa (`RN-NEG-xx`, `RU-xx`).

| JavaDoc | Docstring estilo Google |
|---|---|
| `/** Descripción */` | `"""Descripción."""` |
| `@param cantidad …` | `Args:` → `cantidad: …` |
| `@return …` | `Returns:` → `…` |
| `@throws X …` | `Raises:` → `X: …` |
| Herramienta `javadoc` | Herramienta `pdoc` |

Ejemplo real (`app/servicios/pedido_servicio.py`):

```python
def entregar_pedido(self, pedido_id: int, codigo_presentado: str, usuario: str) -> Pedido:
    """Registra la entrega de un pedido (RN-NEG-07).

    Raises:
        EntregaInvalidaError: Si el código no corresponde al pedido o si el
            pedido no está en estado Listo para retirar.
    """
```

pylint verifica que ningún módulo, clase ni función pública quede sin *docstring* (mensajes C0114, C0115, C0116); el reporte final no registra ninguno.

## 4.2 Documentación generada (HTML)

La documentación navegable está en **`docs/api/index.html`** (ábrala con un navegador; incluye buscador). Para regenerarla tras cambiar el código:

```bash
pdoc app -o docs/api --docformat google
```

Para consultarla con recarga automática mientras se programa: `pdoc app --docformat google` (abre `http://localhost:8080`).

## 4.3 Mapa de módulos

| Módulo | Contenido principal |
|---|---|
| `app` | `create_app(configuracion)`: crea la aplicación, el esquema, el usuario inicial y el menú de ejemplo. |
| `app.config` | `Config`: valores configurables por variables de entorno. |
| `app.datos_demo` | `cargar_datos_demo(conexion)`: 9 productos de ejemplo si el menú está vacío. |
| `app.dominio.modelos` | `Producto`, `Cliente`, `Pedido`, `DetallePedido`, `CambioEstado`, `ResumenPedido`, `Categoria`, `EstadoPedido`. |
| `app.dominio.validaciones` | `validar_cedula`, `validar_nombre`, `validar_celular`, `validar_correo_institucional`, `validar_codigo_producto`, `convertir_precio_a_centavos`, `formatear_centavos`. |
| `app.dominio.excepciones` | `ErrorNegocio` y 12 subclases, cada una con la regla que la origina. |
| `app.persistencia.db` | `ESQUEMA`, `conectar(ruta)`, `crear_esquema(conexion)`. |
| `app.persistencia.repositorios` | `ProductoRepositorio`, `ClienteRepositorio`, `PedidoRepositorio`, `PersonalRepositorio`. |
| `app.servicios.menu_servicio` | `MenuServicio`: consulta y mantenimiento del menú (RU-01, RU-06). |
| `app.servicios.pedido_servicio` | `PedidoServicio`: PN-01 y PN-02, reglas RN-NEG-01 a 07. |
| `app.servicios.cliente_servicio` | `ClienteServicio`: registro e identificación. |
| `app.servicios.personal_servicio` | `PersonalServicio`: registro y autenticación del personal. |
| `app.servicios.generador_codigo` | `generar_codigo_retiro()`, `normalizar_codigo()`. |
| `app.web.comun` | Conexión por petición, decoradores de acceso, CSRF, manejo de errores, comando `crear-personal`. |
| `app.web.cliente` | Rutas del cliente. |
| `app.web.personal` | Rutas del personal. |

## 4.4 API principal de `PedidoServicio`

| Método | Descripción | Excepciones |
|---|---|---|
| `interpretar_cantidades(entradas)` | Convierte los textos del formulario a enteros; vacío o `0` = no seleccionado. | `CantidadInvalidaError` |
| `calcular_resumen(items)` | Valida la selección y calcula subtotales y total con precios vigentes. | `PedidoVacioError`, `CantidadInvalidaError`, `ProductoNoEncontradoError`, `ProductoNoDisponibleError` |
| `confirmar_pedido(cliente_id, items, total_mostrado_centavos)` | Revalida, compara el total y registra el pedido Pendiente con código único (transacción). | las anteriores + `TotalDesactualizadoError` |
| `consultar_pedidos_cliente(cliente_id)` | Pedidos del cliente, más recientes primero. | — |
| `consultar_pedido_cliente(cliente_id, pedido_id)` | Un pedido, solo si pertenece al cliente. | `PedidoNoEncontradoError` |
| `listar_pedidos(estado)` / `contar_por_estado()` | Vista del personal. | — |
| `avanzar_estado(pedido_id, estado_nuevo, usuario)` | Pendiente → En preparación → Listo para retirar. | `TransicionEstadoInvalidaError` |
| `buscar_por_codigo(codigo)` | Localiza el pedido por el código presentado. | `PedidoNoEncontradoError` |
| `entregar_pedido(pedido_id, codigo, usuario)` | Listo para retirar → Entregado si el código coincide. | `EntregaInvalidaError` |
| `historial(pedido_id)` | Cambios de estado con fecha y usuario. | — |

## 4.5 Puntos de extensión

El generador de códigos y el reloj se inyectan en el constructor de `PedidoServicio`, lo que permite cambiar el formato del código o usar otra zona horaria sin modificar la lógica. Para usar otro motor de base de datos basta con reescribir `app/persistencia`, porque los servicios solo dependen de los métodos de los repositorios.
