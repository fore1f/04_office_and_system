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

    print("=== 所有しているカレンダーの一覧 ===")
    calendar_list = service.calendarList().list().execute()
    calendars = calendar_list.get('items', [])

    for calendar in calendars:
        summary = calendar.get('summary')
        id = calendar.get('id')
        primary = calendar.get('primary', False)
        print(f"名前: {summary}")
        print(f"ID: {id}")
        print(f"プライマリ: {primary}")
        print("-" * 30)

        # 各カレンダーの今日の予定をチェック
        now = datetime.datetime.now(datetime.UTC).isoformat()
        events_result = service.events().list(
            calendarId=id, timeMin=now,
            maxResults=5, singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            print("  (予定なし)")
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(f"  - {start}: {event.get('summary')}")
        print("\n")

if __name__ == '__main__':
    main()
