import unittest

from app.domain.exceptions import ValidationError, NotFoundError
from app.domain.events import EventDispatcher
from app.repositories.in_memory import InMemoryOrderRepository, InMemoryPaymentRepository, InMemoryProductRepository
from app.services.notification import CustomerNotificationService
from app.services.order_factory import OrderFactory
from app.services.order_service import OrderService
from app.services.payment_factory import PaymentStrategyFactory
from app.services.payment_service import PaymentService


class OrderPaymentFlowTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.product_repository = InMemoryProductRepository()
        self.order_repository = InMemoryOrderRepository()
        self.payment_repository = InMemoryPaymentRepository()
        self.dispatcher = EventDispatcher()
        self.notification_service = CustomerNotificationService()
        self.dispatcher.subscribe_order_paid(self.notification_service)

        self.order_service = OrderService(
            product_repository=self.product_repository,
            order_repository=self.order_repository,
            order_factory=OrderFactory(),
        )
        self.payment_service = PaymentService(
            order_repository=self.order_repository,
            payment_repository=self.payment_repository,
            payment_factory=PaymentStrategyFactory(),
            event_dispatcher=self.dispatcher,
        )

    def test_create_order_calculates_total(self) -> None:
        order = self.order_service.create_order(
            customer_id="C001",
            items=[{"product_id": "P001", "quantity": 2}, {"product_id": "P002", "quantity": 1}],
        )

        self.assertEqual(order.total, 125.0)
        self.assertEqual(order.status.value, "pending")

    def test_confirmed_payment_marks_order_paid_and_notifies(self) -> None:
        order = self.order_service.create_order(customer_id="C001", items=[{"product_id": "P001", "quantity": 1}])
        payment, _ = self.payment_service.process_payment(
            order_id=order.id,
            method="card",
            details={"card_token": "tok_approved"},
        )
        updated_order = self.order_service.get_order(order.id)

        self.assertEqual(payment.status.value, "confirmed")
        self.assertEqual(updated_order.status.value, "paid")
        self.assertEqual(len(self.notification_service.notifications), 1)

    def test_create_order_with_unknown_product_fails(self) -> None:
        with self.assertRaisesRegex(NotFoundError, "Product not found: P999"):
            self.order_service.create_order(customer_id="C001", items=[{"product_id": "P999", "quantity": 1}])

    def test_payment_with_unsupported_method_fails(self) -> None:
        order = self.order_service.create_order(customer_id="C001", items=[{"product_id": "P001", "quantity": 1}])
        with self.assertRaisesRegex(ValidationError, "Supported methods: card, cash"):
            self.payment_service.process_payment(order_id=order.id, method="bitcoin", details={})
        updated_order = self.order_service.get_order(order.id)
        self.assertEqual(updated_order.status.value, "pending")


if __name__ == "__main__":
    unittest.main()
