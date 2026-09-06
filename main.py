import os
from typing import cast

from sanic import Blueprint, Request, Sanic, json, text
from styx.client import AsyncStyxClient
from styx.client.styx_future import StyxResponse
from styx.common.local_state_backends import LocalStateBackend
from styx.common.stateflow_graph import StateflowGraph

from Entities.Customer import Customer
from Functions.Cart import cart_operator
from Functions.Customer import customer_operator
from Functions.Order import order_operator
from Functions.Payment import payment_operator
from Functions.Seller import seller_operator
from Functions.Stock import stock_operator
# from Functions.Product import product_operator

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
        max_operator_parallelism=n_partitions,
    )
    await styx_client.submit_dataflow(g)
    return json({"Graph submitted": True})


@api.put("cart/<customer_id>/add")
async def add_to_cart(request: Request, customer_id):
    ci = request.json.get("item")  # name subject to change
    req = await styx_client.send_event(cart_operator, customer_id, "add_item", (ci,))
    res = cast(StyxResponse, await req.get())
    return text(
        f"{res.request_id}, {res.in_timestamp}, {res.out_timestamp}, {res.styx_latency_ms}, {res.response}"
    )


@api.post("cart/<customer_id>/checkout")
async def checkout_cart(request: Request, customer_id):
    checkout_request = request.json.get("checkout")

    req = await styx_client.send_event(
        cart_operator, customer_id, "checkout", (customer_id, checkout_request)
    )
    res = cast(StyxResponse, await req.get())
    return text(
        f"{res.request_id}, {res.in_timestamp}, {res.out_timestamp}, {res.styx_latency_ms}, {res.response}"
    )


@api.post("cart/<customer_id>/seal")
async def seal_cart(request: Request, customer_id):
    req = await styx_client.send_event(
        cart_operator, customer_id, "seal", (customer_id,)
    )
    res = cast(StyxResponse, await req.get())
    return text(
        f"{res.request_id}, {res.in_timestamp}, {res.out_timestamp}, {res.styx_latency_ms}, {res.response}"
    )


@api.post("customer")
async def create_customer(request: Request):
    customer = Customer(**(request.json.get("customer")))
    req = await styx_client.send_event(
        customer_operator, customer.Id, "register_customer", (customer,)
    )
    res = cast(StyxResponse, await req.get())
    return text(
        f"{res.request_id}, {res.in_timestamp}, {res.out_timestamp}, {res.styx_latency_ms}, {res.response}"
    )


@api.post("product")
async def create_product(request: Request):
    raise NotImplementedError("This endpoint is not yet implemented.")
    product = Customer(**(request.json.get("produc")))
    req = await styx_client.send_event(
        product_operator, product.Id, "register_product", (product,)
    )
    res = cast(StyxResponse, await req.get())
    return text(
        f"{res.request_id}, {res.in_timestamp}, {res.out_timestamp}, {res.styx_latency_ms}, {res.response}"
    )


@api.patch("product")
async def update_product_price(request):
    raise NotImplementedError("This endpoint is not yet implemented.")


@api.put("product")
async def replace_product(request):
    raise NotImplementedError("This endpoint is not yet implemented.")


@api.post("seller")
async def create_seller(request: Request):
    seller = request.json.get("seller")
    req = await styx_client.send_event(
        seller_operator, seller.Id, "register_seller", (seller,)
    )
    res = cast(StyxResponse, await req.get())
    return text(
        f"{res.request_id}, {res.in_timestamp}, {res.out_timestamp}, {res.styx_latency_ms}, {res.response}"
    )


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
