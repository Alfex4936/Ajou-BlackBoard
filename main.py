import os
import re
import sys
from datetime import datetime, timedelta

import win32api
import yaml
from selectolax.parser import HTMLParser
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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

    CLEAR = lambda self: os.system("cls")
    PAUSE = lambda self: os.system("pause")

    def __init__(self, options):
        print("[1/3] 아주대학교 사이트 접속 하는 중...")
        self.driver = webdriver.Chrome(resource_path("./chrome89.exe"), options=options)
        self.driver.implicitly_wait(5)
        self.day = 0 if self.conf["user"]["day"] < 0 else self.conf["user"]["day"]

    def clickLogin(self):
        # driver.find_element_by_name("userId").send_keys(Config.bb_id)
        self.driver.find_element_by_name("userId").send_keys(self.conf["user"]["id"])
        self.driver.find_element_by_name("password").send_keys(self.conf["user"]["pw"])
        self.driver.find_element_by_xpath('//*[@id="loginSubmit"]').click()

    def getNotices(self):
        # 아주대 메인으로 이동하면 자동으로 로그인 홈페이지로 감
        try:
            self.driver.get(self.conf["link"]["bb"])
        except WebDriverException:
            print("[ERR] 서버 오류, 나중에 다시 시도하세요.")
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
        self.clickLogin()
        print("[2/3] 로그인 완료...")

        print("[3/3] 수강 중인 강의 정리 중...")
        if not self.conf["user"]["cls"]:  # TODO 다르면 초기화 (yml에 last 업뎃 시간 만들고 1달마다 체크?)
            # 수강 중인 클래스를 쉽게 모으기 위해 이동
            self.driver.get(
                "https://eclass2.ajou.ac.kr/webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_2_1&forwardUrl=detach_module%2F_22_1%2F"
            )
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.ID, "_22_1termCourses_noterm"))
                )
            except Exception:
                self.exit()
                sys.exit(1)
            html = self.driver.page_source
            soup = HTMLParser(html, "html.parser")
            classLinks = soup.css("a")

            classIds = []

            pattern = re.compile(r"id=([^&]+)")
            for link in classLinks:
                classIds.append(
                    {
                        "link": self.conf["link"]["web"]
                        + pattern.search(link.attributes["href"]).group(1),
                        "name": link.text().split()[-1],
                    }
                )

            self.conf["user"]["cls"] = classIds
            with open("univ.yaml", "w") as f:
                yaml.dump(self.conf, f)

        # print(conf["user"]["cls"])

        now = datetime.now()
        diffDate = now - timedelta(self.day)

        totalPosts = 0
        self.CLEAR()
        dayMessage = f"{self.day}일" if self.day > 0 else "오늘"
        dayMessage = f"오늘부터 ~ {diffDate.month}월 {diffDate.day}일"
        print(f"\n\n\t>>> {dayMessage}까지 공지 불러오는 중...")

        for i, ajouCls in enumerate(self.conf["user"]["cls"]):
            posts = 0

            classId, className = ajouCls.values()
            self.driver.get(classId)

            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located(
                        (By.ID, "courseMenuPalette_contents")
                    )
                )
                html = self.driver.page_source

                soup = HTMLParser(html, "html.parser")
                titles = soup.css("#announcementList > li > h3")
                contents = soup.css(
                    "#announcementList > li > div.details > div.vtbegenerated"
                )
                dates = soup.css("#announcementList > li > div.details > p > span")
            except Exception:
                self.exit()
                sys.exit(1)

            for title, content, date in zip(titles, contents, dates):
                date = date.text(strip=False)
                postDate = "".join(date.split()[2:5])
                if not postDate:
                    continue

                parsedDate = datetime.strptime(postDate, "%Y년%m월%d일")
                if (now - parsedDate).days <= self.day:
                    totalPosts += 1
                    posts += 1
                    print()
                    print(f">>>>>----- {posts}번째 공지")
                    print(f"\n{className}: {title.text(strip=True)}")
                    print()
                    print(f"링크: {classId}")
                    print(
                        content.text(strip=False)
                        # .encode("utf-8", "ignore")
                        # .decode("utf-8")  emoji는 가능하나, conhost에서 자체적으로 chcp 65001을 해야함
                    )
                    print(f"{date}\n")
                    print("-" * 50)
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
                _, className, post = lesson.values()
                if post > 0:
                    print(f" └ {className}: {post}개의 공지")
            print()

        self.PAUSE()
        self.getFinals()
        self.exit()
        print()
        self.PAUSE()

    def getFinals(self):
        self.CLEAR()

        print("\n\n해야할 목록을 불러오는 중...")
        self.driver.get("https://eclass2.ajou.ac.kr/ultra/stream")
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".js-title-link"))
            )
        except Exception:
            self.exit()
            sys.exit(1)

        html = self.driver.page_source
        soup = HTMLParser(html, "html.parser")
        dueContents = soup.css(
            "div.js-upcomingStreamEntries > ul > li > div > div > div > div > div.name > ng-switch > a"
        )
        dueDates = soup.css(
            "div.js-upcomingStreamEntries > ul > li > div > div > div > div > div.content > span > bb-translate > bdi"
        )
        classNames = soup.css(
            "div.js-upcomingStreamEntries > ul > li > div > div > div > div > div.context.ellipsis > a"
        )
        self.CLEAR()

        print("\n\t--- 제공 예정 ---")
        n = len(dueContents)
        for i in range(n):
            print(classNames[i].text(strip=False))
            print("\t" + dueContents[i].text(strip=False))
            print("\t지정 마감일:" + dueDates[i].text(strip=False))
            print()
        if n == 0:
            print("\n\t모든 할 일을 끝냈습니다.")

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
    __version__ = "1.0.3"

    os.system(f"title 아주대학교 블랙보드 v{__version__}")

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

    bb.getNotices()
