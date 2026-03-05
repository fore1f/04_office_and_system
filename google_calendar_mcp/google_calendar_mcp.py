import datetime
import os.path
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from mcp.server.fastmcp import FastMCP

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

# MCPサーバーの定義
mcp = FastMCP("Google Calendar")

def get_calendar_service():
    """Google Calendar API サービスを取得する。"""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_PATH, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                logger.error(f"トークンのリフレッシュに失敗しました: {e}")
                creds = None
        
        if not creds:
            raise PermissionError("認証が必要です。ターミナルで uv run test_calendar.py を実行して認証を完了させてください。")
    
    return build('calendar', 'v3', credentials=creds)

def get_tasks_service():
    """Google Tasks API サービスを取得する。"""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_PATH, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                logger.error(f"トークンのリフレッシュに失敗しました: {e}")
                creds = None
        
        if not creds:
            raise PermissionError("認証が必要です。ターミナルで uv run test_calendar.py を実行して認証を完了させてください。")
    
    return build('tasks', 'v1', credentials=creds)

def get_calendar_ids(service):
    """アクセス可能なカレンダーのリストを取得する（祝日以外）。"""
    calendar_list = service.calendarList().list().execute()
    ids = []
    for cal in calendar_list.get('items', []):
        cal_id = cal['id']
        # 祝日カレンダーなどは除外したい場合はここでフィルタリング
        if "#holiday@group.v.calendar.google.com" not in cal_id:
            ids.append({'id': cal_id, 'summary': cal.get('summary')})
    return ids

@mcp.tool()
def list_upcoming_events(max_results: int = 20):
    """
    すべてのカレンダーから今後予定されているイベントを取得します。
    """
    try:
        service = get_calendar_service()
        now = datetime.datetime.now(datetime.UTC).isoformat()
        
        calendars = get_calendar_ids(service)
        all_events = []

        for cal in calendars:
            events_result = service.events().list(
                calendarId=cal['id'], timeMin=now,
                maxResults=max_results, singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            for e in events:
                e['calendar_summary'] = cal['summary']
                all_events.append(e)

        if not all_events:
            return "直近の予定は見つかりませんでした。"

        # 全カレンダーの予定を開始時刻順に並び替え
        all_events.sort(key=lambda x: x['start'].get('dateTime', x['start'].get('date')))

        output = "今後の予定:\n"
        for event in all_events[:max_results]:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', '(タイトルなし)')
            cal_name = event['calendar_summary']
            output += f"- [{cal_name}] {start}: {summary}\n"
        return output

    except Exception as e:
        return f"エラーが発生しました: {e}"

@mcp.tool()
def create_calendar_event(summary: str, start_time: str, end_time: str, calendar_name: str = "primary", description: str = ""):
    """
    新しいカレンダーイベントを作成します。
    
    Args:
        summary (str): 予定のタイトル
        start_time (str): 開始時刻 (ISOフォーマット, 例: 2024-03-04T10:00:00+09:00)
        end_time (str): 終了時刻 (ISOフォーマット)
        calendar_name (str): 登録先カレンダー名のキーワード (例: "family", "primary")
        description (str): 予定の説明文
    """
    try:
        service = get_calendar_service()
        
        # カレンダーIDの特定
        target_id = 'primary'
        if calendar_name.lower() != "primary":
            calendars = get_calendar_ids(service)
            for cal in calendars:
                if calendar_name.lower() in cal['summary'].lower():
                    target_id = cal['id']
                    break

        event = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_time, 'timeZone': 'Asia/Tokyo'},
            'end': {'dateTime': end_time, 'timeZone': 'Asia/Tokyo'},
        }

        event = service.events().insert(calendarId=target_id, body=event).execute()
        return f"予定を「{calendar_name}」に作成しました: {event.get('htmlLink')}"

    except Exception as e:
        return f"エラーが発生しました: {e}"

@mcp.tool()
def search_events(query: str):
    """
    すべてのカレンダーからキーワードで予定を検索します。
    """
    try:
        service = get_calendar_service()
        calendars = get_calendar_ids(service)
        all_results = []

        for cal in calendars:
            events_result = service.events().list(
                calendarId=cal['id'], q=query,
                singleEvents=True, orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            for e in events:
                e['calendar_summary'] = cal['summary']
                all_results.append(e)

        if not all_results:
            return f"「{query}」に一致する予定は見つかりませんでした。"

        output = f"「{query}」の検索結果:\n"
        for event in all_results:
            start = event['start'].get('dateTime', event['start'].get('date'))
            output += f"- [{event['calendar_summary']}] {start}: {event.get('summary')}\n"
        return output

    except Exception as e:
        return f"エラーが発生しました: {e}"

@mcp.tool()
def list_task_lists():
    """
    ユーザーのGoogle ToDoリスト（タスクリスト）の一覧を取得します。
    """
    try:
        service = get_tasks_service()
        results = service.tasklists().list().execute()
        items = results.get('items', [])
        
        if not items:
            return "タスクリストが見つかりませんでした。"
        
        output = "利用可能なタスクリスト:\n"
        for item in items:
            output += f"- {item['title']} (ID: {item['id']})\n"
        return output
    except Exception as e:
        return f"エラーが発生しました: {e}"

@mcp.tool()
def list_tasks(tasklist_name: str = "@default"):
    """
    指定したToDoリスト内のタスク一覧（未完了のみ）を取得します。
    
    Args:
        tasklist_name (str): タスクリスト名のキーワード。デフォルトは「@default」(メインのリスト)。
    """
    try:
        service = get_tasks_service()
        
        # タスクリストIDの特定
        tasklist_id = '@default'
        if tasklist_name != "@default":
            lists = service.tasklists().list().execute().get('items', [])
            for l in lists:
                if tasklist_name.lower() in l['title'].lower():
                    tasklist_id = l['id']
                    break
        
        results = service.tasks().list(tasklist=tasklist_id, showCompleted=False).execute()
        items = results.get('items', [])
        
        if not items:
            return f"「{tasklist_name}」に未完了のタスクはありません。"
        
        output = f"「{tasklist_name}」のタスク一覧:\n"
        for item in items:
            status = "[ ]" if item['status'] == 'needsAction' else "[x]"
            output += f"- {status} {item['title']}\n"
            if 'notes' in item:
                output += f"  (メモ: {item['notes']})\n"
        return output
    except Exception as e:
        return f"エラーが発生しました: {e}"

@mcp.tool()
def create_task(title: str, notes: str = "", tasklist_name: str = "@default"):
    """
    新しいタスクをToDoリストに追加します。
    
    Args:
        title (str): タスクのタイトル
        notes (str): タスクのメモ
        tasklist_name (str): 追加先のタスクリスト名
    """
    try:
        service = get_tasks_service()
        
        tasklist_id = '@default'
        if tasklist_name != "@default":
            lists = service.tasklists().list().execute().get('items', [])
            for l in lists:
                if tasklist_name.lower() in l['title'].lower():
                    tasklist_id = l['id']
                    break
                    
        task = {
            'title': title,
            'notes': notes
        }
        
        result = service.tasks().insert(tasklist=tasklist_id, body=task).execute()
        return f"タスク「{title}」をリストに作成しました。"
    except Exception as e:
        return f"エラーが発生しました: {e}"

if __name__ == "__main__":
    mcp.run()
