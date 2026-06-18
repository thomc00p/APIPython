from fastapi import FastAPI, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

from app.domain.exceptions import DomainError
from app.domain.models import Order
from app.repositories.in_memory import InMemoryOrderRepository, InMemoryPaymentRepository, InMemoryProductRepository
from app.schemas import (
    CreateOrderRequest,
    OrderItemResponse,
    OrderResponse,
    PaymentRequest,
    PaymentResponse,
    ProductResponse,
    UpdateOrderStatusRequest,
)
from app.services.notification import CustomerNotificationService
from app.services.order_factory import OrderFactory
from app.services.order_service import OrderService
from app.services.payment_factory import PaymentStrategyFactory
from app.services.payment_service import PaymentService
from app.services.product_service import ProductService
from app.domain.events import EventDispatcher

app = FastAPI(
    title="Truck & Roll",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)


@app.get("/docs", include_in_schema=False)
def custom_docs() -> HTMLResponse:
    swagger_html = get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Truck & Roll – API",
    )
    html = swagger_html.body.decode()

    custom_css = """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

      * { box-sizing: border-box; }

      body, .swagger-ui {
        font-family: 'Inter', system-ui, sans-serif !important;
        background: #f5f4f0 !important;
        color: #1a1a1a !important;
      }

      /* Header */
      .swagger-ui .topbar {
        background: #1c1c1c !important;
        padding: 0 32px !important;
        border-bottom: 3px solid #e8401c !important;
      }
      .swagger-ui .topbar .download-url-wrapper { display: none !important; }
      .swagger-ui .topbar-wrapper { justify-content: flex-start !important; gap: 12px; }
      .swagger-ui .topbar-wrapper img { display: none !important; }
      .swagger-ui .topbar-wrapper::before {
        content: "🚚 Truck & Roll";
        color: #ffffff;
        font-size: 20px;
        font-weight: 700;
        letter-spacing: -0.3px;
      }
      .swagger-ui .topbar-wrapper::after {
        content: "API de gestión de pedidos";
        color: #999;
        font-size: 13px;
        font-weight: 400;
        margin-left: 4px;
        align-self: center;
      }

      /* Info block */
      .swagger-ui .info { margin: 32px 0 24px !important; }
      .swagger-ui .info .title {
        font-size: 26px !important;
        font-weight: 700 !important;
        color: #1c1c1c !important;
        letter-spacing: -0.5px !important;
      }
      .swagger-ui .info .title small { display: none !important; }
      .swagger-ui .info p, .swagger-ui .info li { color: #555 !important; font-size: 14px !important; }

      /* Remove default tag styling */
      .swagger-ui .opblock-tag {
        background: transparent !important;
        border: none !important;
        border-bottom: 1px solid #e0ddd8 !important;
        padding: 10px 0 !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        color: #555 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
      }
      .swagger-ui .opblock-tag:hover { background: transparent !important; }
      .swagger-ui .opblock-tag svg { display: none !important; }

      /* Operation blocks */
      .swagger-ui .opblock {
        border: 1px solid #e0ddd8 !important;
        border-radius: 8px !important;
        margin: 6px 0 !important;
        box-shadow: none !important;
        background: #ffffff !important;
      }
      .swagger-ui .opblock:hover { border-color: #c8c4be !important; }

      /* Method colors — flat, no gradients */
      .swagger-ui .opblock.opblock-get    { border-left: 4px solid #2a6dd9 !important; background: #fff !important; }
      .swagger-ui .opblock.opblock-post   { border-left: 4px solid #1a7a4a !important; background: #fff !important; }
      .swagger-ui .opblock.opblock-patch  { border-left: 4px solid #a05c00 !important; background: #fff !important; }
      .swagger-ui .opblock.opblock-delete { border-left: 4px solid #c0392b !important; background: #fff !important; }

      .swagger-ui .opblock .opblock-summary {
        background: transparent !important;
        border: none !important;
        padding: 12px 16px !important;
      }
      .swagger-ui .opblock-summary-method {
        border-radius: 4px !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        min-width: 58px !important;
        text-align: center !important;
        padding: 4px 0 !important;
      }
      .swagger-ui .opblock.opblock-get    .opblock-summary-method { background: #2a6dd9 !important; }
      .swagger-ui .opblock.opblock-post   .opblock-summary-method { background: #1a7a4a !important; }
      .swagger-ui .opblock.opblock-patch  .opblock-summary-method { background: #a05c00 !important; }
      .swagger-ui .opblock.opblock-delete .opblock-summary-method { background: #c0392b !important; }

      .swagger-ui .opblock-summary-path {
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #1c1c1c !important;
      }
      .swagger-ui .opblock-summary-description {
        font-size: 13px !important;
        color: #777 !important;
      }

      /* Expanded body */
      .swagger-ui .opblock-body { background: #fafaf8 !important; border-top: 1px solid #e0ddd8 !important; }
      .swagger-ui .opblock-section-header {
        background: transparent !important;
        border-bottom: 1px solid #eeecea !important;
        padding: 10px 16px !important;
      }
      .swagger-ui .opblock-section-header h4 {
        font-size: 12px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        color: #555 !important;
      }

      /* Buttons */
      .swagger-ui .btn {
        border-radius: 6px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 7px 16px !important;
        cursor: pointer !important;
        border: none !important;
        transition: opacity 0.15s !important;
      }
      .swagger-ui .btn:hover { opacity: 0.85 !important; }
      .swagger-ui .btn.try-out__btn,
      .swagger-ui .btn.execute { background: #1c1c1c !important; color: #fff !important; }
      .swagger-ui .btn.btn-clear { background: #e0ddd8 !important; color: #1c1c1c !important; }
      .swagger-ui .btn.cancel   { background: #e0ddd8 !important; color: #1c1c1c !important; }
      .swagger-ui .btn.authorize { background: #2a6dd9 !important; color: #fff !important; }
      .swagger-ui .btn.btn-secondary { background: #e0ddd8 !important; color: #1c1c1c !important; }

      /* Response codes */
      .swagger-ui .responses-inner h4,
      .swagger-ui .responses-inner h5 { font-size: 12px !important; color: #555 !important; }
      .swagger-ui .response-col_status { font-weight: 600 !important; }
      .swagger-ui table.responses-table td { border-color: #eeecea !important; }

      /* Code blocks */
      .swagger-ui .highlight-code,
      .swagger-ui textarea,
      .swagger-ui .body-param textarea {
        background: #1c1c1c !important;
        color: #e8e8e8 !important;
        border-radius: 6px !important;
        font-size: 13px !important;
        border: none !important;
      }
      .swagger-ui .microlight { background: #1c1c1c !important; color: #e8e8e8 !important; }

      /* Models section */
      .swagger-ui section.models {
        border: 1px solid #e0ddd8 !important;
        border-radius: 8px !important;
        background: #fff !important;
        margin-top: 24px !important;
      }
      .swagger-ui section.models h4 {
        font-size: 13px !important;
        font-weight: 600 !important;
        color: #555 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
      }
      .swagger-ui .model-box { background: #fafaf8 !important; }

      /* Inputs */
      .swagger-ui input[type=text],
      .swagger-ui input[type=password],
      .swagger-ui select {
        border: 1px solid #d4d0ca !important;
        border-radius: 6px !important;
        background: #fff !important;
        color: #1c1c1c !important;
        font-size: 13px !important;
        padding: 6px 10px !important;
      }
      .swagger-ui input:focus, .swagger-ui select:focus {
        outline: 2px solid #2a6dd9 !important;
        border-color: transparent !important;
      }

      /* Hide the ugly default scheme pill */
      .swagger-ui .scheme-container { background: transparent !important; box-shadow: none !important; padding: 0 !important; }

      /* Scrollbar */
      ::-webkit-scrollbar { width: 6px; height: 6px; }
      ::-webkit-scrollbar-track { background: #f5f4f0; }
      ::-webkit-scrollbar-thumb { background: #c8c4be; border-radius: 3px; }
    </style>
    """

    translate_js = """
    <script>
      const TRANSLATIONS = {
        "Try it out": "Probar",
        "Execute": "Ejecutar",
        "Cancel": "Cancelar",
        "Clear": "Limpiar",
        "Authorize": "Autorizar",
        "Close": "Cerrar",
        "Reset": "Reiniciar",
        "Download": "Descargar",
        "Response body": "Cuerpo de la respuesta",
        "Response headers": "Cabeceras de la respuesta",
        "Responses": "Respuestas",
        "Request body": "Cuerpo del pedido",
        "Parameters": "Parámetros",
        "Parameter": "Parámetro",
        "No parameters": "Sin parámetros",
        "Description": "Descripción",
        "Example Value": "Valor de ejemplo",
        "Model": "Modelo",
        "Name": "Nombre",
        "Type": "Tipo",
        "Required": "Requerido",
        "Code": "Código",
        "Loading...": "Cargando...",
        "Failed to fetch": "Error al conectar",
        "Server response": "Respuesta del servidor",
        "Request URL": "URL de la solicitud",
        "Curl": "Curl",
        "available": "disponibles",
        "Hide": "Ocultar",
        "Show": "Mostrar",
        "default": "por defecto",
        "string": "texto",
        "integer": "entero",
        "boolean": "booleano",
        "array": "lista",
        "object": "objeto",
      };

      function translateNode(node) {
        if (node.nodeType === Node.TEXT_NODE) {
          const t = TRANSLATIONS[node.textContent.trim()];
          if (t) node.textContent = node.textContent.replace(node.textContent.trim(), t);
        }
        node.childNodes.forEach(translateNode);
      }

      const observer = new MutationObserver(mutations => {
        mutations.forEach(m => m.addedNodes.forEach(translateNode));
      });
      observer.observe(document.body, { childList: true, subtree: true });
      window.addEventListener('load', () => translateNode(document.body));
    </script>
    """

    footer_section = """
    <style>
      #tr-guide {
        max-width: 1460px;
        margin: 48px auto 64px;
        padding: 0 20px;
        font-family: 'Inter', system-ui, sans-serif;
        color: #1a1a1a;
      }
      #tr-guide h2 {
        font-size: 18px;
        font-weight: 700;
        margin: 0 0 28px;
        letter-spacing: -0.3px;
      }
      #tr-guide h3 {
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: #999;
        margin: 0 0 12px;
      }

      /* --- Flujo --- */
      #tr-guide .tr-flow {
        background: #fff;
        border: 1px solid #e0ddd8;
        border-radius: 10px;
        padding: 20px 24px;
        margin-bottom: 16px;
      }
      #tr-guide .tr-steps { display: flex; flex-direction: column; gap: 10px; }
      #tr-guide .tr-step { display: flex; align-items: flex-start; gap: 12px; }
      #tr-guide .tr-step-num {
        min-width: 24px; height: 24px;
        background: #1c1c1c; color: #fff;
        border-radius: 50%; font-size: 11px; font-weight: 700;
        display: flex; align-items: center; justify-content: center;
        margin-top: 1px; flex-shrink: 0;
      }
      #tr-guide .tr-step-body { font-size: 13px; color: #444; line-height: 1.55; }
      #tr-guide .tr-step-body strong { color: #1c1c1c; font-weight: 600; }
      #tr-guide .tr-step-body code {
        font-size: 12px; background: #f5f4f0;
        border: 1px solid #e0ddd8; border-radius: 4px;
        padding: 1px 5px; font-family: monospace; color: #1c1c1c;
      }
      #tr-guide .tr-states {
        display: flex; align-items: center; gap: 8px;
        flex-wrap: wrap; margin-top: 16px; padding-top: 16px;
        border-top: 1px solid #eeecea;
      }
      #tr-guide .tr-state {
        font-size: 12px; font-weight: 600; padding: 4px 12px;
        border-radius: 20px; border: 1.5px solid #1c1c1c;
        background: #fff; color: #1c1c1c;
      }
      #tr-guide .tr-arrow-state { color: #bbb; font-size: 14px; }

      /* --- Cards de endpoints (opción A) --- */
      #tr-guide .tr-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 32px;
      }
      @media (max-width: 800px) { #tr-guide .tr-grid { grid-template-columns: 1fr; } }
      #tr-guide .tr-card {
        background: #fff;
        border: 1px solid #e0ddd8;
        border-radius: 10px;
        padding: 18px 22px;
      }
      #tr-guide .tr-card-header {
        display: flex; align-items: baseline;
        gap: 6px; margin-bottom: 10px;
      }
      #tr-guide .tr-method {
        font-size: 12px; font-weight: 700;
        color: #1c1c1c; font-family: monospace;
        letter-spacing: 0.03em;
      }
      #tr-guide .tr-sep { color: #bbb; font-size: 13px; }
      #tr-guide .tr-path {
        font-size: 13px; font-weight: 600;
        color: #1c1c1c; font-family: monospace;
      }
      #tr-guide .tr-card p {
        font-size: 13px; color: #555;
        margin: 0 0 10px; line-height: 1.55;
      }
      #tr-guide .tr-card p:last-child { margin-bottom: 0; }
      #tr-guide .tr-cu {
        font-size: 12px; color: #777;
        border-top: 1px solid #eeecea;
        padding-top: 10px; margin-top: 10px;
      }

      /* --- Tabla de endpoints (opción B) --- */
      #tr-guide .tr-table-wrap {
        background: #fff;
        border: 1px solid #e0ddd8;
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 32px;
      }
      #tr-guide table.tr-table {
        width: 100%; border-collapse: collapse;
        font-size: 13px;
      }
      #tr-guide table.tr-table thead tr {
        background: #f5f4f0;
        border-bottom: 1px solid #e0ddd8;
      }
      #tr-guide table.tr-table th {
        text-align: left; padding: 10px 16px;
        font-size: 11px; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.07em;
        color: #999;
      }
      #tr-guide table.tr-table td {
        padding: 11px 16px;
        border-bottom: 1px solid #f0ede8;
        vertical-align: top;
        color: #444;
        line-height: 1.5;
      }
      #tr-guide table.tr-table tr:last-child td { border-bottom: none; }
      #tr-guide table.tr-table tr:hover td { background: #fafaf8; }
      #tr-guide .td-method {
        font-family: monospace; font-weight: 700;
        color: #1c1c1c; white-space: nowrap;
      }
      #tr-guide .td-path {
        font-family: monospace; color: #1c1c1c;
        white-space: nowrap;
      }
      #tr-guide .td-cu { color: #777; font-size: 12px; white-space: nowrap; }

      #tr-guide .tr-option-label {
        font-size: 11px; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.08em;
        color: #bbb; margin: 28px 0 10px;
      }
    </style>

    <div id="tr-guide">
      <h2>Guía de uso</h2>

      <!-- Flujo completo -->
      <div class="tr-flow">
        <h3>Flujo completo de un pedido</h3>
        <div class="tr-steps">
          <div class="tr-step">
            <div class="tr-step-num">1</div>
            <div class="tr-step-body"><strong>GET /products</strong> — El cajero consulta qué productos hay disponibles antes de tomar el pedido.</div>
          </div>
          <div class="tr-step">
            <div class="tr-step-num">2</div>
            <div class="tr-step-body"><strong>POST /orders</strong> — El cajero registra el pedido con los ítems y cantidades. La API calcula el total automáticamente.</div>
          </div>
          <div class="tr-step">
            <div class="tr-step-num">3</div>
            <div class="tr-step-body"><strong>POST /orders/{id}/payments</strong> — El cliente paga con tarjeta o efectivo. Si el pago es aprobado, el pedido pasa a <code>paid</code> y se dispara la notificación.</div>
          </div>
          <div class="tr-step">
            <div class="tr-step-num">4</div>
            <div class="tr-step-body"><strong>PATCH /orders/{id}/status</strong> con <code>"status": "ready"</code> — El cocinero indica que el pedido está listo para entregar.</div>
          </div>
          <div class="tr-step">
            <div class="tr-step-num">5</div>
            <div class="tr-step-body"><strong>PATCH /orders/{id}/status</strong> con <code>"status": "delivered"</code> — El cajero confirma que el cliente retiró el pedido.</div>
          </div>
        </div>
        <div class="tr-states">
          <span class="tr-state">pending</span>
          <span class="tr-arrow-state">→</span>
          <span class="tr-state">paid</span>
          <span class="tr-arrow-state">→</span>
          <span class="tr-state">ready</span>
          <span class="tr-arrow-state">→</span>
          <span class="tr-state">delivered</span>
        </div>
      </div>

      <!-- Tabla de endpoints -->
      <h3>Endpoints</h3>
      <div class="tr-table-wrap">
        <table class="tr-table">
          <thead>
            <tr>
              <th>Método</th>
              <th>Ruta</th>
              <th>Descripción</th>
              <th>Caso de uso</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="td-method">GET</td>
              <td class="td-path">/products</td>
              <td>Lista los productos disponibles del food truck.</td>
              <td class="td-cu">Paso previo al CU1</td>
            </tr>
            <tr>
              <td class="td-method">POST</td>
              <td class="td-path">/orders</td>
              <td>Registra un nuevo pedido y calcula el total.</td>
              <td class="td-cu">CU1 – Registrar pedido</td>
            </tr>
            <tr>
              <td class="td-method">GET</td>
              <td class="td-path">/orders/{order_id}</td>
              <td>Consulta el estado y detalle de un pedido.</td>
              <td class="td-cu">CU3 – Consultar estado</td>
            </tr>
            <tr>
              <td class="td-method">POST</td>
              <td class="td-path">/orders/{order_id}/payments</td>
              <td>Procesa el pago (tarjeta o efectivo).</td>
              <td class="td-cu">CU2 – Procesar pago</td>
            </tr>
            <tr>
              <td class="td-method">PATCH</td>
              <td class="td-path">/orders/{order_id}/status</td>
              <td>Marca el pedido como listo o confirma su entrega.</td>
              <td class="td-cu">CU4 / CU5</td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
    """

    html = html.replace("</head>", custom_css + "</head>")
    html = html.replace("</body>", footer_section + translate_js + "</body>")
    return HTMLResponse(html)

product_repository = InMemoryProductRepository()
order_repository = InMemoryOrderRepository()
payment_repository = InMemoryPaymentRepository()
event_dispatcher = EventDispatcher()

notification_service = CustomerNotificationService()
event_dispatcher.subscribe_order_paid(notification_service)

order_service = OrderService(
    product_repository=product_repository,
    order_repository=order_repository,
    order_factory=OrderFactory(),
)
product_service = ProductService(product_repository=product_repository)
payment_service = PaymentService(
    order_repository=order_repository,
    payment_repository=payment_repository,
    payment_factory=PaymentStrategyFactory(),
    event_dispatcher=event_dispatcher,
)


def _to_order_response(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        customer_id=order.customer_id,
        status=order.status.value,
        total=order.total,
        items=[
            OrderItemResponse(
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
            )
            for item in order.items
        ],
    )


@app.get("/products", response_model=list[ProductResponse])
def list_products() -> list[ProductResponse]:
    return [ProductResponse(id=p.id, name=p.name, price=p.price) for p in product_service.list_products()]


@app.post("/orders", response_model=OrderResponse, status_code=201)
def create_order(payload: CreateOrderRequest) -> OrderResponse:
    try:
        order = order_service.create_order(
            customer_id=payload.customer_id,
            items=[{"product_id": i.product_id, "quantity": i.quantity} for i in payload.items],
        )
    except DomainError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message) from error
    return _to_order_response(order)


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str) -> OrderResponse:
    try:
        order = order_service.get_order(order_id)
    except DomainError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message) from error
    return _to_order_response(order)


@app.patch("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(order_id: str, payload: UpdateOrderStatusRequest) -> OrderResponse:
    try:
        if payload.status == "ready":
            order = order_service.mark_order_ready(order_id)
        else:
            order = order_service.mark_order_delivered(order_id)
    except DomainError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message) from error
    return _to_order_response(order)


@app.post("/orders/{order_id}/payments", response_model=PaymentResponse)
def process_order_payment(order_id: str, payload: PaymentRequest) -> PaymentResponse:
    try:
        payment, message = payment_service.process_payment(order_id=order_id, method=payload.method, details=payload.details)
    except DomainError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message) from error

    return PaymentResponse(
        id=payment.id,
        order_id=payment.order_id,
        amount=payment.amount,
        method=payment.method,
        status=payment.status.value,
        message=message,
    )
