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

# 必要な権限（ユーザー情報の読み取り）
SCOPES = ['https://www.googleapis.com/auth/admin.directory.user.readonly']

def list_users() -> None:
    """Google Workspaceのユーザー一覧を表示するデモ。"""
    creds = None
    # 既存のトークンを確認
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 有効な認証情報がない場合はログイン処理
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                logger.error("credentials.json が見つかりません。Google Cloud Consoleからダウンロードして配置してください。")
                return
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # 次回のために認証情報を保存
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('admin', 'directory_v1', credentials=creds)
        logger.info('ユーザー一覧を取得中...')
        
        results = service.users().list(customer='my_customer', maxResults=10, orderBy='email').execute()
        users = results.get('users', [])

        if not users:
            print('ユーザーが見つかりませんでした。')
        else:
            print('ユーザー一覧:')
            for user in users:
                print(f"- {user['primaryEmail']} ({user['name']['fullName']})")

    except HttpError as error:
        logger.error(f'APIエラーが発生しました: {error}')

if __name__ == '__main__':
    list_users()
