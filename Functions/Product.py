import logging

from Entities.Product import Product

from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

logger = logging.Logger(__name__)

OPERATOR_NAME = "product"
product_operator = Operator(OPERATOR_NAME)

class ProductDoesNotExist(Exception):
    pass

class ProductAlreadyExists(Exception):
    pass


@product_operator.register
async def create_product(ctx: StatefulFunction, product: Product) -> Product:
    state = ctx.get()
    if state is not None:
        raise ProductAlreadyExists(f"Error: Product with id {ctx.key} already exists")
    ctx.put(product)
    return product

@product_operator.register
async def replace_product(ctx: StatefulFunction, product) -> Product:
    state = ctx.get()
    if state is None:
        raise ProductDoesNotExist(f"Error: Product with id {ctx.key} does not exist")

    ctx.call_remote_async(
        function_name="on_product_update",
        operator_name="stock",
        key=ctx.key,
        params=(product['Version'],)
    )

    ctx.put(product)

    return ctx.get()

@product_operator.register
async def update_product_price(ctx: StatefulFunction, new_price: float) -> Product:
    state = ctx.get()
    if state is None:
        raise ProductDoesNotExist(f"Error: Product with id {ctx.key} does not exist")

    ctx.call_remote_async(
        operator_name="product_cart_router",
        function_name="route_price_update",
        key=ctx.key,
        params=(new_price,)
    )

    state['Price'] = new_price
    ctx.put(state)

    return ctx.get()

@product_operator.register
async def get_product(ctx: StatefulFunction) -> Product:
    state = ctx.get()
    if state is None:
        raise ProductDoesNotExist(f"Error: Product with id {ctx.key} does not exist")
    return state