
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
async def register(ctx: StatefulFunction, cart_id):
    state = ctx.get()
    if state is None:
        ctx.put({"carts": [cart_id]})
    else:
        state["carts"].append(cart_id)
        ctx.put(state)
    return ctx.key




    