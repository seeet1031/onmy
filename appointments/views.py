from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from accounts.models import Appointment, MedicalHistory, Medicine, Symptom, CustomUser, DoctorSchedule
import json
from datetime import datetime, timedelta
import stripe
from collections import defaultdict
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
from django.shortcuts import get_object_or_404
from .helpers import GoogleCalendarHelper
from google_auth_oauthlib.flow import Flow
from google.auth.exceptions import GoogleAuthError
from googleapiclient.errors import HttpError
from accounts.forms import AppointmentForm
from django.conf import settings
from django.utils.timezone import now
from django.db.models import Q
from datetime import datetime, timedelta


# 必要に応じて、適切なSCOPESやredirect_uriを設定してください。
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Stripe APIキーの設定
stripe.api_key = settings.STRIPE_SECRET_KEY

def google_callback(request):
    try:
        # 認証コードを取得
        code = request.GET.get('code')
        if not code:
            return render(request, 'error.html', {"message": "認証コードが見つかりませんでした。"})
        # OAuth2のフローを再構築
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        flow.redirect_uri = 'http://localhost:8000/callback'
        # 認証コードを使用してトークンを取得
        flow.fetch_token(code=code)
        # 認証情報をセッションに保存
        credentials = flow.credentials
        request.session['google_auth'] = credentials_to_dict(credentials)
        # 成功時には予約確認ページにリダイレクト
        return redirect('confirm_appointment')
    
    except GoogleAuthError as e:
        # エラーが発生した場合はエラーページを表示
        return render(request, 'error.html', {"message": str(e)})

def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

def callback(request):
    state = request.session['state']

    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/calendar'],
        state=state,
        redirect_uri='http://localhost:8000/callback'
    )

    flow.fetch_token(authorization_response=request.build_absolute_uri())

    credentials = flow.credentials
    request.session['google_auth'] = credentials_to_dict(credentials)
    refresh_token = request.session['google_auth'].get('refresh_token')
    print(refresh_token)

    return redirect('confirm_appointment')  # 予約確認ページにリダイレクト

def google_login(request):
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/calendar'],
        redirect_uri='http://localhost:8000/callback'
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    request.session['state'] = state
    return redirect(authorization_url)

def google_calendar_auth(request):
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    flow.run_local_server(port=0)

    credentials = flow.credentials
    request.session['credentials'] = credentials_to_dict(credentials)
    refresh_token = request.session['google_auth'].get('refresh_token')
    print(refresh_token)

    return redirect('appointments:appointment_confirm')  # 認証後にリダイレクトするURL

def get_appointment_options(user):
    # ユーザーの診療履歴をチェック
    has_history = MedicalHistory.objects.filter(user=user).exists()
    
    # 診療履歴がない場合は初診のみを選択肢として返す
    if not has_history:
        return ['first']  # 初診のみ
    
    # 診療履歴がある場合は初診と再診の両方を選択肢として返す
    return ['first', 'revisit']  # 初診と再診



@login_required
def appointment_view(request):
    appointment_type_choices = get_appointment_options(request.user)
    
    medicines = Medicine.objects.filter(is_active=True).order_by('category')
    symptoms = Symptom.objects.filter(is_active=True).order_by('category')
    
    medicine_groups = defaultdict(list)
    symptom_groups = defaultdict(list)
    
    # 先生リストを取得
    doctors = CustomUser.objects.filter(role='doctor').select_related('profile')

    for medicine in medicines:
        medicine_groups[medicine.category].append(medicine)
    
    for symptom in symptoms:
        symptom_groups[symptom.category].append(symptom)

    # 現在の日時
    current_datetime = datetime.now()

    # 今日から1週間の日付リストを作成
    today = current_datetime.date()
    date_range = [today + timedelta(days=i) for i in range(7)]

    # 時間リストを作成（30分間隔）
    time_slots = [f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in (0, 30)]

    # DoctorScheduleデータを取得し、現在以降のスケジュールをフィルタリング
    all_schedules = DoctorSchedule.objects.filter(
        Q(date__gt=current_datetime.date()) | 
        Q(date=current_datetime.date(), start_time__gte=current_datetime.time())
    ).order_by('date', 'start_time')

    # スケジュールを日付ごとに辞書に格納
    schedule_dict = {}
    for schedule in all_schedules:
        date_str = schedule.date.strftime('%Y-%m-%d')
        if date_str not in schedule_dict:
            schedule_dict[date_str] = set()
        # スケジュールの時間範囲を30分単位で記録
        current = schedule.start_time
        while current < schedule.end_time:
            time_str = current.strftime('%H:%M')
            schedule_dict[date_str].add(time_str)
            current = (datetime.combine(datetime.today(), current) + timedelta(minutes=30)).time()


    return render(request, 'appointments/appointment.html', {
        'appointment_type_choices': appointment_type_choices,
        'medicine_groups': dict(medicine_groups),
        'symptom_groups': dict(symptom_groups),
        'doctors': doctors,
        'date_range': date_range,
        'time_slots': time_slots,
        'all_schedules': schedule_dict,
    })

def confirm_appointment(request):
    print('スタート')
    if request.method == 'POST' or 'post_data' in request.session:        # セッションにGoogle認証情報があるかを確認
        if 'google_auth' not in request.session:
        # Google認証が必要な場合、認証ビューにリダイレクト            
            # Google認証が必要な場合、POSTデータをセッションに保存
            request.session['post_data'] = request.POST
            # 認証ビューにリダイレクト
            return redirect('google_login')
    
        # Google認証が成功した後、セッションからPOSTデータを取得
        post_data = request.session.pop('post_data', request.POST)

        # POSTデータから各フィールドの値を取得
        appointment_type = post_data.get('appointment_type')
        appointment_date = post_data.get('appointment_date')
        appointment_time = post_data.get('appointment_time')
        doctor_id = post_data.get('doctor_id')
        symptom_or_medicine_categoryid = post_data.get('symptom_or_medicine_categoryid')
        symptom_or_medicine_id = post_data.get('symptom_or_medicine_id')
        symptom_description = post_data.get('symptom_description')
        prescription_needed = post_data.get('prescription_needed') == 'on'
        medications = post_data.get('medications')
        past_illnesses = post_data.get('past_illnesses')
        allergies = post_data.get('allergies')

        # Appointmentモデルのインスタンスを作成して保存
        appointment = Appointment(
            user=request.user,
            doctor_id=doctor_id,
            appointment_type=appointment_type,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            symptom_or_medicine_id = symptom_or_medicine_id,
            symptom_or_medicine_categoryid = symptom_or_medicine_categoryid,
            symptom_description=symptom_description,
            prescription_needed=prescription_needed,
            medications=medications,
            past_illnesses=past_illnesses,
            allergies=allergies,
        )

        # 日付と時間を組み合わせてdatetimeオブジェクトを作成
        appointment_date_time_start = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")

        # 終了時間を開始時間から30分後に設定
        appointment_date_time_end = appointment_date_time_start + timedelta(minutes=30)

        # Doctorオブジェクトを取得
        doctor = get_object_or_404(CustomUser, id=doctor_id)

        print(symptom_description)
        print(appointment_date_time_start.isoformat())
        print(appointment_date_time_end.isoformat())
        print(request.user.email)
        print(doctor.email)

        # Google Meetリンクの生成
        google_helper = GoogleCalendarHelper(request)
        try:
            event = google_helper.create_event(
                summary="診療予約",
                description=symptom_description,
                start_time=appointment_date_time_start.isoformat(),
                end_time=appointment_date_time_end.isoformat(),
                attendees=[request.user.email, doctor.email]
            )
        except HttpError as error:
            error_response = error.content.decode('utf-8')
            
            if 'notACalendarUser' in error_response:
                print('Google Calendar にサインアップしていないため、予約を完了できません。')
            else:
                print("Google Calendar API の呼び出し中にエラーが発生しました。詳細: ")
                print(error_response)
        
        
        # 生成されたGoogle Meetリンクとidを保存
        appointment.meet_link = event.get('hangoutLink')
        appointment.event_id = event.get('id')
        appointment.save()

        user = request.user
        profile = user.profile

        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=5000,
                currency='jpy',
                customer=profile.stripe_customer_id,  # Stripeに保存されているユーザーのCustomer ID
                payment_method=profile.default_payment_method_id,  # デフォルトの支払い方法
                off_session=True,  # ユーザーが直接関与していない取引を行う場合に使用
                confirm=True,  # 自動的に支払いを確認
                capture_method='manual',  # 支払いを保留にする

            )
            # 支払いが成功したら、支払い情報を予約に関連付けることができます。
            appointment.payment_intent_id = payment_intent['id']
            appointment.save()
        except stripe.error.CardError as e:
            # 支払いエラー処理
            err = e.error
            print(err['message'])
        except Exception as e:

            print(str(e))



        # 予約情報のIDをセッションに保存
        request.session['recent_appointment_id'] = appointment.id


    return render(request, 'accounts/user_mypage.html')
    
def appointment_confirmation_page(request):
    # セッションから直近の予約情報を取得する
    appointment_id = request.session.get('recent_appointment_id')
    print(appointment_id)
    if not appointment_id:
        return render(request, 'error.html', {"message": "予約情報が見つかりませんでした。"})

    appointment = Appointment.objects.get(id=appointment_id)

    # 予約確認ページを表示
    return render(request, 'appointments/appointment_confirmation.html', {'appointment': appointment})

def edit_appointment_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()

            google_helper = GoogleCalendarHelper(request)
            start_time=datetime.strptime(f"{appointment.appointment_date} {appointment.appointment_time}", "%Y-%m-%d %H:%M:%S")
            end_time=start_time + timedelta(minutes=30)

            event = google_helper.update_event(
                summary="診療予約",
                description=appointment.symptom_description,
                start_time=start_time,
                end_time=end_time,
                event_id=appointment.event_id,
            )
            
            appointment.meet_link = event.get('hangoutLink')
            appointment.event_id = event.get('id')
            appointment.save()
            return redirect('appointment_list')
    else:
        form = AppointmentForm(instance=appointment)

    return render(request, 'appointments/edit_appointment.html', {'form': form, 'appointment': appointment})