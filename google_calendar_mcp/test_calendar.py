# %%
import datetime
import os.path
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# スコープ設定
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/tasks'
]

# ファイルパス
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')

def main():
    """Google Calendar API 接続テスト"""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("トークンが期限切れのため、リフレッシュを試みています...")
            try:
                creds.refresh(Request())
                with open(TOKEN_PATH, 'w') as token:
                    token.write(creds.to_json())
                print("リフレッシュに成功しました。")
            except Exception as e:
                print(f"リフレッシュに失敗しました（有効期限切れの可能性があります）: {e}")
                creds = None # 失敗した場合は None にして新規認証へ進む
        
        if not creds:
            print("新規に認証を開始します。ブラウザが開きますので承認をお願いします...")
            if not os.path.exists(CREDENTIALS_PATH):
                print("エラー: credentials.json が見つかりません。")
                return
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
            print("認証が完了し、新しいトークンを保存しました。")

    try:
        service = build('calendar', 'v3', credentials=creds)
        
        # 予定を10件取得
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        print('\n直近の予定10件を取得中...')
        events_result = service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=10, singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            print('予定は見つかりませんでした。')
            return

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(f"{start}: {event.get('summary')}")

        # ToDoリストを10件取得
        print('\nToDoリストを取得中...')
        tasks_service = build('tasks', 'v1', credentials=creds)
        task_lists = tasks_service.tasklists().list().execute().get('items', [])
        
        if not task_lists:
            print('ToDoリストが見つかりませんでした。')
        else:
            for tlist in task_lists:
                print(f"リスト: {tlist['title']} (ID: {tlist['id']})")
                tasks = tasks_service.tasks().list(tasklist=tlist['id'], maxResults=5, showCompleted=False).execute().get('items', [])
                if not tasks:
                    print('  未完了のタスクはありません。')
                for task in tasks:
                    print(f"  [ ] {task['title']}")

    except HttpError as error:
        print(f'APIエラー: {error}')

if __name__ == '__main__':
    main()
