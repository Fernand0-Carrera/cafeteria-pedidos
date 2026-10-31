# Gestión de pedidos · Cafetería universitaria

Aplicación web para consultar el menú, registrar pedidos anticipados y retirarlos con un código. Proyecto de Construcción y Evolución de Software · **Release 1.0** (27 de noviembre de 2026).

**Integrantes:** _completar_

## Funcionalidades

- **Clientes:** registro e ingreso con cédula y correo institucional; menú con precios; selección de cantidades; revisión del total; confirmación con código de retiro; seguimiento del estado.
- **Personal:** pedidos por estado en orden de llegada; avance Pendiente → En preparación → Listo para retirar; entrega solo con el código del cliente; mantenimiento de productos, precios y disponibilidad.

## Inicio rápido

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    ·    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Abra <http://127.0.0.1:5000>. Personal: usuario `admin`, clave `cafeteria2026` (cámbiela con `CAFETERIA_ADMIN_CLAVE` antes de la primera ejecución).

## Calidad

```bash
pip install -r requirements-dev.txt
pytest --cov=app          # 88 pruebas, 94 % de cobertura
flake8 app tests run.py   # 0 avisos
pylint app run.py         # 10.00/10
bandit -r app run.py      # sin hallazgos
```

## Estructura

```text
app/dominio        entidades, validaciones, excepciones
app/persistencia   esquema SQLite y repositorios
app/servicios      casos de uso y reglas de negocio
app/web            rutas, plantillas y estilos
tests/             pruebas automatizadas (CP-01 a CP-47)
```

## Ramas

- `main`: versión estable (etiqueta `v1.0.0`).
- `develop`: integración.
- `documentacion`: código estable + carpeta `docs/` con los entregables (requisitos, diseño, ambiente, documentación técnica, análisis estático, casos de prueba, manuales).
