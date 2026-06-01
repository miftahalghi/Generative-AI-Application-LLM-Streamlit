"""
bot/tools/product.py
--------------------
Tool untuk perbandingan produk berbasis pencarian web (RAG sederhana).
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
def product_rag(tool_input: str) -> str:
    """
    Mencari dan membandingkan produk secara real-time dari web.
    Gunakan untuk pertanyaan perbandingan produk seperti laptop, HP, sepatu, dll.
    Input format: 'query=<pertanyaan perbandingan>'
    Contoh: 'query=perbandingan Nike ZoomX vs Adidas UltraBoost'
    """
    try:
        params = parse_input(tool_input)
        query = params.get("query")
        if not query:
            return "Error: 'query' wajib diisi. Contoh: 'query=iPhone 15 vs Samsung S24'"

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

        snippets = []
        for i, r in enumerate(results[:5], 1):
            title = r.get("title", "No title")
            snippet = r.get("snippet", "No snippet")
            url = r.get("url", "")
            snippets.append(f"{i}. {title}\n   {snippet}\n   Sumber: {url}")

        return "Hasil pencarian produk terkini:\n\n" + "\n\n".join(snippets)

    except requests.exceptions.Timeout:
        return "Error: Request pencarian timeout."
    except Exception as e:
        return f"Error pada tool product_rag: {e}"
