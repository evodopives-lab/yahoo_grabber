from fastapi import FastAPI
import requests
from functools import lru_cache
import time

app = FastAPI()

session = requests.Session()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive"
}

# ─────────────────────────────────────
# 🔹 CRUMB (opcional)
# ─────────────────────────────────────
def get_crumb():
    try:
        url = "https://query1.finance.yahoo.com/v1/test/getcrumb"
        r = session.get(url, headers=HEADERS, timeout=5)

        if r.status_code != 200 or not r.text:
            return None

        return r.text.strip()

    except:
        return None


# ─────────────────────────────────────
# 🔹 FALLBACK PRINCIPAL (query2)
# ─────────────────────────────────────
def fallback_quote(ticker: str):
    try:
        url = f"https://query2.finance.yahoo.com/v7/finance/quote?symbols={ticker}.SA"
        r = requests.get(url, headers=HEADERS, timeout=5)

        if r.status_code != 200:
            return {
                "error": f"fallback HTTP {r.status_code}",
                "hint": "Yahoo pode estar bloqueando IP"
            }

        if not r.text:
            return {"error": "fallback vazio"}

        try:
            data = r.json()
        except:
            return {"error": "fallback não é JSON", "raw": r.text[:200]}

        result = data.get("quoteResponse", {}).get("result", [])

        if not result:
            return {"error": "fallback sem dados"}

        result = result[0]

        return {
            "pl": result.get("trailingPE"),
            "pvp": result.get("priceToBook"),
            "lpa": result.get("epsTrailingTwelveMonths"),
            "marketCap": result.get("marketCap"),
            "source": "fallback_query2"
        }

    except Exception as e:
        return {"error": f"fallback erro: {str(e)}"}


# ─────────────────────────────────────
# 🔹 CACHE (evita bloqueio)
# ─────────────────────────────────────
@lru_cache(maxsize=500)
def get_fundamentos_cached(ticker: str):
    return get_fundamentos_raw(ticker)


# ─────────────────────────────────────
# 🔹 FUNÇÃO PRINCIPAL
# ─────────────────────────────────────
def get_fundamentos_raw(ticker: str):

    crumb = get_crumb()

    # Se não conseguir crumb → vai direto fallback
    if not crumb:
        return fallback_quote(ticker)

    url = (
        f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/"
        f"{ticker}.SA?modules=financialData,defaultKeyStatistics&crumb={crumb}"
    )

    try:
        r = session.get(url, headers=HEADERS, timeout=10)

        if r.status_code != 200:
            return fallback_quote(ticker)

        if not r.text:
            return fallback_quote(ticker)

        try:
            data = r.json()
        except:
            return fallback_quote(ticker)

        result = data.get("quoteSummary", {}).get("result")

        if not result:
            return fallback_quote(ticker)

        result = result[0]

        return {
            "pl": result.get("defaultKeyStatistics", {}).get("forwardPE", {}).get("raw"),
            "pvp": result.get("defaultKeyStatistics", {}).get("priceToBook", {}).get("raw"),
            "roe": result.get("financialData", {}).get("returnOnEquity", {}).get("raw"),
            "ebitdaMargin": result.get("financialData", {}).get("ebitdaMargins", {}).get("raw"),
            "source": "quoteSummary"
        }

    except Exception:
        return fallback_quote(ticker)


# ─────────────────────────────────────
# 🔹 ENDPOINTS
# ─────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/fundamentos/{ticker}")
def fundamentos(ticker: str):

    ticker = ticker.upper().strip()

    if not ticker:
        return {"error": "ticker inválido"}

    data = get_fundamentos_cached(ticker)

    return data


# ─────────────────────────────────────
# 🔹 HEALTHCHECK (Railway)
# ─────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "running",
        "time": time.time()
    }
