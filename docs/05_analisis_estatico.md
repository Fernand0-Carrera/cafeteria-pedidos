# 5. Reporte de Análisis Estático del Código

**Fecha de ejecución:** 30 de octubre de 2026 · **Alcance:** `app/`, `tests/`, `scripts/`, `run.py`
**Reportes completos:** carpeta [`docs/reportes/analisis_estatico/`](reportes/analisis_estatico/) (resultados iniciales en la subcarpeta `inicial/`).

## 5.1 Herramientas y configuración

| Herramienta | Qué analiza | Configuración |
|---|---|---|
| **flake8** 7.5.0 | Cumplimiento de PEP 8, errores de sintaxis, nombres no usados (pyflakes), complejidad (mccabe). | `.flake8`: longitud máxima de línea 120. |
| **pylint** 4.1.3 | Errores probables, convenciones, *docstrings* faltantes, diseño (número de atributos, sentencias, argumentos), código duplicado. Calificación de 0 a 10. | `pyproject.toml`: longitud 120; resto por defecto. |
| **bandit** 1.9.4 | Vulnerabilidades de seguridad conocidas (inyección SQL, uso de `random` para secretos, credenciales en código, etc.). | `pyproject.toml`: excluye pruebas y documentación. |
| **radon** 6.0.1 | Complejidad ciclomática (CC) por función, índice de mantenibilidad (MI) por módulo y métricas de tamaño. | Por defecto. Escala CC: A (1–5), B (6–10), C (11–20)… |

Comandos ejecutados:

```bash
flake8 app tests scripts run.py --count --statistics
pylint app run.py scripts --reports=y
pylint tests
bandit -r app run.py
radon cc app -s -a ; radon mi app -s ; radon raw app -s
```

## 5.2 Resultado inicial (primera ejecución sobre el código completo)

| Herramienta | Resultado inicial |
|---|---|
| flake8 | 1 aviso |
| pylint (`app`, `run.py`, `scripts`) | **9.98 / 10** · 2 mensajes |
| pylint (`tests`) | **9.55 / 10** · 19 mensajes |
| bandit | 0 hallazgos, pero con una anotación `# nosec B608` mal ubicada que bandit reportó como advertencia; al retirarla apareció **1 hallazgo de severidad media** |
| radon | Complejidad promedio **A (2.11)**; 1 función con complejidad **C (11)** |

## 5.3 Hallazgos, análisis y correcciones

| # | Herramienta · código | Ubicación | Análisis | Acción |
|---|---|---|---|---|
| H-01 | bandit · **B608** (CWE-89, severidad media) | `persistencia/repositorios.py`, `obtener_por_codigos` | La consulta construía `IN (?, ?, …)` con una *f-string*. Solo se interpolaban signos `?` (no datos del usuario), así que no era explotable, pero el patrón es frágil: un cambio futuro podría interpolar datos. Además se había silenciado con `# nosec`, lo que ocultaba el aviso. | **Corregido**: la lista de códigos se envía como un único parámetro JSON y se recorre con `json_each(?)`. La sentencia SQL ahora es fija. Se eliminó el `# nosec`. |
| H-02 | radon · CC **C (11)** | `dominio/validaciones.py`, `validar_cedula` | La función mezclaba validación de formato, de provincia y el cálculo del dígito verificador. | **Refactorizado**: se extrajeron `_digito_verificador_cedula` y `_provincia_valida`. Complejidad final B (8). También se añadió `isascii()` para no aceptar dígitos Unicode. |
| H-03 | pylint · R0915 *too-many-statements* (70/50) | `scripts/capturas.py`, `main` | Una sola función recorría todos los flujos. | **Refactorizado** en `flujo_registro_de_pedido`, `flujo_preparacion`, `flujo_entrega` y `flujo_menu`. |
| H-04 | pylint · R0902 *too-many-instance-attributes* (8/7) | `dominio/modelos.py`, `Pedido` | La entidad tiene exactamente los atributos que exige la sección 7 de la especificación (más `id`, detalles y nombre del cliente). Dividirla empeoraría la legibilidad. | **Aceptado y justificado**: desactivación local con comentario explicativo en la clase. |
| H-05 | flake8 · E501 / pylint C0301 | `tests/test_pedido_servicio.py:187` | Línea de 121 caracteres en una parametrización. | **Corregido**: parametrización en dos líneas. |
| H-06 | pylint · C0116 ×10 | `tests/conftest.py` | *Fixtures* sin *docstring*. | **Corregido**: se documentó cada *fixture*. |
| H-07 | pylint · W0621 ×8 *redefined-outer-name* | `tests/conftest.py` | Falso positivo: pytest inyecta las *fixtures* como parámetros con el mismo nombre que la función que las define; es el uso documentado de pytest. | **Aceptado y justificado**: desactivación a nivel del módulo `conftest.py` con comentario explicativo. |

## 5.4 Resultado final

| Herramienta | Inicial | Final |
|---|---|---|
| flake8 (avisos) | 1 | **0** |
| pylint `app` + `run.py` + `scripts` | 9.98 | **10.00 / 10** |
| pylint `tests` | 9.55 | **10.00 / 10** |
| bandit (hallazgos medios/altos) | 1 (oculto por `nosec`) | **0** · líneas omitidas por `nosec`: 0 |
| radon CC promedio | A (2.11) | **A (2.09)** |
| radon CC máxima | C (11) | **B (8)** |
| radon MI | — | **A en los 20 módulos** |

### Funciones con mayor complejidad (todas en rango B, aceptable)

| Función | CC | Comentario |
|---|---|---|
| `validaciones.validar_cedula` | B (8) | Una validación por regla de la cédula. |
| `PersonalServicio.registrar` | B (8) | Validación de campos y duplicados. |
| `validaciones.convertir_precio_a_centavos` | B (7) | Formato, decimales, rango. |
| `validaciones.validar_correo_institucional` | B (6) | Usuario, separador y dominio. |

Los 144 bloques restantes (de 148 clases, funciones y métodos analizados) tienen complejidad A.

### Métricas de tamaño (`radon raw app`)

| Métrica | Valor |
|---|---|
| Líneas totales (LOC) | 1 759 |
| Líneas de código fuente (SLOC) | 1 108 |
| Líneas lógicas (LLOC) | 1 046 |
| Líneas de *docstrings* y comentarios (radon: *multi* 166 + *single comments* 124 + *comments* 13) | 303 |
| Pruebas automatizadas | 88 ejecuciones (47 casos de prueba + 3 de apoyo) |

## 5.5 Cobertura de pruebas (complemento del análisis)

Cobertura de líneas y ramas con `pytest --cov=app --cov-branch`: **94 %** (854 sentencias, 140 ramas). Las capas de dominio, persistencia y servicios están entre 96 % y 100 %. Lo no cubierto corresponde a ramas de la interfaz web ya cubiertas a nivel de servicio (por ejemplo, el registro web con datos inválidos) y a la creación de la clave secreta en el primer arranque, verificada manualmente en la instalación. Reporte HTML navegable: `docs/reportes/cobertura/html/index.html`.

## 5.6 Conclusión

El código cumple el requisito RNF-05 (pylint ≥ 9.0, 0 avisos flake8, complejidad promedio A, cobertura ≥ 85 %). El único hallazgo de seguridad (H-01) se corrigió eliminando la causa y no silenciando el aviso. Las dos desactivaciones que permanecen (H-04 y H-07) están justificadas en el propio código. La integración continua (`.github/workflows/ci.yml`) repite este análisis en cada cambio para evitar regresiones.
