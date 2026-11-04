
import asyncio
import json
import os
import websockets

# DERIV CONFIGURATION
APP_ID = os.getenv("DERIV_APP_ID", "YOUR_APP_ID")
API_TOKEN = os.getenv("DERIV_API_TOKEN", "")

SYMBOL = "frxXAUUSD"
CURRENCY = "USD"
STAKE = 1.0
DURATION = 5
FAST_PERIOD = 5
SLOW_PERIOD = 15

async def main():
    if not API_TOKEN:
        raise ValueError("Set your DERIV_API_TOKEN first.")

    url = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"

    async with websockets.connect(url) as ws:
        async def send(data):
            await ws.send(json.dumps(data))
            return json.loads(await ws.recv())

        auth = await send({"authorize": API_TOKEN})
        if "error" in auth:
            print(auth["error"])
            return

        print("Connected to Deriv!")

        # Request recent price candles
        candles = await send({
            "ticks_history": SYMBOL,
            "adjust_start": 1,
            "count": 30,
            "end": "latest",
            "granularity": 60,
            "style": "candles"
        })

        if "error" in candles:
            print(candles["error"])
            return

        prices = [
            float(c["close"])
            for c in candles["candles"]
        ]

        while True:
            fast = sum(prices[-FAST_PERIOD:]) / FAST_PERIOD
            slow = sum(prices[-SLOW_PERIOD:]) / SLOW_PERIOD

            print(f"Fast MA: {fast} | Slow MA: {slow}")

            if fast > slow:
                contract = "CALL"
            elif fast < slow:
                contract = "PUT"
            else:
                contract = None

            if contract:
                proposal = await send({
                    "proposal": 1,
                    "amount": STAKE,
                    "basis": "stake",
                    "contract_type": contract,
                    "currency": CURRENCY,
                    "duration": DURATION,
                    "duration_unit": "m",
                    "symbol": SYMBOL
                })

                if "error" in proposal:
                    print(proposal["error"])
                else:
                    print("Signal:", contract)
                    print("Proposal received. No trade placed.")

            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())

