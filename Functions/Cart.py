import logging
from datetime import datetime

from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

from Entities.Cart import Cart
from Entities.CartItem import CartItem
from Entities.CartStatus import CartStatus
from Requests.CustomerCheckout import CheckoutRequest, CustomerCheckout

logger = logging.getLogger(__name__)
cart_operator = Operator("cart")


class CheckoutAlreadySent(Exception):
    pass


class ItemsNegative(Exception):
    pass


class CartDoesNotExist(Exception):
    pass


class CustomerIdMismatch(Exception):
    pass


# For now we assume that a customer only can have one cart
@cart_operator.register
async def add_item(ctx: StatefulFunction, item: dict):

    cartItem: CartItem = CartItem(**item)
    if cartItem.quantity <= 0:
       raise ItemsNegative(f"Error: Item {cartItem.ProductId} shows no positive quantity")

    cart_data: Cart = ctx.get()

    if cart_data.status is CartStatus.CHECKOUT_SENT:
        raise CheckoutAlreadySent(
            f"Error: Cart with id {ctx.key} for customer {cart_data.CustomerId} has already checked out "
        )

    cart_data.items.append(cartItem)

    return ctx.key


@cart_operator.register
async def seal(ctx: StatefulFunction):
    cart_data: Cart = ctx.get()
    if cart_data is None:
        raise CartDoesNotExist(f"Error: Cart with id {ctx.key} does not exist")
    doSeal(cart_data)
    return cart_data.customerId


def doSeal(cart: Cart | None):
    if cart is None:
        raise CartDoesNotExist()

    cart.status = CartStatus.OPEN


@cart_operator.register
async def checkout(
    ctx: StatefulFunction, customer_id: int, customerCheckout_dict: dict
):
    customerCheckout = CustomerCheckout(**customerCheckout_dict)
    if customer_id is not customerCheckout.customerId:
        raise CustomerIdMismatch()
    data = ctx.get()
    if data is None:
        raise CartDoesNotExist()
    cart: Cart = ctx.get()
    if cart.status is CartStatus.CHECKOUT_SENT:
        raise CheckoutAlreadySent()

    checkoutRequest = CheckoutRequest(
        customerCheckout=customerCheckout,
        items=cart.items,
        timestamp=datetime.now(),
        instanceId=customerCheckout.instanceId,
    )
    ctx.call_remote_async("order", "checkout_request", ctx.key, (checkoutRequest,))

    doSeal(cart)
    return customer_id


@cart_operator.register
async def get(ctx: StatefulFunction):
    data = ctx.get()
    if data is None:
        raise CartDoesNotExist()
    return data
