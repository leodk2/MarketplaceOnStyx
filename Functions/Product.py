import logging

import msgspec

from Entities.Product import Product

from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

logger = logging.Logger(__name__)

OPERATOR_NAME = "product"
operator = Operator(OPERATOR_NAME)

class ProductDoesNotExist(Exception):
    pass

class ProductAlreadyExists(Exception):
    pass

#TODO: should this have any remote calls?
@operator.register
async def create_product(ctx: StatefulFunction, product: Product) -> Product:
    state = ctx.get()
    if state is not None:
        raise ProductAlreadyExists(f"Product with id {ctx.key} already exists")
    ctx.put(product)
    return product

@operator.register
async def replace_product(ctx: StatefulFunction, product) -> Product:
    state = ctx.get()
    if state is None:
        raise ProductDoesNotExist(f"Product with id {ctx.key} does not exist")

    ctx.call_remote_async(
        function_name="on_product_update",
        operator_name="stock",
        key=ctx.key,
        params=(product['Version'],)
    )

    ctx.put(product)

    return ctx.get()

@operator.register
async def update_product_price(ctx: StatefulFunction, new_price: float) -> Product:
    state = ctx.get()
    if state is None:
        raise ProductDoesNotExist(f"Product with id {ctx.key} does not exist")
    
    ctx.call_remote_async(
        function_name="on_product_update_price",
        operator_name="cart",
        key=ctx.key,
        params=(new_price,)
    )

    state['Price'] = new_price
    ctx.put(state)

    return ctx.get()

@operator.register
async def get_product(ctx: StatefulFunction) -> Product:
    state = ctx.get()
    if state is None:
        raise ProductDoesNotExist(f"Product with id {ctx.key} does not exist")
    return state