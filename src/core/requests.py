from collections.abc import AsyncGenerator
from functools import cache

from httpx import AsyncClient, AsyncHTTPTransport


@cache
def get_http_transport() -> AsyncHTTPTransport:
    return AsyncHTTPTransport(retries=3, http2=True)


async def get_http_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=get_http_transport()) as client:
        yield client
