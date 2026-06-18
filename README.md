# Truck & Roll – API Backend

API REST en Python para el sistema de gestión de pedidos de food trucks.
Cubre el registro de pedidos, procesamiento de pagos, seguimiento de estado y notificación al cliente.

Desarrollado con **FastAPI**.

---

## Cómo funciona esta API

Una API REST es un servicio que recibe pedidos HTTP (GET, POST, PATCH, etc.) y devuelve datos en formato JSON. El frontend no tiene lógica de negocio propia — solo le pide cosas al backend y muestra lo que recibe.

El flujo típico es:

```
Frontend (React, etc.)  ──►  API (este proyecto)  ──►  Datos en memoria
                         HTTP                      lógica de negocio
```

Por ejemplo, cuando el cajero registra un pedido en la pantalla, el frontend manda un `POST /orders` con los ítems. La API valida, calcula el total, guarda el pedido y devuelve el JSON con el resultado. El frontend nunca calcula precios ni valida stock — eso es responsabilidad del backend.

### Qué es `/docs` y para qué sirve

`http://127.0.0.1:8000/docs` es una página web que se genera automáticamente a partir del código de la API. Sirve para **explorar y probar todos los endpoints desde el navegador**, sin necesidad de escribir código ni usar herramientas externas.

Cómo usarla:
1. Con el servidor corriendo, abrís `http://127.0.0.1:8000/docs` en el navegador.
2. Ves la lista de todos los endpoints disponibles.
3. Hacés click en uno → **"Probar"** → completás los campos del formulario → **"Ejecutar"**.
4. La página muestra la respuesta: el JSON que devuelve la API, el código HTTP (200, 201, 404, etc.) y la URL exacta que se llamó.

Es útil para el equipo de frontend para entender qué manda cada endpoint y qué devuelve, sin tener que leer el código fuente.

---

## Requisitos

- Python 3.11 o superior (probado con 3.12)
- No requiere base de datos: usa almacenamiento en memoria (los datos se pierden al reiniciar el servidor)

---

## Instalación

### Windows (PowerShell o CMD)

```powershell
# 1. Crear entorno virtual
python -m venv .venv

# 2. Activar entorno virtual
.venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

### macOS / Linux (bash / zsh)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Ejecutar la API

```bash
uvicorn app.main:app --reload
```

La API queda disponible en:

- Base URL: `http://127.0.0.1:8000`
- **Swagger UI (documentación interactiva):** `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Con `--reload` el servidor se reinicia automáticamente al guardar cambios en el código.

---

## Ejecutar los tests

```bash
python -m pytest tests/ -v
```

---

## Endpoints

### Productos

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/products` | Lista todos los productos disponibles |

### Pedidos

| Método | Ruta | Descripción | Caso de Uso |
|--------|------|-------------|-------------|
| `POST` | `/orders` | Crea un nuevo pedido | CU1 – Registrar pedido |
| `GET` | `/orders/{order_id}` | Consulta el estado de un pedido | CU3 – Consultar estado |
| `PATCH` | `/orders/{order_id}/status` | Avanza el estado del pedido (`ready` o `delivered`) | CU4 / CU5 |

### Pagos

| Método | Ruta | Descripción | Caso de Uso |
|--------|------|-------------|-------------|
| `POST` | `/orders/{order_id}/payments` | Procesa el pago de un pedido | CU2 – Procesar pago |

---

## Flujo completo de un pedido

```
1. GET  /products                       → ver qué hay disponible
2. POST /orders                         → el cajero registra el pedido
3. POST /orders/{id}/payments           → el cliente paga (tarjeta o efectivo)
4. PATCH /orders/{id}/status {"status":"ready"}     → el cocinero marca listo
5. PATCH /orders/{id}/status {"status":"delivered"} → el cajero confirma entrega
```

Los estados válidos de un pedido son: `pending` → `paid` → `ready` → `delivered`.
Las transiciones fuera de orden devuelven `409 Conflict`.

---

## Medios de pago soportados

| `method` | Descripción | Campo requerido en `details` |
|----------|-------------|------------------------------|
| `card` | Pago con tarjeta | `card_token` (string; si empieza con `"fail"` simula rechazo) |
| `cash` | Pago en efectivo | ninguno |

---

## Probar los endpoints

El archivo [`truck_roll.http`](truck_roll.http) contiene ejemplos listos para usar con la extensión **REST Client** de VS Code.

1. Instalar la extensión: buscar "REST Client" (humao.rest-client) en el marketplace de VS Code.
2. Abrir `truck_roll.http`.
3. Hacer click en "Send Request" sobre cada bloque.

> El archivo captura automáticamente el `order_id` del pedido creado y lo reutiliza en las llamadas siguientes.

---

## Productos de ejemplo (seed)

Al iniciar, la API carga los siguientes productos:

| ID | Nombre | Precio (UYU) |
|----|--------|-------------|
| P001 | Hamburguesa clásica | 290 |
| P002 | Papas fritas | 120 |
| P003 | Coca-Cola 500ml | 80 |
| P004 | Chivito al pan | 350 |
| P005 | Agua mineral | 60 |

---

## Arquitectura (resumen para el equipo de frontend)

- **`app/domain/`** – Modelos de negocio (`Order`, `Product`, `Payment`) y excepciones.
- **`app/repositories/`** – Interfaces de acceso a datos y su implementación en memoria.
- **`app/services/`** – Lógica de negocio (`OrderService`, `PaymentService`). No dependen de la capa HTTP.
- **`app/main.py`** – Endpoints FastAPI. Solo traduce HTTP ↔ servicios.
- **`tests/`** – Tests unitarios del flujo completo, sin levantar el servidor.
