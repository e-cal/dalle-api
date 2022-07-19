import sys
import time
from enum import Enum

LOADING_STYLES = [
    "dots",
    "spinner",
    "braille",
    "counter",
]


class LoadingMsg:
    def __init__(self, msg: str, style: str, delay=0.3) -> None:
        if style not in LOADING_STYLES:
            raise Exception(
                f"Loading style \"{style}\" not supported. Supported styles: {', '.join(LOADING_STYLES)}."
            )

        self.msg = msg
        self.delay = delay

        self.generator = (
            self.dots_generator()
            if style == "dots"
            else self.spinner_generator("/-\\|")
            if style == "spinner"
            else self.spinner_generator("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
            if style == "braille"
            else self.counter()
        )

    def dots_generator(self):
        while True:
            for i in range(4):
                yield self.msg + ("." * i) + (" " * (3 - i))

    def spinner_generator(self, chars):
        while True:
            for c in chars:
                yield self.msg + " " + c

    def counter(self):
        i = 0
        while True:
            yield self.msg + ("." * i)
            i += 1

    def print(self):
        msg = next(self.generator)
        sys.stdout.write(msg)
        sys.stdout.flush()
        time.sleep(self.delay)
        sys.stdout.write("\b" * (len(msg) + 1))


if __name__ == "__main__":
    loader = LoadingMsg("Generating images", "braille")
    while True:
        loader.print()
