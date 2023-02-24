import os
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def resource_path(another_way):
    try:
        usual_way = (
            sys._MEIPASS
        )  # When in .exe, this code is executed, that enters temporary directory that is created automatically during runtime.
    except Exception:
        usual_way = os.path.dirname(
            __file__
        )  # When the code in run from python console, it runs through this exception.
    return os.path.join(usual_way, another_way)


def test_driver1():
    options = Options()
    options.add_argument("--log-level=3")
    options.add_argument("--headless")
    options.add_argument(
        "User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"
    )

    driver = webdriver.Chrome(resource_path("./chrome89.exe"), options=options)

    driver.implicitly_wait(5)
