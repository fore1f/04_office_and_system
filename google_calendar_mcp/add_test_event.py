import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token.json')
SCOPES = ['https://www.googleapis.com/auth/calendar']

def main():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    service = build('calendar', 'v3', credentials=creds)

    # ファミリーカレンダーのIDを探す
    calendar_list = service.calendarList().list().execute()
    family_cal_id = 'primary'
    for cal in calendar_list.get('items', []):
        if 'Family' in cal.get('summary', '') or 'ファミリー' in cal.get('summary', ''):
            family_cal_id = cal['id']
            break

    # 予定の設定 (2026-03-03 10:00 - 11:00)
    start_time = "2026-03-03T10:00:00"
    end_time = "2026-03-03T11:00:00"
    
    event = {
        'summary': 'テスト',
        'start': {'dateTime': start_time, 'timeZone': 'Asia/Tokyo'},
        'end': {'dateTime': end_time, 'timeZone': 'Asia/Tokyo'},
    }

    event = service.events().insert(calendarId=family_cal_id, body=event).execute()
    print(f"ファミリーカレンダーに予定を登録しました: {event.get('htmlLink')}")

if __name__ == '__main__':
    main()
