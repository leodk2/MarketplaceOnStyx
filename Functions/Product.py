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

@operator.register
async def create_product(ctx: StatefulFunction, product: Product) -> Product:
    state = ctx.get()
    if state is not None:
        raise ProductAlreadyExists(f"Product with id {ctx.key} already exists")
    product = msgspec.convert(product, type=Product)
    ctx.put(product)
    return product

@operator.register
async def replace_product(ctx: StatefulFunction, product: Product) -> Product:
    state = ctx.get()
    if state is None:
        raise ProductDoesNotExist(f"Product with id {ctx.key} does not exist")
    product = msgspec.convert(product, type=Product)
    ctx.put(product)
    return ctx.get()

@operator.register
async def update_product_price(ctx: StatefulFunction, product: Product) -> Product:
    state = ctx.get()
    if state is None:
        raise ProductDoesNotExist(f"Product with {ctx.key} does not exist")
    product = msgspec.convert(product, type=Product)
    state.Price = product.Price
    ctx.put(state)
    return state

@operator.register
async def get_product(ctx: StatefulFunction) -> Product:
    state = ctx.get()
    if state is None:
        raise ProductDoesNotExist(f"Product with {ctx.key} does not exist")
    return state