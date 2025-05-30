#_ py/log_config.py
from postgrest.exceptions import APIError
import logging

logger = logging.getLogger(__name__)

def safe_select(client, table, *args, **kwargs):
    try:
        resp = client.table(table).select(*args, **kwargs).execute()
        return resp.data or []
    except APIError as err:
        # Log the full error so you can see status, hint, details, etc.
        logger.error("Supabase APIError: %s", err.args[0])
        raise
