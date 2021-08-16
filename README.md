# 아주대학교 BB 파서

## 사용법

*개인 설정은 어디로 전송되지 않습니다. (로컬에서만 작동)*

Windows (v1.0.5):
[AjouBB.zip 다운로드](https://github.com/Alfex4936/Ajou-BlackBoard/releases/download/v1.0.5/AjouBB_v1.0.5.zip)

Linux (v1.0.3):
[AjouBB.tar.xz 다운로드](https://github.com/Alfex4936/Ajou-BlackBoard/releases/download/v1.0.3/AjouBlackBoard_v1.0.3_linux64.tar.xz)

위에 파일을 다운로드 한 후 `univ.yaml`을 notepad나 텍스트 편집기로 열어서

자신의 블랙보드 아이디와 비밀번호를 입력시킨다.

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
