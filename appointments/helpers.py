from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
import os
import json

# 必要なスコープを定義します
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarHelper:

    def __init__(self, request):
        self.request = request
        creds = None

        # セッションからクレデンシャルを取得
        if 'google_auth' in self.request.session:
            google_auth = self.request.session['google_auth']
            
            # セッションにリフレッシュトークンがない場合は、settings.pyから補完
            if 'refresh_token' not in google_auth or not google_auth['refresh_token']:
                google_auth['refresh_token'] = settings.GOOGLE_REFRESH_TOKEN

            # クレデンシャルを生成
            creds = Credentials(**google_auth)

        # クレデンシャルがない場合は、OAuth 2.0のフローを開始
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
            # クレデンシャルをセッションに保存
            self.request.session['google_auth'] = creds_to_dict(creds)
        
        self.creds = creds
    
    def update_event(self, summary, description, start_time, end_time, event_id):
        try:
            # Google APIサービスの初期化
            service = build('calendar', 'v3', credentials=self.creds)

            # 更新するデータ
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
            }
            # イベントの更新
            updated_event = service.events().update(
                calendarId='primary',
                eventId=event_id,  # 保存されているイベントIDを使用
                body=event
            ).execute()

            print(f"Google Calendar イベントが更新されました: {updated_event.get('htmlLink')}")
            return updated_event
        except HttpError as error:
            print(f"An error occurred: {error}")
            raise Exception("Google Calendar APIのエラーにより、イベントを更新できませんでした。")

    def create_event(self, summary, description, start_time, end_time, attendees):
        service = build('calendar', 'v3', credentials=self.creds)
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'Asia/Tokyo',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'Asia/Tokyo',
            },
            'conferenceData': {
                'createRequest': {
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    },
                    'requestId': 'some-random-id',
                }
            },
        }
        try:
            # イベントを作成
            event = service.events().insert(calendarId='primary', body=event, conferenceDataVersion=1).execute()
            return event
        except HttpError as error:
            error_content = error.content.decode('utf-8')
            if 'notACalendarUser' in error_content:
                raise Exception("参加者のうちの1人がGoogle Calendarを利用していません。")
            else:
                raise Exception(f"Google Calendar APIエラー: {error_content}")

def creds_to_dict(creds):
    return {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }