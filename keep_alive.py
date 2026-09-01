import asyncio
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


async def ping_self():
    """
    Pings the Render deployment every 14 minutes to prevent cold starts.
    Render free tier spins down after 15 minutes of inactivity.
    """
    if not settings.render_url:
        logger.info("RENDER_URL not set — keep-alive disabled (local dev)")
        return

    await asyncio.sleep(30)  # Wait for app to fully start

    async with httpx.AsyncClient() as client:
        while True:
            try:
                resp = await client.get(f"{settings.render_url}/health", timeout=10)
                logger.info(f"Keep-alive ping: {resp.status_code}")
            except Exception as e:
                logger.warning(f"Keep-alive ping failed: {e}")
            await asyncio.sleep(settings.keep_alive_interval_seconds)
