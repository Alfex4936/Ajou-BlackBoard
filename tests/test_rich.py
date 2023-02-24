from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.theme import Theme

TEXT = """
>>>>>----- 강의1(X123-3) - 1번째 공지

강의1(X123-3): 출석관련 안내

링크:
https://eclass2.ajou.ac.kr/webapps/blackboard/execute/announcement?method

 - 코로나19 확진으로 격리기간 중 출석인정: 1. 과목 담당 교수자에게 해당 내용 미리 통지       2. 격리기간 + 이름이
포함된 문자 캡쳐(또는 격리통지서) 후 전자출석부 출결변경신청시 첨부
 코로나19 관련 출석인정 안내_교무팀 ☜클릭
 - 출석 인정 관련 안내사항:  출석인정   ☜클릭


포함된 링크:
        코로나19 관련 출석인정 안내_교무팀☜클릭 [
https://www.ajou.ac.kr/kr/ajou/notice.do?mode=view&articleNo=180913&article.offset=0&articleLimit=10 ]
        - 출석 인정 관련 안내사항:출석인정☜클릭 [ https://www.ajou.ac.kr/kr/bachelor/class-recognition.do ]

게시 날짜: 2022년 9월 28일 수요일 오전 10시 11분 56초 KST

--------------------------------------------------

>>>>>----- 강의1(X123-3) - 2번째 공지

강의1(X123-3): 출석체크 변경 안내

링크:
https://eclass2.ajou.ac.kr/webapps/blackboard/execute/announcement?method

 전자출결 시스템 불안정 및 강연 중 퇴실 방지를 위한 출석체크 방식을 변경합니다.


  변경 전: 블루투스(비콘) 출석체크 + 소감문 제출 ☞ 변경 후: 지정좌석제(착석여부) + 소감문 제출
 지정 좌석은 매 수업 대강당 출입구에 좌석 배치도 비치 예정.  원하는 좌석에 학번 작성 후 입실하시면 됩니다.
 *학번 기입시 볼펜으로 깔끔하게 기입해주세요.


 * 금주 수업(09. 29)부터 변경된 출석체크 방식이 적용됩니다.


220927 연암관 좌석배치도.pdf
 
 
 문의: abc@ajou.ac.kr  문의시 학번, 이름(202212345, 홍길동) 작성! 




포함된 링크:
        220927 연암관 좌석배치도.pdf [
https://eclass2.ajou.ac.kr/bbcswebdav/pid-207638-dt-announcement-rid- ]

게시 날짜: 2022년 9월 29일 목요일 오후 1시 13분 00초 KST


--------------------------------------------------

>>>>>----- 강의2(F123-1) - 1번째 공지

강의2(F123-1): 팀프로젝트 공지

링크:
https://eclass2.ajou.ac.kr/webapps/blackboard/execute/announcement?method

 안녕하세요? 
 수업중에 공지했던 팀프로젝트에 대해 좀더 명확히 하고자 다시한번 공지합니다.


 예상일정은 다음과 같으며 여러가지 사정을 보아가며 일부 조정가능할수 있습니다.
 팀프로젝트 프로포절 발표: 10월32일 (월) 15:00 팀별 5분발표, 1분질의 예정
 팀프로젝트 중간발표 1차: 11월 11일 (월) 15:00 팀별 5분발표, 1분질의예정
 팀프로젝트 중간발표 2차: 11월 11일 (월) 15:00 팀별 5분발표, 1분질의예정
 팀프로젝트 최종 발표: 12월 12일 (월) 15:00 팀별 5분발표, 1분질의예정


포함된 링크:
없음

게시 날짜: 2022년 9월 23일 금요일 오후 1시 44분 56초 KST

--------------------------------------------------
총 9개의 공지
 └ 강의1(X123-3): 5개의 공지
 └ 강의2(F123-1): 1개의 공지
 └ 강의3(F161-1): 1개의 공지
 └ 강의 강의4(F0961-1): 2개의 공지

>>>>>-----< 제공 예정 >-----<<<<<

"""


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
        r"(?P<bold_green>제공 예정|동영상 출석 현황|.요일|결석|출석|기말|중간|과제|주제|조별|발표|성적|마감일|휴강|보강)",
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
        "csw.class_name": "bold yellow",
        "csw.bold_green": "bold green",
    }
)
console = Console(highlighter=NoticeHighlighter(), theme=theme)


def test_text():
    # console.print("Send funds to money@example.org")
    console.print(TEXT)


if __name__ == "__main__":
    test_text()
