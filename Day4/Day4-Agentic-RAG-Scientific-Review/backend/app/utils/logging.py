import logging
import re

_SENSITIVE_PATTERN = re.compile(
    r"(api[_-]?key|authorization|x-groq-key)\s*[:=]\s*\S+", re.IGNORECASE
)


class RedactSensitiveFilter(logging.Filter):
    """Defense-in-depth: scrubs api_key/Authorization-looking substrings from log
    records. The primary control is simply never logging request bodies/headers."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _SENSITIVE_PATTERN.sub(r"\1: [REDACTED]", record.msg)
        return True


def configure_logging() -> None:
    root = logging.getLogger()
    redact_filter = RedactSensitiveFilter()
    for handler in root.handlers:
        handler.addFilter(redact_filter)
    logging.getLogger("uvicorn.access").addFilter(redact_filter)
