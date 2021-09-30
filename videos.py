import os
import re
import sys
import time
import urllib.request
from datetime import datetime
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
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class Video:
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
            print("[1/3] 아주대학교 사이트 접속 하는 중...")
        else:
            print("[1/3] Entering Ajou website...")

        self.driver = webdriver.Chrome(
            resource_path(
                ChromeDriverManager(
                    log_level=0, cache_valid_range=1, print_first_line=False
                ).install()
            ),
            options=options,
        )
        self.driver.implicitly_wait(5)
        self.day = 0 if self.conf["user"]["day"] < 0 else self.conf["user"]["day"]

    def click_login(self):
        # driver.find_element_by_name("userId").send_keys(Config.bb_id)
        self.driver.find_element_by_name("userId").send_keys(self.conf["user"]["id"])
        self.driver.find_element_by_name("password").send_keys(self.conf["user"]["pw"])
        self.driver.find_element_by_xpath('//*[@id="loginSubmit"]').click()

    def init_ajou(self):
        # 아주대 메인으로 이동하면 자동으로 로그인 홈페이지로 감
        try:
            self.driver.get(self.conf["link"]["bb"])
        except WebDriverException:
            if self.LANG == "ko":
                print("[ERR] 서버 오류, 나중에 다시 시도하세요.")
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

        # 로그인하기
        self.click_login()
        if self.LANG == "ko":
            print("[2/3] 로그인 완료...")
        else:
            print("[2/3] Logged in successfully...")

        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "course-org-list"))
        )

        if self.LANG == "ko":
            print("[3/3] 수강 중인 강의 정리 중...")
        else:
            print("[3/3] Organizing my lectures...")

        # 한달마다 강의 체크
        now = datetime.now()
        assert self.conf["user"]["date"] != ""
        last_parsed = datetime.strptime(self.conf["user"]["date"], "%Y-%m-%d")

        if (
            not self.conf["user"]["cls"] or abs(last_parsed.month - now.month) > 0
        ):  # 비어있거나 매달 체크
            # 수강 중인 클래스를 쉽게 모으기 위해 이동
            # self.driver.get(
            #     "https://eclass2.ajou.ac.kr/webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_2_1&forwardUrl=detach_module%2F_22_1%2F"
            # )

            self.driver.find_element_by_xpath(
                '//*[@id="main-content-inner"]/div/div[1]/div[1]/div/div/div[5]/div/div[1]/button[1]'
            ).send_keys(Keys.ENTER)

            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "course-org-list"))
            )

            time.sleep(1.5)

            html = self.driver.page_source
            soup = HTMLParser(html, "html.parser")
            courseTitles = soup.css("a > h4.js-course-title-element")
            courseUIDs = soup.css(
                "div.element-details.summary > div.multi-column-course-id"
            )

            courseIds = self.driver.find_elements_by_xpath(
                '//*[contains(@id,"course-list-course-")]'
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
            time.sleep(1)

        del last_parsed
        self.CLEAR()
        if self.LANG == "ko":
            print("\n>>>>>-----< 동영상 출석 현황 >-----<<<<<\n")
        else:
            print("\n>>>>>-----< VIDEO ATTENDANCE STATUS >-----<<<<<\n")

        videos = sorted(self.get_attendance(), key=lambda x: x.due_date)

        if self.LANG == "ko":
            print(f"# 봐야할 영상 {len(videos)}개\n")
        else:
            print(f"# {len(videos)} videos to watch \n")

        for i, video in enumerate(videos, start=1):
            print(f"{i}. {video.name} ({video.watched_time}/{video.approve_time})")

        self.PAUSE()
        self.exit()

    def get_attendance(self):
        student_id = self.conf["user"]["student_id"]

        result = []

        for my_class in self.conf["user"]["cls"]:
            uid = my_class["uid"]
            # name = my_class["name"]

            with TemporaryDirectory() as temp:
                urllib.request.urlretrieve(
                    f"https://eclass2.ajou.ac.kr/webapps/bbgs-OnlineAttendance-BB5ff5398b9f3ea/excel?selectedUserId={student_id}&crs_batch_uid={uid}&title={student_id}&column={quote('사용자명,위치,컨텐츠명,학습한시간,학습인정시간,컨텐츠시간,온라인출석진도율,온라인출석상태(P/F)')}",
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
            soup = HTMLParser(f.read(), "html.parser")
            titles = soup.css("tr > td:nth-child(3)")  # 컨텐츠명
            if not len(titles):
                return result
            studied_times = soup.css("tr > td:nth-child(4)")  # 학습한 시간
            approved_times = soup.css("tr > td:nth-child(5)")  # 학습 인정 시간
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
                if current_video_due < now:
                    continue

                studied_time = studied_times[i].text(strip=True)
                if not studied_time:
                    if self.LANG == "ko":
                        studied_time = "0초"
                    else:
                        studied_time = "0s"
                approved_time = approved_times[i].text(strip=True)
                if self.LANG != "ko":
                    approved_time = approved_time.replace("시간", "h")
                    approved_time = approved_time.replace("분", "m")
                    approved_time = approved_time.replace("초", "s")

                result.append(
                    Video(
                        title,
                        studied_time,
                        approved_time,
                        pf_status,
                        current_video_due,
                    )
                )

                # print(f"동영상: {titles[i].text(strip=True)}")
                # print(
                #     f"\t학습한 시간: {studied_time} | 학습인정 시간: {approved_times[i].text(strip=True)} | {pf_status}"
                # )

        return result
        # operator.attrgetter("key") is faster on big arrays

    def exit(self):
        # print("\n종료 중...")
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
    #             print("BB 아이디와 비밀번호를 입력하고 다시 실행하세요.")
    #             exit(1)
    __version__ = "1.0.0"

    os.system(f"title Ajou BB v{__version__}")

    options = Options()
    options.add_experimental_option(
        "excludeSwitches", ["enable-logging"]
    )  # Dev listening on...
    options.add_argument("--log-level=3")
    options.add_argument("--headless")
    options.add_argument(
        "User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"
    )

    bb = BlackBoard(options)

    # windows에서 콘솔 앱 종료 버튼 누를 때
    win32api.SetConsoleCtrlHandler(bb.exit, True)

    bb.init_ajou()
