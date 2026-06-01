"""
bot/utils.py
------------
Fungsi-fungsi kecil yang dipakai bersama oleh modul lain.
"""


def parse_input(input_str: str) -> dict:
    """
    Mengurai string berformat 'key=value;key2=value2' menjadi dict.

    Menggunakan str.partition("=") agar value yang mengandung "="
    (seperti URL atau base64) tidak ikut terpotong.

    Contoh:
        parse_input("lat=-6.2;lon=106.8")
        → {"lat": "-6.2", "lon": "106.8"}

        parse_input("url=https://example.com?a=1;title=Test")
        → {"url": "https://example.com?a=1", "title": "Test"}
    """
    result = {}
    for part in input_str.split(";"):
        part = part.strip()
        if not part:
            continue
        key, _, value = part.partition("=")
        result[key.strip()] = value.strip()
    return result
