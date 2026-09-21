from Entities.TransactionMark import TransactionMark
import logging
from dataclasses import asdict

from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

from Entities.Customer import Customer
from Entities.CustomerNotificationType import CustomerNotificationType

logger = logging.getLogger(__name__)
customer_operator = Operator("customer")


class CustomerDoesNotExist(Exception):
    pass


class CustomerAlreadyExists(Exception):
    pass


@customer_operator.register
async def register_customer(ctx: StatefulFunction, customer: dict):
    if ctx.get() is not None:
        raise CustomerAlreadyExists("error: customer already exists")

    newCustomer: Customer = Customer(**customer)

    ctx.call_remote_async(
        operator_name="cart", key=newCustomer.id, function_name="create_cart"
    )

    ctx.put(asdict(newCustomer))
    return ctx.key


@customer_operator.register
async def GetCustomer(ctx: StatefulFunction):
    state = ctx.get()
    if state is None:
        raise CustomerDoesNotExist(f"Customer with {ctx.key} does not exist")
    return Customer(**state)


@customer_operator.register
async def payment_notification(ctx: StatefulFunction, notificationType_value):
    notificationType = CustomerNotificationType(notificationType_value)
    state = ctx.get()

    if state is None:
        raise CustomerDoesNotExist()
    customer = Customer(**state)

    match notificationType:
        case CustomerNotificationType.PAYMENT_SUCCESS:
            customer.success_payment_count += 1
        case CustomerNotificationType.PAYMENT_FAILED:
            customer.failed_payment_count += 1
        case CustomerNotificationType.CHECKOUT_FAILED:
            customer.failed_payment_count += 1
    ctx.put(asdict(customer))


@customer_operator.register
async def handle_delivery_notification(ctx: StatefulFunction):
    state = ctx.get()
    customer: Customer
    if state is None:
        raise CustomerDoesNotExist()
    else:
        customer = Customer(**state)
    customer.delivery_count += 1
    ctx.put(asdict(customer))


@customer_operator.register
async def get_all_state(ctx: StatefulFunction) -> dict:
    return ctx.data


@customer_operator.register
async def set_all_state(ctx: StatefulFunction, state: dict) -> dict:
    if state:
        ctx.batch_insert(state)
    else:
        ctx.put(None)
    return state
