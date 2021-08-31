import asyncio
import os
import re
import sys
import webbrowser
from datetime import datetime, timedelta
from urllib.parse import quote

import yaml
from kivy.app import async_runTouchApp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineListItem, ThreeLineListItem
from kivymd.uix.snackbar import Snackbar
from selectolax.parser import HTMLParser
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from utils.parser import Homepage

nFont = lambda text: f"[font=NanumBarunGothic.ttf]{text}[/font]"


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

    # CLEAR = lambda _: os.system("cls")
    # PAUSE = lambda _: os.system("pause")

    def __init__(self, options):
        print("[1/3] 아주대학교 사이트 접속 하는 중...")
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

    def clickLogin(self):
        # driver.find_element_by_name("userId").send_keys(Config.bb_id)
        self.driver.find_element_by_name("userId").send_keys(self.conf["user"]["id"])
        self.driver.find_element_by_name("password").send_keys(self.conf["user"]["pw"])
        self.driver.find_element_by_xpath('//*[@id="loginSubmit"]').click()

    def getNotices(self):
        notices = {"total_posts": 0}

        # 아주대 메인으로 이동하면 자동으로 로그인 홈페이지로 감
        try:
            self.driver.get(self.conf["link"]["bb"])
        except WebDriverException:
            print("[ERR] 서버 오류, 나중에 다시 시도하세요.")
            self.exit()
            return notices

        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".btn-login"))
            )
        except Exception:
            self.exit()
            return notices

        # 로그인하기
        self.clickLogin()
        print("[2/3] 로그인 완료...")

        print("[3/3] 수강 중인 강의 정리 중...")

        # 한달마다 강의 체크
        now = datetime.now()
        assert self.conf["user"]["date"] != ""
        last_parsed = datetime.strptime(self.conf["user"]["date"], "%Y-%m-%d")

        if (
            not self.conf["user"]["cls"] or abs(last_parsed.month - now.month) > 0
        ):  # 비어있거나 매달 체크
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
                return notices

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

            self.conf["user"]["date"] = now.strftime("%Y-%m-%d")  # ex) 2021-12-31
            self.conf["user"]["cls"] = classIds
            with open("univ.yaml", "w") as f:
                yaml.dump(self.conf, f)

        del last_parsed

        # print(conf["user"]["cls"])

        diffDate = now - timedelta(self.day)

        totalPosts = 0

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
                return notices

            if className not in notices:
                notices[className] = {"url": classId, "posts": 0, "contents": []}

            for title, content, date in zip(titles, contents, dates):
                title = title.text(strip=True)
                date = date.text(strip=False)

                postDate = "".join(date.split()[2:5])
                if not postDate:
                    continue
                parsedDate = datetime.strptime(postDate, "%Y년%m월%d일")

                if (now - parsedDate).days <= self.day:
                    notices["total_posts"] += 1
                    notices[className]["posts"] += 1
                    notices[className]["contents"].append(
                        (title, content.text(strip=False), date)
                    )
                else:
                    break
            self.conf["user"]["cls"][i]["posts"] = posts  # 각 강의마다 공지 몇 개인지 체크

        # div.name > ng-switch > a

        return notices

    def getFinals(self):
        finals = {}

        # print("\n\n해야할 목록을 불러오는 중...")

        self.driver.get("https://eclass2.ajou.ac.kr/ultra/stream")
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".js-title-link"))
            )
        except Exception:
            self.exit()
            return finals

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
        # self.CLEAR()

        for i in range(len(dueContents)):
            classNames[i] = classNames[i].text(strip=False)
            if classNames[i] not in finals:
                finals[classNames[i]] = {"contents": []}

            finals[classNames[i]].append(
                (dueContents[i].text(strip=False), dueDates[i].text(strip=False))
            )

        return finals

    def exit(self):
        # print("\n종료 중...")
        self.driver.close()
        self.driver.quit()
        return True


class Mine(MDBoxLayout):
    ...


class Content(BoxLayout):
    pass


class MyThreeLinkListItem(ThreeLineListItem):
    def __init__(self, **kwargs):

        if "value" in kwargs:
            self.name, self.content = kwargs.pop("value")

            self.app = kwargs.pop("app")
            kwargs["on_press"] = lambda _: self.app.show_bb_notice_content(
                self.name, self.content
            )
            self.link = kwargs.pop("link")
        else:
            self.link = kwargs.pop("link")
            kwargs["on_press"] = lambda _: webbrowser.open(self.link)
        super().__init__(**kwargs)


class Example(MDApp):
    lib_dialog = None
    ask_dialog = None
    bb_dialog = None

    notices = None
    finals = None

    def build(self):
        return Mine()

    def on_start(self):
        notices, _ = Homepage.parseNotices()
        assert notices != None

        for notice in notices:
            self.root.ids.container.add_widget(
                MyThreeLinkListItem(
                    text=nFont(notice.title),
                    secondary_text=nFont(notice.writer),
                    tertiary_text=nFont(notice.date),
                    link=notice.link,
                )
            )

        self.root.ids.etc_list.add_widget(
            OneLineListItem(
                text=nFont("중앙 도서관 좌석 현황 보기"),
                on_release=lambda _: self.show_library_dialog(),
            )
        )

        self.root.ids.etc_list.add_widget(
            OneLineListItem(
                text=nFont("학사 일정 보기"), on_release=lambda _: self.show_library_dialog(),
            )
        )

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
        self.notices = bb.getNotices()
        self.finals = bb.getFinals()

        for className, classContent in self.notices.items():
            if className == "total_posts":
                continue
            if classContent["posts"] == 0:
                continue

            for title, content, date in classContent["contents"]:
                self.root.ids.bbcontainer.add_widget(
                    MyThreeLinkListItem(
                        text=nFont(title),
                        secondary_text=nFont(content[:45] + "..."),
                        tertiary_text=nFont(date),
                        link=classContent["url"],
                        app=self,
                        value=(className, content)
                        # on_release=lambda _: self.show_bb_notice_content(
                        #     className, content
                        # ),
                    )
                )

    def show_bb_notice_content(self, name, content):
        self.bb_dialog = MDDialog(
            size_hint=(0.7, 0.6), title=nFont(name), text=nFont(content),
        )
        self.bb_dialog.open()

    def show_library_dialog(self):
        if not self.lib_dialog:
            library = Homepage.loadLibrary()
            assert library != None, Snackbar(text=nFont("잠시 후 다시 시도해주세요 :(")).open()

            text = []
            for data in library["data"]["list"]:
                text.append(
                    f'{data["name"]}: {data["available"]}/{data["activeTotal"]} (잔여/전체)'
                )
            self.lib_dialog = MDDialog(
                title=nFont("중앙 도서관 좌석 현황"), text=nFont("\n".join(text)),
            )
        self.lib_dialog.open()

    def show_search_dialog(self):
        if not self.ask_dialog:
            content = Content()
            self.ask_dialog = MDDialog(
                title=nFont("원하는 공지 제목 키워드"),
                type="custom",
                content_cls=content,
                buttons=[
                    MDFlatButton(
                        text=nFont("닫기"),
                        text_color=self.theme_cls.primary_color,
                        on_release=lambda _: self.ask_dialog.dismiss(),
                    ),
                    MDFlatButton(
                        text=nFont("검색하기"),
                        text_color=self.theme_cls.primary_color,
                        on_release=lambda _: self.search(content),
                    ),
                ],
            )
        self.ask_dialog.open()

    def refresh(self):
        notices, _ = Homepage.parseNotices()
        assert notices != None, Snackbar(text=nFont("잠시 후 다시 시도해주세요 :(")).open()

        self.root.ids.container.clear_widgets()

        for notice in notices:
            self.root.ids.container.add_widget(
                MyThreeLinkListItem(
                    text=nFont(notice.title),
                    secondary_text=nFont(notice.writer),
                    tertiary_text=nFont(notice.date),
                    link=notice.link,
                )
            )

        Snackbar(text=nFont("공지를 다시 불러왔습니다!")).open()

    def search(self, content):
        self.ask_dialog.dismiss()
        keyword = content.ids.md_search.text.strip()
        notices, _ = Homepage.parseNotices(
            url=f"https://ajou.ac.kr/kr/ajou/notice.do?mode=list&srSearchKey=&srSearchVal={quote(keyword)}&articleLimit=30&article.offset=0",
            length=30,
        )

        if notices is None:
            Snackbar(text=nFont(f"{keyword}에 관한 공지가 없습니다.")).open()
            return

        self.root.ids.container.clear_widgets()

        for notice in notices:
            self.root.ids.container.add_widget(
                MyThreeLinkListItem(
                    text=nFont(notice.title),
                    secondary_text=nFont(notice.writer),
                    tertiary_text=nFont(notice.date),
                    link=notice.link,
                )
            )

        Snackbar(text=nFont(f"{keyword}에 관한 공지를 불러왔습니다!")).open()


Example().run()

