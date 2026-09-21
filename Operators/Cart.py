from dataclasses import asdict
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


class CartAlreadyExists(Exception):
    pass


class CustomerIdMismatch(Exception):
    pass


class ItemAlreadyInCart(Exception):
    pass


@cart_operator.register
async def create_cart(ctx: StatefulFunction):
    if ctx.get() is not None:
        raise CartAlreadyExists(
            f"Error: Cart for customer with id {ctx.key} already exists"
        )

    cart: Cart = Cart(
        customerId=ctx.key,
        status=CartStatus.OPEN,
        items=[],
        instanceId=0,  # TODO: don't know what to put here
        divergencies=[],  # TODO: don't know what to put here
    )

    ctx.put(asdict(cart))
    return ctx.key


@cart_operator.register
async def add_item(ctx: StatefulFunction, item: dict):

    cartItem: CartItem = CartItem(**item)
    if cartItem.quantity <= 0:
        raise ItemsNegative(
            f"Error: Item {cartItem.productId} shows no positive quantity"
        )

    state = ctx.get()
    if state is None:
        raise CartDoesNotExist(f"Error: Cart with id {ctx.key} does not exist")

    cart_data: Cart = Cart(**state)

    if cart_data.status is CartStatus.CHECKOUT_SENT:
        raise CheckoutAlreadySent(
            f"Error: Cart with id {ctx.key} for customer {cart_data.customerId} has already checked out "
        )

    ctx.call_remote_async(
        operator_name="product_cart_router",
        key=cartItem.productId,
        function_name="register",
        params=(ctx.key,),
    )

    if cartItem in cart_data.items:
        raise ItemAlreadyInCart(
            f"Error: Item {cartItem.productId} is already in cart {ctx.key}"
        )

    cart_data.items.append(cartItem)

    ctx.put(asdict(cart_data))

    return ctx.key


@cart_operator.register
async def seal(ctx: StatefulFunction):
    state = ctx.get()
    if state is None:
        raise CartDoesNotExist(f"Error: Cart with id {ctx.key} does not exist")
    cart_data: Cart = Cart(**state)
    doSeal(ctx, cart_data)
    ctx.put(asdict(cart_data))
    return cart_data.customerId


def doSeal(ctx: StatefulFunction, cart: Cart | None):
    if cart is None:
        raise CartDoesNotExist()
    cart.status = CartStatus.OPEN
    for item in cart.items:
        ctx.call_remote_async(
            operator_name="product_cart_router",
            key=item.productId,
            function_name="unregister",
            params=(ctx.key,),
        )
    cart.items = []


@cart_operator.register
async def checkout(
    ctx: StatefulFunction, customer_id: int, customerCheckout_dict: dict
):
    customerCheckout = CustomerCheckout(**customerCheckout_dict)
    if customer_id is not customerCheckout.CustomerId:
        raise CustomerIdMismatch()
    state = ctx.get()
    if state is None:
        raise CartDoesNotExist()
    cart: Cart = Cart(**state)
    if cart.status is CartStatus.CHECKOUT_SENT:
        raise CheckoutAlreadySent()

    checkoutRequest = CheckoutRequest(
        customerCheckout=customerCheckout,
        items=cart.items,
        timestamp=datetime.now(),
        instanceId=customerCheckout.instanceId,
    )
    ctx.call_remote_async(
        "order", "checkout_request", ctx.key, (asdict(checkoutRequest),)
    )

    doSeal(ctx, cart)
    ctx.put(asdict(cart))

    return customer_id


@cart_operator.register
async def get(ctx: StatefulFunction):
    data = ctx.get()
    if data is None:
        raise CartDoesNotExist()
    return data


@cart_operator.register
async def update_cart_price(ctx: StatefulFunction, new_price: float):
    state = ctx.get()
    if state is None:
        raise CartDoesNotExist(
            f"Error: Cart for customer with id {ctx.key} does not exist"
        )

    cart: Cart = Cart(**state)

    for item in cart.items:
        item.unitPrice = new_price

    ctx.put(asdict(cart))

    return ctx.key


@cart_operator.register
async def get_all_state(ctx: StatefulFunction) -> dict:
    return ctx.data


@cart_operator.register
async def set_all_state(ctx: StatefulFunction, state: dict) -> dict:
    if state:
        ctx.batch_insert(state)
    else:
        ctx.put(None)
    return state
