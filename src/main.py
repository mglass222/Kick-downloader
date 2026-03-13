"""Entry point for the Kick Stream Recorder application."""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def main() -> None:
    from .gui.app import App

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
