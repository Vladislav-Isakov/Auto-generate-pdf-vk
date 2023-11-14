from flask import render_template, flash, redirect, url_for, request, \
    jsonify, make_response, get_flashed_messages, abort, session, send_file
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db
from app.models import User, users_with_access_to_the_panel
from app.functions import AutoSendingEmailsAdmin
import time
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from app.classes import AdminPFD

# Проверка на доступ пользователя к панели
# если доступа нет - разлогирование
@app.before_request
async def before_request():
    if current_user.is_authenticated:
        if current_user.checking_access_to_the_panel() is None:
            flash('У Вас нет доступа к панели управления, вы будете разлогинены.', 'info')
            logout_user()
        current_user.last_seen = round(time.time())
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
@login_required
async def index():

    response = make_response(render_template('base.html'))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.route('/mail', methods=['GET', 'POST'])
@login_required
async def mail():
    # если необходимо встроить другое фоновое изображение следует раскомитить функцию и вставить в контекстный
    # менеджер название файла-изображения-щаблона для генерации PDF файла из гланой директории проекта
    # with open("example_mail_pdf.png", "rb") as img_file:
    #     b64_string = base64.b64encode(img_file.read()).decode()
    #     print(b64_string)

    # Данные для генерации тестового файла
    # Например для проверки как будет смотреться итоговый вариант
    pdf_file = AdminPFD({
        "header": "", #Заголовок, например: Гендиректору «VK» Владимиру С. К. info@authors.vk.company
        "greeting": "", #Приветствие, пример: Уважаемый Владимир Кириенко!
        "body": "", #Тело - описание которое будет в шаблоне
        "date": "22.08.2023" #Дата которая будет указана в pdf-файле, в футере
    })

    pdf_file.generate_admin_pdf()

    # Аналогично что описано выше, но введённые данные будут отображены только на странице по url /mail
    data = {
        "header": "",
        "greeting": "",
        "body": "",
        "date": ""
    }
    response = make_response(render_template('pdf/mail.html', data=data))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

# Url путь чтобы можно было скачать сгенерированный файл
@app.get('/pdf/mail/<path:path_to_file>')
@login_required
async def mail_pdf(path_to_file):
    if not os.path.exists(f'app/static/generate_pdf/mail/{path_to_file}'):
        response = make_response(render_template('errors/file_not_found.html', file=path_to_file))
        response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response
    return send_file(f'static/generate_pdf/mail/{path_to_file}', as_attachment=True)


# Url, который начинает генерацию PFD файлов
@app.get('/generate')
@login_required
async def generate_pdf():
    AutoSendingEmailsAdmin()
    return 'Генерация PDF файлов началась.'

# Url для получения токена - доступа к аккаунту пользователя
# для последующего чтения Google Sheets
@app.get('/google')
@login_required
async def google():
    SCOPES = app.config['SCOPES_GOOGLE']
    SAMPLE_SPREADSHEET_ID = app.config['TABLE_LETTERS_TO_MANAGERS_SPREADSHEET_ID']
    SAMPLE_RANGE_NAME = 'A1:B2'
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            flow.authorization_url(access_type='offline')
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)

        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME).execute()
    except HttpError as err:
        app.logger.error('Возникла ошибка в контексте аккаунта пользователя с ID: %s при попытке получить данные из таблицы, url: /google', current_user.vk_id, exc_info=True)
    return 'Ok'

@app.route('/user_notifications', methods=['GET'])
def user_notifications():
    json_notifications = {}
    for notifications in get_flashed_messages(with_categories=True):
        json_notifications.update({'message': notifications[1], 'category': notifications[0]})
    response = make_response(render_template('notifications/user_flash_notifications.html', json_notifications=json_notifications))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.get('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.args.get('uid', None) is not None:
        user_request = users_with_access_to_the_panel.query.filter_by(vk_id=int(request.args.get('uid'))).first()
        if user_request is None:
            session['user_vk_id'] = int(request.args.get('uid'))
            response = make_response(render_template('login/request_access_to_the_panel.html', vk_id=int(request.args.get('uid'))))
            response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            return response
        elif user_request is not None and user_request.access == 'Запрошен':
            flash('Вам ещё не выдали доступ к панели, ожидайте.', 'error')
            return redirect(url_for('login'))
        elif user_request is not None and user_request.access == 'Выдан':
            info_user = User.query.filter_by(vk_id=int(request.args.get('uid'))).first()
            if info_user is None:
                user = User(vk_id=int(request.args.get('uid')))
                db.session.add(user)
                db.session.commit()
                info_user = User.query.filter_by(vk_id=int(request.args.get('uid'))).first()
            session.pop('user_vk_id', None)
            login_user(info_user, remember=True)
            flash('Вы успешно вошли в свой аккаунт. Добро пожаловать в панель управления.', 'info')
            return redirect(url_for('index'))
    #Установка заголовков ответа сервера
    response = make_response(render_template('login/login.html'))
    response.headers['Strict-Transport-Security'] = 'max-age=15768000; includeSubDomains'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.post('/login')
def login_post():
    if request.form.get('method', None) is None:
        flash('Произошла ошибка, не найден метод действия, повторите попытку запроса доступа.', 'error')
        return abort(400)
    if request.form.get('method') == 'request_access':
        if session.get('user_vk_id', None) is None:
            flash('Произошла ошибка, не найдены данные аккаунта, повторите попытку запроса доступа.', 'error')
            return abort(400)
        user = users_with_access_to_the_panel.query.filter_by(vk_id=int(session['user_vk_id'])).first()
        if user is not None:
            flash('Вы уже запрашивали доступ к панели, повторный запрос не требуется.', 'error')
            return abort(400)
        else:
            user = users_with_access_to_the_panel(vk_id=int(session['user_vk_id']))
            db.session.add(user)
            db.session.commit()
        flash('Доступ успешно запрошен, ожидайте выдачи доступа к панели.', 'info')
        return redirect('/login', 303)
    else:
        flash('Произведено неизвестное действие, возможно Вы делаете что-то неправильно.', 'error')
        return redirect('/login', 303)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))