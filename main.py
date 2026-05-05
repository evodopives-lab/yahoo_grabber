from fastapi import FastAPI
import requests

app = FastAPI()

session = requests.Session()

def get_crumb():
    url = "https://query1.finance.yahoo.com/v1/test/getcrumb"
    r = session.get(url)
    return r.text

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/fundamentos/{ticker}")
def fundamentos(ticker: str):

    crumb = get_crumb()

    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}.SA?modules=financialData,defaultKeyStatistics&crumb={crumb}"

    r = session.get(url)

    data = r.json()

    try:
        result = data["quoteSummary"]["result"][0]

        return {
            "pl": result["defaultKeyStatistics"]["forwardPE"]["raw"],
            "pvp": result["defaultKeyStatistics"]["priceToBook"]["raw"],
            "roe": result["financialData"]["returnOnEquity"]["raw"],
            "ebitdaMargin": result["financialData"]["ebitdaMargins"]["raw"]
        }

    except:
        return {"error": "dados indisponíveis"}
