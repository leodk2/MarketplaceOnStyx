import os
import random
from timeit import default_timer as timer
import uuid

from sanic import Blueprint, Sanic
from sanic import Sanic, json

from styx.client import AsyncStyxClient
from styx.client import AsyncStyxClient
from styx.client.styx_future import StyxResponse
from styx.common.local_state_backends import LocalStateBackend
from styx.common.stateflow_graph import StateflowGraph

# from functions.order import order_operator
# from functions.payment import payment_operator
# from functions.stock import stock_operator


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
    n_partitions: int = int(n_partitions)
    g = StateflowGraph(
        APP_NAME,
        operator_state_backend=LocalStateBackend.DICT,
        max_operator_parallelism=n_partitions
    )
    await styx_client.submit_dataflow(g)
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

@api.post("product")
async def create_product(request):
    raise NotImplementedError("This endpoint is not yet implemented.")

@api.patch("product")
async def update_product_price(request):
    raise NotImplementedError("This endpoint is not yet implemented.")

@api.put("product")
async def replace_product(request):
    raise NotImplementedError("This endpoint is not yet implemented.")

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
