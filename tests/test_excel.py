import tempfile
import urllib.request
from urllib.parse import quote

import xlrd
import yaml
from selectolax.parser import HTMLParser


def read_html(filename: str):
    with open(filename, "r", encoding="utf-8") as f:
        soup = HTMLParser(f.read(), "html.parser")
        titles = soup.css("tr > td:nth-child(3)")  # 컨텐츠명
        if len(titles):
            return
        studied_times = soup.css("tr > td:nth-child(4)")  # 학습한 시간
        approved_times = soup.css("tr > td:nth-child(5)")  # 학습 인정 시간
        pf_status = soup.css("tr > td:nth-child(8)")  # P/F

        for i in range(len(titles)):
            print(titles[i].text())
            print(studied_times[i].text())
            print(approved_times[i].text())
            print(pf_status[i].text())
            print()


def test_download():
    with open("univ.yaml") as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)

    student_id = conf["user"]["student_id"]

    for my_class in conf["user"]["cls"]:
        uid = my_class["uid"]

        with tempfile.TemporaryDirectory() as temp:
            urllib.request.urlretrieve(
                f"https://eclass2.ajou.ac.kr/webapps/bbgs-OnlineAttendance-BB5ff5398b9f3ea/excel?selectedUserId={student_id}&crs_batch_uid={uid}&title={student_id}&column={quote('사용자명,위치,컨텐츠명,학습한시간,학습인정시간,컨텐츠시간,온라인출석진도율,온라인출석상태(P/F)')}",
                f"{temp}/test.html",
            )

            read_html(f"{temp}/test.html")


if __name__ == "__main__":
    test_download()
