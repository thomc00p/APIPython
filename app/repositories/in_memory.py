from app.domain.models import Order, Payment, Product
from app.repositories.interfaces import OrderRepository, PaymentRepository, ProductRepository


class InMemoryProductRepository(ProductRepository):
    def __init__(self) -> None:
        self._products: dict[str, Product] = {
            "P001": Product(id="P001", name="Hamburguesa clásica", price=290.0),
            "P002": Product(id="P002", name="Papas fritas", price=120.0),
            "P003": Product(id="P003", name="Coca-Cola 500ml", price=80.0),
            "P004": Product(id="P004", name="Chivito al pan", price=350.0),
            "P005": Product(id="P005", name="Agua mineral", price=60.0),
        }

    def list_all(self) -> list[Product]:
        return list(self._products.values())

    def get_by_id(self, product_id: str) -> Product | None:
        return self._products.get(product_id)

    def get_by_ids(self, product_ids: set[str]) -> dict[str, Product]:
        return {product_id: product for product_id in product_ids if (product := self._products.get(product_id)) is not None}


class InMemoryOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}

    def save(self, order: Order) -> Order:
        self._orders[order.id] = order
        return order

    def get_by_id(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)


class InMemoryPaymentRepository(PaymentRepository):
    def __init__(self) -> None:
        self._payments_by_order: dict[str, Payment] = {}

    def save(self, payment: Payment) -> Payment:
        self._payments_by_order[payment.order_id] = payment
        return payment

    def get_by_order_id(self, order_id: str) -> Payment | None:
        return self._payments_by_order.get(order_id)
