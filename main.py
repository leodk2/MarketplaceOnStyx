from sanic import Blueprint, Sanic

app = Sanic("marketplaceonstyx")
api = Blueprint("api", url_prefix="/api/v1")


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
