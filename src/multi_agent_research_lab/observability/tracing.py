import logging
from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any

from langfuse import Langfuse

from multi_agent_research_lab.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
# Initialize Langfuse client if API keys are configured
if settings.langfuse_public_key and settings.langfuse_secret_key:
    try:
        langfuse_client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except Exception as e:
        logger.error(f"Failed to initialize Langfuse client: {e}")
        langfuse_client = None
else:
    langfuse_client = None


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Span context used to record performance metrics and send traces to Langfuse."""
    started = perf_counter()
    span_data: dict[str, Any] = {"name": name, "attributes": attributes or {}, "duration_seconds": None}
    
    lf_span = None
    if langfuse_client:
        try:
            # Create a span in Langfuse
            lf_span = langfuse_client.span(
                name=name,
                metadata=attributes or {}
            )
        except Exception as e:
            logger.warning(f"Failed to create Langfuse span: {e}")

    try:
        yield span_data
    finally:
        duration = perf_counter() - started
        span_data["duration_seconds"] = duration
        
        if lf_span:
            try:
                lf_span.end(metadata={"duration_seconds": duration})
            except Exception as e:
                logger.warning(f"Failed to end Langfuse span: {e}")
