# 1. Documentación de Requisitos

**Proyecto:** Gestión de pedidos de una cafetería universitaria
**Versión del producto:** Release 1.0 · **Fecha comprometida:** 27 de noviembre de 2026
**Fuente:** *Especificación inicial de necesidades del cliente*, versión 1.0 (27/10/2026)

## 1.1 Propósito y alcance

Este documento traduce la especificación del cliente en historias de usuario con criterios de aceptación, requisitos funcionales y no funcionales verificables, y una matriz de trazabilidad que conecta cada necesidad con el código y con los casos de prueba. También registra las ambigüedades encontradas y la decisión tomada para cada una (sección 1.8), como pide la sección 10 de la especificación.

El sistema permite a estudiantes y docentes consultar el menú, registrar pedidos anticipados y retirarlos con un código; y al personal de cafetería mantener el menú y registrar el avance de cada pedido hasta su entrega.

## 1.2 Usuarios del sistema

| Actor | Descripción | Necesidades principales |
|---|---|---|
| Cliente | Estudiante o docente identificado por código, nombre, apellido, cédula, celular y correo institucional. | Ver el menú con precios, pedir, conocer el total, obtener un código de retiro y seguir el estado del pedido. |
| Personal de cafetería | Trabajador que mantiene el menú y procesa los pedidos. | Registrar y actualizar productos, consultar pedidos por estado, registrar avances y entregas. |

## 1.3 Requisitos de negocio

| ID | Requisito de negocio | Cómo lo atiende la solución |
|---|---|---|
| RN-01 | Reducir el tiempo empleado en registrar los pedidos durante períodos de alta demanda. | El cliente registra su pedido desde su dispositivo antes de llegar; el personal no digita pedidos. |
| RN-02 | Facilitar que los clientes conozcan los productos y precios antes de pedir. | Menú público con productos disponibles y precios (HU-03). |
| RN-03 | Mejorar el seguimiento de los pedidos desde su recepción hasta la entrega. | Estados con orden obligatorio, vista por estado para el personal y línea de tiempo con fecha y responsable de cada cambio (HU-07, HU-11, HU-12). |
| RN-04 | Reducir confusiones al entregar pedidos. | Entrega solo con código de retiro verificado y solo si el pedido está Listo para retirar (HU-13). |

## 1.4 Historias de usuario

Prioridad según MoSCoW (M = imprescindible, S = importante, C = deseable). Estimación en puntos de historia (escala Fibonacci). Los criterios de aceptación usan el formato *Dado / Cuando / Entonces* y cada uno está cubierto por al menos un caso de prueba (columna CP).

### HU-01 · Registrarme como cliente
**Como** estudiante o docente **quiero** registrarme con mis datos **para** poder hacer pedidos y consultarlos.
Prioridad: M · Estimación: 3 · Origen: sección 7 (Cliente)

| # | Criterio de aceptación | CP |
|---|---|---|
| 1 | **Dado** que ingreso nombre, apellido, cédula válida, celular y correo institucional, **cuando** envío el formulario, **entonces** quedo registrado, recibo un código `CLI-xxxxx` y paso al menú. | CP-36, CP-41 |
| 2 | **Dado** una cédula con dígito verificador incorrecto, un celular que no empieza con 09 o un correo de otro dominio, **cuando** envío, **entonces** veo el motivo y no se registra nada. | CP-01–CP-06, CP-37 |
| 3 | **Dado** que la cédula o el correo ya están registrados, **cuando** envío, **entonces** se me informa y no se crea un duplicado. | CP-37 |

### HU-02 · Identificarme como cliente
**Como** cliente registrado **quiero** ingresar con mi cédula y correo **para** pedir y ver mis pedidos.
Prioridad: M · Estimación: 2 · Origen: sección 7

| # | Criterio de aceptación | CP |
|---|---|---|
| 1 | **Dado** que mi cédula y correo coinciden con un registro, **cuando** ingreso, **entonces** accedo al menú con mi nombre visible. | CP-38 |
| 2 | **Dado** una combinación que no coincide, **cuando** ingreso, **entonces** veo «La cédula y el correo no corresponden a un cliente registrado». | CP-38 |
| 3 | **Dado** que no he ingresado, **cuando** intento revisar un pedido o ver «Mis pedidos», **entonces** se me lleva a la pantalla de ingreso. | CP-43 |

### HU-03 · Consultar el menú (RU-01)
**Como** cliente **quiero** ver los productos disponibles con sus precios **para** decidir qué pedir.
Prioridad: M · Estimación: 2

| # | Criterio de aceptación | CP |
|---|---|---|
| 1 | **Dado** productos disponibles y no disponibles, **cuando** abro el menú, **entonces** veo solo los disponibles, agrupados en alimentos y bebidas, con su precio. | CP-09, CP-41 |
| 2 | **Dado** que no he ingresado, **cuando** abro el menú, **entonces** puedo verlo pero se me invita a ingresar para pedir. | CP-41 |

### HU-04 · Seleccionar productos y cantidades (RU-02)
**Como** cliente **quiero** indicar la cantidad de cada producto **para** armar mi pedido.
Prioridad: M · Estimación: 3 · Reglas: RN-NEG-01, RN-NEG-02

| # | Criterio de aceptación | CP |
|---|---|---|
| 1 | **Dado** el menú, **cuando** escribo cantidades en uno o más productos, **entonces** solo esos productos forman la selección. | CP-14, CP-41 |
| 2 | **Dado** que no escribo ninguna cantidad, **cuando** pido revisar, **entonces** veo «Seleccione al menos un producto» (RN-NEG-01). | CP-15, CP-45 |
| 3 | **Dado** una cantidad negativa, decimal o no numérica, **cuando** pido revisar, **entonces** veo que debe ser un entero positivo (RN-NEG-01). | CP-16, CP-45 |
| 4 | **Dado** una cantidad mayor que el máximo configurado (50), **cuando** pido revisar, **entonces** se rechaza. | CP-17 |
| 5 | **Dado** un producto no disponible, **cuando** intento incluirlo, **entonces** se rechaza (RN-NEG-02). | CP-18, CP-45 |

### HU-05 · Conocer el importe total antes de confirmar (RU-03)
**Como** cliente **quiero** ver el detalle y el total **para** confirmar sabiendo cuánto pagaré.
Prioridad: M · Estimación: 2 · Reglas: RN-NEG-03

| # | Criterio de aceptación | CP |
|---|---|---|
| 1 | **Dado** una selección válida, **cuando** pido revisar, **entonces** veo cada producto con cantidad, precio vigente y subtotal, y el total igual a la suma de precio × cantidad. | CP-14, CP-41 |
| 2 | **Dado** que un precio cambió mientras revisaba, **cuando** confirmo, **entonces** el pedido no se registra, veo el nuevo total y debo confirmar otra vez. | CP-23, CP-46 |

### HU-06 · Confirmar el pedido y obtener un código de retiro (RU-04)
**Como** cliente **quiero** confirmar y recibir un código **para** retirar mi pedido sin confusiones.
Prioridad: M · Estimación: 5 · Reglas: RN-NEG-04, RN-NEG-05, RN-NEG-06

| # | Criterio de aceptación | CP |
|---|---|---|
| 1 | **Dado** que reviso una selección válida, **cuando** confirmo, **entonces** el pedido se registra en estado Pendiente con fecha, total y un código de retiro de 6 caracteres que se muestra en pantalla. | CP-20, CP-41 |
| 2 | **Dado** cualquier cantidad de pedidos, **cuando** se confirman, **entonces** ningún código de retiro se repite (RN-NEG-05). | CP-21 |
| 3 | **Dado** un pedido confirmado, **cuando** el personal cambia después el precio del producto, **entonces** mi pedido conserva el precio con el que se confirmó (RN-NEG-04). | CP-22 |
| 4 | **Dado** que un producto deja de estar disponible antes de confirmar, **cuando** confirmo, **entonces** se informa el motivo y el pedido no se registra (PN-01 paso 7). | CP-24 |

### HU-07 · Consultar el estado de mis pedidos (RU-05)
**Como** cliente **quiero** ver el estado de mis pedidos **para** saber cuándo retirarlos.
Prioridad: M · Estimación: 3

| # | Criterio de aceptación | CP |
|---|---|---|
| 1 | **Dado** que tengo pedidos, **cuando** abro «Mis pedidos», **entonces** veo cada uno con fecha, código, estado y total, del más reciente al más antiguo. | CP-25, CP-41 |
| 2 | **Dado** un pedido, **cuando** abro su detalle, **entonces** veo el seguimiento con la hora de cada estado alcanzado. | CP-34, CP-42 |
| 3 | **Dado** el pedido de otro cliente, **cuando** intento abrirlo, **entonces** no se muestra. | CP-25, CP-43 |

### HU-08 · Registrar productos en el menú (RU-06)
**Como** personal **quiero** agregar productos **para** mantener el menú actualizado.
Prioridad: M · Estimación: 3

| # | Criterio de aceptación | CP |
|---|---|---|
| 1 | **Dado** código, nombre, categoría, precio y disponibilidad válidos, **cuando** guardo, **entonces** el producto aparece en el listado (y en el menú si está disponible). | CP-10, CP-47 |
| 2 | **Dado** un código ya existente, un precio ≤ 0 o con más de dos decimales, **cuando** guardo, **entonces** veo el motivo y no se registra. | CP-08, CP-11, CP-47 |

### HU-09 · Actualizar productos, precios y disponibilidad (RU-06)
**Como** personal **quiero** modificar productos y marcarlos como disponibles o no **para** reflejar lo que realmente puedo vender.
Prioridad: M · Estimación: 3 · Reglas: RN-NEG-02, RN-NEG-04

| # | Criterio de aceptación | CP |
|---|---|---|
| 1 | **Dado** un producto, **cuando** cambio nombre, categoría o precio, **entonces** los nuevos pedidos usan los nuevos valores y los anteriores conservan los suyos. | CP-12, CP-22 |
| 2 | **Dado** un producto disponible, **cuando** lo desactivo, **entonces** deja de aparecer en el menú del cliente y no puede pedirse. | CP-13, CP-47 |

### HU-10 · Ingresar como personal
**Como** personal **quiero** ingresar con usuario y clave **para** que solo el personal procese pedidos y modifique el menú.
Prioridad: M · Estimación: 2

| # | Criterio de aceptación | CP |
|---|---|---|
| 1 | **Dado** usuario y clave correctos, **cuando** ingreso, **entonces** veo la lista de pedidos. | CP-39, CP-42 |
| 2 | **Dado** una clave incorrecta, **cuando** ingreso, **entonces** veo «Usuario o clave incorrectos». | CP-39, CP-43 |
| 3 | **Dado** que no he ingresado, **cuando** abro una página del personal, **entonces** se me redirige al ingreso. | CP-43 |

### HU-11 · Consultar pedidos por estado (RU-07)
**Como** personal **quiero** ver los pedidos agrupados por estado y en orden de llegada **para** atenderlos en orden.
Prioridad: M · Estimación: 2

| # | Criterio de aceptación | CP |
|---|---|---|
| 1 | **Dado** pedidos en varios estados, **cuando** abro una pestaña de estado, **entonces** veo solo esos pedidos, del más antiguo al más reciente, con cliente, productos y total, y el número de pedidos en cada pestaña. | CP-26, CP-42 |

### HU-12 · Registrar el avance de preparación (RU-07)
**Como** personal **quiero** marcar un pedido como En preparación y luego como Listo para retirar **para** que el cliente sepa cuándo acercarse.
Prioridad: M · Estimación: 3 · Reglas: RN-NEG-06

| # | Criterio de aceptación | CP |
|---|---|---|
| 1 | **Dado** un pedido Pendiente, **cuando** pulso «Iniciar preparación», **entonces** pasa a En preparación; y desde ahí, con «Marcar listo para retirar», pasa a Listo para retirar. | CP-26, CP-42 |
| 2 | **Dado** cualquier pedido, **cuando** intento saltar, retroceder o repetir un estado, **entonces** se rechaza. | CP-27, CP-28 |
| 3 | **Dado** que dos empleados avanzan el mismo pedido a la vez, **cuando** ambos guardan, **entonces** solo el primero tiene efecto y el segundo recibe un aviso. | CP-35 |

### HU-13 · Entregar un pedido verificando el código (RU-07)
**Como** personal **quiero** registrar la entrega solo con el código del cliente **para** no entregar pedidos equivocados.
Prioridad: M · Estimación: 3 · Reglas: RN-NEG-07

| # | Criterio de aceptación | CP |
|---|---|---|
| 1 | **Dado** un pedido Listo para retirar, **cuando** escribo el código que presenta el cliente (sin importar mayúsculas, espacios o guiones) y registro la entrega, **entonces** pasa a Entregado. | CP-30, CP-42 |
| 2 | **Dado** un código que no corresponde al pedido, **cuando** registro la entrega, **entonces** se rechaza. | CP-31, CP-42 |
| 3 | **Dado** un pedido Pendiente o En preparación, **cuando** intento entregarlo aunque el código sea correcto, **entonces** se rechaza. | CP-32 |
| 4 | **Dado** un pedido ya Entregado, **cuando** intento entregarlo otra vez, **entonces** se rechaza. | CP-33 |
| 5 | **Dado** que intento pasar a Entregado sin código, **cuando** uso el avance de estado, **entonces** se rechaza. | CP-29 |

## 1.5 Requisitos funcionales

| ID | El sistema debe… | HU | Verificación |
|---|---|---|---|
| RF-01 | registrar clientes validando cédula ecuatoriana (módulo 10), celular `09xxxxxxxx` y correo del dominio institucional configurado, sin duplicar cédula ni correo. | HU-01 | CP-01–CP-06, CP-36, CP-37 |
| RF-02 | asignar a cada cliente un código único con formato `CLI-00001`. | HU-01 | CP-36 |
| RF-03 | identificar al cliente por cédula y correo institucional. | HU-02 | CP-38 |
| RF-04 | mostrar el menú con productos disponibles, categoría y precio. | HU-03 | CP-09 |
| RF-05 | aceptar cantidades enteras positivas hasta un máximo configurable (50 por defecto). | HU-04 | CP-16, CP-17 |
| RF-06 | rechazar pedidos vacíos, con productos inexistentes o no disponibles, indicando el motivo. | HU-04 | CP-15, CP-18, CP-19, CP-45 |
| RF-07 | calcular subtotales y total con el precio vigente antes de la confirmación. | HU-05 | CP-14 |
| RF-08 | volver a validar disponibilidad y total al confirmar, y rechazar si el total cambió. | HU-05, HU-06 | CP-23, CP-24, CP-46 |
| RF-09 | registrar el pedido en estado Pendiente con fecha, total, detalle con precio unitario congelado y código de retiro único de 6 caracteres. | HU-06 | CP-20, CP-21, CP-22 |
| RF-10 | listar los pedidos del cliente con su estado, y mostrar el detalle y el seguimiento solo a su dueño. | HU-07 | CP-25, CP-43 |
| RF-11 | registrar, editar y activar/desactivar productos. | HU-08, HU-09 | CP-10–CP-13, CP-47 |
| RF-12 | autenticar al personal con usuario y clave almacenada como hash. | HU-10 | CP-39 |
| RF-13 | listar pedidos por estado en orden de llegada, con conteo por estado. | HU-11 | CP-26 |
| RF-14 | permitir solo las transiciones Pendiente → En preparación → Listo para retirar. | HU-12 | CP-26–CP-28 |
| RF-15 | registrar Entregado solo para pedidos Listos para retirar y con el código correcto. | HU-13 | CP-29–CP-33 |
| RF-16 | guardar el historial de cambios de estado con fecha y usuario. | HU-07, HU-12 | CP-34 |

## 1.6 Requisitos no funcionales

| ID | Categoría | Requisito | Verificación |
|---|---|---|---|
| RNF-01 | Persistencia | Productos, clientes, pedidos e historial persisten entre ejecuciones (SQLite en archivo). | CP-40 |
| RNF-02 | Integridad | Las reglas críticas se refuerzan también en la base de datos: `UNIQUE` en código de retiro, cédula, correo y código de producto; `CHECK` en estados, precios y cantidades; claves foráneas activas. | Revisión del esquema (doc. de diseño §2.6) |
| RNF-03 | Seguridad | Claves del personal con hash (PBKDF2/scrypt de Werkzeug); protección CSRF en todo formulario; cookies de sesión `HttpOnly` y `SameSite=Lax`; consultas SQL parametrizadas; redirecciones solo a rutas internas. | CP-39, CP-43, CP-44, bandit |
| RNF-04 | Usabilidad | Interfaz en español, adaptable a celulares (desde 360 px), mensajes de error que indican qué corregir, foco de teclado visible. | Manual de usuario, captura 16 |
| RNF-05 | Mantenibilidad | Calificación pylint ≥ 9.0, 0 avisos flake8, complejidad ciclomática promedio A, cobertura de pruebas ≥ 85 %. | Reporte de análisis estático y de cobertura |
| RNF-06 | Portabilidad | Funciona en Windows, macOS y Linux con Python 3.11 o superior, sin servicios externos. | Manual de instalación |
| RNF-07 | Rendimiento | Las páginas responden en menos de 1 s con hasta 1 000 pedidos en una instalación local. | Índices por estado y cliente; suite completa (88 pruebas) en < 3 s |
| RNF-08 | Concurrencia | Dos usuarios del personal no pueden aplicar el mismo cambio de estado dos veces. | CP-35 |

## 1.7 Reglas de negocio y su implementación

| Regla | Dónde se aplica | Prueba |
|---|---|---|
| RN-NEG-01 Al menos un producto; cantidades enteras positivas. | `PedidoServicio.interpretar_cantidades`, `calcular_resumen`; `CHECK (cantidad > 0)` | CP-15, CP-16 |
| RN-NEG-02 Solo productos disponibles en nuevos pedidos. | `PedidoServicio.calcular_resumen` (al revisar y al confirmar); menú filtrado | CP-09, CP-18, CP-24 |
| RN-NEG-03 Total = Σ precio vigente × cantidad. | `ResumenPedido.total_centavos`; verificación del total mostrado al confirmar | CP-14, CP-23 |
| RN-NEG-04 El precio del pedido no cambia si cambia el menú. | `detalle_pedido.precio_unitario_centavos` guarda una copia del precio | CP-22 |
| RN-NEG-05 Código de retiro único. | Generador aleatorio seguro + verificación + `UNIQUE (codigo_retiro)` | CP-21 |
| RN-NEG-06 Pendiente → En preparación → Listo para retirar → Entregado, en ese orden. | `EstadoPedido.siguiente`, `PedidoServicio.avanzar_estado` | CP-26–CP-28 |
| RN-NEG-07 Entregado solo desde Listo para retirar y con el código del cliente. | `PedidoServicio.entregar_pedido` | CP-29–CP-33 |

## 1.8 Ambigüedades detectadas y decisiones tomadas

La especificación deja abiertos varios puntos. El equipo tomó las decisiones siguientes, que deben **validarse con el cliente** antes del cierre del Release 1.0.

| # | Ambigüedad | Decisión | Justificación |
|---|---|---|---|
| A-01 | ¿Cómo se identifica el cliente para consultar sus pedidos? | Registro único con sus datos; luego ingresa con cédula y correo institucional. | La sección 7 pide identificarlo con datos personales; evita gestionar contraseñas en la primera versión. |
| A-02 | ¿Qué es un «correo institucional»? | Correo cuyo dominio es el configurado (`CAFETERIA_DOMINIO_CORREO`, por defecto `universidad.edu.ec`) o un subdominio suyo. | Distintas instituciones usan dominios distintos; se deja configurable. |
| A-03 | ¿Cómo se valida la cédula? | Algoritmo oficial de módulo 10 (personas naturales). | Evita registros con cédulas mal digitadas. |
| A-04 | ¿Existe un límite de cantidad por producto? | Máximo 50 unidades por producto, configurable. | Previene errores de digitación (p. ej. 500 en lugar de 5). No contradice RN-NEG-01. |
| A-05 | ¿Qué ocurre si cambia un precio entre la revisión y la confirmación? | Se rechaza la confirmación, se muestra el nuevo total y el cliente confirma otra vez. | RU-03 exige que el cliente conozca el total antes de confirmar; cobrarle un total distinto lo contradiría. |
| A-06 | ¿El menú del cliente muestra productos no disponibles? | No; solo los disponibles (el personal ve todos). | RU-01 habla de «productos disponibles». |
| A-07 | ¿Quién ve el código de retiro? | Solo el cliente. El personal busca el pedido escribiendo el código que el cliente presenta. | Si el personal viera el código, la verificación de RN-NEG-07 perdería sentido. |
| A-08 | Formato del código de retiro. | 6 caracteres de un alfabeto sin caracteres ambiguos (sin 0/O, 1/I/L), generado con `secrets`. | Fácil de leer en voz alta; ~887 millones de combinaciones, difícil de adivinar. |
| A-09 | ¿Puede eliminarse un producto? | No; se desactiva. | Preserva la integridad de pedidos históricos que lo referencian. |
| A-10 | ¿Puede cancelarse un pedido? | No en el Release 1.0. | La especificación no lo menciona y RN-NEG-06 no define un estado Cancelado. Se propone para una versión posterior. |
| A-11 | Moneda y redondeo. | Dólares estadounidenses; importes almacenados en centavos enteros. | Evita errores de redondeo de punto flotante. |
| A-12 | ¿Cómo se autentica el personal? | Usuario y clave; se crea un usuario inicial (`admin`) y pueden añadirse otros por línea de comandos. | La especificación no detalla gestión de usuarios del personal. |

## 1.9 Fuera de alcance (Release 1.0)

Pago electrónico o cobro en línea, integración con servicios financieros, notificaciones por correo o mensajería, impresoras o lectores de códigos, promociones, reembolsos, pedidos programados, gestión de inventario de ingredientes, cancelación de pedidos y gestión de usuarios del personal desde la interfaz.

## 1.10 Matriz de trazabilidad

| Negocio | Usuario | Historia | Requisitos | Componentes principales | Casos de prueba |
|---|---|---|---|---|---|
| RN-02 | RU-01 | HU-03 | RF-04 | `MenuServicio.listar_menu`, `cliente.menu` | CP-09, CP-41 |
| RN-01 | RU-02 | HU-04 | RF-05, RF-06 | `PedidoServicio.interpretar_cantidades`, `calcular_resumen` | CP-15–CP-19, CP-45 |
| RN-01, RN-02 | RU-03 | HU-05 | RF-07, RF-08 | `ResumenPedido`, `cliente.revisar` | CP-14, CP-23, CP-46 |
| RN-01, RN-04 | RU-04 | HU-06 | RF-08, RF-09 | `PedidoServicio.confirmar_pedido`, `generador_codigo` | CP-20–CP-24, CP-41 |
| RN-03 | RU-05 | HU-07 | RF-10, RF-16 | `consultar_pedidos_cliente`, `historial` | CP-25, CP-34 |
| RN-02 | RU-06 | HU-08, HU-09 | RF-11 | `MenuServicio`, `personal.productos` | CP-10–CP-13, CP-22, CP-47 |
| RN-03 | RU-07 | HU-11, HU-12 | RF-13, RF-14 | `PedidoServicio.listar_pedidos`, `avanzar_estado` | CP-26–CP-28, CP-35, CP-42 |
| RN-04 | RU-07 | HU-13 | RF-15 | `PedidoServicio.entregar_pedido`, `personal.entrega` | CP-29–CP-33, CP-42 |
| — | (sección 7) | HU-01, HU-02 | RF-01–RF-03 | `ClienteServicio`, `validaciones` | CP-01–CP-06, CP-36–CP-38 |
| — | (sección 3) | HU-10 | RF-12 | `PersonalServicio` | CP-39, CP-43, CP-44 |
| — | (sección 8) | — | RNF-01 | `persistencia.db` | CP-40 |
