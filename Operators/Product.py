from dataclasses import asdict
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

class ProductReplaceError(Exception):
    pass

@product_operator.register
async def create_product(ctx: StatefulFunction, product: dict) -> dict:
    state = ctx.get()
    if state is not None:
        raise ProductAlreadyExists(f"Error: Product with id {ctx.key} already exists")
    ctx.put(product)
    return product

@product_operator.register
async def replace_product(ctx: StatefulFunction, product: dict) -> dict:
    state = ctx.get()
    if state is None:
        raise ProductDoesNotExist(f"Error: Product with id {ctx.key} does not exist")

    existingProduct: Product = Product(**state)
    newProduct: Product = Product(**product)

    if existingProduct.SellerId != newProduct.SellerId:
        raise ProductReplaceError(f"Error: Cannot replace product with a different seller id")

    ctx.call_remote_async(
        function_name="on_product_update",
        operator_name="stock",
        key=f"{newProduct.SellerId}:{ctx.key}",
        params=(newProduct.Version,)
    )

    ctx.put(asdict(newProduct))

    return ctx.get()


@product_operator.register
async def update_product_price(ctx: StatefulFunction, new_price: float) -> dict:
    state = ctx.get()
    if state is None:
        raise ProductDoesNotExist(f"Error: Product with id {ctx.key} does not exist")

    ctx.call_remote_async(
        operator_name="product_cart_router",
        function_name="route_price_update",
        key=ctx.key,
        params=(new_price,)
    )

    product: Product = Product(**state)
    product.Price = new_price
    
    ctx.put(asdict(product))

    return ctx.get()


@product_operator.register
async def get_product(ctx: StatefulFunction) -> dict:
    state = ctx.get()
    if state is None:
        raise ProductDoesNotExist(f"Error: Product with id {ctx.key} does not exist")
    return state




@product_operator.register
async def get_all_state(ctx: StatefulFunction) -> dict:
    return ctx.data


@product_operator.register
async def set_all_state(ctx: StatefulFunction, state: dict) -> dict:
    if state:
        ctx.batch_insert(state)
    else:
        ctx.put(None)
    return state
