from styx.common.operator import Operator
from styx.common.stateful_function import StatefulFunction

op = Operator("seller_dashboard")  # keyed by seller id


@op.register
async def ongoing_order_entries(ctx: StatefulFunction):
    # call shipment to get notifications that is still ongoing
    # From there call payment to get payments on those ongoing orders that hasn't failed(somehow) [listing 1]
    # call a new function on the seller_dashboard operator, that does the aggregations. [mix of listing 2 and 3]
    # return those aggregations.
    pass
