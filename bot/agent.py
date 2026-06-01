"""
bot/agent.py
------------
Membangun LangChain agent dengan:
- Groq sebagai LLM provider (cloud-based, gratis)
- System prompt dari file teks
- Tool-calling loop otomatis via create_agent (LangChain v1.x)
"""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver

from bot.tools import ALL_TOOLS

# Path ke file system prompt
_PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.txt"


def _load_system_prompt() -> str:
    """Membaca system prompt dari file teks."""
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    return ""  # fallback kosong jika file tidak ditemukan


def _get_secret(key: str, default: str = "") -> str:
    """
    Membaca secret dari Streamlit Cloud (st.secrets) dengan fallback ke os.environ.
    Ini memungkinkan project berjalan di Streamlit Cloud maupun lokal.
    """
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        pass
    return os.environ.get(key, default)


def build_agent():
    """
    Membangun dan mengembalikan agent graph yang siap digunakan.

    Menggunakan Groq sebagai LLM provider:
    - Model default: llama-3.1-8b-instant (gratis, cepat)
    - API key dibaca dari st.secrets atau environment variable
    - create_agent (LangChain v1.x) menggantikan AgentExecutor + create_react_agent
    """
    load_dotenv()

    groq_api_key = _get_secret("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError(
            "GROQ_API_KEY tidak ditemukan. "
            "Set di Streamlit Cloud Secrets atau file .env"
        )

    llm = ChatGroq(
        model=_get_secret("GROQ_MODEL", "llama-3.1-8b-instant"),
        api_key=groq_api_key,
        temperature=0,
        max_tokens=1024,
    )

    system_prompt = _load_system_prompt()

    memory = MemorySaver()
    agent = create_agent(
        model=llm,
        tools=ALL_TOOLS,
        system_prompt=system_prompt if system_prompt else None,
        checkpointer=memory,
    )

    return agent
