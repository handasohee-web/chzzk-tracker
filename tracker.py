import os
import json
import requests
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

# 1. 깃허브 시크릿 자격 증명
try:
    creds_json = json.loads(os.environ['GOOGLE_SHEET_CREDENTIALS'])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    gc = gspread.authorize(creds)
except Exception as e:
    print(f"❌ 구글 시트 인증 실패: {e}")
    exit(1)

CHANNEL_ID = "13146b286a730297d7938bcbc1999a3d"
SHEET_NAME = "치지직_타임라인"

def run_tracker():
    try:
        # 치지직 API 호출
        api_url = f"https://api.chzzk.naver.com/service/v1/channels/{CHANNEL_ID}/live-detail"
        response = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"})
        
        # [디버그] 응답 상태 확인
        print(f"📡 API 응답 코드: {response.status_code}")
        
        raw_data = response.json()
        content = raw_data.get("content")

        # 만약 방송 정보가 아예 없다면 (채널 ID가 틀렸거나 비공개일 때)
        if not content:
            print(f"⚠️ 방송 정보를 가져오지 못했습니다. (메시지: {raw_data.get('message')})")
            return

        status = content.get("status", "CLOSE")
        category = content.get("liveCategoryValue", "카테고리 없음") if status == "OPEN" else "방송 꺼짐"
        title = content.get("liveTitle", "제목 없음") if status == "OPEN" else "방송 꺼짐"
        
        print(f"👀 현재 상태: {status} | 카테고리: {category} | 제목: {title}")

        # 구글 시트 연결
        sh = gc.open(SHEET_NAME).sheet1
        all_values = sh.get_all_values()
        
        if not all_values:
            sh.append_row(["기록 시간", "방송 상태", "카테고리", "방송 제목"])
            last_row = [None, None, None, None]
        else:
            last_row = all_values[-1]

        # 변경 사항이 있을 때만 시트에 추가
        if last_row[2] != category or last_row[3] != title:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sh.append_row([now, status, category, title])
            print(f"📝 시트 기록 완료!")
        else:
            print("😴 변경 사항이 없어 기록하지 않았습니다.")

    except Exception as e:
        print(f"❌ 실행 중 에러 발생: {e}")

if __name__ == "__main__":
    run_tracker()
