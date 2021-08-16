import os
import webbrowser
from urllib.parse import quote

from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineListItem, ThreeLineListItem
from kivymd.uix.snackbar import Snackbar

from utils.parser import Homepage

nFont = lambda text: f"[font=NanumBarunGothic.ttf]{text}[/font]"


class Mine(MDBoxLayout):
    ...


class Content(BoxLayout):
    pass


class MyThreeLinkListItem(ThreeLineListItem):
    def __init__(self, **kwargs):
        self.link = kwargs.pop("link")
        kwargs["on_press"] = lambda _: webbrowser.open(self.link)
        super().__init__(**kwargs)


class Example(MDApp):
    lib_dialog = None
    ask_dialog = None

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
                text=nFont("학사 일정 보기"),
                on_release=lambda _: self.show_library_dialog(),
            )
        )

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
