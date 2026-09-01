from supabase import create_client, Client
from app.core.config import settings
from functools import lru_cache


@lru_cache
def get_supabase() -> Client:
    """Initialize and return the Supabase client instance."""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
