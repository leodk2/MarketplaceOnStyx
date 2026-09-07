from __future__ import annotations
import os
from typing import cast

from sanic import Blueprint, Request, Sanic, json, text
from sanic import Blueprint, Sanic
from sanic import Sanic, json
from sanic_ext import openapi

from styx.client import AsyncStyxClient
from styx.client.styx_future import StyxResponse
from styx.common.local_state_backends import LocalStateBackend
from styx.common.stateflow_graph import StateflowGraph

from Operators.Customer import customer_operator
from Operators.Order import order_operator
from Operators.Payment import payment_operator
from Operators.Seller import seller_operator
from Operators.Product import product_operator 
from Operators.Cart import cart_operator 
from Operators.Stock import stock_operator 
from Operators.ProductCartRouter import product_cart_router_operator

import Entities.Product as product_entity
import Entities.Cart as cart_entity
import Entities.CartItem as cart_item_entity
import Entities.CartStatus as cart_status_entity
import Entities.StockItem as stock_item_entity
from Entities.Product import Product
from Entities.StockItem import StockItem
from Entities.Customer import Customer

import Requests.CustomerCheckout as customer_checkout_entity

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


@api.post("/submit/<n_partitions:int>")
async def submit_dataflow_graph(_, n_partitions: int):
    n_partitions = int(n_partitions)
    
    g = StateflowGraph(
        APP_NAME,
        operator_state_backend=LocalStateBackend.DICT,
        max_operator_parallelism=n_partitions,
    )

    product_operator.set_n_partitions(n_partitions)
    cart_operator.set_n_partitions(n_partitions)
    stock_operator.set_n_partitions(n_partitions)
    product_cart_router_operator.set_n_partitions(n_partitions)
    payment_operator.set_n_partitions(n_partitions)
    order_operator.set_n_partitions(n_partitions)
    seller_operator.set_n_partitions(n_partitions)
    customer_operator.set_n_partitions(n_partitions)

    g.add_operators(
        product_operator,
        cart_operator,
        stock_operator,
        product_cart_router_operator,
        payment_operator,
        order_operator,
        seller_operator,
        customer_operator,
    )

    await styx_client.submit_dataflow(
        g,
        external_modules=(
            product_entity,
            cart_entity,
            cart_item_entity,
            cart_status_entity,
            customer_checkout_entity,
            stock_item_entity,
        ),
    )
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
@openapi.body(Product, validate=True)
async def create_product(_, body: Product):
    future = await styx_client.send_event(
        operator=product_operator,
        function="create_product",
        key=body.ProductId,
        params=(body,)
    )

    result: StyxResponse | None = await future.get()
    if result is None:
        return json({"Error": "Failed to create product"}, status=500)

    if is_error(result.response):
        return json(result.response, status=500)
    
    return json(result.response)

@api.patch("product")
@openapi.body(Product, validate=True)
async def update_product_price(_, body: Product):
    future = await styx_client.send_event(
        operator=product_operator,
        function="update_product_price",
        key=body.ProductId,
        params=(body.Price,)
    )

    result: StyxResponse | None = await future.get()
    if result is None:
        return json({"Error": "Failed to update product price"}, status=500)

    if is_error(result.response):
        return json(result.response, status=500)

    return json(result.response)


@api.put("product")
@openapi.body(Product, validate=True)
async def replace_product(_, body: Product):
    future = await styx_client.send_event(
        operator=product_operator,
        function="replace_product",
        key=body.ProductId,
        params=(body,)
    )
    
    result: StyxResponse | None = await future.get()
    if result is None:
        return json({"Error": "Failed to update product"}, status=500)

    if is_error(result.response):
        return json(result.response, status=500)
    
    return json(result.response)

@api.get("product/<product_id:int>")
async def get_product(_, product_id: int):
    future = await styx_client.send_event(
        operator=product_operator,
        key=product_id,
        function="get_product"
    )
    result: StyxResponse | None = await future.get()
    if result is None:
        return json({"Error": "Failed to get product"}, status=500)

    if is_error(result.response):
        return json(result.response, status=500)

    return json(result.response)


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
@openapi.body(StockItem, validate=True)
async def create_stock(_, body: StockItem):
    future = await styx_client.send_event(
        operator=stock_operator,
        key=body.ProductId,
        function="create_stock",
        params=(body,)
    )
    result: StyxResponse | None = await future.get()
    if result is None:
        return json({"Error": "Failed to create stock"}, status=500)

    if is_error(result.response):
        return json(result.response, status=500)

    return json(result.response)

@api.get("stock/<product_id:int>")
async def get_stock(_, product_id: int):
    future = await styx_client.send_event(
        operator=stock_operator,
        key=product_id,
        function="get_stock"
    )
    result: StyxResponse | None = await future.get()
    if result is None:
        return json({"Error": "Failed to get stock"}, status=500)

    if is_error(result.response):
        return json(result.response, status=500)
    
    return json(result.response)


app.blueprint(api)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)





def is_error(obj):
    return isinstance(obj, str) and obj.startswith("Error: ")



