import httpx

http_client: httpx.AsyncClient | None = None


async def init_http_client():
    global http_client
    http_client = httpx.AsyncClient(
        timeout=30,
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )


async def close_http_client():
    global http_client
    if http_client:
        await http_client.aclose()


def get_http_client() -> httpx.AsyncClient:
    if not http_client:
        raise RuntimeError("HTTP client is not initialized")
    return http_client
