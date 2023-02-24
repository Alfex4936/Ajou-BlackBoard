import logging
from pathlib import Path

home = str(Path.home())  # "C:\Users\name"

logging.basicConfig(
    filename=f"{home}\\.ajou_bb",
    filemode="a",
    format="TIME %(asctime)s | %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG,
)


def test_log_one():
    logging.info("Running AjouBB")
    logging.warning("Loading notices")
    logging.error("Error loading videos")

    with open(f"{home}\\.ajou_bb", "r") as f:
        for line in f.readlines():
            print(line)


if __name__ == "__main__":
    test_log_one()
