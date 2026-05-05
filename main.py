from fastapi import FastAPI
import requests

app = FastAPI()

session = requests.Session()

def get_crumb():
    url = "https://query1.finance.yahoo.com/v1/test/getcrumb"
    r = session.get(url)
    return r.text

@app.get("/fundamentos/{ticker}")
def fundamentos(ticker: str):

    try:
        crumb = get_crumb()

        url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}.SA?modules=financialData,defaultKeyStatistics&crumb={crumb}"

        r = session.get(url, timeout=10)

        data = r.json()

        # 🔥 proteção contra null
        result = data.get("quoteSummary", {}).get("result")

        if not result:
            return {
                "error": "Yahoo retornou vazio",
                "raw": data
            }

        result = result[0]

        return {
            "pl": result.get("defaultKeyStatistics", {}).get("forwardPE", {}).get("raw"),
            "pvp": result.get("defaultKeyStatistics", {}).get("priceToBook", {}).get("raw"),
            "roe": result.get("financialData", {}).get("returnOnEquity", {}).get("raw"),
            "ebitdaMargin": result.get("financialData", {}).get("ebitdaMargins", {}).get("raw")
        }

    except Exception as e:
        return {
            "error": str(e)
        }

def fallback_quote(ticker: str):
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}.SA"
    r = requests.get(url)
    data = r.json()

    result = data["quoteResponse"]["result"][0]

    return {
        "pl": result.get("trailingPE"),
        "pvp": result.get("priceToBook"),
        "lpa": result.get("epsTrailingTwelveMonths"),
        "marketCap": result.get("marketCap")
    }

