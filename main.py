from __future__ import annotations

import os
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from enum import Enum
from importlib import import_module
from pkgutil import iter_modules
from typing import cast

from sanic import Blueprint, Request, Sanic, json, text
from sanic_ext import openapi
from styx.client import AsyncStyxClient
from styx.client.styx_future import StyxResponse
from styx.common.local_state_backends import LocalStateBackend
from styx.common.stateflow_graph import StateflowGraph

import Entities
import Entities.CartItem as cart_item_entity
import Entities.Customer as customer_entity
import Entities.Product as product_entity
import Entities.Seller as seller_entity
import Entities.StockItem as stock_item_entity
import Requests
import States
from Operators.Cart import cart_operator
from Operators.Customer import customer_operator
from Operators.Order import order_operator
from Operators.Payment import payment_operator
from Operators.Product import product_operator
from Operators.ProductCartRouter import product_cart_router_operator
from Operators.Seller import seller_operator
from Operators.Stock import stock_operator
from Operators.Shipment import shipment_operator

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
APPLICATION_MODULES = tuple(
    import_module(module.name)
    for package in (Entities, Requests, States)
    for module in iter_modules(package.__path__, f"{package.__name__}.")
)


app.add_task(styx_client.open(consume=True))


def is_error(obj):
    return isinstance(obj, str) and obj.casefold().startswith("error:")


def jsonable(value):
    if is_dataclass(value):
        return jsonable(asdict(value))
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return jsonable(value.value)
    if isinstance(value, dict):
        return {key: jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(item) for item in value]
    return value


def create_response(result: StyxResponse | None, failure_message: str):
    if result is None:
        return json({"Error": failure_message}, status=500)

    if is_error(result.response):
        return json(result.response, status=500)

    return json(jsonable(result.response))


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
    shipment_operator.set_n_partitions(n_partitions)

    g.add_operators(
        product_operator,
        cart_operator,
        stock_operator,
        product_cart_router_operator,
        payment_operator,
        order_operator,
        seller_operator,
        customer_operator,
        shipment_operator,
    )

    await styx_client.submit_dataflow(
        g,
        external_modules=APPLICATION_MODULES,
    )
    return json({"Graph submitted": True})


@api.put("cart/<customer_id>/add")
@openapi.body(cart_item_entity.CartItem, validate=True)
async def add_to_cart(_, customer_id, body: cart_item_entity.CartItem):
    req = await styx_client.send_event(cart_operator, customer_id, "add_item", (body,))
    res = cast(StyxResponse, await req.get())
    return create_response(res, "Failed to add item to cart " + customer_id)


@api.post("cart/<customer_id>/checkout")
async def checkout_cart(request: Request, customer_id):
    checkout_request = request.json.get("checkout")

    req = await styx_client.send_event(
        cart_operator, customer_id, "checkout", (customer_id, checkout_request)
    )
    res = cast(StyxResponse, await req.get())
    return create_response(res, "Failed to checkout customer " + customer_id)


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
@openapi.body(customer_entity.Customer, validate=True)
async def create_customer(_, body: customer_entity.Customer):
    future = await styx_client.send_event(
        operator=customer_operator,
        key=body.Id,
        function="register_customer",
        params=(body,),
    )
    result: StyxResponse | None = await future.get()
    return create_response(
        result,
        "Failed to create customer",
    )


@api.post("product")
@openapi.body(product_entity.Product, validate=True)
async def create_product(_, body: product_entity.Product):
    future = await styx_client.send_event(
        operator=product_operator,
        function="create_product",
        key=body.ProductId,
        params=(body,),
    )

    result: StyxResponse | None = await future.get()
    return create_response(result, "Failed to create product")


@api.patch("product")
@openapi.body(product_entity.Product, validate=True)
async def update_product_price(_, body: product_entity.Product):
    future = await styx_client.send_event(
        operator=product_operator,
        function="update_product_price",
        key=body.ProductId,
        params=(body.Price,),
    )

    result: StyxResponse | None = await future.get()
    if result is None:
        return json({"Error": "Failed to update product price"}, status=500)

    if is_error(result.response):
        return json(result.response, status=500)

    return json(result.response)


@api.put("product")
@openapi.body(product_entity.Product, validate=True)
async def replace_product(_, body: product_entity.Product):
    future = await styx_client.send_event(
        operator=product_operator,
        function="replace_product",
        key=body.ProductId,
        params=(body,),
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
        operator=product_operator, key=product_id, function="get_product"
    )
    result: StyxResponse | None = await future.get()
    if result is None:
        return json({"Error": "Failed to get product"}, status=500)

    if is_error(result.response):
        return json(result.response, status=500)

    return json(result.response)


@api.post("seller")
@openapi.body(seller_entity.Seller, validate=True)
async def create_seller(_, body: seller_entity.Seller):
    future = await styx_client.send_event(
        operator=seller_operator,
        key=body.Id,
        function="register_seller",
        params=(body,),
    )
    result: StyxResponse | None = await future.get()
    return create_response(result, "Failed to create seller")


@api.get("seller/dashboard/<seller_id:int>")
async def get_seller_dashboard(request, seller_id: int):
    future = await styx_client.send_event(
        seller_operator,
        seller_id,
        "get_dashboard",
    )
    result: StyxResponse | None = await future.get()

    return create_response(result, "Could not get dashboard")


@api.patch("shipment/<tid>")
async def deliver_shipment(_, tid):
    future = await styx_client.send_event(
        shipment_operator,
        tid,
        "deliver_shipment",
    )
    result: StyxResponse | None = await future.get()

    return create_response(result, "Could not deliver shipment")


@api.post("stock")
@openapi.body(stock_item_entity.StockItem)
async def create_stock(request: Request):
    data = dict(request.json)
    for field in ("created_at", "updated_at"):
        if isinstance(data.get(field), str):
            data[field] = datetime.fromisoformat(data[field])
    body = stock_item_entity.StockItem(**data)

    future = await styx_client.send_event(
        operator=stock_operator,
        key=f"{body.seller_id}:{body.product_id}",
        function="create_stock",
        params=(body,),
    )
    result: StyxResponse | None = await future.get()
    return create_response(result, "Failed to create stock")


@api.get("stock/<seller_id:int>/<product_id:int>")
async def get_stock(_, seller_id: int, product_id: int):
    future = await styx_client.send_event(
        operator=stock_operator, key=f"{seller_id}:{product_id}", function="get_stock"
    )
    result: StyxResponse | None = await future.get()
    if result is None:
        return json({"Error": "Failed to get stock"}, status=500)

    if is_error(result.response):
        return json(result.response, status=500)

    return json(result.response)


# this only works with one partition, but it's useful for debugging and testing
@api.get("allState")
async def get_all_state(_):
    future = await styx_client.send_event(
        operator=cart_operator, key="all", function="get_all_state"
    )
    cart_result: StyxResponse | None = await future.get()
    if cart_result is None:
        return json({"Error": "Failed to get all state"}, status=500)

    future = await styx_client.send_event(
        operator=customer_operator, key="all", function="get_all_state"
    )
    customer_result: StyxResponse | None = await future.get()
    if customer_result is None:
        return json({"Error": "Failed to get all state"}, status=500)

    future = await styx_client.send_event(
        operator=order_operator, key="all", function="get_all_state"
    )
    order_result: StyxResponse | None = await future.get()
    if order_result is None:
        return json({"Error": "Failed to get all state"}, status=500)

    future = await styx_client.send_event(
        operator=payment_operator, key="all", function="get_all_state"
    )
    payment_result: StyxResponse | None = await future.get()
    if payment_result is None:
        return json({"Error": "Failed to get all state"}, status=500)

    future = await styx_client.send_event(
        operator=product_operator, key="all", function="get_all_state"
    )
    product_result: StyxResponse | None = await future.get()
    if product_result is None:
        return json({"Error": "Failed to get all state"}, status=500)

    future = await styx_client.send_event(
        operator=product_cart_router_operator, key="all", function="get_all_state"
    )
    product_cart_router_result: StyxResponse | None = await future.get()
    if product_cart_router_result is None:
        return json({"Error": "Failed to get all state"}, status=500)

    future = await styx_client.send_event(
        operator=seller_operator, key="all", function="get_all_state"
    )
    seller_result: StyxResponse | None = await future.get()
    if seller_result is None:
        return json({"Error": "Failed to get all state"}, status=500)

    future = await styx_client.send_event(
        operator=shipment_operator, key="all", function="get_all_state"
    )
    shipment_result: StyxResponse | None = await future.get()
    if shipment_result is None:
        return json({"Error": "Failed to get all state"}, status=500)
    
    future = await styx_client.send_event(
        operator=stock_operator, key="all", function="get_all_state"
    )
    stock_result: StyxResponse | None = await future.get()
    if stock_result is None:
        return json({"Error": "Failed to get all state"}, status=500)

    result: dict = {
        "cart": cart_result.response,
        "customer": customer_result.response,
        "order": order_result.response,
        "payment": payment_result.response,
        "product": product_result.response,
        "product_cart_router": product_cart_router_result.response,
        "seller": seller_result.response,
        "shipment": shipment_result.response,
        "stock": stock_result.response
    }

    return json(result)


# this only works with one partition, but it's useful for debugging and testing
@api.put("allState")
@openapi.body(
    {
        "application/json": openapi.Object(
            properties={
                "cart": openapi.Object(),
                "customer": openapi.Object(),
                "order": openapi.Object(),
                "payment": openapi.Object(),
                "product": openapi.Object(),
                "product_cart_router": openapi.Object(),
                "seller": openapi.Object(),
                "shipment": openapi.Object(),
                "stock": openapi.Object(),
            }
        )
    }
)
async def put_all_state(request: Request):
    payload: dict = request.json

    for operator_name, operator in (
        ("cart", cart_operator),
        ("customer", customer_operator),
        ("order", order_operator),
        ("payment", payment_operator),
        ("product", product_operator),
        ("product_cart_router", product_cart_router_operator),
        ("seller", seller_operator),
        ("shipment", shipment_operator),
        ("stock", stock_operator),
    ):
        state = payload.get(operator_name)
        if not state:
            continue

        future = await styx_client.send_event(
            operator=operator, key="all", function="set_all_state", params=(state,)
        )
        result: StyxResponse | None = await future.get()
        if result is None:
            return json({"Error": "Failed to set all state"}, status=500)

        if is_error(result.response):
            return json(result.response, status=500)

    return json({"State set": True})


app.blueprint(api)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
