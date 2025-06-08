# py/logflare_handler.py
import os
import json
import logging
import requests
from datetime import datetime
from logging import Handler
from concurrent.futures import ThreadPoolExecutor, as_completed


class LogflareHandler(Handler):
    """
    A logging.Handler that ships logs to Logflare asynchronously. """

    _executor = ThreadPoolExecutor(max_workers=4)

    def __init__(self):
        super().__init__()
        self.api_key    = os.getenv("LOGFLARE_API_KEY")
        self.source_id  = os.getenv("LOGFLARE_SOURCE_ID")
        if not self.api_key or not selff.source_id:
            raise RuntimeError("LOGFLARE_API_KEY and LOGFLARE_SOURCE_ID must be set")

        self.endpoint = (
            f"https://api.logflare.app/logs"
            f"?api_key={self.api_key}"
            f"&source={self.source_id}"
        )

        # Use a small request session (optional but slightly more efficient)
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

        # # We’ll do non‐blocking HTTP requests on a background thread
        # # so that our bot’s event loop is not held up.
        # self._thread_lock = threading.Lock()

        # Optional: buffer to batch records
        # self._buffer = []
        # self._max_batch = 10


    def emit(self, record: logging.LogRecord) -> None:
        try:
            payload = self.format_payload(record)

            # If you want batching, uncomment:
            # self._buffer.append(payload)
            # if len(self._buffer) >= self._max_batch:
            #     batch = self._buffer[:]
            #     self._buffer.clear()
            #     self._executor.submit(self._post_batch, batch)
            # else:
            #     self._executor.submit(self._post, payload)

            # Fire-and-forget via thread pool
            self._executor.submit(self._post, payload)
        except Exception:
            logging.getLogger(__name__).warning(
                "LogflareHandler.emit() failed to schedule post", exc_info=True
            )


    def format_payload(self, record: logging.LogRecord) -> dict:
        """
        Convert a LogRecord into the JSON structure Logflare expects.
        You can add any fields you like—tags, custom attributes, etc.
        """
        message   = record.getMessage()
        timestamp = datetime.utcfromtimestamp(record.created).isoformat() + "Z"

        meta = {
            "logger_name": record.name,
            "module": record.module,
            "funcName": record.funcName,
            "line_no": record.lineno,
        }

        payload = {
            "timestamp": timestamp,
            "level": record.levelname,
            "message": message,
            "meta": meta,
        }

        if record.exc_info:
            # use a temporary Formatter just for exceptions
            exc_text = logging.Formatter().formatException(record.exc_info)
            payload["meta"]["exc_info"] = exc_text

        return payload


    def _post(self, payload: dict):
        try:
            self._session.post(self.endpoint, json=payload, timeout=3.0)
        except Exception as e:
            logging.getLogger(__name__).warning(
                "LogflareHandler POST failed: %s", e, exc_info=True
            )

    # If you need batching, implement something like:
    # def _post_batch(self, batch: list[dict]):
    #     try:
    #         self._session.post(self.endpoint, json=batch, timeout=3.0)
    #     except Exception as e:
    #         logging.getLogger(__name__).warning(
    #             "LogflareHandler batch POST failed: %s", e, exc_info=True
    #         )