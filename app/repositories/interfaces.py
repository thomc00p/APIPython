from abc import ABC, abstractmethod

from app.domain.models import Order, Payment, Product


class ProductRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[Product]:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, product_id: str) -> Product | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_ids(self, product_ids: set[str]) -> dict[str, Product]:
        raise NotImplementedError


class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> Order:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, order_id: str) -> Order | None:
        raise NotImplementedError


class PaymentRepository(ABC):
    @abstractmethod
    def save(self, payment: Payment) -> Payment:
        raise NotImplementedError

    @abstractmethod
    def get_by_order_id(self, order_id: str) -> Payment | None:
        raise NotImplementedError
