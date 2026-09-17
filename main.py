from fastapi import FastAPI, HTTPException
import requests
import time

app = FastAPI(
    title="ADA Tabdeal Bridge",
    version="1.0.0"
)

TABDEAL_BASE = "https://api1.tabdeal.org"
TRADES_ENDPOINT = f"{TABDEAL_BASE}/r/api/v1/trades"
DEPTH_ENDPOINT = f"{TABDEAL_BASE}/r/api/v1/depth"
TIME_ENDPOINT = f"{TABDEAL_BASE}/r/api/v1/time"

SYMBOL = "ADAUSDT"
REQUEST_TIMEOUT = 10


def tabdeal_get(url, params=None):
    response = requests.get(
        url,
        params=params,
        timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    return response.json()


@app.get("/")
def root():
    return {
        "bridge": "ADA Tabdeal Bridge",
        "status": "online",
        "symbol": SYMBOL,
        "source": "Tabdeal Public API"
    }


@app.get("/health")
def health():
    try:
        server_time = tabdeal_get(TIME_ENDPOINT)

        return {
            "status": "healthy",
            "source": "Tabdeal",
            "server_time": server_time
        }

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )


@app.get("/adausdt")
def adausdt():
    try:
        trades = tabdeal_get(
            TRADES_ENDPOINT,
            {
                "symbol": SYMBOL,
                "limit": 1
            }
        )

        if not trades:
            raise HTTPException(
                status_code=502,
                detail="No trade data returned"
            )

        trade = trades[0]

        price = float(trade["price"])
        quantity = float(trade["qty"])
        timestamp = int(trade["time"])

        now_ms = int(time.time() * 1000)
        age_ms = now_ms - timestamp

        return {
            "symbol": SYMBOL,
            "price": price,
            "quantity": quantity,
            "timestamp": timestamp,
            "age_ms": age_ms,
            "is_buyer_maker": trade.get("isBuyerMaker"),
            "source": "Tabdeal Public Trades API"
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Trade acquisition failed: {str(e)}"
        )


@app.get("/adausdt/depth")
def adausdt_depth():
    try:
        depth = tabdeal_get(
            DEPTH_ENDPOINT,
            {
                "symbol": SYMBOL,
                "limit": 5
            }
        )

        bids = depth.get("bids", [])
        asks = depth.get("asks", [])

        best_bid = float(bids[0][0]) if bids else None
        best_ask = float(asks[0][0]) if asks else None

        return {
            "symbol": SYMBOL,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "bids": bids,
            "asks": asks,
            "source": "Tabdeal Public Depth API"
        }

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Depth acquisition failed: {str(e)}"
        )
