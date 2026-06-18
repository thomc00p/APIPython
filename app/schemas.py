from pydantic import BaseModel, Field


class ProductResponse(BaseModel):
    id: str
    name: str
    price: float


class OrderItemRequest(BaseModel):
    product_id: str = Field(min_length=1)
    quantity: int = Field(gt=0)


class CreateOrderRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    items: list[OrderItemRequest] = Field(min_length=1)


class OrderItemResponse(BaseModel):
    product_id: str
    quantity: int
    unit_price: float
    subtotal: float


class OrderResponse(BaseModel):
    id: str
    customer_id: str
    status: str
    total: float
    items: list[OrderItemResponse]


class UpdateOrderStatusRequest(BaseModel):
    status: str = Field(pattern="^(ready|delivered)$")


class PaymentRequest(BaseModel):
    method: str = Field(min_length=1)
    details: dict[str, str] = Field(default_factory=dict)


class PaymentResponse(BaseModel):
    id: str
    order_id: str
    amount: float
    method: str
    status: str
    message: str
