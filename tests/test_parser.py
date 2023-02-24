from selectolax.parser import HTMLParser


def test_br():
    HTML = """
    <div class="vtbegenerated">
 <p>ABC이(가) 예약된 Zoom 회의에 귀하를 초대합니다.</p> 
 <p>주제: CLASS<br>시간: 2022년 9월 5일 &nbsp;03:00 오후 서울<br>&nbsp; &nbsp; &nbsp; &nbsp; 매주 월, 수에, 16개 되풀이 항목<br>&nbsp; &nbsp; &nbsp; &nbsp; 2022년 9월 5일 &nbsp;03:00 오후<br>&nbsp; &nbsp; &nbsp; &nbsp; 2022년 9월 7일 &nbsp;03:00 오후<br>&nbsp; &nbsp; &nbsp; &nbsp; 2022년 9월 12일 &nbsp;03:00 오후<br>&nbsp; &nbsp; &nbsp; &nbsp; 2022년 9월 14일 &nbsp;03:00 오후<br>&nbsp; &nbsp; &nbsp; &nbsp; 2022년 9월 19일 &nbsp;03:00 오후<br>&nbsp; &nbsp; &nbsp; &nbsp; 2022년 9월 21일 &nbsp;03:00 오후<br>&nbsp; &nbsp; &nbsp; &nbsp; 2022년 9월 26일 &nbsp;03:00 오후<br>&nbsp; &nbsp; &nbsp; &nbsp; 2022년 9월 28일 &nbsp;03:00 오후<br>&nbsp; &nbsp; &nbsp; &nbsp; 2022년 10월 3일 &nbsp;03:00 오후<br>&nbsp; &nbsp; &nbsp; &nbsp; 2022년 10월 5일 &nbsp;03:00 오후<br>&nbsp; &nbsp; &nbsp; &nbsp; 2022년 10월 10일 &nbsp;03:00 오후<br>&nbsp; &nbsp; &nbsp; &nbsp; 2022년 10월 12일 &nbsp;03:00 오후<br>&nbsp; &nbsp; &nbsp; &nbsp; 2022년 10월 17일 &nbsp;03:00 오후<br>&nbsp; &nbsp; &nbsp; &nbsp; 2022년 10월 19일 &nbsp;03:00 오후<br>&nbsp; &nbsp; &nbsp; &nbsp; 2022년 10월 24일 &nbsp;03:00 오후<br>&nbsp; &nbsp; &nbsp; &nbsp; 2022년 10월 26일 &nbsp;03:00 오후<br>다음 iCalendar(.ics) 파일을 다운로드하고 일정 시스템으로 가져오십시오.<br>매주: <a href="https://ajou-ac-kr.zoom.us/meeting/tZwpfuiqqzkqHtebaVURj92-bVadXAS0VBua/ics?icsToken=98tyKuGgqjIrGNGXsB2ERpw-Bor4d-rwmHpfgrdYnh7TNhJZO1G7NNRDNopeI4jm">https://ajou-ac-kr.zoom.us/meeting/tZwpfuiqqzkqHtebaVURj92-bVadXAS0VBua/ics?icsToken=98tyKuGgqjIrGNGXsB2ERpw-Bor4d-rwmHpfgrdYnh7TNhJZO1G7NNRDNopeI4jm</a></p> 
 <p>Zoom 회의 참가<br><a href="https://zoom">zoom</a></p> 
 <p>회의 ID: 123 456 789<br>암호: 123</p>
</div>
    """
    soup = HTMLParser(str.replace(HTML, "<br>", "\n", -1))

    content = soup.css_first("div.vtbegenerated")
    content.replace_with("<br>")

    text = content.text(strip=False)
    # text = unicodedata.normalize("NFKD", text)
    print(text)


if __name__ == "__main__":
    test_br()
