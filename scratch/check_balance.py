import sys
import asyncio
import os
import config
from execution.broker import Broker

async def main():
    try:
        broker = Broker(testnet=config.TESTNET)
        print("Fetching balance from Binance Testnet...")
        balance = broker.fetch_balance()
        
        print("\n--- Account Balance ---")
        if 'total' in balance:
            for coin, amount in balance['total'].items():
                if amount > 0:
                    print(f"{coin}: {amount}")
        else:
            print("Could not fetch structured balance. Raw data:")
            print(balance)
            
    except Exception as e:
        print(f"Error fetching balance: {e}")

if __name__ == "__main__":
    asyncio.run(main())
