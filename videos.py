import os
import re
import sys
import time
import urllib.request
from datetime import datetime
from operator import attrgetter
from random import random
from tempfile import TemporaryDirectory
from typing import List
from urllib.parse import quote

import win32api
import yaml
from selectolax.parser import HTMLParser
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class Video:
    __slots__ = ("name", "watched_time", "approve_time", "pf", "due_date")

    def __init__(self, name, watched_time, approve_time, pf, current_video_up):
        self.name = name
        self.watched_time = watched_time
        self.approve_time = approve_time
        self.pf = pf
        self.due_date = current_video_up

    def __repr__(self):
        return f"<Video name={self.name}, watched_time={self.watched_time}, self.approve_time={self.approve_time}>"

    def __bool__(self):
        return self.pf == "P"


def resource_path(another_way):
    try:
        usual_way = (
            sys._MEIPASS  # type: ignore
        )  # When in .exe, this code is executed, that enters temporary directory that is created automatically during runtime.
    except Exception:
        usual_way = os.path.dirname(
            __file__
        )  # When the code in run from python console, it runs through this exception.
    return os.path.join(usual_way, another_way)


class BlackBoard:
    with open("./univ.yaml") as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)

    CLEAR = lambda _: os.system("cls")
    PAUSE = lambda _: os.system("pause")
    LANG = conf["user"]["lang"]

    def __init__(self, options):
        if self.LANG == "ko":
            print("[1/3] ??????????????? ????????? ?????? ?????? ???...")
        else:
            print("[1/3] Entering Ajou website...")

        self.driver = webdriver.Chrome(
            service=Service(
                resource_path(
                    ChromeDriverManager(
                        log_level=0, cache_valid_range=1, print_first_line=False
                    ).install()
                )
            ),
            options=options,
        )
        self.driver.implicitly_wait(5)
        self.day = 0 if self.conf["user"]["day"] < 0 else self.conf["user"]["day"]

    def click_login(self):
        # driver.find_element_by_name("userId").send_keys(Config.bb_id)
        self.driver.find_element(By.NAME, "userId").send_keys(self.conf["user"]["id"])
        self.driver.find_element(By.NAME, "password").send_keys(self.conf["user"]["pw"])
        self.driver.find_element(By.XPATH, '//*[@id="loginSubmit"]').click()

    def init_ajou(self):
        # ????????? ???????????? ???????????? ???????????? ????????? ??????????????? ???
        try:
            self.driver.get(self.conf["link"]["bb"])
        except WebDriverException:
            if self.LANG == "ko":
                print("[ERR] ?????? ??????, ????????? ?????? ???????????????.")
            else:
                print("[ERR] Server Error, please try it again.")

            self.PAUSE()
            self.exit()
            sys.exit(1)

        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".btn-login"))
            )
        except Exception:
            self.exit()
            sys.exit(1)

        # ???????????????
        self.click_login()
        try:
            self.driver.switch_to.alert.accept()
        except:
            ...

        if self.LANG == "ko":
            print("[2/3] ????????? ??????...")
        else:
            print("[2/3] Logged in successfully...")

        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "course-org-list"))
        )

        if self.LANG == "ko":
            print("[3/3] ?????? ?????? ?????? ?????? ???...")
        else:
            print("[3/3] Loading my courses in this semester...")

        # ???????????? ?????? ??????
        now = datetime.now()
        assert self.conf["user"]["date"] != ""
        last_parsed = datetime.strptime(self.conf["user"]["date"], "%Y-%m-%d")

        if (
            not self.conf["user"]["cls"] or abs(last_parsed.month - now.month) > 0
        ):  # ??????????????? ?????? ??????
            # ?????? ?????? ???????????? ?????? ????????? ?????? ??????
            # self.driver.get(
            #     "https://eclass2.ajou.ac.kr/webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_2_1&forwardUrl=detach_module%2F_22_1%2F"
            # )

            self.driver.find_element_by_xpath(
                '//*[@id="main-content-inner"]/div/div[1]/div[1]/div/div/div[6]/div/div[1]/button[1]'
            ).send_keys(Keys.ENTER)

            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "course-org-list"))
            )

            time.sleep(1.5)

            html = self.driver.page_source
            soup = HTMLParser(html)
            courseTitles = soup.css("a > h4.js-course-title-element")
            courseUIDs = soup.css(
                "div.element-details.summary > div.multi-column-course-id"
            )

            courseIds = self.driver.find_elements(
                By.XPATH, '//*[contains(@id,"course-list-course-")]'
            )

            classes = []

            for link, uid, cid in zip(courseTitles, courseUIDs, courseIds):
                classes.append(
                    {
                        "uid": uid.text(strip=True),
                        "id": cid.get_attribute("id")[19:],
                        "name": " ".join(link.text(strip=True).split()[1:]),
                        "link": self.conf["link"]["web"] + cid.get_attribute("id")[19:],
                    }
                )

            self.conf["user"]["date"] = now.strftime("%Y-%m-%d")  # ex) 2021-12-31
            self.conf["user"]["cls"] = classes
            with open("univ.yaml", "w") as f:
                yaml.dump(self.conf, f)
            with open("./univ.yaml") as f:
                self.conf = yaml.load(f, Loader=yaml.FullLoader)

        del last_parsed
        self.CLEAR()
        if self.LANG == "ko":
            print("\n>>>>>-----< ????????? ?????? ?????? >-----<<<<<\n")
        else:
            print("\n>>>>>-----< VIDEO ATTENDANCE STATUS >-----<<<<<\n")

        # videos = sorted(self.get_attendance(), key=lambda x: x.due_date)
        videos = sorted(self.get_attendance(), key=attrgetter("due_date"))

        if self.LANG == "ko":
            print(f"# ????????? ?????? {len(videos)}???\n")
        else:
            print(f"# {len(videos)} videos to watch \n")

        for i, video in enumerate(videos, start=1):
            print(f"{i}. {video.name} ({video.watched_time}/{video.approve_time})")

        self.exit()
        self.PAUSE()

    def get_attendance(self):
        student_id = self.conf["user"]["student_id"]

        result = []

        for my_class in self.conf["user"]["cls"]:
            uid = my_class["uid"]
            # name = my_class["name"]

            with TemporaryDirectory() as temp:
                urllib.request.urlretrieve(
                    f"https://eclass2.ajou.ac.kr/webapps/bbgs-OnlineAttendance-BB5ff5398b9f3ea/excel?selectedUserId={student_id}&crs_batch_uid={uid}&title={student_id}&column={quote('????????????,??????,????????????,???????????????,??????????????????,???????????????,????????????????????????,?????????????????????(P/F)')}",
                    f"{temp}/temp.html",
                )

                result.extend(self.read_html(f"{temp}/temp.html"))

                time.sleep(random())
        return result

    def read_html(self, filename: str) -> List[Video]:
        result: List[Video] = []
        pattern = r"~ (\d+-\d+-\d+)"
        now = datetime.now()

        with open(filename, "r", encoding="utf-8") as f:
            soup = HTMLParser(f.read())
            titles = soup.css("tr > td:nth-child(3)")  # ????????????
            if not titles:
                return result
            studied_times = soup.css("tr > td:nth-child(4)")  # ????????? ??????
            approved_times = soup.css("tr > td:nth-child(5)")  # ?????? ?????? ??????
            pf_statuses = soup.css("tr > td:nth-child(8)")  # P/F

            for i in range(len(titles)):
                pf_status = pf_statuses[i].text(strip=True)
                title = titles[i].text(strip=True)

                if pf_status == "P":
                    continue
                current_video_due = datetime.strptime(
                    re.search(pattern, title).group(1), "%Y-%m-%d"
                )

                # current_video_up, current_video_due = datetime.strptime(
                #     dates[0], "%Y-%m-%d"
                # ), datetime.strptime(dates[1], "%Y-%m-%d")
                if (now - current_video_due).days > 0:
                    continue

                studied_time = studied_times[i].text(strip=True)
                if not studied_time:
                    if self.LANG == "ko":
                        studied_time = "0???"
                    else:
                        studied_time = "0s"
                approved_time = approved_times[i].text(strip=True)
                if self.LANG != "ko":
                    approved_time = approved_time.replace("??????", "h")
                    approved_time = approved_time.replace("???", "m")
                    approved_time = approved_time.replace("???", "s")

                result.append(
                    Video(
                        title,
                        studied_time,
                        approved_time,
                        pf_status,
                        current_video_due,
                    )
                )

                # print(f"?????????: {titles[i].text(strip=True)}")
                # print(
                #     f"\t????????? ??????: {studied_time} | ???????????? ??????: {approved_times[i].text(strip=True)} | {pf_status}"
                # )

        return result
        # operator.attrgetter("key") is faster on big arrays

    def exit(self):
        # print("\n?????? ???...")
        self.driver.close()
        self.driver.quit()
        return True


if __name__ == "__main__":
    #     if not Path("./univ.yaml").is_file():
    #         with open("univ.yaml", "a") as f:
    #             string = """link:
    #   bb: https://eclass2.ajou.ac.kr/ultra/course
    #   web: https://eclass2.ajou.ac.kr/webapps/blackboard/execute/announcement?method=search&context=course_entry&handle=announcements_entry&mode=view&course_id=
    # user:
    #   cls:
    #   id:
    #   pw:
    # """
    #             f.write(string)
    #             print("BB ???????????? ??????????????? ???????????? ?????? ???????????????.")
    #             exit(1)
    __version__ = "1.0.2"

    os.system(f"title Ajou BB video v{__version__}")

    options = Options()
    options.add_experimental_option(
        "excludeSwitches", ["enable-logging"]
    )  # Dev listening on...
    options.add_argument("--log-level=3")
    options.add_argument("--headless")
    options.add_argument(
        "User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
    )

    bb = BlackBoard(options)

    # windows?????? ?????? ??? ?????? ?????? ?????? ???
    win32api.SetConsoleCtrlHandler(bb.exit, True)

    bb.init_ajou()
