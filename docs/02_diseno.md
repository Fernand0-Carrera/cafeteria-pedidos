# 2. Documentación de Diseño

## 2.1 Visión general de la arquitectura

La aplicación es una aplicación web monolítica organizada en **cuatro capas**. Cada capa solo depende de las capas inferiores, lo que permite probar las reglas de negocio sin servidor web ni navegador.

```mermaid
flowchart TB
    subgraph Navegador
        U1[Cliente<br/>celular o PC]
        U2[Personal<br/>PC del mostrador]
    end
    subgraph "Capa web · app/web"
        W1[cliente.py<br/>Blueprint del cliente]
        W2[personal.py<br/>Blueprint del personal]
        W3[comun.py<br/>sesión, CSRF, errores]
        T[Plantillas Jinja2 + estilos.css]
    end
    subgraph "Capa de servicios · app/servicios"
        S1[MenuServicio]
        S2[PedidoServicio]
        S3[ClienteServicio]
        S4[PersonalServicio]
        S5[generador_codigo]
    end
    subgraph "Capa de persistencia · app/persistencia"
        R[Repositorios<br/>Producto, Cliente, Pedido, Personal]
        DB[(SQLite<br/>instance/cafeteria.db)]
    end
    subgraph "Dominio · app/dominio"
        D[modelos · validaciones · excepciones]
    end
    U1 & U2 -->|HTTP| W1 & W2
    W1 & W2 --> W3
    W1 & W2 --> T
    W1 & W2 --> S1 & S2 & S3 & S4
    S2 --> S5
    S1 & S2 & S3 & S4 --> R
    R --> DB
    S1 & S2 & S3 & S4 & R -.usa.-> D
```

| Capa | Responsabilidad | No debe |
|---|---|---|
| Web | Recibir peticiones, leer formularios, controlar sesión y CSRF, elegir la plantilla y los mensajes. | Contener reglas de negocio ni SQL. |
| Servicios | Ejecutar los casos de uso y aplicar las reglas RN-NEG-01 a 07; controlar transacciones. | Conocer HTTP ni HTML. |
| Persistencia | Leer y escribir filas y convertirlas en entidades. | Decidir si una operación es válida. |
| Dominio | Entidades, enumeraciones de estado, validaciones de datos y excepciones de negocio. | Depender de otras capas. |

## 2.2 Decisiones de diseño

| # | Decisión | Alternativas consideradas | Motivo |
|---|---|---|---|
| D-01 | Python 3.11+ con Flask | Java/Spring Boot, Node/Express | Ligero, sin servidor de aplicaciones; facilita la instalación en los equipos del equipo y del docente. |
| D-02 | SQLite en archivo | MySQL, PostgreSQL | Cumple la persistencia sin instalar un motor; suficiente para una cafetería. El acceso pasa por repositorios, así que cambiar de motor solo afecta a esa capa. |
| D-03 | SQL con `sqlite3` estándar, sin ORM | SQLAlchemy | Menos dependencias y SQL visible para el análisis del curso. |
| D-04 | Importes en centavos enteros | `float`, `Decimal` en BD | Exactitud en sumas (RN-NEG-03). |
| D-05 | Precio unitario copiado en `detalle_pedido` | Calcular desde `producto` | Cumple RN-NEG-04 de forma estructural. |
| D-06 | Estados como `Enum` con orden implícito y método `siguiente()` | Tabla de transiciones | Un solo lugar define el orden de RN-NEG-06. |
| D-07 | Entrega mediante búsqueda por código | Botón «Entregar» en la lista | Obliga a verificar el código (RN-NEG-07, RN-04). |
| D-08 | Control de concurrencia optimista (`UPDATE … WHERE estado = ?`) | Bloqueos | Evita dobles avances con dos empleados o doble clic, sin bloquear. |
| D-09 | Inyección del generador de código y del reloj en `PedidoServicio` | Llamadas directas | Permite probar colisiones de código y fechas exactas. |
| D-10 | Renderizado en servidor con Jinja2, sin JavaScript obligatorio | SPA con React | Menor complejidad; funciona en cualquier navegador; actualización automática por `meta refresh`. |

## 2.3 Diagrama de casos de uso

```mermaid
flowchart LR
    C((Cliente))
    P((Personal))
    subgraph Sistema de pedidos de cafetería
        CU1([CU-01 Registrarse])
        CU2([CU-02 Identificarse])
        CU3([CU-03 Consultar menú])
        CU4([CU-04 Registrar pedido])
        CU4a([Seleccionar productos<br/>y cantidades])
        CU4b([Revisar importe total])
        CU4c([Confirmar y obtener código])
        CU5([CU-05 Consultar estado])
        CU6([CU-06 Ingresar como personal])
        CU7([CU-07 Mantener menú])
        CU8([CU-08 Consultar pedidos por estado])
        CU9([CU-09 Registrar avance])
        CU10([CU-10 Entregar pedido])
        CU10a([Verificar código de retiro])
    end
    C --- CU1 & CU2 & CU3 & CU4 & CU5
    CU4 -.include.-> CU4a & CU4b & CU4c
    P --- CU6 & CU7 & CU8 & CU9 & CU10
    CU10 -.include.-> CU10a
```

## 2.4 Modelo de dominio (diagrama de clases)

```mermaid
classDiagram
    direction LR
    class Producto {
        +int id
        +str codigo
        +str nombre
        +Categoria categoria
        +int precio_centavos
        +bool disponible
    }
    class Categoria {
        <<enumeration>>
        ALIMENTO
        BEBIDA
    }
    class Cliente {
        +int id
        +str codigo
        +str nombre
        +str apellido
        +str cedula
        +str celular
        +str correo
        +nombre_completo() str
    }
    class Pedido {
        +int id
        +str codigo_retiro
        +int cliente_id
        +EstadoPedido estado
        +str fecha_registro
        +int total_centavos
        +list~DetallePedido~ detalles
    }
    class DetallePedido {
        +int producto_id
        +str codigo_producto
        +str nombre_producto
        +int cantidad
        +int precio_unitario_centavos
        +subtotal_centavos() int
    }
    class EstadoPedido {
        <<enumeration>>
        PENDIENTE
        EN_PREPARACION
        LISTO_PARA_RETIRAR
        ENTREGADO
        +siguiente() EstadoPedido
        +etiqueta() str
    }
    class CambioEstado {
        +EstadoPedido estado
        +str fecha
        +str usuario
    }
    class ResumenPedido {
        +list~DetallePedido~ detalles
        +total_centavos() int
    }
    Producto --> Categoria
    Cliente "1" --> "0..*" Pedido : registra
    Pedido "1" *-- "1..*" DetallePedido : contiene
    DetallePedido "0..*" --> "1" Producto : referencia
    Pedido --> EstadoPedido
    Pedido "1" *-- "1..*" CambioEstado : historial
    ResumenPedido *-- DetallePedido
```

### Clases de servicio

```mermaid
classDiagram
    direction TB
    class PedidoServicio {
        -ProductoRepositorio _productos
        -PedidoRepositorio _pedidos
        -int _cantidad_maxima
        -Callable _generar_codigo
        -Callable _reloj
        +interpretar_cantidades(entradas) dict
        +calcular_resumen(items) ResumenPedido
        +confirmar_pedido(cliente_id, items, total_mostrado) Pedido
        +consultar_pedidos_cliente(cliente_id) list
        +consultar_pedido_cliente(cliente_id, pedido_id) Pedido
        +listar_pedidos(estado) list
        +avanzar_estado(pedido_id, estado_nuevo, usuario) Pedido
        +buscar_por_codigo(codigo) Pedido
        +entregar_pedido(pedido_id, codigo, usuario) Pedido
        +historial(pedido_id) list
    }
    class MenuServicio {
        +listar_menu() list
        +listar_todos() list
        +registrar_producto(...) Producto
        +actualizar_producto(...) Producto
        +cambiar_disponibilidad(codigo, disponible) Producto
    }
    class ClienteServicio {
        +registrar(...) Cliente
        +identificar(cedula, correo) Cliente
    }
    class PersonalServicio {
        +registrar(usuario, nombre, clave)
        +autenticar(usuario, clave) str
    }
    class ErrorNegocio {
        +str mensaje
        +str regla
    }
    ErrorNegocio <|-- PedidoVacioError
    ErrorNegocio <|-- CantidadInvalidaError
    ErrorNegocio <|-- ProductoNoDisponibleError
    ErrorNegocio <|-- TotalDesactualizadoError
    ErrorNegocio <|-- TransicionEstadoInvalidaError
    ErrorNegocio <|-- EntregaInvalidaError
    ErrorNegocio <|-- ValidacionError
    PedidoServicio ..> ErrorNegocio : lanza
    MenuServicio ..> ErrorNegocio : lanza
    ClienteServicio ..> ErrorNegocio : lanza
```

Las excepciones guardan la regla de negocio que las origina (atributo `regla`), lo que facilita la trazabilidad entre el código, los requisitos y las pruebas.

## 2.5 Ciclo de vida del pedido (diagrama de estados)

```mermaid
stateDiagram-v2
    [*] --> Pendiente : cliente confirma (código único, RN-NEG-05)
    Pendiente --> EnPreparacion : personal «Iniciar preparación»
    EnPreparacion --> ListoParaRetirar : personal «Marcar listo para retirar»
    ListoParaRetirar --> Entregado : personal verifica código (RN-NEG-07)
    Entregado --> [*]
    state "En preparación" as EnPreparacion
    state "Listo para retirar" as ListoParaRetirar
    note right of Pendiente
        No se permite saltar, retroceder
        ni repetir estados (RN-NEG-06)
    end note
```

## 2.6 Diagramas de secuencia

### PN-01 · Registro de un pedido

```mermaid
sequenceDiagram
    actor C as Cliente
    participant W as cliente.py
    participant S as PedidoServicio
    participant RP as ProductoRepositorio
    participant RD as PedidoRepositorio
    participant DB as SQLite
    C->>W: GET /menu
    W->>RP: listar(solo_disponibles=True)
    RP-->>W: productos
    W-->>C: menú con precios
    C->>W: POST /pedido/revisar (cantidades)
    W->>S: interpretar_cantidades() + calcular_resumen()
    S->>RP: obtener_por_codigos()
    alt selección inválida (RN-NEG-01/02)
        S-->>W: ErrorNegocio
        W-->>C: menú con mensaje del motivo
    else selección válida
        S-->>W: ResumenPedido (total)
        W-->>C: pantalla de revisión con total
    end
    C->>W: POST /pedido/confirmar (total_mostrado)
    W->>S: confirmar_pedido(cliente, items, total_mostrado)
    S->>S: calcular_resumen() otra vez
    alt total distinto (precio cambió)
        S-->>W: TotalDesactualizadoError
        W-->>C: revisión con nuevo total
    else total igual
        loop hasta encontrar un código libre
            S->>RD: existe_codigo(código)
        end
        S->>RD: crear(pedido, detalles, historial) [transacción]
        RD->>DB: INSERT pedido / detalle_pedido / historial_estado
        S-->>W: Pedido (Pendiente)
        W-->>C: ticket con código de retiro
    end
```

### PN-02 · Preparación y entrega

```mermaid
sequenceDiagram
    actor P as Personal
    actor C as Cliente
    participant W as personal.py
    participant S as PedidoServicio
    participant RD as PedidoRepositorio
    P->>W: GET /personal/pedidos?estado=PENDIENTE
    W->>S: listar_pedidos(PENDIENTE)
    S-->>W: pedidos en orden de llegada
    P->>W: POST /pedidos/{id}/avanzar (EN_PREPARACION)
    W->>S: avanzar_estado()
    S->>RD: actualizar_estado(id, PENDIENTE → EN_PREPARACION)
    Note over S,RD: UPDATE … WHERE estado = 'PENDIENTE'<br/>0 filas = otro usuario ya lo cambió
    S->>RD: registrar_historial()
    P->>W: POST /pedidos/{id}/avanzar (LISTO_PARA_RETIRAR)
    C->>P: presenta el código de retiro
    P->>W: POST /personal/entrega (código)
    W->>S: buscar_por_codigo()
    S-->>W: pedido y estado
    P->>W: POST /personal/entrega/confirmar (id, código)
    W->>S: entregar_pedido(id, código, usuario)
    alt código no coincide o estado ≠ Listo
        S-->>W: EntregaInvalidaError
    else correcto
        S->>RD: actualizar_estado(LISTO → ENTREGADO) + historial
        W-->>P: «registrado como Entregado»
    end
```

## 2.7 Modelo de datos

```mermaid
erDiagram
    CLIENTE ||--o{ PEDIDO : registra
    PEDIDO ||--|{ DETALLE_PEDIDO : contiene
    PRODUCTO ||--o{ DETALLE_PEDIDO : "se incluye en"
    PEDIDO ||--|{ HISTORIAL_ESTADO : registra
    CLIENTE {
        int id PK
        text codigo UK "CLI-00001"
        text nombre
        text apellido
        text cedula UK
        text celular
        text correo UK
    }
    PRODUCTO {
        int id PK
        text codigo UK
        text nombre
        text categoria "ALIMENTO | BEBIDA"
        int precio_centavos "> 0"
        int disponible "0 | 1"
    }
    PEDIDO {
        int id PK
        text codigo_retiro UK
        int cliente_id FK
        text estado "4 valores"
        text fecha_registro
        int total_centavos "> 0"
    }
    DETALLE_PEDIDO {
        int id PK
        int pedido_id FK
        int producto_id FK
        text codigo_producto
        text nombre_producto
        int cantidad "> 0"
        int precio_unitario_centavos "> 0"
    }
    HISTORIAL_ESTADO {
        int id PK
        int pedido_id FK
        text estado
        text fecha
        text usuario
    }
    PERSONAL {
        int id PK
        text usuario UK
        text nombre
        text hash_clave
    }
```

### Diccionario de datos (restricciones relevantes)

| Tabla.columna | Restricción | Regla que protege |
|---|---|---|
| `pedido.codigo_retiro` | `NOT NULL UNIQUE` | RN-NEG-05 |
| `pedido.estado` | `CHECK (estado IN (…4 valores…))` | RN-NEG-06 |
| `pedido.total_centavos` | `CHECK (> 0)` | RN-NEG-01 |
| `detalle_pedido.cantidad` | `CHECK (> 0)` | RN-NEG-01 |
| `detalle_pedido.precio_unitario_centavos` | copia del precio al confirmar | RN-NEG-04 |
| `detalle_pedido (pedido_id, producto_id)` | `UNIQUE` | un producto aparece una vez por pedido |
| `producto.precio_centavos` | `CHECK (> 0)` | precios válidos |
| `cliente.cedula`, `cliente.correo` | `UNIQUE` | sin clientes duplicados |
| Índices `idx_pedido_estado`, `idx_pedido_cliente` | — | RNF-07 rendimiento |

`detalle_pedido` guarda también código y nombre del producto: el pedido histórico se muestra igual aunque el producto se renombre después.

## 2.8 Diseño de la interfaz

### Mapa de navegación

```mermaid
flowchart LR
    I[Inicio /] --> M[Menú /menu]
    I --> PI[Ingreso personal]
    M -->|sin sesión| IN[Ingresar /ingresar] & RG[Registro /registro]
    IN & RG --> M
    M -->|Revisar pedido| RV[Revisión con total]
    RV -->|Cambiar selección| M
    RV -->|Confirmar pedido| DT[Ticket y seguimiento<br/>/mis-pedidos/id]
    DT --> MP[Mis pedidos]
    MP --> DT
    PI --> PP[Pedidos por estado]
    PP <--> EN[Entregar con código]
    PP <--> PR[Productos del menú]
    PR --> PF[Agregar / editar producto]
```

### Rutas

| Método | Ruta | Acceso | Descripción | HU |
|---|---|---|---|---|
| GET | `/` | público | Inicio con acceso para cliente y personal | — |
| GET, POST | `/registro` | público | Registro de cliente | HU-01 |
| GET, POST | `/ingresar` | público | Identificación del cliente | HU-02 |
| POST | `/salir` | cliente | Cerrar sesión | — |
| GET | `/menu` | público | Menú con precios; cantidades si hay sesión | HU-03, HU-04 |
| POST | `/pedido/revisar` | cliente | Valida selección y muestra total | HU-04, HU-05 |
| POST | `/pedido/confirmar` | cliente | Registra pedido y genera código | HU-06 |
| GET | `/mis-pedidos` | cliente | Pedidos del cliente | HU-07 |
| GET | `/mis-pedidos/<id>` | cliente dueño | Ticket, seguimiento y detalle | HU-06, HU-07 |
| GET, POST | `/personal/ingresar` | público | Ingreso del personal | HU-10 |
| GET | `/personal/pedidos?estado=` | personal | Pedidos por estado | HU-11 |
| POST | `/personal/pedidos/<id>/avanzar` | personal | Avance de estado | HU-12 |
| GET, POST | `/personal/entrega` | personal | Búsqueda por código | HU-13 |
| POST | `/personal/entrega/confirmar` | personal | Registro de entrega | HU-13 |
| GET | `/personal/productos` | personal | Listado del menú | HU-08, HU-09 |
| GET, POST | `/personal/productos/nuevo` | personal | Alta de producto | HU-08 |
| GET, POST | `/personal/productos/<codigo>/editar` | personal | Edición | HU-09 |
| POST | `/personal/productos/<codigo>/disponibilidad` | personal | Activar/desactivar | HU-09 |

### Lineamientos visuales

El menú se presenta como la **pizarra** de la cafetería (fondo verde pizarra, líneas punteadas entre nombre y precio), un referente que el cliente ya conoce del mostrador. El código de retiro se presenta como un **ticket** con letras grandes en fuente monoespaciada para leerlo fácilmente en voz alta. Cada estado tiene un color fijo (azul Pendiente, ámbar En preparación, verde Listo para retirar, gris Entregado) que se repite en todas las pantallas. Los estilos están en un único archivo (`app/web/static/estilos.css`), se adaptan a celulares y respetan el modo oscuro del sistema y la preferencia de movimiento reducido.

## 2.9 Diseño de seguridad

| Amenaza | Medida |
|---|---|
| Robo de claves del personal | Hash con sal (`werkzeug.security`, scrypt); nunca se guarda la clave en texto. |
| Falsificación de solicitudes (CSRF) | Token aleatorio por sesión en todo formulario `POST`; se rechaza si falta o no coincide. |
| Inyección SQL | Todas las consultas son parametrizadas; la consulta por lista de códigos usa `json_each(?)` en lugar de construir SQL. |
| Acceso a pedidos ajenos | `consultar_pedido_cliente` compara el dueño del pedido con el cliente de la sesión. |
| Redirección abierta | `ruta_local` solo acepta rutas internas (`/…`, no `//…`). |
| Adivinar códigos de retiro | 31⁶ ≈ 887 millones de combinaciones generadas con `secrets`. |
| Manipulación de cookies | Sesión firmada con clave secreta aleatoria persistida en `instance/secret_key`; cookies `HttpOnly` y `SameSite=Lax`. |

## 2.10 Manejo de errores

Las violaciones de reglas se modelan como subclases de `ErrorNegocio`. Las rutas las capturan y muestran el mensaje en la misma pantalla (código HTTP 422 en validaciones, 409 si el total cambió, 401 en credenciales). Los errores no capturados de tipo `ErrorNegocio` se muestran en la página de error con código 400. Los errores HTTP 404 y 405 tienen páginas propias en español. Toda operación que escribe varias filas (pedido, detalles e historial) se ejecuta en una transacción: si algo falla no queda un pedido incompleto.
