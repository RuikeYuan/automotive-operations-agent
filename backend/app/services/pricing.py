import os
from statistics import median
from decimal import Decimal, ROUND_HALF_UP


def money(value):
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_price(sales, condition, quantity, age_days, market_reference, acquisition_cost):
    if condition not in {"good", "fair", "excellent", "untested"} or quantity < 0 or age_days < 0:
        raise ValueError("Invalid pricing factors")
    if market_reference <= 0 or acquisition_cost < 0 or any(s <= 0 for s in sales):
        raise ValueError("Invalid reference prices")
    base = median(sales) if sales else market_reference
    condition_factor = {"good":1.0, "fair":.75, "excellent":1.15, "untested":.55}[condition]
    stock_factor = .90 if quantity >= 5 else .95 if quantity >= 2 else 1.0
    age_factor = .85 if age_days > 180 else .95 if age_days > 90 else 1.0
    margin = float(os.getenv("MIN_MARGIN", ".20"))
    if not 0 <= margin < 1:
        raise ValueError("MIN_MARGIN must be in [0,1)")
    floor = acquisition_cost / (1-margin)
    suggested = money(max(base * condition_factor * stock_factor * age_factor, floor))
    return {"suggested_price":suggested, "currency":"EUR", "price_range":{"min":money(max(floor,suggested*.9)), "max":money(suggested*1.1)}, "factors":[{"name":"base", "value":base, "source":"historical_median" if sales else "synthetic_market_reference"}, {"name":"condition", "value":condition_factor}, {"name":"stock", "value":stock_factor}, {"name":"age", "value":age_factor}, {"name":"margin_floor", "value":money(floor)}], "confidence":.85 if len(sales)>=3 else .55 if sales else .3, "history_count":len(sales)}

