from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

from Entities.StockItem import StockItem

OPERATOR_NAME = "stock"
stock_operator = Operator(OPERATOR_NAME)


class StockItemDoesNotExist(Exception):
    pass  
class StockItemAlreadyExists(Exception):
    pass


@stock_operator.register
async def on_product_update(ctx: StatefulFunction, newVersion: str) -> StockItem:
    state = ctx.get()
    if state is None:
        raise StockItemDoesNotExist(f"Error: StockItem with id {ctx.key} does not exist")
    state['Version'] = newVersion
    ctx.put(state)
    return ctx.get()

@stock_operator.register
async def create_stock(ctx: StatefulFunction, stock_item: StockItem) -> StockItem:
    state = ctx.get()
    if state is not None:
        raise StockItemAlreadyExists(f"Error: StockItem with id {ctx.key} already exists")
    ctx.put(stock_item)
    return stock_item

@stock_operator.register
async def get_stock(ctx: StatefulFunction) -> StockItem:
    state = ctx.get()
    if state is None:
        raise StockItemDoesNotExist(f"Error: StockItem with id {ctx.key} does not exist")
    return state
