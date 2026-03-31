import os
import json
import requests
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

# 1. 깃허브 시크릿에서 자격 증명 가져오기
creds_json = json.loads(os.environ['GOOGLE_SHEET_CREDENTIALS'])
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
gc = gspread.authorize(creds)

# 설정
CHANNEL_ID = "13146b286a730297d7938bcbc1999a3d"
SHEET_NAME = "치지직_타임라인"

def run_tracker():
    try:
        sh = gc.open(SHEET_NAME).sheet1
        
        # 치지직 API 확인
        api_url = f"https://api.chzzk.naver.com/service/v1/channels/{CHANNEL_ID}/live-detail"
        data = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}).json().get("content", {})
        
        status = data.get("status")
        category = data.get("liveCategoryValue", "카테고리 없음") if status == "OPEN" else "방송 꺼짐"
        title = data.get("liveTitle", "제목 없음") if status == "OPEN" else "방송 꺼짐"
        
        # 시트의 마지막 줄 가져오기 (이전 기록 확인)
        all_values = sh.get_all_values()
        if not all_values:
            sh.append_row(["기록 시간", "방송 상태", "카테고리", "방송 제목"])
            last_row = [None, None, None, None]
        else:
            last_row = all_values[-1]

        # 이전 기록과 다를 때만 추가 (2번:카테고리, 3번:제목)
        if last_row[2] != category or last_row[3] != title:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sh.append_row([now, status, category, title])
            print(f"📝 변경 감지 및 기록 완료: {category}")
        else:
            print("💤 변경 사항 없음.")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    run_tracker()
