"""
Langfuse utilities for tracing and debugging Open WebUI chat processing.
Uses Langfuse v3 context manager API for cleaner trace management.
"""

import logging
from langfuse import Langfuse

from open_webui.env import (
    LANGFUSE_SECRET_KEY,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_HOST,
)

log = logging.getLogger(__name__)

# Global Langfuse client instance
_langfuse_client = None


def get_langfuse_client() -> Langfuse:
    """Get or create Langfuse client instance."""
    global _langfuse_client
    
    if _langfuse_client is None:
        if not LANGFUSE_SECRET_KEY or not LANGFUSE_PUBLIC_KEY:
            log.warning("Langfuse is enabled but missing required keys (LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY)")
            raise ValueError("Langfuse is enabled but missing required keys (LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY)")
            
        _langfuse_client = Langfuse(
            secret_key=LANGFUSE_SECRET_KEY,
            public_key=LANGFUSE_PUBLIC_KEY,
            host=LANGFUSE_HOST,
        )
        log.info(f"Langfuse client initialized with host: {LANGFUSE_HOST}")
            
    return _langfuse_client


def get_trace_url_from_span(span) -> str:
    """Get the Langfuse trace URL from a span context."""
    try:
        # Get the trace ID from the span
        trace_id = span.trace_id
        if trace_id and LANGFUSE_HOST:
            # Construct the trace URL
            # Remove trailing slash from host if present
            host = LANGFUSE_HOST.rstrip('/')
            return f"{host}/trace/{trace_id}"
        return None
    except Exception as e:
        log.warning(f"Failed to get trace URL from span: {e}")
        return None

def get_prompt(prompt_name: str) -> str:
    """Get a prompt from Langfuse."""
    langfuse_client = get_langfuse_client()
    return langfuse_client.get_prompt(prompt_name).compile()