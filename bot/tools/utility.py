"""
bot/tools/utility.py
--------------------
Tools umum: kalkulator, pencarian web, cuaca, dan cat fact.
"""

import os

import requests
import streamlit as st
from langchain_core.tools import tool

from bot.utils import parse_input


def _get_secret(key: str, default: str = "") -> str:
    """Membaca secret dari st.secrets dengan fallback ke os.environ."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.environ.get(key, default)


@tool
def multiply(tool_input: str) -> str:
    """
    Mengalikan dua angka.
    Input format: 'a=<angka>;b=<angka>'
    Contoh: 'a=12;b=7.5'
    """
    try:
        params = parse_input(tool_input)
        if "a" not in params or "b" not in params:
            return "Error: input harus mengandung 'a' dan 'b'. Contoh: 'a=12;b=7.5'"
        a = float(params["a"])
        b = float(params["b"])
        return str(a * b)
    except ValueError:
        return "Error: 'a' dan 'b' harus berupa angka."
    except Exception as e:
        return f"Error pada tool multiply: {e}"


@tool
def search(query: str) -> str:
    """
    Melakukan pencarian web menggunakan search engine.
    Gunakan tool ini untuk mencari informasi terkini atau yang tidak diketahui.
    Input: string pertanyaan/query pencarian.
    """
    try:
        search_token = _get_secret("SEARCH_TOKEN")
        if not search_token:
            return "Error: SEARCH_TOKEN tidak ditemukan di environment."

        response = requests.post(
            "https://api.search1api.com/search",
            json={"search_service": "google", "query": query},
            headers={
                "Authorization": f"Bearer {search_token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        response.raise_for_status()
        results = response.json().get("results", [])

        if not results:
            return "Tidak ada hasil ditemukan untuk query tersebut."

        # Format ringkas agar tidak membanjiri konteks agent
        formatted = []
        for i, r in enumerate(results[:5], 1):
            title = r.get("title", "No title")
            snippet = r.get("snippet", "No snippet")
            url = r.get("url", "")
            formatted.append(f"{i}. {title}\n   {snippet}\n   {url}")

        return "\n\n".join(formatted)

    except requests.exceptions.Timeout:
        return "Error: Request pencarian timeout."
    except Exception as e:
        return f"Error pada tool search: {e}"


@tool
def get_weather(tool_input: str) -> str:
    """
    Mendapatkan cuaca terkini berdasarkan koordinat latitude & longitude.
    Gunakan tool 'search' terlebih dahulu untuk mendapatkan koordinat kota.
    Input format: 'lat=<latitude>;lon=<longitude>'
    Contoh: 'lat=-6.2;lon=106.8'
    """
    try:
        params = parse_input(tool_input)
        if "lat" not in params or "lon" not in params:
            return "Error: input harus mengandung 'lat' dan 'lon'. Contoh: 'lat=-6.2;lon=106.8'"

        lat = float(params["lat"])
        lon = float(params["lon"])

        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
                "hourly": "relative_humidity_2m",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        cw = data.get("current_weather", {})
        temp = cw.get("temperature", "N/A")
        wind = cw.get("windspeed", "N/A")
        code = cw.get("weathercode", "N/A")

        return (
            f"Cuaca saat ini di koordinat ({lat}, {lon}):\n"
            f"- Suhu: {temp}°C\n"
            f"- Kecepatan angin: {wind} km/h\n"
            f"- Kode cuaca (WMO): {code}"
        )
    except ValueError:
        return "Error: lat dan lon harus berupa angka."
    except Exception as e:
        return f"Error pada tool get_weather: {e}"


@tool
def cat_fact(tool_input: str = "") -> str:
    """
    Mengembalikan fakta unik dan acak tentang kucing.
    Tidak memerlukan input apapun.
    """
    try:
        response = requests.get(
            "https://catfact.ninja/fact",
            params={"max_length": 200},
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("fact", "Tidak ada fakta tersedia saat ini.")
    except Exception as e:
        return f"Error pada tool cat_fact: {e}"
