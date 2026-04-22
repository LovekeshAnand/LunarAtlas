import redis.asyncio as redis
import asyncio

async def test():
    try:
        r = redis.from_url('redis://127.0.0.1:6379/0')
        await r.ping()
        print('PONG! Redis connected.')
    except Exception as e:
        print(f'Failed: {e}')

asyncio.run(test())
