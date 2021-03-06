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

    ORDINAL = lambda _, n: "%d%s" % (
        n,
        "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10 :: 4],
    )
    CLEAR = lambda _: os.system("cls")
    PAUSE = lambda _: os.system("pause")
    LANG = conf["user"]["lang"]

    def __init__(self, options):
        if self.LANG == "ko":
            print("[1/3] ??????????????? ????????? ?????? ?????? ???...")
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
        # ????????? ???????????? ???????????? ???????????? ????????? ??????????????? ???
        try:
            self.driver.get(self.conf["link"]["bb"])
        except WebDriverException:
            if self.LANG == "ko":
                print("[ERR] ?????? ??????, ????????? ?????? ???????????????.")
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

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            "button[ng-click='baseCourses.slideToPrevTerm()']",
                        )
                    )
                )
                self.driver.find_element(
                    By.CSS_SELECTOR, "button[ng-click='baseCourses.slideToPrevTerm()']"
                ).click()
            except Exception:
                ...

            courseTitles, courseUIDs, courseIds = self.__load_classes()

            while not courseTitles or not courseUIDs or not courseIds:
                courseTitles, courseUIDs, courseIds = self.__load_classes()

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

        # time.sleep(3)
        # self.exit()
        # sys.exit(0)

        del last_parsed
        diffDate = now - timedelta(self.day)

        totalPosts = 0
        self.CLEAR()
        if self.LANG == "ko":
            dayMessage = f"{self.day}???" if self.day > 0 else "??????"
            dayMessage = f"???????????? ~ {diffDate.month}??? {diffDate.day}???"
        else:
            import calendar

            dayMessage = f"{self.day}???" if self.day > 0 else "??????"
            dayMessage = f"from Today to {calendar.month_abbr[diffDate.month]} {self.ORDINAL(diffDate.day)}"

        if self.LANG == "ko":
            print(f"\n\n\t>>> {dayMessage}?????? ?????? ???????????? ???...")
        else:
            print(f"\n\n\t>>> Loading {dayMessage}...")

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
                    parsedDate = datetime.strptime(postDate, "%Y???%m???%d???")
                except ValueError:  # ?????? ?????? ex) September14,2021
                    postDate = "".join(date.split()[3:6])
                    # postDate = postDate.replace(",", "")
                    locale.setlocale(locale.LC_ALL, "en")
                    parsedDate = datetime.strptime(postDate, "%B%d,%Y")
                    locale.setlocale(locale.LC_ALL, "Korean_Korea")

                if (now - parsedDate).days <= self.day:
                    totalPosts += 1
                    posts += 1
                    print()
                    if self.LANG == "ko":
                        print(f">>>>>----- {className} - {posts}?????? ??????")
                    else:
                        print(f">>>>>----- {self.ORDINAL(posts)} notice of {className}")
                    print(f"\n{className}: {title.text(strip=True)}")
                    print()
                    if self.LANG == "ko":
                        print(f"??????: {noticeLink}")
                    else:
                        print(f"Link: {noticeLink}")
                    print(
                        content.text(strip=False)
                        # .encode("utf-8", "ignore")
                        # .decode("utf-8")  emoji??? ????????????, conhost?????? ??????????????? chcp 65001??? ?????????
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
            self.conf["user"]["cls"][i]["posts"] = posts  # ??? ???????????? ?????? ??? ????????? ??????

        # div.name > ng-switch > a

        if totalPosts == 0:
            self.CLEAR()
            if self.LANG == "ko":
                print(f"\n\n\t{dayMessage} ?????? ????????? ?????????!!!\n")
            else:
                print(f"\n\n\tNo posts during {dayMessage}!!!\n")
        else:
            if self.LANG == "ko":
                print(f"??? {totalPosts}?????? ??????")
            else:
                print(f"Total {totalPosts} notices")
            for lesson in self.conf["user"]["cls"]:
                _, noticeLink, className, _, post = lesson.values()
                if post > 0:
                    if self.LANG == "ko":
                        print(f" ??? {className}: {post}?????? ??????")
                    else:
                        if post == 1:
                            print(f" ??? {className}: {post} notice")
                        else:
                            print(f" ??? {className}: {post} notices")
            print()

        # self.PAUSE()
        self.get_todos()
        self.get_attendance()
        self.exit()
        self.PAUSE()
        sys.exit(0)

    def __load_classes(self):
        html = self.driver.page_source
        soup = HTMLParser(html)
        courseTitles = soup.css("a > h4.js-course-title-element")
        courseUIDs = soup.css(
            "div.element-details.summary > div.multi-column-course-id"
        )  # grid

        if not courseUIDs:  # list
            courseUIDs = soup.css(
                "div.element-details.summary > div.small-12 > div > span"
            )

        courseIds = self.driver.find_elements(
            By.XPATH, '//*[contains(@id,"course-list-course-")]'
        )

        try:
            courseIds[0].get_attribute("id")
        except Exception:
            return self.__load_classes()

        return courseTitles, courseUIDs, courseIds

    def get_todos(self):
        # self.CLEAR()

        # print("\n\n????????? ????????? ???????????? ???...")
        if self.LANG == "ko":
            print("\n>>>>>-----< ?????? ?????? >-----<<<<<\n")
        else:
            print("\n>>>>>-----< TO-DO >-----<<<<<\n")

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
            if self.LANG == "ko":
                print("\t?????? ?????????: " + dueDates[i].text(strip=False))
            else:
                print("\tDue: " + dueDates[i].text(strip=False))
            print()
        if n == 0:
            if self.LANG == "ko":
                print("\n\t?????? ??? ?????? ???????????????.")
            else:
                print("\n\tNothing to do.")

    def get_attendance(self):
        if self.LANG == "ko":
            print("\n>>>>>-----< ????????? ?????? ?????? >-----<<<<<\n")
        else:
            print("\n>>>>>-----< VIDEO ATTENDANCE STATUS >-----<<<<<\n")

        videos = sorted(self.__get_attendance(), key=attrgetter("due_date"))

        if self.LANG == "ko":
            print(f"# ????????? ?????? {len(videos)}???\n")
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
    __version__ = "1.0.9"

    os.system("chcp 65001 > nul")
    os.system(f"title Ajou BlackBoard v{__version__}")

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

    bb.get_notices()
