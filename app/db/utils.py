import json
import logging
from datetime import datetime

from bson import ObjectId, Binary
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import PythonLexer
from pymongo.monitoring import CommandListener

logger = logging.getLogger(__name__)


class CommandLogger(CommandListener):
    """Log MongoDB commands and their durations"""

    def started(self, event):
        logger.debug(f"Command {event.command_name} started - {event.command}")
        print(f"Command: {event.command}")
        print(f"Database: {event.database_name}")

    def succeeded(self, event):
        logger.debug(f"Command {event.command_name} succeeded in {event.duration_micros}μs")
        print(f"Reply: {event.reply}")

    def failed(self, event):
        logger.debug(f"Command {event.command_name} failed in {event.duration_micros}μs")
        print(f"Failure: {event.failure}")


class MongoJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (ObjectId, Binary)):
            return str(o)
        elif isinstance(o, datetime):
            return o.isoformat()
        elif isinstance(o, bytes):
            return o.decode('utf-8', errors='replace')
        return super().default(o)


class ColorMongoLogger(CommandListener):
    def __init__(self):
        self.lexer = PythonLexer()
        self.formatter = Terminal256Formatter(style="monokai")
        self.encoder = MongoJSONEncoder(indent=2)

    def _colorize(self, text):
        return highlight(text, self.lexer, self.formatter).strip()

    def _safe_dumps(self, data):
        try:
            return self.encoder.encode(data)
        except Exception as e:
            return f"<<Non-serializable: {type(data).__name__}>>"

    def started(self, event):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        cmd = self._safe_dumps(event.command)
        print(f"\n\033[33m[{timestamp}] \033[36mSTARTED \033[35m{event.command_name}\033[0m")
        print(f"\033[34mDatabase:\033[0m {event.database_name}")
        print(f"\033[34mCommand:\033[0m {self._colorize(cmd)}")

    def succeeded(self, event):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        duration_ms = event.duration_micros / 1000
        print(f"\n\033[33m[{timestamp}] \033[32mSUCCEEDED \033[35m{event.command_name}\033[0m "
              f"\033[33m({duration_ms:.2f}ms)\033[0m")

        if hasattr(event, 'reply'):
            reply = self._safe_dumps(event.reply)
            print(f"\033[34mReply:\033[0m {self._colorize(reply)}")

    def failed(self, event):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        duration_ms = event.duration_micros / 1000
        print(f"\n\033[33m[{timestamp}] \033[31mFAILED \033[35m{event.command_name}\033[0m "
              f"\033[33m({duration_ms:.2f}ms)\033[0m")
        print(f"\033[31mError:\033[0m {self._colorize(str(event.failure))}")
