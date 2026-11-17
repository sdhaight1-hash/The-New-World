"""Start World Bible Studio with initial Markdown import and browser opening.

Running this repeatedly never overwrites entries already in the local database.
"""
from __future__ import annotations

import argparse
import threading
import webbrowser

from seed import seed
from server import serve, DB_DEFAULT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DB_DEFAULT))
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    seed(args.db)
    if not args.no_browser:
        timer = threading.Timer(0.7, webbrowser.open, args=(f"http://127.0.0.1:{args.port}/app/",))
        timer.daemon = True
        timer.start()
    serve(args.db, args.port)


if __name__ == "__main__":
    main()
