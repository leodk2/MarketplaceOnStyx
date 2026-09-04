import os

from sanic import Blueprint, Sanic
from sanic import Sanic, json
from sanic_ext import openapi

from styx.client import AsyncStyxClient
from styx.client.styx_future import StyxResponse
from styx.common.local_state_backends import LocalStateBackend
from styx.common.stateflow_graph import StateflowGraph

import Functions.Product as product
import Entities.Product as product_entity
# from functions.order import order_operator
# from functions.payment import payment_operator
# from functions.stock import stock_operator

from Entities.Product import Product

APP_NAME = "marketplaceonstyx"

app = Sanic(APP_NAME)

app.config.SWAGGER_UI_CONFIGURATION = {
    "docExpansion": "list",  # or "none"
    "apisSorter": "alpha",
    "operationsSorter": "alpha",
}

api = Blueprint("api", url_prefix="/api/v1")


STYX_HOST: str = os.environ["STYX_HOST"]
STYX_PORT: int = int(os.environ["STYX_PORT"])
KAFKA_URL: str = os.environ["KAFKA_URL"]

styx_client = AsyncStyxClient(STYX_HOST, STYX_PORT, KAFKA_URL)

app.add_task(styx_client.open(consume=True))


@api.post("/submit/<n_partitions>")
async def submit_dataflow_graph(_, n_partitions: int):
    g = StateflowGraph(
        APP_NAME,
        operator_state_backend=LocalStateBackend.DICT,
        max_operator_parallelism=n_partitions
    )

    product.operator.set_n_partitions(n_partitions)

    g.add_operators(
        product.operator
    )

    await styx_client.submit_dataflow(g, external_modules=(product_entity,))
    return json({"Graph submitted": True})



@api.put("cart/<customer_id>/add")
async def add_to_cart(request, customer_id):
    
    raise NotImplementedError("This endpoint is not yet implemented.")

@api.post("cart/<customer_id>/checkout")
async def checkout_cart(request, customer_id):
    raise NotImplementedError("This endpoint is not yet implemented.")

@api.post("cart/<customer_id>/seal")
async def seal_cart(request, customer_id):
    raise NotImplementedError("This endpoint is not yet implemented.")

@api.post("customer")
async def create_customer(request):
    raise NotImplementedError("This endpoint is not yet implemented.")

#TODO: how to return other than 200 


@api.post("product")
@openapi.body(Product, validate=True)
async def create_product(_, body: Product):
    future = await styx_client.send_event(
        operator=product.operator,
        function="create_product",
        key=body.ProductId,
        params=(body,)
    )

    result: StyxResponse | None = await future.get()
    if result is None:
        return json({"Error": "Failed to create product"}, status=500)
    
    return json(result.response)

@api.patch("product")
@openapi.body(Product, validate=True)
async def update_product_price(_, body: Product):
    future = await styx_client.send_event(
        operator=product.operator,
        function="update_product_price",
        key=body.ProductId,
        params=(body.Price,)
    )

    result: StyxResponse | None = await future.get()
    if result is None:
        return json({"Error": "Failed to update product price"}, status=500)
    
    return json(result.response)

@api.put("product")
@openapi.body(Product, validate=True)
async def replace_product(_, body: Product):
    future = await styx_client.send_event(
        operator=product.operator,
        function="replace_product",
        key=body.ProductId,
        params=(body,)
)
    
    result: StyxResponse | None = await future.get()
    if result is None:
        return json({"Error": "Failed to update product price"}, status=500)
    
    return json(result.response)

@api.get("product/<product_id>")
async def get_product(_, product_id: int):
    future = await styx_client.send_event(
        operator=product.operator,
        key=product_id,
        function="get_product"
    )
    result: StyxResponse | None = await future.get()
    if result is None:
        return json({"Error": "Failed to get product"}, status=500)

    return json(result.response)

@api.post("seller")
async def create_seller(request):
    raise NotImplementedError("This endpoint is not yet implemented.")


@api.get("seller/dashboard/<seller_id>")
async def get_seller_dashboard(request, seller_id):
    raise NotImplementedError("This endpoint is not yet implemented.")

@api.patch("shipment/<tid>")
async def deliver_shipment(request, tid):
    raise NotImplementedError("This endpoint is not yet implemented.")

@api.post("stock")
async def create_stock(request):
    raise NotImplementedError("This endpoint is not yet implemented.")


app.blueprint(api)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
