import os, json, threading, logging, requests
from datetime import datetime
from logging import Handler, LogRecord


class LogflareHandler(Handler):
    """
    Einfache Handler, der jeden LogRecord in einem Hintergrund-Thread
    an Logflare schickt.
    """
    def __init__(self):
        super().__init__()
        self.setFormatter(logging.Formatter())  # sorgt für formatException()
        self.api_key   = os.getenv("LOGFLARE_API_KEY")
        self.source_id = os.getenv("LOGFLARE_SOURCE_ID")
        if not self.api_key or not self.source_id:
            raise RuntimeError("LOGFLARE_API_KEY und LOGFLARE_SOURCE_ID müssen gesetzt sein")
        self.endpoint = f"https://api.logflare.app/logs?api_key={self.api_key}&source={self.source_id}"
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def emit(self, record: LogRecord) -> None:
        try:
            payload = self.format_payload(record)
            # Startet einen kurzen Thread pro Log
            threading.Thread(target=self._post, args=(payload,), daemon=True).start()
        except Exception:
            logging.getLogger(__name__).warning("LogflareHandler.emit() Fehler", exc_info=True)

    def format_payload(self, record: LogRecord) -> dict:
        ts = datetime.utcfromtimestamp(record.created).isoformat() + "Z"
        base = {
            "timestamp": ts,
            "level":     record.levelname,
            "message":   record.getMessage(),
            "meta": {
                "logger":   record.name,
                "module":   record.module,
                "func":     record.funcName,
                "line":     record.lineno
            }
        }
        if record.exc_info:
            base["meta"]["exc_info"] = self.formatter.formatException(record.exc_info)
        return base

    def _post(self, payload: dict):
        try:
            self._session.post(self.endpoint, json=payload, timeout=3)
        except Exception:
            pass  # still swallow
