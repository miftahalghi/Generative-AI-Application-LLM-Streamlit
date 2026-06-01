"""
bot/tools/__init__.py
---------------------
Mengekspor semua tools dalam satu list `ALL_TOOLS`.
Cukup import dari sini di agent.py — tidak perlu import per-file.
"""

from bot.tools.utility import multiply, search, get_weather, cat_fact
from bot.tools.vehicle import get_brands, get_models_and_years, order_vehicle, view_orders
from bot.tools.product import product_rag

ALL_TOOLS = [
    multiply,
    search,
    get_weather,
    cat_fact,
    get_brands,
    get_models_and_years,
    order_vehicle,
    view_orders,
    product_rag,
]
