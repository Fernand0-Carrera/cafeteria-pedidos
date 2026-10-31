# 6. Casos de Prueba y Resultados de Ejecución

**Fecha de ejecución:** 30 de octubre de 2026 · **Versión probada:** 1.0.0
**Evidencias:** carpeta [`docs/reportes/pruebas/`](reportes/pruebas/) (salida completa de pytest, archivo JUnit XML y salidas de las ejecuciones fallidas y repetidas) y [`docs/reportes/cobertura/html/index.html`](reportes/cobertura/html/index.html).

## 6.1 Estrategia de pruebas

| Nivel | Qué se prueba | Herramienta | Casos |
|---|---|---|---|
| Unitarias | Validaciones del dominio y reglas de negocio de cada servicio, con base de datos en memoria. | pytest | CP-01 a CP-40 |
| Integración | Rutas web + servicios + base de datos en archivo, mediante el cliente HTTP de Flask (sesiones, formularios, redirecciones, códigos HTTP). | pytest + Flask test client | CP-41 a CP-47 |
| Sistema (extremo a extremo) | Los procesos PN-01 y PN-02 completos en un navegador Chromium real, con protección CSRF activa. | Playwright (`scripts/capturas.py`) | PS-01 |

**Técnicas de diseño aplicadas.** *Partición de equivalencia* (cédulas, correos, precios y cantidades válidos e inválidos); *valores límite* (cantidad máxima 5/6, precio 0/0.01/1000/1000.01, 9/10/11 dígitos de cédula); *transición de estados* (todas las transiciones permitidas y prohibidas de RN-NEG-06/07); *tabla de decisión* para la entrega (estado × código correcto/incorrecto); *pruebas de concurrencia* (doble avance de estado).

**Criterios de salida.** 100 % de los casos ejecutados y aprobados; todo caso fallido analizado, corregido y re-ejecutado; cobertura ≥ 85 %.

## 6.2 Entorno de ejecución

| Elemento | Valor |
|---|---|
| Sistema operativo | Windows 11 (`win32`) |
| Python / pytest / pytest-cov | 3.13.14 / 9.2.0 / 7.1.0 |
| Base de datos | SQLite 3.50.4 (en memoria para unitarias; archivo temporal para integración) |
| Navegador (PS-01) | Chromium (Playwright 1.56.0) |
| Comando | `pytest -v --cov=app --cov-branch --junitxml=docs/reportes/pruebas/resultados_junit.xml` |

## 6.3 Resumen de resultados

| Indicador | Primera ejecución | Ejecución final |
|---|---|---|
| Casos de prueba diseñados | 47 (CP-01 a CP-47) + 3 de apoyo | 47 + 3 |
| Ejecuciones (incluye parametrizaciones) | 88 | 88 |
| Aprobadas | 86 | **88** |
| Fallidas | **2** (CP-41 y CP-44) | **0** |
| Cobertura de líneas y ramas | — | **94 %** |
| Tiempo total | 3.12 s | 3.89 s |

Dos casos no fueron exitosos al inicio. Ambos revelaron defectos reales del producto; su análisis, solución y re-ejecución están en la sección 6.5.

## 6.4 Catálogo de casos de prueba

Columnas: **Esperado** = resultado esperado; **Obtenido** = resultado de la ejecución final; **Estado** = resultado en la primera ejecución → resultado final. Cada caso se implementa en una función `test_cpXX_…` del archivo indicado.

### Validación de datos — `tests/test_validaciones.py`

| ID | Requisito | Técnica | Datos de entrada | Esperado | Obtenido | Estado |
|---|---|---|---|---|---|---|
| CP-01 | RF-01 | Partición (válida) | `" 1710034065 "`, cédula de provincia 30 | Se acepta sin espacios | Aceptadas | Aprobado |
| CP-02 | RF-01 | Partición (inválida) | `1710034064` (verificador alterado) | `ValidacionError` «dígito verificador» | Rechazada con ese mensaje | Aprobado |
| CP-03 | RF-01 | Valores límite, partición | `""`, 9 dígitos, 11 dígitos, con letra, provincia 25, provincia 00, tercer dígito 6 (7 ejecuciones) | Cada una rechazada con su motivo | 7/7 rechazadas con el motivo correcto | Aprobado |
| CP-04 | RF-01 | Partición (válida) | `Ana@Epn.edu.ec`, `a.b-c@estud.epn.edu.ec` | Aceptados en minúsculas | Aceptados | Aprobado |
| CP-05 | RF-01 | Partición (inválida) | `@gmail.com`, `…edu.ec.com`, `@fakeepn.edu.ec`, sin @, sin usuario, con espacio (6 ejecuciones) | Rechazados «correo institucional» | 6/6 rechazados | Aprobado |
| CP-06 | RF-01 | Partición, límites | Celular `099 123 4567` (válido), `0891234567`, 9 y 11 dígitos, letras; nombre `R2D2` | Válidos aceptados, inválidos rechazados | Según lo esperado | Aprobado |
| CP-07 | HU-08 | Partición (válida) | `1.50`, `1,5`, `2`, ` 0.05 `, `1000` (5 ejecuciones) | 150, 150, 200, 5, 100000 centavos | Coinciden | Aprobado |
| CP-08 | HU-08 | Límites, partición | `0`, `-1`, `1.505`, `abc`, `""`, `1000.01`, `NaN`, `Infinity` (8 ejecuciones) | `ValidacionError` | 8/8 rechazados | Aprobado |

### Menú — `tests/test_menu_servicio.py`

| ID | Requisito | Precondición | Pasos / datos | Esperado | Obtenido | Estado |
|---|---|---|---|---|---|---|
| CP-09 | HU-03, RN-NEG-02 | Menú de ejemplo (A05 no disponible) | `listar_menu()` y `listar_todos()` | Cliente ve solo disponibles con precio > 0; personal ve también A05 | Correcto | Aprobado |
| CP-10 | HU-08 | — | Registrar `b05`, «Té de hierbas», BEBIDA, `0.90` | Guardado como `B05`, 90 centavos, disponible | Correcto | Aprobado |
| CP-11 | HU-08 | A01 existe | Código A01 repetido; categoría POSTRE; nombre vacío; precio −2 | Duplicado / validación rechazados | 4/4 rechazados | Aprobado |
| CP-12 | HU-09 | — | Actualizar A01 a «… grande», 3.10, no disponible; actualizar código inexistente | Cambios guardados; inexistente → `ProductoNoEncontradoError` | Correcto | Aprobado |
| CP-13 | HU-09 | B01 disponible | Desactivar y reactivar B01 | Desaparece y reaparece en el menú del cliente | Correcto | Aprobado |

### Registro de pedidos (PN-01) — `tests/test_pedido_servicio.py`

| ID | Requisito | Precondición | Pasos / datos | Esperado | Obtenido | Estado |
|---|---|---|---|---|---|---|
| CP-14 | HU-05, RN-NEG-03 | Precios A01 2.50, B02 1.75, B04 0.75 | `calcular_resumen({A01:2, B02:1, B04:3})` | Subtotales 500, 175, 225; total 900 | Coinciden | Aprobado |
| CP-15 | HU-04, RN-NEG-01 | Cliente registrado | Selección `{}`; formulario con todos vacíos o `0` | `PedidoVacioError` en revisión y confirmación | Correcto | Aprobado |
| CP-16 | HU-04, RN-NEG-01 | — | Texto: `-1`, `1.5`, `abc`, `2e1`, `²`, ` - 3`; valores: `0`, `-2`, `1.5`, `True`, `"3"` (11 ejecuciones) | `CantidadInvalidaError` | 11/11 rechazadas | Aprobado |
| CP-17 | HU-04 | Máximo configurado = 5 | Cantidades 5 y 6 | 5 aceptada (total 1250); 6 rechazada | Correcto | Aprobado |
| CP-18 | HU-04, RN-NEG-02 | A05 no disponible | Confirmar `{A01:1, A05:1}` | `ProductoNoDisponibleError`; no se crea pedido | Correcto | Aprobado |
| CP-19 | HU-04 | — | Producto `Z99` | `ProductoNoEncontradoError` | Correcto | Aprobado |
| CP-20 | HU-06, RN-NEG-05/06 | Reloj fijo 2026-11-03 10:15 | Confirmar `{A01:2, B01:1}` con total mostrado 600 | Pedido Pendiente, código de 6 caracteres del alfabeto, fecha fija, total 600, detalle con precios 250 y 100 | Correcto | Aprobado |
| CP-21 | HU-06, RN-NEG-05 | — | (a) 300 pedidos seguidos; (b) generador que repite `AAAAAA`; (c) generador que siempre repite | (a) 300 códigos distintos; (b) se reintenta y asigna `BBBBBB`; (c) error, nunca un código repetido | Correcto (3 ejecuciones) | Aprobado |
| CP-22 | HU-06, RN-NEG-04 | Pedido A01×2 a 2.50 | Subir el precio de A01 a 3.00 | El pedido conserva 250 c/u y total 500; un pedido nuevo cuesta 600 | Correcto | Aprobado |
| CP-23 | HU-05, RN-NEG-03 | Cliente ve total 250 | Cambiar precio a 2.75 y confirmar con total 250 | `TotalDesactualizadoError` con «$2.75»; sin pedido | Correcto | Aprobado |
| CP-24 | HU-06, RN-NEG-02 | Selección A01+B01 revisada | Desactivar B01 y confirmar | `ProductoNoDisponibleError`; sin registro parcial | Correcto | Aprobado |
| CP-25 | HU-07 | Pedidos de Ana y de Luis | Ana lista sus pedidos y abre el de Luis y el #9999 | Solo ve el suyo, Pendiente; los otros → `PedidoNoEncontradoError` | Correcto | Aprobado |

### Preparación y entrega (PN-02) — `tests/test_pedido_servicio.py`

| ID | Requisito | Precondición | Pasos / datos | Esperado | Obtenido | Estado |
|---|---|---|---|---|---|---|
| CP-26 | HU-11, HU-12, RN-NEG-06 | Pedido Pendiente | Avanzar a En preparación y a Listo | Estados en orden; conteo de Listo = 1 | Correcto | Aprobado |
| CP-27 | RN-NEG-06 | Pedido Pendiente | Avanzar directo a Listo para retirar | `TransicionEstadoInvalidaError`; sigue Pendiente | Correcto | Aprobado |
| CP-28 | RN-NEG-06 | Pedido Listo | Pasar a En preparación, a Pendiente o repetir Listo | Las 3 rechazadas | Correcto | Aprobado |
| CP-29 | RN-NEG-07 | Pedido Listo | `avanzar_estado(…, ENTREGADO)` | Rechazado: exige código | Correcto | Aprobado |
| CP-30 | HU-13, RN-NEG-07 | Pedido Listo | Buscar y entregar con el código tal cual, en minúsculas, con espacios y con guion (4 ejecuciones) | Pedido encontrado y Entregado | 4/4 Entregado | Aprobado |
| CP-31 | HU-13, RN-04 | Pedido Listo + otro pedido | Entregar con el código del otro pedido; buscar `ZZZZZZ` | `EntregaInvalidaError` «no corresponde»; no encontrado; sigue Listo | Correcto | Aprobado |
| CP-32 | HU-13, RN-NEG-07 | Pedido Pendiente | Entregar con código correcto en Pendiente y en En preparación | Rechazado en ambos estados | Correcto | Aprobado |
| CP-33 | HU-13, RN-04 | Pedido Entregado | Entregar otra vez | Rechazado | Correcto | Aprobado |
| CP-34 | HU-07, RF-16 | Pedido Listo | Entregar como `maria`; leer historial | 4 estados en orden; usuarios cliente, admin, admin, maria; con fecha | Correcto | Aprobado |
| CP-35 | RNF-08 | Pedido Pendiente | Dos actualizaciones Pendiente → En preparación; servicio con estado leído obsoleto | La primera aplica, la segunda no; el servicio avisa «otro usuario» | Correcto | Aprobado |

### Clientes, personal y persistencia — `tests/test_cliente_personal.py`

| ID | Requisito | Precondición | Pasos / datos | Esperado | Obtenido | Estado |
|---|---|---|---|---|---|---|
| CP-36 | HU-01, RF-02 | Base vacía | Registrar « Ana », correo en mayúsculas | Código `CLI-00001`, nombre y correo normalizados | Correcto | Aprobado |
| CP-37 | HU-01 | Ana registrada | Repetir cédula; repetir correo; cédula inválida | Duplicados rechazados con su motivo; cédula inválida rechazada | Correcto | Aprobado |
| CP-38 | HU-02 | Ana registrada | Cédula + correo correctos; correo ajeno; cédula ajena; vacíos | Solo la primera combinación identifica | Correcto | Aprobado |
| CP-39 | HU-10, RNF-03 | Sin personal | Registrar `Maria`; autenticar bien y mal; duplicado; clave corta; vacíos | Autentica sin importar mayúsculas; la clave no aparece en la base; errores rechazados | Correcto | Aprobado |
| CP-40 | RNF-01 | Archivo de base nuevo | Iniciar la app, registrar cliente y pedido, cerrar, iniciar de nuevo | El pedido se encuentra por su código; 9 productos y 1 usuario (sin duplicar datos iniciales) | Correcto | Aprobado |

### Integración web — `tests/test_web.py`

| ID | Requisito | Pasos | Esperado | Obtenido | Estado |
|---|---|---|---|---|---|
| CP-41 | PN-01, HU-01–07 | Menú sin sesión → registro → menú → revisar A01×2 + B02×1 → confirmar | Sin sesión: precios y aviso para ingresar, sin campos de cantidad; revisión muestra $6.75; ticket con código de 6 caracteres y estado Pendiente; aparece en «Mis pedidos» | Correcto | **Fallido → Aprobado** (ver 6.5.2) |
| CP-42 | PN-02, HU-10–13 | Cliente confirma; personal ingresa, avanza dos veces, intenta entregar con `AAAAAA`, busca con el código en minúsculas y entrega | El personal no ve el código en la lista; el cliente ve Listo para retirar; código erróneo rechazado; entrega registrada; seguimiento del cliente marca Entregado | Correcto | Aprobado |
| CP-43 | HU-02, HU-10, RN-NEG | Visitar páginas protegidas sin sesión; clave errónea; Luis abre el pedido de Ana | Redirección a los ingresos; 401 con clave errónea; 400 al abrir pedido ajeno | Correcto | Aprobado |
| CP-44 | RNF-03 | POST de ingreso sin token CSRF y luego con el token de la página | Sin token: 400 «El formulario expiró»; con token: 302 | Correcto | **Fallido → Aprobado** (ver 6.5.1) |
| CP-45 | PN-01 paso 7 | Revisar selección vacía, cantidad `1.5`, producto A05; confirmar sin selección | 422 con el motivo en cada caso; «El pedido no se confirmó»; sin pedidos | Correcto | Aprobado |
| CP-46 | HU-05, RN-NEG-03 | Cliente revisa A01×2 ($5.00); personal sube A01 a $3.00; cliente confirma | 409 «Los precios cambiaron» con nuevo total $6.00; al confirmar 600 se registra | Correcto | Aprobado |
| CP-47 | HU-08, HU-09 | Alta de B05 con `0,90`; alta con precio 0; desactivar B05; editar código inexistente | B05 a $0.90 en la lista; 422 «mayor que cero»; B05 fuera del menú; 400 | Correcto | Aprobado |

### Pruebas de apoyo

| Prueba | Verifica | Estado |
|---|---|---|
| `test_formato_de_dinero_y_codigo_de_producto` | Formato `$0.05`, `$12.50`; normalización del código de producto | Aprobado |
| `test_estado_siguiente_y_etiquetas` | Orden de estados y nombres exactos de la especificación | Aprobado |
| `test_paginas_publicas_y_errores` | Inicio 200, página inexistente 404, redirección externa bloqueada | Aprobado |

## 6.5 Casos no exitosos en la primera ejecución

### 6.5.1 CP-44 · Protección CSRF

**Resultado de la primera ejecución** (evidencia: `reportes/pruebas/cp44_ejecucion1_fallida.txt`):

```text
tests/test_web.py::test_cp44_proteccion_csrf FAILED                      [100%]
>       assert respuesta.status_code == 400 and "expiró" in respuesta.get_data(as_text=True)
E       assert (302 == 400)
FAILED tests/test_web.py::test_cp44_proteccion_csrf - assert (302 == 400)
============================== 1 failed in 0.46s ==============================
```

**Análisis.** Se esperaba que un formulario enviado sin token fuera rechazado (400), pero el ingreso se aceptó (302). La verificación comparaba el token del formulario con el de la sesión así:

```python
enviado = request.form.get("csrf", "")
if not secrets.compare_digest(enviado, session.get("csrf", "")):
    abort(400, ...)
```

Si la víctima nunca había abierto una página de la aplicación, su sesión no tenía token; ambos valores eran la cadena vacía y `"" == ""` daba por válida la petición. **Causa raíz:** usar `""` como valor por defecto de ambos lados de la comparación. **Impacto:** un sitio malicioso podía enviar formularios en nombre de un usuario (por ejemplo, confirmar pedidos o, si la sesión del personal existía sin token, cambiar estados). **Severidad:** alta.

**Solución** (`app/web/comun.py`): si la sesión no tiene token, la petición se rechaza.

```python
esperado = session.get("csrf")
enviado = request.form.get("csrf", "")
if not esperado or not secrets.compare_digest(enviado, esperado):
    abort(400, ...)
```

**Re-ejecución** (evidencia: `reportes/pruebas/cp44_ejecucion2_exitosa.txt`):

```text
tests/test_web.py::test_cp44_proteccion_csrf PASSED                      [100%]
============================== 1 passed in 0.33s ==============================
```

La suite completa se ejecutó de nuevo: 88 aprobadas, sin regresiones.

### 6.5.2 CP-41 · Menú sin sesión

**Contexto.** Al revisar la trazabilidad se vio que el criterio 2 de HU-03 («sin ingresar, puedo ver el menú pero se me invita a ingresar para pedir») no tenía prueba. Se amplió CP-41 para verificar que, sin sesión, el menú muestra precios y la invitación, y que no hay ningún control de cantidad (`cant_A01` no aparece en la página).

**Resultado de la primera ejecución** (evidencia: `reportes/pruebas/cp41_ejecucion1_fallida.txt`):

```text
tests/test_web.py::test_cp41_flujo_completo_registro_de_pedido FAILED    [100%]
>       assert "$2.50" in anonimo and "para hacer un pedido" in anonimo and "cant_A01" not in anonimo
E       assert ('$2.50' in '<!doctype html>…' and … and 'cant_A01' not in '<!doctype h…')
tests\test_web.py:12: AssertionError
============================== 1 failed in 0.36s ==============================
```

**Análisis.** La página no tenía campos de cantidad, pero sí conservaba `<label for="cant_A01">` en cada producto. Esa etiqueta apuntaba a un control inexistente. **Causa raíz:** la plantilla `menu.html` condicionaba el `<input>` a la sesión, pero no la `<label>`. **Impacto:** defecto de accesibilidad: los lectores de pantalla anuncian un campo que no existe, y el HTML es inválido. **Severidad:** baja.

**Solución** (`app/web/templates/cliente/menu.html`): la etiqueta `<label for>` se genera solo cuando existe el campo; sin sesión el nombre del producto es texto simple.

**Re-ejecución** (evidencia: `reportes/pruebas/cp41_ejecucion2_exitosa.txt`):

```text
tests/test_web.py::test_cp41_flujo_completo_registro_de_pedido PASSED    [100%]
============================== 1 passed in 0.27s ==============================
```

Suite completa: 88 aprobadas.

## 6.6 Prueba de sistema PS-01 (navegador real)

| Campo | Contenido |
|---|---|
| Objetivo | Demostrar PN-01 y PN-02 completos con la configuración real (CSRF activo, base en archivo). |
| Ejecución | `python scripts/capturas.py docs/img` |
| Pasos | 1) Inicio. 2) Registro de Ana Pérez. 3) Selección Sánduche ×2 + Capuchino ×1. 4) Revisión con total $6.75. 5) Confirmación y ticket. 6) Cantidad `1.5` → mensaje de error. 7) Ingreso del personal. 8) Iniciar preparación. 9) Marcar listo. 10) Cliente ve «Listo para retirar». 11) Personal busca por el código. 12) Registra la entrega. 13) Cliente ve el seguimiento completo. 14) Listado y alta de producto. 15) Menú en pantalla de celular (390 px). |
| Resultado esperado | Todos los pasos se completan sin errores y cada pantalla muestra lo descrito. |
| Resultado obtenido | Completado sin errores; 16 capturas generadas en `docs/img/` (usadas en el manual de usuario). |
| Estado | Aprobado |

## 6.7 Cobertura por módulo

| Módulo | Cobertura |
|---|---|
| `dominio/` (modelos, validaciones, excepciones) | 100 % |
| `servicios/` | 99–100 % |
| `persistencia/` | 96–100 % |
| `web/comun.py` · `web/cliente.py` · `web/personal.py` | 96 % · 87 % · 83 % |
| `app/__init__.py` | 72 % |
| **Total (líneas y ramas)** | **94 %** |

## 6.8 Cómo reproducir

```bash
pip install -r requirements-dev.txt
pytest -v                                           # todas las pruebas
pytest -v -k cp44                                    # un caso específico
pytest --cov=app --cov-branch --cov-report=html      # cobertura → htmlcov/index.html
python scripts/capturas.py docs/img                  # prueba de sistema PS-01
```
