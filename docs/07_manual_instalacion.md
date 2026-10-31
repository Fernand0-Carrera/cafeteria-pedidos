# 7. Manual de Instalación

Este manual explica cómo instalar y ejecutar el sistema de pedidos de la cafetería en un computador con Windows, macOS o Linux.

## 7.1 Requisitos

| Elemento | Requisito |
|---|---|
| Sistema operativo | Windows 10/11, macOS 12 o superior, o Linux con Python disponible |
| Python | **3.11 o superior** (incluye SQLite con soporte JSON, que la aplicación usa) |
| Git | Cualquier versión reciente (opcional; también puede descargarse el ZIP desde GitHub) |
| Espacio en disco | ~50 MB con dependencias |
| Navegador | Chrome, Edge, Firefox o Safari actualizados |
| Red | Solo para descargar dependencias. La aplicación funciona sin Internet. |

Para verificar Python abra una terminal (en Windows: *PowerShell*) y ejecute:

```bash
python --version        # en macOS/Linux puede ser: python3 --version
```

Si no está instalado, descárguelo de <https://www.python.org/downloads/>. En Windows marque la casilla **«Add python.exe to PATH»** durante la instalación.

## 7.2 Obtener el código

```bash
git clone https://github.com/fernand0-carrera/cafeteria-pedidos.git
cd cafeteria-pedidos
```

Sin Git: en GitHub pulse **Code → Download ZIP**, descomprima el archivo y abra una terminal dentro de la carpeta `cafeteria-pedidos`.

## 7.3 Crear el entorno virtual e instalar dependencias

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Si PowerShell indica que la ejecución de scripts está deshabilitada, ejecute una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y repita la activación.

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Al activar el entorno, la línea de la terminal empieza con `(.venv)`.

## 7.4 Configuración (opcional)

La aplicación funciona sin configurar nada. Para adaptarla, defina estas variables de entorno **antes de la primera ejecución**:

| Variable | Valor por defecto | Para qué sirve |
|---|---|---|
| `CAFETERIA_DOMINIO_CORREO` | `epn.edu.ec` | Dominio aceptado para el correo institucional de los clientes. |
| `CAFETERIA_ADMIN_USUARIO` | `admin` | Usuario del personal que se crea en la primera ejecución. |
| `CAFETERIA_ADMIN_CLAVE` | `cafeteria2026` | Clave de ese usuario (mínimo 8 caracteres). **Cámbiela en una instalación real.** |
| `CAFETERIA_DATOS_DEMO` | `1` | `1` carga 9 productos de ejemplo si el menú está vacío; `0` inicia con el menú vacío. |
| `CAFETERIA_CANTIDAD_MAXIMA` | `50` | Unidades máximas de un producto en un pedido. |
| `CAFETERIA_DB` | `instance/cafeteria.db` | Ruta del archivo de base de datos. |
| `CAFETERIA_HOST` / `CAFETERIA_PUERTO` | `127.0.0.1` / `5000` | Dirección y puerto del servidor. |
| `CAFETERIA_SECRET_KEY` | se genera sola | Clave que firma las sesiones; si no se define se crea en `instance/secret_key`. |

Ejemplos:

```powershell
# Windows (PowerShell), válido para la terminal actual
$env:CAFETERIA_DOMINIO_CORREO = "epn.edu.ec"
$env:CAFETERIA_ADMIN_CLAVE = "UnaClaveSegura2026"
```

```bash
# macOS / Linux
export CAFETERIA_DOMINIO_CORREO=epn.edu.ec
export CAFETERIA_ADMIN_CLAVE=UnaClaveSegura2026
```

## 7.5 Ejecutar la aplicación

```bash
python run.py
```

Abra **<http://127.0.0.1:5000>** en el navegador. En la primera ejecución se crean automáticamente la carpeta `instance/`, la base de datos `instance/cafeteria.db`, el usuario del personal y, si corresponde, el menú de ejemplo. Para detener el servidor pulse `Ctrl + C` en la terminal. Los datos se conservan para la próxima ejecución.

**Primer ingreso del personal:** en la página de inicio elija «Entrar como personal» con usuario `admin` y la clave configurada (por defecto `cafeteria2026`).

## 7.6 Uso en la red local de la cafetería

Para que los clientes pidan desde sus celulares conectados a la misma red Wi-Fi:

```bash
# Windows
$env:CAFETERIA_HOST = "0.0.0.0"; python run.py
# macOS / Linux
CAFETERIA_HOST=0.0.0.0 python run.py
```

Averigüe la IP del equipo (`ipconfig` en Windows, `ip addr` o `ifconfig` en macOS/Linux) y comparta la dirección `http://<IP>:5000`. Si Windows pregunta, permita el acceso de Python en el firewall para redes privadas.

Para un uso continuo se recomienda un servidor de producción en lugar del servidor de desarrollo de Flask:

```bash
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 run:app
```

## 7.7 Administración

| Tarea | Cómo hacerlo |
|---|---|
| Crear otro usuario del personal | `flask --app run crear-personal maria "María López"` (pide la clave dos veces) |
| Respaldar los datos | Con la aplicación detenida, copie `instance/cafeteria.db` a otro lugar. |
| Restaurar un respaldo | Detenga la aplicación y reemplace `instance/cafeteria.db` por la copia. |
| Empezar con datos limpios | Detenga la aplicación y elimine `instance/cafeteria.db`; se recreará en la siguiente ejecución. |
| Actualizar a una nueva versión | `git pull` y luego `pip install -r requirements.txt`. La base de datos existente se conserva. |

## 7.8 Instalación para desarrollo y verificación

```bash
pip install -r requirements-dev.txt
pytest                       # debe terminar con «88 passed»
```

Los demás comandos de calidad están en la *Documentación del ambiente de desarrollo* (sección 3.6).

## 7.9 Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `python` no se reconoce como comando | Python no está en el PATH | Reinstale marcando «Add python.exe to PATH», o use `py` en Windows. |
| `ModuleNotFoundError: No module named 'flask'` | Entorno virtual no activado | Active `.venv` (paso 7.3) y vuelva a ejecutar. |
| `Address already in use` / puerto ocupado | Otro programa usa el puerto 5000 | Defina `CAFETERIA_PUERTO=5001` (u otro). En macOS el puerto 5000 puede estar ocupado por *AirPlay Receiver*. |
| `sqlite3.OperationalError: no such table: json_each` | Python con SQLite antiguo | Instale Python 3.11 o superior desde python.org. |
| «El formulario expiró» al enviar un formulario | La sesión cambió (por ejemplo, se reinició con otra clave secreta) | Recargue la página y envíe de nuevo. |
| «Usuario o clave incorrectos» con `admin` | La clave se definió con `CAFETERIA_ADMIN_CLAVE` en la primera ejecución | Use esa clave, o elimine la base para recrearla (se pierden los datos). |
| Los celulares no abren la página | Servidor escuchando solo en `127.0.0.1` o firewall | Use `CAFETERIA_HOST=0.0.0.0` y permita Python en el firewall. |
