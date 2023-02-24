# 아주대학교 BB 파서

![스크린샷, 2022-06-20 14-54-27](https://user-images.githubusercontent.com/2356749/174534648-b7fb604a-490b-4709-9bca-9abcea53c5df.png)

![제목 없음](https://user-images.githubusercontent.com/2356749/189145106-dcab33c8-3b7a-424e-8673-86a9a2f8f218.png)

`AjouBB` is a Python project aimed at helping students at Ajou University keep track of their classes more efficiently.

By using Selenium, the project automates the process of logging into BlackBoard, the online platform used by the university, and scrapes all relevant information for the student.

The student ID and password are entered into the config.yaml file, and with just a few simple steps, AjouBB will retrieve the following information for the student:

- All class notices from the current semester (within `days` config value)
- A list of all upcoming, unfinished assignments
- Videos to watch for attendance purposes

This project saves students time and effort, as they no longer have to manually check each individual class page for updates and new assignments.

AjouBB makes staying on top of coursework a breeze, allowing students to focus on their studies and excel in their classes.

## 사용법

*개인 설정은 어디로 전송되지 않습니다. (로컬에서만 작동)*

Windows (v1.1.1):
[AjouBB.zip 다운로드](https://github.com/Alfex4936/Ajou-BlackBoard/releases/download/v1.1.1/AjouBB_v1.1.1.zip)

Linux amd64 (v1.1.1):
[AjouBB.tar.xz 다운로드](https://github.com/Alfex4936/Ajou-BlackBoard/releases/download/v1.1.1/AjouBB_v1.1.1_linux.tar.xz)

위에 파일을 다운로드 한 후 `univ.yaml`을 notepad나 텍스트 편집기로 열어서

자신의 블랙보드 아이디, 비밀번호와 학번을 입력시킨다.

day옵션은 몇 일이내 공지까지 불러올 것인지 정한다. (ex. 0은 오늘 공지만)

`AjouBlackBoard`를 실행한다. (*윈도우: 컴퓨터 시작에 자동 실행은 `startup.bat`을 추가 실행하세요*)

![yaml](https://user-images.githubusercontent.com/2356749/113546947-f7c97c80-9627-11eb-9d5f-aba93dda4848.gif)

## 기능 1 - 공지

자동으로 수강 중인 코스의 공지를 day 옵션에 맞게 불러온다.

* `univ.yaml`의 day 값이 1이여서 4월 26일부터 4월 27일 공지를 불러왔음
![ajou](https://user-images.githubusercontent.com/2356749/116214126-5eead480-a781-11eb-9fc2-126fd3867ba8.gif)

## 기능 2 - 제공 예정

코스 공지를 보여준 후 아무 키나 누르면 `제공 예정` 부분을 불러온다.

![due](https://user-images.githubusercontent.com/2356749/113511215-b5f1f500-9599-11eb-9516-18bfb8ffcf8a.gif)

## 기능 3 - 온라인 동영상 출석 현황

봐야할 영상들을 불러온다. (`videos.py` 참고)

![video](https://user-images.githubusercontent.com/2356749/135459264-ea25ebc3-3395-49df-963e-5a739f5460b9.png)

# GUI 버전 (on progress)

[gui 폴더](https://github.com/Alfex4936/Ajou-BlackBoard/tree/main/gui)

Kivy + KivyMD을 이용한 멀티 플랫폼 앱 개발

## 공지 (검색, 새로고침)

RefreshLayout으로 바꿔서 pull to refresh 방식이 나을듯

![main](https://user-images.githubusercontent.com/2356749/129508421-f65116c7-fb29-48da-a63d-d37ac21af770.png)

![search](https://user-images.githubusercontent.com/2356749/129508425-66e86004-9e52-4fb6-b91a-897694fe2633.png)

## 블랙보드 공지 (NOT YET)

수강 중인 수업들 공지 제목만 따고 클릭하면 Dialog로 전체 내용 보여주기
## additional (NOT YET)

1. 학사일정

2. 중앙 도서관 좌석 현황

![library](https://user-images.githubusercontent.com/2356749/129508427-3aa54863-b43e-4f47-8e1e-d231ef8796b1.png)

3. 학식