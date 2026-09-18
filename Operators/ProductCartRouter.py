
from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

import logging

logger = logging.Logger(__name__)

OPERATOR_NAME = "product_cart_router"
product_cart_router_operator = Operator(OPERATOR_NAME)

# the key to this operator is product_id

class ProductCartRoutingDoesNotExist(Exception):
    pass


@product_cart_router_operator.register
async def route_price_update(ctx: StatefulFunction, new_price: float):
    state = ctx.get()
    if state is None:
        raise ProductCartRoutingDoesNotExist(f"Error: No carts registered for product {ctx.key}")

    for cart_id in state["carts"]:
        ctx.call_remote_async(
            operator_name="cart", 
            key=cart_id, 
            function_name="update_cart_price",
            params=(new_price,)
        )

    return ctx.key


@product_cart_router_operator.register
async def register(ctx: StatefulFunction, cart_id: int):
    state = ctx.get()
    if state is None:
        ctx.put({"carts": [cart_id]})
    else:
        state["carts"].append(cart_id)
        ctx.put(state)
    return ctx.key


@product_cart_router_operator.register
async def unregister(ctx: StatefulFunction, cart_id: int):
    state = ctx.get()
    if state is None:
        raise ProductCartRoutingDoesNotExist(f"Error: No carts registered for product {ctx.key}")
    state["carts"].remove(cart_id)
    ctx.put(state)
    return ctx.key


@product_cart_router_operator.register
async def get_all_state(ctx: StatefulFunction) -> dict:
    return ctx.data


@product_cart_router_operator.register
async def set_all_state(ctx: StatefulFunction, state: dict) -> dict:
    if state:
        ctx.batch_insert(state)
    else:
        ctx.put(None)
    return state