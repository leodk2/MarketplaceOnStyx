from dataclasses import asdict
from Entities.CustomerNotificationType import CustomerNotificationType
import logging
from Entities.Customer import Customer
from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction


logger = logging.Logger(__name__)
customer_operator = Operator("customer")


class CustomerDoesNotExist(Exception):
    pass


@customer_operator.register
async def RegisterCustomer(ctx: StatefulFunction, customer: Customer):
    ctx.put(asdict(customer))


@customer_operator.register
async def GetCustomer(ctx: StatefulFunction):
    state = ctx.get()
    if state is None:
        raise CustomerDoesNotExist(f"Customer with {ctx.key} does not exist")
    return Customer(**state)


@customer_operator.register
async def CustomerNotification(
    ctx: StatefulFunction, notificationType: CustomerNotificationType
):
    state = ctx.get()

    if state is None:
        raise CustomerDoesNotExist()
    customer = Customer(**state)

    match notificationType:
        case CustomerNotificationType.PAYMENT_SUCCESS:
            customer.SuccessPaymentCount += 1
        case CustomerNotificationType.PAYMENT_FAILED:
            customer.FailedPaymentCount += 1
        case CustomerNotificationType.CHECKOUT_FAILED:
            customer.FailedPaymentCount += 1
    ctx.put(customer)


@customer_operator.register
async def HandleDeliveryNotification(ctx: StatefulFunction):
    state = ctx.get()
    customer: Customer
    if state is None:
        raise CustomerDoesNotExist()
    else:
        customer = Customer(**state)
    customer.DeliveryCount += 1
    ctx.put(customer)
