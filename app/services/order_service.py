from uuid import uuid4

from app.domain.exceptions import ConflictError, NotFoundError
from app.domain.models import Order
from app.repositories.interfaces import OrderRepository, ProductRepository
from app.services.order_factory import OrderFactory


class OrderService:
    def __init__(
        self,
        product_repository: ProductRepository,
        order_repository: OrderRepository,
        order_factory: OrderFactory,
    ) -> None:
        self._product_repository = product_repository
        self._order_repository = order_repository
        self._order_factory = order_factory

    def create_order(self, customer_id: str, items: list[dict]) -> Order:
        product_ids = {item["product_id"] for item in items}
        products = self._product_repository.get_by_ids(product_ids)
        order = self._order_factory.create(
            order_id=str(uuid4()),
            customer_id=customer_id,
            requested_items=items,
            products=products,
        )
        return self._order_repository.save(order)

    def get_order(self, order_id: str) -> Order:
        order = self._order_repository.get_by_id(order_id)
        if order is None:
            raise NotFoundError("Order not found")
        return order

    def mark_order_ready(self, order_id: str) -> Order:
        order = self._order_repository.get_by_id(order_id)
        if order is None:
            raise NotFoundError("Order not found")
        try:
            order.mark_ready()
        except ValueError as exc:
            raise ConflictError(str(exc)) from exc
        return self._order_repository.save(order)

    def mark_order_delivered(self, order_id: str) -> Order:
        order = self._order_repository.get_by_id(order_id)
        if order is None:
            raise NotFoundError("Order not found")
        try:
            order.mark_delivered()
        except ValueError as exc:
            raise ConflictError(str(exc)) from exc
        return self._order_repository.save(order)
