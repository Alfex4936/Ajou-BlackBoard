import locale
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timedelta
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
            print("[1/3] Entering ajou bb website...")

        dr = Service(
            resource_path(
                ChromeDriverManager(
                    log_level=0, cache_valid_range=1, print_first_line=False
                ).install()
            )
        )

        self.driver = webdriver.Chrome(
            service=dr,
            options=options,
        )
        self.driver.implicitly_wait(5)
        self.day = 0 if self.conf["user"]["day"] < 0 else self.conf["user"]["day"]

    def click_login(self):
        self.driver.find_element(By.NAME, "userId").send_keys(self.conf["user"]["id"])
        self.driver.find_element(By.NAME, "password").send_keys(self.conf["user"]["pw"])
        self.driver.find_element(By.XPATH, '//*[@id="loginSubmit"]').click()

    def get_notices(self):
        # 아주대 메인으로 이동하면 자동으로 로그인 홈페이지로 감
        try:
            self.driver.get(self.conf["link"]["bb"])
        except WebDriverException:
            if self.LANG == "ko":
                print("[ERR] 서버 오류, 나중에 다시 시도하세요.")
            else:
                print("[ERR] Server Error, please try it again.")
            self.exit()
            self.PAUSE()
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
        try:
            self.driver.switch_to.alert.accept()
        except:
            ...

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
            print("[3/3] Loading my courses in this semester...")

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

            try:
                self.driver.find_element(
                    By.XPATH,
                    '//*[@id="main-content-inner"]/div/div[1]/div[1]/div/div/div[6]/div/div[1]/button[1]',
                ).send_keys(Keys.ENTER)
            except Exception:
                ...

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

        # print(conf["user"]["cls"])

        diffDate = now - timedelta(self.day)

        totalPosts = 0
        self.CLEAR()
        dayMessage = f"{self.day}일" if self.day > 0 else "오늘"
        dayMessage = f"오늘부터 ~ {diffDate.month}월 {diffDate.day}일"
        print(f"\n\n\t>>> {dayMessage}까지 공지 불러오는 중...")

        for i, ajouCls in enumerate(self.conf["user"]["cls"]):
            posts = 0

            _, noticeLink, className, _ = ajouCls.values()
            self.driver.get(noticeLink)

            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located(
                        (By.ID, "courseMenuPalette_contents")
                    )
                )
                html = self.driver.page_source

                soup = HTMLParser(html)
                titles = soup.css("#announcementList > li > h3")
                contents = soup.css(
                    "#announcementList > li > div.details > div.vtbegenerated"
                )
                dates = soup.css("#announcementList > li > div.details > p > span")
            except Exception:
                self.exit()
                sys.exit(0)

            for title, content, date in zip(titles, contents, dates):
                date = date.text(strip=False)
                postDate = "".join(date.split()[2:5])
                if not postDate:
                    continue

                try:
                    parsedDate = datetime.strptime(postDate, "%Y년%m월%d일")
                except ValueError:  # 영문 강의 ex) September14,2021
                    postDate = "".join(date.split()[3:6])
                    # postDate = postDate.replace(",", "")
                    locale.setlocale(locale.LC_ALL, "en")
                    parsedDate = datetime.strptime(postDate, "%B%d,%Y")
                    locale.setlocale(locale.LC_ALL, "Korean_Korea")

                if (now - parsedDate).days <= self.day:
                    totalPosts += 1
                    posts += 1
                    print()
                    print(f">>>>>----- {posts}번째 공지")
                    print(f"\n{className}: {title.text(strip=True)}")
                    print()
                    print(f"링크: {noticeLink}")
                    print(
                        content.text(strip=False)
                        # .encode("utf-8", "ignore")
                        # .decode("utf-8")  emoji는 가능하나, conhost에서 자체적으로 chcp 65001을 해야함
                    )
                    print(f"{date}\n")
                    print("-" * 50)
                    # Notification(
                    #     title=f"\n{className}: {title.text(strip=True)}",
                    #     description=content.text(strip=False),
                    #     icon_path="./ico/ms-icon-310x310.ico",  # On Windows .ico is required, on Linux - .png
                    #     duration=None,  # forever
                    #     callback_on_click=lambda: webbrowser.open(
                    #         "https://eclass2.ajou.ac.kr/ultra/course"
                    #     )
                    #     # urgency="normal",
                    # ).send()
                else:
                    break
            self.conf["user"]["cls"][i]["posts"] = posts  # 각 강의마다 공지 몇 개인지 체크

        # div.name > ng-switch > a

        if totalPosts == 0:
            self.CLEAR()
            print(f"\n\n\t{dayMessage} 이내 공지가 없네요!!!\n")
        else:
            print(f"총 {totalPosts}개의 공지")
            for lesson in self.conf["user"]["cls"]:
                _, noticeLink, className, _, post = lesson.values()
                if post > 0:
                    print(f" └ {className}: {post}개의 공지")
            print()

        # self.PAUSE()
        self.get_todos()
        self.get_attendance()
        self.exit()
        self.PAUSE()
        sys.exit(0)

    def get_todos(self):
        # self.CLEAR()

        # print("\n\n해야할 목록을 불러오는 중...")
        print("\n>>>>>-----< 제공 예정 >-----<<<<<\n")
        self.driver.get("https://eclass2.ajou.ac.kr/ultra/stream")
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".js-title-link"))
            )
        except Exception:
            self.exit()
            sys.exit(1)

        html = self.driver.page_source
        soup = HTMLParser(html)
        dueContents = soup.css(
            "div.js-upcomingStreamEntries > ul > li > div > div > div > div > div.name > ng-switch > a"
        )
        dueDates = soup.css(
            "div.js-upcomingStreamEntries > ul > li > div > div > div > div > div.content > span > bb-translate > bdi"
        )
        classNames = soup.css(
            "div.js-upcomingStreamEntries > ul > li > div > div > div > div > div.context.ellipsis > a"
        )
        # self.CLEAR()

        n = len(dueContents)
        for i in range(n):
            print(classNames[i].text(strip=False))
            print("\t" + dueContents[i].text(strip=False))
            print("\t지정 마감일:" + dueDates[i].text(strip=False))
            print()
        if n == 0:
            print("\n\t모든 할 일을 끝냈습니다.")

    def get_attendance(self):
        if self.LANG == "ko":
            print("\n>>>>>-----< 동영상 출석 현황 >-----<<<<<\n")
        else:
            print("\n>>>>>-----< VIDEO ATTENDANCE STATUS >-----<<<<<\n")

        videos = sorted(self.__get_attendance(), key=attrgetter("due_date"))

        if self.LANG == "ko":
            print(f"# 봐야할 영상 {len(videos)}개\n")
        else:
            print(f"# {len(videos)} videos to watch \n")

        for i, video in enumerate(videos, start=1):
            print(f"{i}. {video.name} ({video.watched_time}/{video.approve_time})")

    def __get_attendance(self):
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
            soup = HTMLParser(f.read())
            titles = soup.css("tr > td:nth-child(3)")  # 컨텐츠명
            if not titles:
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
                if (now - current_video_due).days > 0:
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
    __version__ = "1.0.8"

    os.system(f"title 아주대학교 블랙보드 v{__version__}")

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

    # windows에서 콘솔 앱 종료 버튼 누를 때
    win32api.SetConsoleCtrlHandler(bb.exit, True)

    bb.get_notices()
