import logging
from typing import Dict, Any

from pymongo import monitoring


class QueryLogger(monitoring.CommandListener):
    def started(self, event):
        logging.info(f"Query started - {event.command_name} - {self._redact(event.command)}")

    def succeeded(self, event):
        logging.info(
            f"Query succeeded - {event.command_name} "
            f"in {event.duration_micros / 1000:.2f}ms"
        )

    def failed(self, event):
        logging.error(
            f"Query failed - {event.command_name} "
            f"in {event.duration_micros / 1000:.2f}ms - {event.failure}"
        )

    def _redact(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive information from logs"""
        redacted = command.copy()
        if 'filter' in redacted:
            if 'password' in redacted['filter']:
                redacted['filter']['password'] = '***REDACTED***'
        return redacted


def setup_mongo_logging():
    """Register MongoDB query logger"""
    monitoring.register(QueryLogger())
