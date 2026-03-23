#!/usr/bin/env python3
import hashlib
import subprocess
import time
import sys

DISPLAYS = sys.argv[1:] if len(sys.argv) > 1 else [":0", ":1"]
POLL_INTERVAL = 0.5


def get_clipboard(display: str) -> bytes:
    try:
        return subprocess.check_output(
            ["xclip", "-display", display, "-selection", "clipboard", "-o"],
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return b""


def set_clipboard(display: str, data: bytes) -> None:
    p = subprocess.Popen(
        ["xclip", "-display", display, "-selection", "clipboard"],
        stdin=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    p.communicate(data)


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sync_loop() -> None:
    prev: dict[str, bytes] = {d: b"" for d in DISPLAYS}
    last_written: dict[str, str | None] = {d: None for d in DISPLAYS}

    while True:
        for src in DISPLAYS:
            content = get_clipboard(src)

            # Skip if empty, unchanged, or we wrote it ourselves
            if not content:
                continue
            if content == prev[src]:
                continue
            if content_hash(content) == last_written[src]:
                prev[src] = content
                continue

            # New content from this display — push to all others
            h = content_hash(content)
            for dst in DISPLAYS:
                if dst != src:
                    set_clipboard(dst, content)
                    last_written[dst] = h
                    prev[dst] = content

            prev[src] = content

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    print(f"Syncing clipboard across: {', '.join(DISPLAYS)}")
    print("Press Ctrl+C to stop.\n")
    try:
        sync_loop()
    except KeyboardInterrupt:
        print("Stopped.")
