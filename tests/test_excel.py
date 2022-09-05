import concurrent.futures
import re
import tempfile
import threading
import time
import urllib.request
from concurrent import futures
from datetime import datetime
from typing import Dict, List
from urllib.parse import quote

import yaml
from selectolax.parser import HTMLParser


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


def read_html2(filename: str) -> List[Video]:
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
                re.search(pattern, title).group(1), "%Y-%m-%d"  # type: ignore
            )

            # current_video_up, current_video_due = datetime.strptime(
            #     dates[0], "%Y-%m-%d"
            # ), datetime.strptime(dates[1], "%Y-%m-%d")
            if (now - current_video_due).days > 0:
                continue

            studied_time = studied_times[i].text(strip=True)
            approved_time = approved_times[i].text(strip=True)

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


def read_html(filename: str):
    with open(filename, "r", encoding="utf-8") as f:
        soup = HTMLParser(f.read())
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

    start = time.perf_counter()
    for my_class in conf["user"]["cls"]:
        uid = my_class["uid"]

        with tempfile.TemporaryDirectory() as temp:
            urllib.request.urlretrieve(
                f"https://eclass2.ajou.ac.kr/webapps/bbgs-OnlineAttendance-BB5ff5398b9f3ea/excel?selectedUserId={student_id}&crs_batch_uid={uid}&title={student_id}&column={quote('사용자명,위치,컨텐츠명,학습한시간,학습인정시간,컨텐츠시간,온라인출석진도율,온라인출석상태(P/F)')}",
                f"{temp}/test.html",
            )

            read_html(f"{temp}/test.html")
    finish = time.perf_counter()
    print(f"Finished in {round(finish-start, 2)} second(s)")


def load(student_id: str, a_class: Dict[str, str], result: List[Video]):
    uid = a_class["uid"]

    with tempfile.TemporaryDirectory() as temp:
        urllib.request.urlretrieve(
            f"https://eclass2.ajou.ac.kr/webapps/bbgs-OnlineAttendance-BB5ff5398b9f3ea/excel?selectedUserId={student_id}&crs_batch_uid={uid}&title={student_id}&column={quote('사용자명,위치,컨텐츠명,학습한시간,학습인정시간,컨텐츠시간,온라인출석진도율,온라인출석상태(P/F)')}",
            f"{temp}/test.html",
        )

        # read_html(f"{temp}/test.html")
        result.extend(read_html2(f"{temp}/test.html"))


def test_multi_download():

    with open("univ.yaml") as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)

    student_id = conf["user"]["student_id"]
    classes = conf["user"]["cls"]

    start = time.perf_counter()

    result = []

    with futures.ThreadPoolExecutor(max_workers=len(classes)) as exec:
        for my_class in classes:
            exec.submit(load, student_id, my_class, result)
        # fut = (exec.submit(load, student_id, my_class) for my_class in classes)
        # for r in concurrent.futures.as_completed(fut):
        #     print(r.result())

    # threads = (
    #     threading.Thread(target=load, args=(student_id, my_class))
    #     for my_class in classes
    # )
    # for thread in threads:
    #     thread.start()

    # for thread in threads:
    #     thread.join()

    finish = time.perf_counter()
    print(result)
    print(f"Finished in {round(finish-start, 2)} second(s)")


if __name__ == "__main__":
    test_download()
    test_multi_download()
