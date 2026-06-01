"""
bot/tools/vehicle.py
--------------------
Tools untuk fitur kendaraan: cari merek, model/tahun, pesan, dan lihat order.
Semua operasi DB melalui bot.database — tidak ada koneksi langsung di sini.
"""

import time
import requests
from langchain_core.tools import tool
from bot.utils import parse_input
from bot import database as db

FIPE_BASE = "https://parallelum.com.br/fipe/api/v1"


@tool
def get_brands(tool_input: str) -> str:
    """
    Mendapatkan daftar merek kendaraan berdasarkan tipe.
    Input format: 'vehicle_type=<tipe>'
    Pilihan tipe: carros (mobil), motos (motor), caminhoes (truk)
    Contoh: 'vehicle_type=carros'
    """
    try:
        params = parse_input(tool_input)
        vt = params.get("vehicle_type")
        if not vt:
            return "Error: 'vehicle_type' wajib diisi. Contoh: 'vehicle_type=carros'"

        limit = int(params.get("limit", 20))
        response = requests.get(f"{FIPE_BASE}/{vt}/marcas", timeout=15)
        response.raise_for_status()
        data = response.json()[:limit]

        lines = [f"- {item['nome']} (kode: {item['codigo']})" for item in data]
        return f"Daftar merek untuk '{vt}':\n" + "\n".join(lines)

    except Exception as e:
        return f"Error pada tool get_brands: {e}"


@tool
def get_models_and_years(tool_input: str) -> str:
    """
    Mendapatkan daftar model dan tahun tersedia untuk merek tertentu.
    Gunakan setelah mendapatkan brand_code dari tool get_brands.
    Input format: 'vehicle_type=<tipe>;brand_code=<kode>'
    Contoh: 'vehicle_type=carros;brand_code=7'
    """
    try:
        params = parse_input(tool_input)
        vt = params.get("vehicle_type")
        brand_code = params.get("brand_code")

        if not vt or not brand_code:
            return "Error: 'vehicle_type' dan 'brand_code' wajib diisi."

        limit = int(params.get("limit", 3))

        models_resp = requests.get(
            f"{FIPE_BASE}/{vt}/marcas/{brand_code}/modelos", timeout=15
        )
        models_resp.raise_for_status()
        modelos = models_resp.json().get("modelos", [])[:limit]

        if not modelos:
            return f"Tidak ada model ditemukan untuk brand_code={brand_code}."

        result_lines = []
        for model in modelos:
            model_name = model["nome"]
            model_code = model["codigo"]

            years_resp = requests.get(
                f"{FIPE_BASE}/{vt}/marcas/{brand_code}/modelos/{model_code}/anos",
                timeout=15,
            )
            years_resp.raise_for_status()
            years = years_resp.json()[:limit]

            year_str = ", ".join(
                [f"{y['nome']} (kode: {y['codigo']})" for y in years]
            )
            result_lines.append(
                f"Model: {model_name} (kode: {model_code})\n  Tahun: {year_str}"
            )
            time.sleep(0.2)  # rate limiting

        return "\n\n".join(result_lines)

    except Exception as e:
        return f"Error pada tool get_models_and_years: {e}"


@tool
def order_vehicle(tool_input: str) -> str:
    """
    Membuat order kendaraan baru.
    Input format: 'customer_name=<nama>;vehicle_type=<tipe>;brand_code=<kode>;model_code=<kode>;year_code=<kode>'
    Contoh: 'customer_name=Budi;vehicle_type=carros;brand_code=21;model_code=4828;year_code=2020-3'
    Pastikan sudah mendapatkan brand_code, model_code, dan year_code dari tools sebelumnya.
    """
    try:
        params = parse_input(tool_input)

        required = ["customer_name", "vehicle_type", "brand_code", "model_code", "year_code"]
        missing = [k for k in required if k not in params]
        if missing:
            return f"Error: field berikut wajib diisi: {', '.join(missing)}"

        order = db.insert_order(
            customer_name=params["customer_name"],
            vehicle_type=params["vehicle_type"],
            brand_code=params["brand_code"],
            model_code=params["model_code"],
            year_code=params["year_code"],
        )

        return (
            f"Order berhasil dibuat!\n"
            f"- ID Order: #{order['id']}\n"
            f"- Pelanggan: {order['customer_name']}\n"
            f"- Kendaraan: {order['vehicle_type']} | Brand: {order['brand_code']} | "
            f"Model: {order['model_code']} | Tahun: {order['year_code']}\n"
            f"- Estimasi pengiriman: {order['delivery_date']}"
        )

    except Exception as e:
        return f"Error pada tool order_vehicle: {e}"


@tool
def view_orders(tool_input: str = "") -> str:
    """
    Menampilkan semua order yang sudah dibuat.
    Tidak memerlukan input apapun.
    """
    try:
        orders = db.fetch_all_orders()
        if not orders:
            return "Belum ada order yang tersimpan."

        lines = []
        for o in orders:
            lines.append(
                f"Order #{o['id']} — {o['customer_name']}\n"
                f"  Tipe: {o['vehicle_type']} | Brand: {o['brand_code']} | "
                f"Model: {o['model_code']} | Tahun: {o['year_code']}\n"
                f"  Tanggal Order: {o['order_date'][:10]}\n"
                f"  Estimasi Pengiriman: {o['delivery_date'][:10]}"
            )

        return f"Total {len(orders)} order ditemukan:\n\n" + "\n\n".join(lines)

    except Exception as e:
        return f"Error pada tool view_orders: {e}"
