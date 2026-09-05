from confluent_kafka import TIMESTAMP_CREATE_TIME
from datetime import datetime
from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

from Entities.Cart import Cart
from Entities.CartItem import CartItem
from Entities.CartStatus import CartStatus
from Requests.CustomerCheckout import CustomerCheckout, CheckoutRequest
import logging

logger = logging.Logger(__name__)

OPERATOR_NAME = "cart"
operator = Operator(OPERATOR_NAME)


class CheckoutAlreadySent(Exception):
    pass


class ItemsNegative(Exception):
    pass


class CartDoesNotExist(Exception):
    pass


class CustomerIdMismatch(Exception):
    pass


# For now we assume that a customer only can have one cart
@operator.register
async def add(ctx: StatefulFunction, cartItem: CartItem):
    if cartItem.Quantity <= 0:
        raise ItemsNegative(f"Item {cartItem.ProductId} shows no positive quantity")

    cart_data: Cart = ctx.get()

    if cart_data.Status is CartStatus.CHECKOUT_SENT:
        raise CheckoutAlreadySent(
            f"Cart with id {ctx.key} for customer {cart_data.CustomerId} has already checked out "
        )

    cart_data.Items.append(CartItem.model_validate(dict(cartItem)))

    return ctx.key


@operator.register
async def seal(ctx: StatefulFunction):

    cart_data: Cart = ctx.get()
    if cart_data is None:
        raise CartDoesNotExist()

    cart_data.Status = CartStatus.OPEN


@operator.register
async def checkout(
    ctx: StatefulFunction, customer_id: int, customerCheckout: CustomerCheckout
):
    if customer_id is not customerCheckout.CustomerId:
        raise CustomerIdMismatch()
    cart: Cart = ctx.get()
    if cart is None:
        raise CartDoesNotExist()
    elif cart.Status is CartStatus.CHECKOUT_SENT:
        raise CheckoutAlreadySent()

    checkoutRequest = CheckoutRequest(
        customerCheckout=customerCheckout,
        items=cart.Items,
        timestamp=datetime.now(),
        instanceId=customerCheckout.InstanceId,
    )
    ctx.call_remote_async("order", "CheckouRequest", ctx.key, (checkoutRequest,))

    ctx.call_remote_async("cart", "seal", ctx.key)


@operator.register
async def get(ctx: StatefulFunction):
    return ctx.get()



@operator.register
async def on_product_update_price(ctx: StatefulFunction, new_price: float):
    # raise NotImplementedError("This function is not yet implemented."
    # TODO: what should happen on product price update? 
    return "Dummy return"