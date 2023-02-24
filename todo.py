import os
import sys
from datetime import datetime

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

os.environ["WDM_LOG"] = "0"
pl = sys.platform

if pl == "win32":
    import win32api


class NoticeHighlighter(RegexHighlighter):
    """My custom highlighter for AjouBB"""

    base_style = "csw."
    highlights = [
        r"(?P<email>[\w-]+@([\w-]+\.)+[\w-]+)",
        r"(?P<student_id>\d{9})",  # 202209301
        r"(?P<number>\d*번째 공지)",
        r"(?P<url>(file|https|http|ws|wss)://[-0-9a-zA-Z$_+!`(),.?/;:&=%#]*)",
        r"(?P<date>[0-9]+월.[0-9]+일(\s\(.*\))?)",  # 10월31일 (월)
        r"(?P<time>\d{1,2}:\d{1,2})",
        r"(?P<total_notice>총.*공지)",
        r"(?P<per_course>(?<=└ ).*)",  # └ 강좌(X-1): 5개의 공지
        r"(?P<class_name>(?<=----- ).*\))",  # >>>>>----- "CLASS(ABC-1)"
        r"(?P<bold_green>제공 예정|동영상 출석 현황|.요일|출석|기말|중간|과제|주제|조별|발표|성적|마감일|휴강|보강|마감일)",
        r"(?P<bold_red>결석|마감일|Due|적발|채점|않음|오류)",
    ]


theme = Theme(
    {
        "csw.email": "bold red",
        "csw.student_id": "bold red",
        "csw.url": "bold blue",
        "csw.date": "bold yellow",
        "csw.time": "bold yellow",
        "csw.number": "bold green",
        "csw.total_notice": "bold red",
        "csw.per_course": "bold green",
        "csw.class_name": "bold bright_cyan",
        "csw.bold_green": "bold green",
        "csw.bold_red": "bold red",
    }
)

console = Console(highlighter=NoticeHighlighter(), theme=theme)


def resource_path(another_way: str) -> str:
    try:
        usual_way = sys._MEIPASS  # type: ignore
    except Exception:
        usual_way = os.path.dirname(__file__)
    return os.path.join(usual_way, another_way)


class BlackBoard:
    ORDINAL = lambda _, n: "%d%s" % (
        n,
        "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10 :: 4],
    )

    CLEAR = lambda _: os.system("cls" if pl == "win32" else "clear")
    PAUSE = lambda _: os.system(
        "pause"
        if pl == "win32"
        else "/bin/bash -c \"read -sp 'Press [Enter] to finish\n' -n 1 key\""
    )

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

        dr = Service(resource_path(ChromeDriverManager(cache_valid_range=14).install()))

        self.driver = webdriver.Chrome(
            service=dr,
            options=options,
        )
        self.driver.implicitly_wait(5)
        self.day = 0 if self.conf["user"]["day"] < 0 else self.conf["user"]["day"]
        self.now = datetime.now()

    def run(self):
        self.CLEAR()
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
            self.PAUSE()
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
            self.PAUSE()
            sys.exit(1)
        try:  # 중복된 로그인
            self.driver.switch_to.alert.accept()
        except:
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

        # self.get_notices()
        self.get_todos()
        # self.get_attendance()

        from notifypy import Notify

        notification = Notify(
            default_notification_title="로딩이 끝났습니다.",
            default_notification_message="Made by CSW",
            default_notification_application_name="Ajou University",
        )
        notification.send(block=False)

        self.exit()
        self.PAUSE()
        sys.exit(0)

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

    def get_todos(self):
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

        self.CLEAR()
        # print("\n\n해야할 목록을 불러오는 중...")
        if self.LANG == "ko":
            console.print("\n>>>>>----------< 제공 예정 >----------<<<<<\n")
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
        now = datetime.now()
        content = f"@ {now.year}년 {now.month}월 {now.day}일 할 일 목록\n"

        for i in range(n):
            class_name = classNames[i].text(strip=False)
            content += class_name.split(maxsplit=1)[1] + ": "
            print(class_name)  # ABC_ name name

            hw_name = dueContents[i].text(strip=False)
            content += hw_name.split(maxsplit=1)[1] + " > "
            print("\t" + hw_name)

            hw_date = dueDates[i].text(strip=False)
            if self.LANG == "ko":
                console.print("\t지정 마감일: " + hw_date)
            else:
                console.print("\tDue: " + hw_date)

            hw_date = hw_date.split()
            content += (
                hw_date[1][:-1] + "월 " + hw_date[2][:-1] + "일 " + hw_date[3] + "까지"
            )

            content += "\n\n"
            print()
        if n == 0:
            if self.LANG == "ko":
                print("\n\t모든 할 일을 끝냈습니다.")
            else:
                print("\n\tNothing to do.")

        with open(file=os.path.expanduser("~/Desktop/TODO.txt"), mode="a") as f:
            f.write(content)

    def exit(self):
        # print("\n종료 중...")
        self.driver.close()
        self.driver.quit()
        return True


if __name__ == "__main__":
    __version__ = "1.0.0"

    if pl == "win32":
        os.system("chcp 65001 > nul")
        os.system(f"title AjouHW v{__version__}")
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
        "User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"
    )

    bb = BlackBoard(options)

    if pl == "win32":
        # windows에서 콘솔 앱 종료 버튼 누를 때
        win32api.SetConsoleCtrlHandler(bb.exit, True)

    bb.run()
