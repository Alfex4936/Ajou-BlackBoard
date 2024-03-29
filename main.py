import os
import re
import sys
from concurrent import futures
from datetime import datetime, timedelta
from locale import LC_ALL, setlocale
from operator import attrgetter
from tempfile import TemporaryDirectory
from typing import Dict, List
from urllib.parse import quote
from urllib.request import urlretrieve

import win32api
import yaml
from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.theme import Theme
from selectolax.parser import HTMLParser
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.driver_cache import DriverCacheManager

os.environ["WDM_LOG"] = "0"
# Constants
PL = sys.platform
LANG = "ko"  # Set your language preference here


# class NoticeHighlighter(RegexHighlighter):
#     """My custom highlighter for AjouBB"""

#     base_style = "csw."
#     highlights = [
#         r"(?P<email>[\w-]+@([\w-]+\.)+[\w-]+)",
#         r"(?P<student_id>\d{9})",  # 202209301
#         r"(?P<number>\d*번째 공지)",
#         r"(?P<url>(file|https|http|ws|wss)://[-0-9a-zA-Z$_+!`(),.?/;:&=%#]*)",
#         r"(?P<date>[0-9]+월.[0-9]+일(\s\(.*\))?)",  # 10월31일 (월)
#         r"(?P<time>\d{1,2}:\d{1,2})",
#         r"(?P<total_notice>총.*공지)",
#         r"(?P<per_course>(?<=└ ).*)",  # └ 강좌(X-1): 5개의 공지
#         r"(?P<class_name>(?<=----- ).*\))",  # >>>>>----- "CLASS(ABC-1)"
#         r"(?P<bold_green>제공 예정|동영상 출석 현황|.요일|출석|기말|중간|과제|주제|조별|발표|성적|마감일|휴강|보강|마감일)",
#         r"(?P<bold_red>결석|마감일|Due|적발|채점|않음|오류)",
#     ]


# theme = Theme(
#     {
#         "csw.email": "bold red",
#         "csw.student_id": "bold red",
#         "csw.url": "bold blue",
#         "csw.date": "bold yellow",
#         "csw.time": "bold yellow",
#         "csw.number": "bold green",
#         "csw.total_notice": "bold red",
#         "csw.per_course": "bold green",
#         "csw.class_name": "bold bright_cyan",
#         "csw.bold_green": "bold green",
#         "csw.bold_red": "bold red",
#     }
# )


class NoticeHighlighter(RegexHighlighter):
    """My custom highlighter for AjouBB"""

    base_style = "csw."
    highlights = [
        r"(?P<email>[\w-]+@([\w-]+\.)+[\w-]+)",
        r"(?P<student_id>\d{9})",
        r"(?P<number>\d*번째 공지)",
        r"(?P<url>(file|https|http|ws|wss)://[-0-9a-zA-Z$_+!`(),.?/;:&=%#]*)",
        r"(?P<date>[0-9]+월.[0-9]+일(\s\(.*\))?)",
        r"(?P<time>\d{1,2}:\d{1,2})",
        r"(?P<total_notice>총.*공지)",
        r"(?P<per_course>(?<=└ ).*)",
        r"(?P<class_name>(?<=----- ).*\))",
        r"(?P<important_green>제공 예정|동영상 출석 현황|.요일|출석|기말|중간|과제|주제|조별|발표|성적|마감일|휴강|보강)",
        r"(?P<important_red>결석|마감일|Due|적발|채점|않음|오류)",
        r"(?P<course_list>내 수업 목록:)",
        r"(?P<course_name>\b[\w가-힣]+과[가-힣]+\([\w-]+\)\b)",  # For course names like 자기이해와 진로탐색(X564-1)
        r"(?P<course_code>\([\w-]+\))",  # For course codes like (X564-1)
        r"(?P<special_action>봐야할 영상|모든 할 일을 끝냈습니다\.)",  # For special actions or notices
    ]


theme = Theme(
    {
        "csw.email": "bold magenta",
        "csw.student_id": "bold magenta",
        "csw.url": "blue",
        "csw.date": "italic yellow",
        "csw.time": "yellow",
        "csw.number": "bold green",
        "csw.total_notice": "bold red",
        "csw.per_course": "green",
        "csw.class_name": "bold cyan",
        "csw.important_green": "bold green",
        "csw.important_red": "bold red",
        "csw.course_list": "bold underline",
        "csw.course_name": "bold bright_white",
        "csw.course_code": "italic bright_yellow",
        "csw.special_action": "bold bright_magenta",
    }
)

console = Console(highlighter=NoticeHighlighter(), theme=theme)


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


def resource_path(another_way: str) -> str:
    try:
        usual_way = sys._MEIPASS  # type: ignore
    except Exception:
        usual_way = os.path.dirname(__file__)
    return os.path.join(usual_way, another_way)


class BlackBoard:
    BB_LINK = "https://eclass2.ajou.ac.kr/ultra/course"
    CLASS_LINK = "https://eclass2.ajou.ac.kr/webapps/blackboard/execute/announcement?method=search&context=course_entry&handle=announcements_entry&mode=view&course_id="

    def __init__(self, options):
        with open("./univ.yaml") as f:
            self.conf = yaml.load(f, Loader=yaml.FullLoader)

        self.LANG = self.conf["user"]["lang"]
        if self.LANG == "ko":
            print("[1/3] 아주대학교 사이트 접속 하는 중...")
        else:
            print("[1/3] Entering ajou bb website...")

        dr = Service(
            resource_path(
                ChromeDriverManager(
                    cache_manager=DriverCacheManager(valid_range=1)
                ).install()
            )
        )

        self.driver = webdriver.Chrome(
            service=dr,
            options=options,
        )
        self.driver.implicitly_wait(5)
        self.day = 0 if self.conf["user"]["day"] < 0 else self.conf["user"]["day"]
        self.now = datetime.now()

    def run(self):
        # 사이트 로딩
        # 아주대 메인으로 이동하면 자동으로 로그인 홈페이지로 감
        try:
            self.driver.get(self.BB_LINK)
        except WebDriverException:
            if self.LANG == "ko":
                print("[ERR] 서버 오류, 나중에 다시 시도하세요.")
            else:
                print("[ERR] Server Error, please try it again.")
            self.exit()
            self.pause_console()
            sys.exit(1)

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".btn-login"))
            )
        except Exception:
            self.exit()
            sys.exit(1)

        # 로그인하기
        is_good_id = self.click_login()
        if not is_good_id:
            print(f"[ERROR] {self.driver.switch_to.alert.text}")
            self.driver.switch_to.alert.accept()
            self.exit()
            self.pause_console()
            sys.exit(1)
        try:  # 중복된 로그인
            self.driver.switch_to.alert.accept()
        except Exception:
            ...

        if self.LANG == "ko":
            print("[2/3] 로그인 완료...")
        else:
            print("[2/3] Logged in successfully...")

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

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.last-item"))
            )
        except Exception:
            self.exit()
            sys.exit(1)

        self.driver.execute_script(
            'document.querySelector("#main-content-inner").scrollTo(0, document.body.scrollHeight)'
        )

        # 사이트 로딩 done

        self.get_notices()
        self.get_todos()
        self.get_attendance()

        from notifypy import Notify

        notification = Notify(
            default_notification_title="로딩이 끝났습니다.",
            default_notification_message="Made by CSW",
            default_notification_application_name="Ajou University",
        )
        notification.send(block=False)

        self.exit()
        self.pause_console()
        sys.exit(0)

    def debug(self):
        # 아주대 메인으로 이동하면 자동으로 로그인 홈페이지로 감
        try:
            self.driver.get(self.BB_LINK)
        except WebDriverException:
            if self.LANG == "ko":
                print("[ERR] 서버 오류, 나중에 다시 시도하세요.")
            else:
                print("[ERR] Server Error, please try it again.")
            self.exit()
            self.pause_console()
            sys.exit(1)

        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".btn-login"))
            )
        except Exception:
            self.exit()
            self.pause_console()
            sys.exit(1)

        # 로그인하기
        is_good_id = self.click_login()
        if not is_good_id:
            print(self.driver.switch_to.alert.text)
            self.driver.switch_to.alert.accept()
            self.exit()
            self.pause_console()
            sys.exit(1)
        try:
            self.driver.switch_to.alert.accept()
        except:
            ...

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

        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.last-item"))
            )
        except Exception:
            self.exit()
            sys.exit(1)

        # time.sleep(1)

        self.driver.execute_script(
            'document.querySelector("#main-content-inner").scrollTo(0, document.body.scrollHeight)'
        )

        with open("./selenium.html", "w") as f:
            f.write(self.driver.page_source)

        self.driver.save_screenshot("selenium.png")

        self.__reset_yaml()
        self.__update_yaml()

        self.exit()
        self.pause_console()
        sys.exit(0)

    def to_ordinal(self, n):
        return "%d%s" % (
            n,
            "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10 :: 4],
        )

    def clear_console(self):
        os.system("cls" if PL == "win32" else "clear")

    def pause_console(self):
        os.system(
            "pause"
            if PL == "win32"
            else "/bin/bash -c \"read -sp 'Press [Enter] to finish\n' -n 1 key\""
        )

    def get_notices(self):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "course-org-list"))
        )

        if self.LANG == "ko":
            print("[3/3] 수강 중인 강의 정리 중...")
        else:
            print("[3/3] Loading my courses in this semester...")

        # 한달마다 강의 체크
        assert self.conf["user"]["date"] != ""
        last_parsed = datetime.strptime(self.conf["user"]["date"], "%Y-%m-%d")

        if (
            not self.conf["user"]["cls"] or abs(last_parsed.month - self.now.month) > 0
        ):  # 비어있거나 매달 체크, 수강 중인 클래스를 쉽게 모으기 위해 이동
            self.__update_yaml()

        del last_parsed
        diffDate = self.now - timedelta(self.day)

        total_posts = 0
        self.clear_console()

        if self.LANG == "ko":
            dayMessage = f"{self.day}일" if self.day > 0 else "오늘"
            dayMessage = f"{diffDate.month}월 {diffDate.day}일부터 ~ 오늘"
        else:
            import calendar

            dayMessage = f"{self.day}일" if self.day > 0 else "오늘"
            dayMessage = f"from {calendar.month_abbr[diffDate.month]} {self.to_ordinal(diffDate.day)} to Today"

            del calendar

        if self.LANG == "ko":
            print(f"\n\n\t>>> {dayMessage}까지 공지 불러오는 중...")
        else:
            print(f"\n\n\t>>> Loading {dayMessage}...")

        sum_classes_have_notices = 0

        for i, ajouCls in enumerate(self.conf["user"]["cls"]):
            posts = 0

            _, noticeLink, className, _ = ajouCls.values()
            self.driver.get(noticeLink)

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.ID, "courseMenuPalette_contents")
                    )
                )
                html = self.driver.page_source

                soup = HTMLParser(str.replace(html, "<br>", "\n", -1))
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

                contained_links: Dict[str, str] = dict()

                for node in content.iter():
                    href = node.css_first("a")
                    if href:
                        contained_links[node.text(strip=True)[:10] + "..."] = href.attrs["href"]  # type: ignore

                try:
                    parsedDate = datetime.strptime(postDate, "%Y년%m월%d일")
                except ValueError:  # 영문 강의 ex) September14,2021
                    postDate = "".join(date.split()[3:6])
                    # postDate = postDate.replace(",", "")
                    setlocale(LC_ALL, "en")
                    parsedDate = datetime.strptime(postDate, "%B%d,%Y")
                    setlocale(LC_ALL, "Korean_Korea")

                if (self.now - parsedDate).days <= self.day:
                    total_posts += 1
                    posts += 1
                    print()
                    if self.LANG == "ko":
                        console.print(f">>>>>----- {className} - {posts}번째 공지")
                    else:
                        console.print(
                            f">>>>>----- [red]{self.to_ordinal(posts)}[/red] notice of [bold bright_cyan]{className}[/bold bright_cyan]"
                        )
                    print(f"\n{className}: {title.text(strip=True)}")
                    print()
                    if self.LANG == "ko":
                        console.print(f"링크: {noticeLink}")
                    else:
                        console.print(f"Link: {noticeLink}")

                    console.print(
                        content.text(strip=False)
                        # .encode("utf-8", "ignore")
                        # .decode("utf-8")  emoji는 가능하나, conhost에서 자체적으로 chcp 65001을 해야함
                    )
                    links = "\n".join(
                        list(
                            f"\t{text} \[ {link} ]"  # [something] doesn't print
                            for (text, link) in contained_links.items()
                        )
                    )
                    # print(f"\n포함된 링크:\n{links if links else '없음'}\n")
                    console.print(f"\n포함된 링크:\n{links if links else '없음'}\n")
                    console.print(f"{date}\n")
                    print("-" * 50)
                else:
                    break
            if posts > 0:
                sum_classes_have_notices += 1
            self.conf["user"]["cls"][i]["posts"] = posts  # 각 강의마다 공지 몇 개인지 체크

        # div.name > ng-switch > a

        if total_posts == 0:
            self.clear_console()
            if self.LANG == "ko":
                print(f"\n\n\t{dayMessage} 이내 공지가 없네요!!!\n")
            else:
                print(f"\n\n\tNo posts during {dayMessage}!!!\n")
        else:
            if self.LANG == "ko":
                console.print(f"총 {sum_classes_have_notices}개의 수업에서 {total_posts}개의 공지")
            else:
                print(f"Total {total_posts} notices")
            for lesson in self.conf["user"]["cls"]:
                _, noticeLink, className, _, post = lesson.values()
                if post > 0:
                    if self.LANG == "ko":
                        console.print(f" └ {className}: {post}개의 공지")
                    else:
                        if post == 1:
                            console.print(f" └ {className}: {post} notice")
                        else:
                            console.print(f" └ {className}: {post} notices")
            print()

        print("\n내 수업 목록:")
        for my_class in self.conf["user"]["cls"]:
            _, _, class_name, _, _ = my_class.values()  # here, posts
            print(f"\t{class_name}")
        print()

        # self.pause_console()

    def click_login(self) -> bool:
        self.driver.find_element(By.NAME, "userId").send_keys(self.conf["user"]["id"])
        self.driver.find_element(By.NAME, "password").send_keys(self.conf["user"]["pw"])
        self.driver.find_element(By.XPATH, '//*[@id="loginSubmit"]').click()
        # alert 뜨면 틀린 비번
        try:
            alert_msg = self.driver.switch_to.alert.text
            if "틀렸습니다" in alert_msg or "아닙니다" in alert_msg:
                return False
        except:
            ...
        return True

    @staticmethod
    def __reset_yaml():
        # if not Path("./univ.yaml").is_file():
        with open("./univ.yaml", "w") as f:
            string = """user:
    cls:
    date: '2022-01-01'
    day: 3
    id: 아이디
    pw: 비밀번호
    lang: ko
    student_id: 학번
"""
            f.write(string)

    def __update_yaml(self):
        courseTitles, courseUIDs, courseIds = self.__load_classes()

        while not courseTitles or not courseUIDs or not courseIds:
            courseTitles, courseUIDs, courseIds = self.__load_classes()

        classes = list(
            {
                "uid": uid.text(strip=True),
                "id": cid.get_attribute("id")[19:],
                "name": " ".join(link.text(strip=True).split()[1:]),
                "link": self.CLASS_LINK + cid.get_attribute("id")[19:],
            }
            for link, uid, cid in zip(courseTitles, courseUIDs, courseIds)
        )  # tuple causes !!python: tuple

        self.conf["user"]["date"] = self.now.strftime("%Y-%m-%d")  # ex) 2021-12-31
        self.conf["user"]["cls"] = classes
        with open("./univ.yaml", "w") as f:
            yaml.dump(self.conf, f)
            # time.sleep(1)

        with open("./univ.yaml") as f:
            self.conf = yaml.load(f, Loader=yaml.FullLoader)

    def __load_classes(self):
        html = self.driver.page_source
        # print(html)
        soup = HTMLParser(html)
        courseTitles = soup.css("a > h4.js-course-title-element")
        courseUIDs = soup.css(
            "div.element-details.summary > div.multi-column-course-id"
        )  # grid

        # for title in courseTitles:
        #     # print(str.encode(title.text(strip=True)))
        #     if title.text(strip=True) == "":
        #         time.sleep(1)
        #         return self.__load_classes()

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
        # self.clear_console()

        # print("\n\n해야할 목록을 불러오는 중...")
        if self.LANG == "ko":
            console.print("\n>>>>>-----< 제공 예정 >-----<<<<<\n")
        else:
            print("\n>>>>>-----< TO-DO >-----<<<<<\n")

        self.driver.get("https://eclass2.ajou.ac.kr/ultra/stream")
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.empty-note"))
            )
        except Exception:
            ...  # ignore
        else:
            if self.LANG == "ko":
                print("\n\t모든 할 일을 끝냈습니다.")
            else:
                print("\n\tNothing to do.")
            return

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
        # self.clear_console()

        n = len(dueContents)
        for i in range(n):
            print(classNames[i].text(strip=False))
            print("\t" + dueContents[i].text(strip=False))
            if self.LANG == "ko":
                console.print("\t지정 마감일: " + dueDates[i].text(strip=False))
            else:
                console.print("\tDue: " + dueDates[i].text(strip=False))
            print()
        if n == 0:
            if self.LANG == "ko":
                print("\n\t모든 할 일을 끝냈습니다.")
            else:
                print("\n\tNothing to do.")

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
        classes = self.conf["user"]["cls"]
        result = []

        with futures.ThreadPoolExecutor(max_workers=len(classes)) as exec:
            for my_class in classes:
                exec.submit(self.__multithread_load, student_id, my_class, result)

        return result

    def read_html(self, filename: str) -> List[Video]:
        result: List[Video] = []
        pattern = r"~ (\d+-\d+-\d+)"

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
                p = re.search(pattern, title)
                if p is None:
                    continue
                current_video_due = datetime.strptime(p.group(1), "%Y-%m-%d")

                # current_video_up, current_video_due = datetime.strptime(
                #     dates[0], "%Y-%m-%d"
                # ), datetime.strptime(dates[1], "%Y-%m-%d")
                if (self.now - current_video_due).days > 0:
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

    def __multithread_load(
        self, student_id: str, a_class: Dict[str, str], result: List[Video]
    ) -> None:
        uid = a_class["uid"]

        with TemporaryDirectory() as temp:
            urlretrieve(
                f"https://eclass2.ajou.ac.kr/webapps/bbgs-OnlineAttendance-BB5ff5398b9f3ea/excel?selectedUserId={student_id}&crs_batch_uid={uid}&title={student_id}&column={quote('사용자명,위치,컨텐츠명,학습한시간,학습인정시간,컨텐츠시간,온라인출석진도율,온라인출석상태(P/F)')}",
                f"{temp}/test.html",
            )

            result.extend(self.read_html(f"{temp}/test.html"))

    def exit(self):
        # print("\n종료 중...")
        self.driver.close()
        self.driver.quit()
        return True


if __name__ == "__main__":
    __version__ = "1.1.1"

    if PL == "win32":
        os.system("chcp 65001 > nul")
        os.system(f"title AjouBB v{__version__}")
    else:
        os.system(f"/bin/bash -c \"echo -ne '\033]0;AjouBB v{__version__}\007'\"")

    options = Options()
    options.add_experimental_option(
        "excludeSwitches", ["enable-logging"]
    )  # Dev listening on...
    options.add_argument("--log-level=3")
    options.add_argument("--headless")
    options.add_argument("--window-size=800,1024")  # more than 5 classes
    options.add_argument(
        "User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    )

    prefs = {
        "profile.managed_default_content_settings.images": 2
    }  # Block third-party images from loading on all websites
    options.add_experimental_option("prefs", prefs)
    bb = BlackBoard(options)

    if PL == "win32":
        # windows에서 콘솔 앱 종료 버튼 누를 때
        win32api.SetConsoleCtrlHandler(bb.exit, True)  # type: ignore

    bb.run()
