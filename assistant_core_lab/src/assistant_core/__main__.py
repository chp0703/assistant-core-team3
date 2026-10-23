"""Command-line adapter: answers on stdout, logs and errors on stderr."""

import argparse
import sys

from pydantic import ValidationError

from assistant_core.config import load_settings
from assistant_core.errors import ConfigError
from assistant_core.knowledge import KnowledgeError
from assistant_core.logging_setup import setup_logging
from assistant_core.models import Message
from assistant_core.service import create_service


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ask the offline Lab 3 study assistant.")
    parser.add_argument("text", nargs="+", help="A message of 1 to 2000 characters.")
    parser.add_argument("--session-id", default="local", help="A non-sensitive session identifier.")
    parser.add_argument("--json", action="store_true", help="Print the structured Response as JSON.")
    args = parser.parse_args(argv)
    try:
        msg = Message(text=" ".join(args.text), session_id=args.session_id)
    except ValidationError:
        print("Invalid message: use 1 to 2000 characters containing non-whitespace text.", file=sys.stderr)
        return 2
    try:
        settings = load_settings()
        try:
            setup_logging(settings.log_level)
        except ValueError as error:
            raise ConfigError("Invalid LOG_LEVEL.") from error
        service = create_service(settings)
    except (ConfigError, KnowledgeError) as error:
        print(f"Cannot start assistant: {error}", file=sys.stderr)
        return 1
    response = service.handle(msg)
    if args.json:
        print(response.model_dump_json())
        return 0
    print(response.answer)
    for source in response.sources:
        print(f"(source: {source.id} - {source.title})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
