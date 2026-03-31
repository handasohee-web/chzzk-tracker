import os
import json
import requests
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

def run_tracker():
    print("🚀 트래커 가동 시작...")
    
    # 1. 구글 인증 시도
    try:
        creds_json = json.loads(os.environ['GOOGLE_SHEET_CREDENTIALS'])
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
        gc = gspread.authorize(creds)
        print("✅ 구글 시트 인증 성공!")
    except Exception as e:
        print(f"❌ 인증 에러: {e}")
        return

    # 2. 치지직 최신 폴링(Polling) API로 데이터 가져오기
    CHANNEL_ID = "13146b286a730297d7938bcbc1999a3d"
    API_URL = f"https://api.chzzk.naver.com/polling/v2/channels/{CHANNEL_ID}/live-status"
    
    # 💡 핵심: 봇이 아닌 진짜 크롬 브라우저인 것처럼 완벽하게 위장!
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://chzzk.naver.com",
        "Referer": f"https://chzzk.naver.com/live/{CHANNEL_ID}"
    }
    
    try:
        response = requests.get(API_URL, headers=headers)
        print(f"📡 API 응답 코드: {response.status_code}")
        
        data = response.json()
        content = data.get("content")

        if content is None:
            print("⚠️ 방송 데이터(content)가 비어있습니다. 응답을 확인하세요.")
            print(f"📦 전체 응답 내용: {data}")
            return

        status = content.get("status", "CLOSE")
        category = content.get("liveCategoryValue", "카테고리 없음") if status == "OPEN" else "방송 꺼짐"
        title = content.get("liveTitle", "제목 없음") if status == "OPEN" else "방송 꺼짐"
        print(f"👀 현재 상태: {status} | 카테고리: {category} | 제목: {title}")

        # 3. 시트 기록
        SHEET_NAME = "치지직_타임라인"
        sh = gc.open(SHEET_NAME).sheet1
        all_values = sh.get_all_values()
        
        # 첫 번째 줄에 뼈대가 없으면 만들어줌
        if not all_values:
            sh.append_row(["기록 시간", "방송 상태", "카테고리", "방송 제목"])
            last_row = [None, None, None, None]
        else:
            last_row = all_values[-1]

        # 변경 사항이 있을 때만 추가
        if last_row[2] != category or last_row[3] != title:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sh.append_row([now, status, category, title])
            print(f"📝 시트 기록 완료! ({category})")
        else:
            print("😴 변경 사항 없음. 기록을 생략합니다.")

    except Exception as e:
        print(f"❌ 데이터 처리 중 에러 발생: {e}")

if __name__ == "__main__":
    run_tracker()
