import re
from datetime import datetime, timedelta

import os
import sys
import yaml
from selectolax.parser import HTMLParser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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


class BlackBoard:
    options = Options()
    options.add_argument("--log-level=3")
    options.add_argument("--headless")
    options.add_argument(
        "User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"
    )

    with open("./univ.yaml") as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)

    def __init__(self):
        self.driver = webdriver.Chrome(
            resource_path("./chrome89.exe"), options=self.options
        )
        self.driver.implicitly_wait(5)
        self.day = 0 if self.conf["user"]["day"] < 0 else self.conf["user"]["day"]

    def getNotices(self):
        self.driver.implicitly_wait(5)

        self.driver.get(self.conf["link"]["bb"])
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".btn-login"))
            )
        finally:
            pass

        self.driver.find_element_by_name("userId").send_keys(self.conf["user"]["id"])
        # driver.find_element_by_name("userId").send_keys(Config.bb_id)
        self.driver.find_element_by_name("password").send_keys(self.conf["user"]["pw"])
        self.driver.find_element_by_xpath('//*[@id="loginSubmit"]').click()

        self.driver.get(
            "https://eclass2.ajou.ac.kr/webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_2_1&forwardUrl=detach_module%2F_22_1%2F"
        )
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "_22_1termCourses_noterm"))
            )
        except Exception:
            exit(1)
        finally:
            pass
        # _22_1termCourses_noterm > ul > li:nth-child(2) > a
        # _22_1termCourses_noterm > ul > li:nth-child(1) > a

        if not self.conf["user"]["cls"]:
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

        posts = 0
        os.system("cls")
        dayMessage = f"{self.day}일" if self.day > 0 else "오늘"
        dayMessage = f"오늘부터 ~ {diffDate.month}월 {diffDate.day}일"
        print(f"\n\n\t>>> {dayMessage}까지 공지 불러오는 중...")

        for ajouCls in self.conf["user"]["cls"]:
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
            finally:
                pass

            for title, content, date in zip(titles, contents, dates):
                date = date.text(strip=False)
                postDate = "".join(date.split()[2:5])
                if not postDate:
                    continue

                parsedDate = datetime.strptime(postDate, "%Y년%m월%d일")
                if (now - parsedDate).days <= self.day:
                    posts += 1
                    print()
                    print(f">>>>>----- {posts}번째 공지")
                    print(f"\n{className}: {title.text(strip=True)}")
                    print()
                    print(f"링크: {classId}")
                    print(content.text(strip=False))
                    print(f"{date}\n")
                    print("-" * 50)
                else:
                    break

        # div.name > ng-switch > a

        if posts == 0:
            os.system("cls")
            print(f"\n\n\t{dayMessage} 이내 공지가 없네요!!!\n")

        os.system("pause")
        self.getFinals()

        self.driver.close()
        self.driver.quit()
        print("\n>>>")
        os.system("pause")

    def getFinals(self):
        os.system("cls")

        print("\n\t해야할 목록을 불러오는 중...")
        self.driver.get("https://eclass2.ajou.ac.kr/ultra/stream")
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".js-title-link"))
            )
        finally:
            pass

        html = self.driver.page_source
        soup = HTMLParser(html, "html.parser")
        DueContents = soup.css(
            "div.js-upcomingStreamEntries > ul > li > div > div > div > div > div.name > ng-switch > a"
        )
        dueDates = soup.css(
            "div.js-upcomingStreamEntries > ul > li > div > div > div > div > div.content > span > bb-translate > bdi"
        )
        classNames = soup.css(
            "div.js-upcomingStreamEntries > ul > li > div > div > div > div > div.context.ellipsis > a"
        )

        print("\n\t--- 제공 예정 ---")
        n = len(DueContents)
        for i in range(n):
            print(classNames[i].text(strip=False))
            print("\t" + DueContents[i].text(strip=False))
            print("\t지정 마감일:" + dueDates[i].text(strip=False))
            print()


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
    bb = BlackBoard()
    bb.getNotices()
