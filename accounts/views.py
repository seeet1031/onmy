from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, UserProfileForm, ProfileForm
from .models import Department, Profile, DoctorProfile, Appointment, DoctorSchedule
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db.models import Case, When, Value, CharField
from accounts.models import Appointment, Medicine, Symptom,Prescription
from collections import defaultdict
from django.shortcuts import render, get_object_or_404
from .models import MedicalRecord, CustomUser
from datetime import datetime, timedelta
from django.http import JsonResponse
import json
from django.utils.dateparse import parse_date, parse_time
from django.urls import reverse


# Stripe APIキーの設定
stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def user_signup_view(request):

    # 初期預かり金の設定
    intent = stripe.PaymentIntent.create(
        amount=5000,  # 金額を設定
        currency='jpy',
        payment_method_types=["card"],
    )
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = ProfileForm(request.POST, request.FILES)
        
        # 支払い方法はrequest.POSTから取得
        #payment_method_type = request.POST.get('payment_method')
        payment_method_type = 'card'

        print(user_form)
        print(profile_form)

        if user_form.is_valid() and profile_form.is_valid():

            # 顧客IDを保存する
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            # Stripe顧客を作成
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}",
            )
            profile.stripe_customer_id = customer.id

            try:
                if payment_method_type == 'card':
                    # カード情報の取得
                    token = request.POST.get('stripeToken')
                    if not token:
                        raise ValueError("カード情報が不足しています。")

                    # 支払い方法を作成
                    payment_method = stripe.PaymentMethod.create(
                        type="card",
                        card={"token": token},
                        billing_details={
                            "name": f"{user.first_name} {user.last_name}",
                        },
                    )

                    # 3. PaymentMethodを顧客にアタッチ
                    stripe.PaymentMethod.attach(
                        payment_method.id,
                        customer=customer.id,
                    )

                    # 4. 顧客のデフォルト支払い方法を設定
                    stripe.Customer.modify(
                        customer.id,
                        invoice_settings={"default_payment_method": payment_method.id},
                    )

                elif payment_method_type == 'alipay':
                    # Alipayの場合の処理
                    payment_method = stripe.PaymentMethod.create(
                        type="alipay",
                        billing_details={
                            "name": f"{user.first_name} {user.last_name}",
                        },
                    )

                # デフォルトの支払い方法として設定
                profile.default_payment_method_id = payment_method.id
                profile.save()

                login(request, user)
                return redirect('user_mypage')

            except stripe.error.CardError as e:
                return render(request, 'accounts/user_signup.html', {
                    'error': str(e),
                    'user_form': user_form,
                    'profile_form': profile_form
                })

    else:
        user_form = CustomUserCreationForm()
        profile_form = ProfileForm()

    return render(request, 'accounts/user_signup.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })

def user_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.role == 'user':
            login(request, user)
            return redirect('user_mypage')
        else:
            return render(request, 'accounts/user_login.html', {'error': 'Invalid credentials'})
    return render(request, 'accounts/user_login.html')

def doctor_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.role == 'doctor':
            login(request, user)
            return redirect('doctor_mypage')
        else:
            return render(request, 'accounts/doctor_login.html', {'error': 'Invalid credentials'})
    return render(request, 'accounts/doctor_login.html')

def admin_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.role == 'admin':
            login(request, user)
            return redirect('admin_mypage')
        else:
            return render(request, 'accounts/admin_login.html', {'error': 'Invalid credentials'})
    return render(request, 'accounts/admin_login.html')


@login_required
def user_mypage_view(request):
    if request.user.role != 'user':
        return redirect('user_login')
    
    # 現在の日時を取得
    now = datetime.now()
    # 24時間後の日時を計算
    next_24_hours = now + timedelta(hours=24)

    # 現在の日時と24時間後の日時の範囲でフィルタリング
    appointments = Appointment.objects.filter(
        user=request.user,
        status='in_progress',
        appointment_date__gte=now.date(),
        appointment_date__lte=next_24_hours.date()
    ).order_by('appointment_date', 'appointment_time')

    medicines = Medicine.objects.filter(is_active=True).order_by('category')
    symptoms = Symptom.objects.filter(is_active=True).order_by('category')
    
    medicine_groups = defaultdict(list)
    symptom_groups = defaultdict(list)
    
    # 辞書に薬名と症状名をマッピング
    medicine_dict = {medicine.id: medicine.name for medicine in medicines}
    symptom_dict = {symptom.id: symptom.name for symptom in symptoms}
    
    for medicine in medicines:
        medicine_groups[medicine.category].append(medicine)
    
    for symptom in symptoms:
        symptom_groups[symptom.category].append(symptom)

    # appointmentsに対応する薬名または症状名を追加
    for appointment in appointments:
        if appointment.symptom_or_medicine_categoryid == 1:  # 症状の場合
            appointment.symptom_name = symptom_dict.get(appointment.symptom_or_medicine_id, "")
        elif appointment.symptom_or_medicine_categoryid == 2:  # 薬の場合
            appointment.medicine_name = medicine_dict.get(appointment.symptom_or_medicine_id, "")

    return render(request, 'accounts/user_mypage.html', {
        'appointments': appointments,
        'medicine_groups': dict(medicine_groups),
        'symptom_groups': dict(symptom_groups),
    })


@login_required
def doctor_mypage_view(request):
    if request.user.role != 'doctor':
        return redirect('doctor_login')
    
    # 現在のログインユーザーが医師であることを確認
    if request.user.role != 'doctor':
        return render(request, 'error.html', {"message": "このページにアクセスする権限がありません。"})
    
    # 現在の日時を取得
    now = datetime.now()
    # 24時間後の日時を計算
    next_24_hours = now + timedelta(hours=24)

    # 現在の日時と24時間後の日時の範囲でフィルタリング
    appointments = Appointment.objects.filter(
        doctor=request.user,
        status='in_progress',
        appointment_date__gte=now.date(),
        appointment_date__lte=next_24_hours.date()
    ).order_by('appointment_date', 'appointment_time')

    medicines = Medicine.objects.filter(is_active=True).order_by('category')
    symptoms = Symptom.objects.filter(is_active=True).order_by('category')
    
    medicine_groups = defaultdict(list)
    symptom_groups = defaultdict(list)
    
    # 辞書に薬名と症状名をマッピング
    medicine_dict = {medicine.id: medicine.name for medicine in medicines}
    symptom_dict = {symptom.id: symptom.name for symptom in symptoms}
    
    for medicine in medicines:
        medicine_groups[medicine.category].append(medicine)
    
    for symptom in symptoms:
        symptom_groups[symptom.category].append(symptom)

    # appointmentsに対応する薬名または症状名を追加
    for appointment in appointments:
        if appointment.symptom_or_medicine_categoryid == 1:  # 症状の場合
            appointment.symptom_name = symptom_dict.get(appointment.symptom_or_medicine_id, "")
        elif appointment.symptom_or_medicine_categoryid == 2:  # 薬の場合
            appointment.medicine_name = medicine_dict.get(appointment.symptom_or_medicine_id, "")

    return render(request, 'accounts/doctor_mypage.html', {
        'appointments': appointments,
        'medicine_groups': dict(medicine_groups),
        'symptom_groups': dict(symptom_groups),
    })












@login_required
def admin_mypage_view(request):
    if request.user.role != 'admin':
        return redirect('admin_login')
    return render(request, 'accounts/admin_mypage.html')


def logout_view(request):
    if request.user.is_authenticated:
        user_role = request.user.role
        logout(request)
        if user_role == 'admin':
            return redirect('admin_login')
        elif user_role == 'doctor':
            return redirect('doctor_login')
        else:
            return redirect('user_login')
    else:
        return redirect('user_login')

@login_required
def basic_info_view(request):
    if request.user.is_authenticated:
        user_role = request.user.role
        if user_role == 'admin':
            profile = DoctorProfile.objects.get(user=request.user)
            return render(request, 'accounts/doctor_basic_info.html', {'profile': profile})
        elif user_role == 'doctor':
            profile = DoctorProfile.objects.get(user=request.user)
            return render(request, 'accounts/doctor_basic_info.html', {'profile': profile})
        
    profile = Profile.objects.get(user=request.user)
    return render(request, 'accounts/basic_info.html', {'profile': profile})

@login_required
def edit_basic_info_view(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            payment_method_type = profile_form.cleaned_data.get('payment_method', None)
            stripe_token = request.POST.get('stripeToken', None)
            
            if payment_method_type == 'card' and stripe_token:
                if profile.stripe_customer_id:
                    # 新しい支払い方法を作成
                    payment_method = stripe.PaymentMethod.create(
                        type="card",
                        card={"token": stripe_token},
                        billing_details={
                            "name": f"{user.first_name} {user.last_name}",
                        },
                    )
                    
                    # 支払い方法をStripeの顧客にアタッチ
                    stripe.PaymentMethod.attach(
                        payment_method.id,
                        customer=profile.stripe_customer_id,
                    )

                    # デフォルトの支払い方法を更新
                    stripe.Customer.modify(
                        profile.stripe_customer_id,
                        invoice_settings={
                            'default_payment_method': payment_method.id,
                        },
                    )
                    
                    # ローカルデータベースの更新
                    profile.default_payment_method_id = payment_method.id
                    profile.save()
                    print('いいいい')
                    print(stripe_token)

            elif payment_method_type == 'alipay':
                profile.default_payment_method_id = None
                profile.save()
            
            print('ああああ')
            print(payment_method_type)
            return render(request, 'accounts/basic_info.html', {'profile': profile})
    
    else:
        user_form = CustomUserCreationForm(instance=user)
        profile_form = ProfileForm(instance=profile)

        # Stripeから既存のカード情報を取得
        if profile.stripe_customer_id:
            payment_methods = stripe.PaymentMethod.list(
                customer=profile.stripe_customer_id,
                type="card",
            )
            if payment_methods.data:
                # 最初のカード情報を取得してテンプレートに渡す
                card_info = payment_methods.data[0].card

    print(card_info)
    return render(request, 'accounts/edit_basic_info.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'card_info': card_info,  # カード情報をテンプレートに渡す
    })

@login_required
def appointment_list_view(request):
    appointments = Appointment.objects.filter(user=request.user, status='in_progress').order_by('-appointment_date')
    past_appointments = Appointment.objects.filter(user=request.user).exclude(status='in_progress').order_by('-appointment_date')
    return render(request, 'accounts/appointment_list.html', {'appointments': appointments,'past_appointments':past_appointments})

login_required
def doctor_appointment_list_view(request):
    # 現在のログインユーザーが医師であることを確認
    if request.user.role != 'doctor':
        return render(request, 'error.html', {"message": "このページにアクセスする権限がありません。"})
    
    appointments = Appointment.objects.filter(doctor=request.user, status='in_progress').order_by('appointment_date', 'appointment_time')
    medicines = Medicine.objects.filter(is_active=True).order_by('category')
    symptoms = Symptom.objects.filter(is_active=True).order_by('category')
    
    medicine_groups = defaultdict(list)
    symptom_groups = defaultdict(list)
    
    # 辞書に薬名と症状名をマッピング
    medicine_dict = {medicine.id: medicine.name for medicine in medicines}
    symptom_dict = {symptom.id: symptom.name for symptom in symptoms}
    
    for medicine in medicines:
        medicine_groups[medicine.category].append(medicine)
    
    for symptom in symptoms:
        symptom_groups[symptom.category].append(symptom)

    # appointmentsに対応する薬名または症状名を追加
    for appointment in appointments:
        if appointment.symptom_or_medicine_categoryid == 1:  # 症状の場合
            appointment.symptom_name = symptom_dict.get(appointment.symptom_or_medicine_id, "")
        elif appointment.symptom_or_medicine_categoryid == 2:  # 薬の場合
            appointment.medicine_name = medicine_dict.get(appointment.symptom_or_medicine_id, "")

    return render(request, 'accounts/doctor_appointment_list.html', {
        'appointments': appointments,
        'medicine_groups': dict(medicine_groups),
        'symptom_groups': dict(symptom_groups),
    })


def save_prescription(request):
    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')
        status = request.POST.get('status')
        consultation_fee = float(request.POST.get('consultation_fee'))
        total_fee = float(request.POST.get('total_fee'))
        diagnosis = 'diagnosis' in request.POST

        treatment_type = request.POST.get('treatment_type')
        insurance_coverage = int(request.POST.get('insurance_coverage', 0))
        total_fee = float(request.POST.get('total_fee'))  # 実際の総料金

        # 保険診療の場合の割引の適用
        if treatment_type == 'insurance':
            # 保険負担分を計算して引く
            discount_rate = insurance_coverage / 100
            final_amount = total_fee * (1 - discount_rate)
        else:
            final_amount = total_fee


        appointment = Appointment.objects.get(id=appointment_id)
        print(appointment.payment_intent_id)
        print(appointment.status)
        appointment.status = status
        appointment.save()

        # 薬の保存
        medicines = request.POST.getlist('medicine[]')
        custom_medicines = request.POST.getlist('medicine_custom[]')
        days = request.POST.getlist('days[]')

        for i, medicine_id in enumerate(medicines):
            if medicine_id == 'other':
                medicine_name = custom_medicines[i]
                price = 1000  # 仮の価格、実際にはユーザー入力を考慮する
            else:
                medicine = Medicine.objects.get(id=medicine_id)
                medicine_name = medicine.name
                price = 500  # 仮の価格、実際にはマスタの価格を使用

            Prescription.objects.create(
                appointment=appointment,
                medicine_name=medicine_name,
                price=price,
                days=days[i]
            )

        print('aaaa')
        print(appointment.payment_intent_id)
        if appointment.payment_intent_id and isinstance(appointment.payment_intent_id, str):
            print('bbb')

        # Stripe支払いの実行
        try:
            payment_intent = stripe.PaymentIntent.capture(
                appointment.payment_intent_id,
                amount=int(total_fee)  # Stripeは金額をセント単位で扱う
            )
        except stripe.error.StripeError as e:
            print(f"Stripeエラー: {str(e)}")

        # 処方を保存または送信の処理
        if request.POST.get('action') == 'send':
            # 処方箋の送信処理（例: メールで送信など）
            send_prescription(appointment)
        else:
            # 処方箋を作成するだけの場合
            pass

        return redirect('doctor_appointment_list')  # 処方箋作成後にリダイレクトする先を指定

def send_prescription(appointment):
    # 処方箋を患者に送信する処理を記述（例: メール送信など）
    # ここにメール送信や他の処理を追加できます
    pass


@login_required
def patient_list_view(request):
    doctor_id = request.user.id
    # ログインしている医者が担当している患者のリストを取得（Appointmentでグループ化）
    patients = CustomUser.objects.filter(user_appointments__doctor_id=doctor_id).distinct()
    return render(request, 'accounts/patient_list.html', {'patients': patients})    

def medical_record_list_view(request, user_id,appointment_id):
    user = get_object_or_404(CustomUser, id=user_id)
    records = MedicalRecord.objects.filter(user=user).order_by('-created_at')
    return render(request, 'accounts/medical_record_list.html', {'records': records, 'user': user, 'appointment_id':appointment_id})

def medical_record_detail_view(request, record_id,user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    records = MedicalRecord.objects.filter(id=record_id).order_by('-created_at')
    return render(request, 'accounts/medical_record_detail.html', {'records': records, 'user': user})


def create_medical_record_view(request, user_id,appointment_id):
    user = get_object_or_404(CustomUser, id=user_id)
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == 'POST':
        # POSTデータを取得してカルテを作成
        chief_complaint = request.POST.get('chief_complaint')
        cause = request.POST.get('cause')
        main_symptoms = request.POST.get('main_symptoms')
        progress = request.POST.get('progress')
        prescription = request.POST.get('prescription')
        treatment = request.POST.get('treatment')

        MedicalRecord.objects.create(
            user=user,
            doctor=request.user,  # 現在ログインしている医師を設定
            record_content=f"主訴: {chief_complaint}, 原因: {cause}, 主要症状: {main_symptoms}, 経過: {progress}, 処方: {prescription}, 処置: {treatment}",
            appointment_id=appointment.id
        )
        # Appointmentのステータスを 'examined' に更新
        appointment.status = 'examined'
        appointment.save()

        
        records = MedicalRecord.objects.filter(user=user).order_by('-created_at')
        #return redirect('medical_record_list', user_id=user.id)
        return redirect('doctor_appointment_list')

    return render(request, 'accounts/create_medical_record.html', {'user': user, 'appointment': appointment, 'appointment_id': appointment_id})



@login_required
def doctor_schedule_view(request):
    # 今日から1週間の日付リストを作成
    today = datetime.now().date()
    dates = [today + timedelta(days=i) for i in range(7)]

    # 時間リストを作成（30分間隔）
    times = [f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in (0, 30)]

    # DoctorScheduleデータを取得し、schedule_dictに格納
    doctor_schedules = DoctorSchedule.objects.filter(doctor=request.user)
    schedule_dict = defaultdict(list)

    for schedule in doctor_schedules:
        date_str = schedule.date.strftime('%Y-%m-%d')
        time_str = schedule.start_time.strftime('%H:%M')  # 開始時間を文字列に変換
        schedule_dict[date_str].append(time_str)  # 各日付に時間を追加

    # 各日付の時間をソートしておく
    for date in schedule_dict:
        schedule_dict[date] = sorted(schedule_dict[date])

    return render(request, 'accounts/doctor_schedule.html', {
        'dates': dates,
        'times': times,
        'schedule_dict': schedule_dict,
    })

def save_schedule_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            schedule_data = data.get('schedule', [])

            # スケジュール保存のロジック
            for item in schedule_data:
                date = parse_date(item['date'])
                time = parse_time(item['time'])

                # スケジュールがすでに登録されているか確認
                if not DoctorSchedule.objects.filter(doctor=request.user, date=date, start_time=time).exists():
                    # 30分単位で終了時間を計算
                    end_time = (datetime.combine(date, time) + timedelta(minutes=30)).time()

                    # DoctorScheduleモデルにスケジュールを保存
                    DoctorSchedule.objects.create(
                        doctor=request.user,
                        date=date,
                        start_time=time,
                        end_time=end_time
                    )

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@csrf_exempt
def delete_schedule_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            date = data.get('date')
            time_range = data.get('times')  # 例: "01:30 - 03:00"

            if not date or not time_range:
                return JsonResponse({'success': False, 'message': '日付または時間範囲が指定されていません。'})

            # 時間範囲を分割して、開始時間と終了時間を取得
            start_time_str, end_time_str = time_range.split(' - ')
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()

            # 日付をdatetimeオブジェクトに変換
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()

            # データベースから該当するエントリを削除
            DoctorSchedule.objects.filter(
                date=date_obj,
                start_time__gte=start_time,
                start_time__lt=end_time  # 終了時間は開始時間よりも小さい（開始時間から30分ごとのデータの範囲内）
            ).delete()

            return JsonResponse({'success': True, 'message': 'スケジュールが削除されました。'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': '無効なJSON形式です。'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    else:
        return JsonResponse({'success': False, 'message': '無効なリクエストメソッドです。'})
    





login_required
def admin_appointment_list_view(request):
    # 現在のログインユーザーが医師であることを確認
    if request.user.role != 'admin':
        return render(request, 'error.html', {"message": "このページにアクセスする権限がありません。"})
    
    appointments = Appointment.objects.filter(status='examined').order_by('appointment_date', 'appointment_time')
    medicines = Medicine.objects.filter(is_active=True).order_by('category')
    symptoms = Symptom.objects.filter(is_active=True).order_by('category')
    
    medicine_groups = defaultdict(list)
    symptom_groups = defaultdict(list)
    
    # 辞書に薬名と症状名をマッピング
    medicine_dict = {medicine.id: medicine.name for medicine in medicines}
    symptom_dict = {symptom.id: symptom.name for symptom in symptoms}
    
    for medicine in medicines:
        medicine_groups[medicine.category].append(medicine)
    
    for symptom in symptoms:
        symptom_groups[symptom.category].append(symptom)

    # appointmentsに対応する薬名または症状名を追加
    for appointment in appointments:
        if appointment.symptom_or_medicine_categoryid == 1:  # 症状の場合
            appointment.symptom_name = symptom_dict.get(appointment.symptom_or_medicine_id, "")
        elif appointment.symptom_or_medicine_categoryid == 2:  # 薬の場合
            appointment.medicine_name = medicine_dict.get(appointment.symptom_or_medicine_id, "")

    return render(request, 'accounts/admin_appointment_list.html', {
        'appointments': appointments,
        'medicine_groups': dict(medicine_groups),
        'symptom_groups': dict(symptom_groups),
    })



@login_required
def cancel_appointment(request):
    appointment_id = request.POST.get('appointment_id')
    try:
        appointment = Appointment.objects.get(id=appointment_id, user=request.user)
        appointment.status = 'cancelled'
        print(111)

        appointment.save()
        return JsonResponse({'success': True})
    except Appointment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Appointment does not exist.'})