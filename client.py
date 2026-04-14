import asyncio
import random
import sys
import time
from string import ascii_letters

import aiohttp

try:
    URL = sys.argv[1]
except IndexError:
    URL = "http://localhost:8000"

try:
    CONCURRENCY = int(sys.argv[2])
except IndexError:
    CONCURRENCY = 100
except ValueError:
    print("Usage: python client.py <url> <concurrency>")
    sys.exit(1)


start = time.perf_counter()
errors = []


async def fetch(session: aiohttp.ClientSession, index: int) -> None:
    async with session.get(URL + "/heroes/") as response:
        await response.read()
        if response.status != 200:
            errors.append((index, response.status))
        print(f"[{index}] status={response.status}")


async def create(session: aiohttp.ClientSession, index: int) -> None:
    async with session.post(URL + "/heroes/", json=random_hero(index)) as response:
        await response.read()
        if response.status != 200:
            errors.append((index, response.status))
        print(f"[{index}] status={response.status}")


async def main() -> None:
    print("Creating heroes...")
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[create(session, i) for i in range(CONCURRENCY)])

    print("Fetching heroes...")
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[fetch(session, i) for i in range(CONCURRENCY)])


def random_hero(ix):
    return {
        "name": f"Hero {ix} ",
        "age": random.randint(0, 1000),
        "secret_name": "".join(random.choices(ascii_letters, k=20)),
    }


asyncio.run(main())
print(f"{CONCURRENCY} requests finished in {time.perf_counter() - start:.2f} seconds")
print(f"    encountered {len(errors)} errors")
