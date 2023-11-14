import os
import ast
import json
import requests
from datetime import datetime
from pprint import pprint as print
from requests.exceptions import Timeout
from app import app, db
from app.classes import AdminPFD, SertificatePDF
from app.mail import send_email
from sqlalchemy.orm import joinedload
from flask import flash, jsonify, request, abort
from flask_login import current_user
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import unidecode

def replacing_quotes(word: str) -> str:
    """Ищет в словах одинарные кавычки, и заменяет их на кавычки-ёлочки, таким образом текст в PDF файле будет выглядеть лучше и читабельнее"""
    if word[0] == "'" or word[0] == '"':
        word = list(word)
        word[0] = "«"
        word = ''.join(word)
        if word.replace('«', '').replace('»', '')[0] == "'" or word.replace('«', '').replace('»', '')[0] == '"':
            word = word.replace('«"', '««').replace("«'", '««')
    if word[-1] == "'" or word[-1] == '"':
        word = list(word)
        word[-1] = "»"
        word = ''.join(word)
        if word.replace('«', '').replace('»', '')[-1] == "'" or word.replace('«', '').replace('»', '')[-1] == '"':
            word = word.replace('"»', '»»').replace("'»", '»»')
    word = word.replace("'", '').replace('"', '')
    return word

async def get_information_on_the_google_table(table_id: str, info_table=False, info_table_grid=False) -> json:
    """Получение информации о таблице по её table_id"""
    SCOPES = app.config['SCOPES_GOOGLE']
    SPREADSHEET_ID = table_id
    creds = None
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except:
            app.logger.error(f'Ошибка валидности токена для взаимодействия с GOOGLE таблицами.', exc_info=True)
            return
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except:
                with open('token.json', 'r+') as file:
                    json_token = ast.literal_eval(file.read())
                    try:
                        data_google_token = requests.post('https://accounts.google.com/o/oauth2/token', data={'client_id': json_token.get('client_id'), 'client_secret': json_token.get('client_secret'), 'refresh_token': json_token.get('refresh_token'), 'grant_type': 'refresh_token'}, timeout=10).json()
                    except Timeout:
                        return
                    if data_google_token.get('error', None) is not None and data_google_token.get('error') == 'invalid_grant':
                        return
                    json_token['token'] = str(data_google_token['access_token'])
                    file.seek(0)
                    file.truncate()
                    file.write(str(json_token))
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        service = build('sheets', 'v4', credentials=creds)
        # Call the Sheets API
        sheet = service.spreadsheets()
        if info_table is not False and info_table_grid is not False:
            response_data = sheet.get(spreadsheetId=SPREADSHEET_ID,
                                        ranges=[], includeGridData=True).execute()
        elif info_table is not False and info_table_grid is False:
            response_data = sheet.get(spreadsheetId=SPREADSHEET_ID,
                                        ranges=[], includeGridData=False).execute()
        return response_data
    except HttpError as err:
        app.logger.error(f'Произошла ошибка получения информации о таблице: \n {err}', exc_info=True)
        return

def values_batch_update_in_google_spreadsheet(SPREADSHEET_ID: str = "", input_body: list[dict] = [], value_input_option: str ="USER_ENTERED") -> None:
    """Вставляет значения в таблицу, по указанному диапазону ячеек, диапазон ячеек указывается в параметре input_body"""

    if SPREADSHEET_ID == "":
        flash('Невозможно изменить значение ячейки, не обнаружено ID таблицы.', 'error')
        return
    
    SCOPES: str = app.config['SCOPES_GOOGLE']
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if creds is None:
        app.logger.error(f'Ошибка множественного изменения ячеек таблицы, отсутствует параметр creds.')
        return
    
    try:
        service = build('sheets', 'v4', credentials=creds)
        body = {
            'valueInputOption': value_input_option,
            'data': input_body,
            'includeValuesInResponse': False
        }
        result = service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID, body=body).execute()
    except HttpError as error:
        app.logger.error(f'Ошибка множественного изменения ячеек таблицы: \n\n {error}')
        return
    return

def AutoSendingEmailsAdmin(SPREADSHEET_ID: str = app.config['TABLE_LETTERS_TO_MANAGERS_SPREADSHEET_ID'], value_render_option: str = 'FORMATTED_VALUE', date_time_render_option: str = 'SERIAL_NUMBER', major_dimension: str = 'ROWS') -> None:
    SCOPES: str = app.config['SCOPES_GOOGLE']
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if creds is None:
        app.logger.error(f'Ошибка получения значений страниц произошла ошибка, отсутствует параметр creds.')
        return
    
    service = build('sheets', 'v4', credentials=creds)
    range = "Ответы на форму (1)" #Название листа, с которого читаются значение ячеек

    try:
        response = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=range, valueRenderOption=value_render_option, dateTimeRenderOption=date_time_render_option, majorDimension=major_dimension).execute()
    except TypeError as msg:
        app.logger.error(f'Ошибка получения данных из таблицы писем гос. пабликам: \n {msg}', exc_info=True)
        return
    number_user = 1
    for value in response['values'][1:]:
        current_date = datetime.now().strftime('%d-%m-%y %H:%M:%S')
        status = ''
        try:
            status = value[18]
            can_send = value[20]
            if can_send == 'FALSE':
                can_send = False
            elif can_send == 'TRUE':
                can_send = True
        except IndexError:
            status = False
            can_send = False
            pass
        number_user += 1
        if not status and can_send or status != 'Доставлено' and can_send:
            try:
                email_one = value[3]
                email_two = value[12]
            except IndexError as msg:
                app.logger.error(f'Ошибка получения данных почты: \n {msg}', exc_info=True)
                values_batch_update_in_google_spreadsheet(SPREADSHEET_ID, [
                    {
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                f"{current_date}"
                            ]
                        ],
                        "range": f"R{number_user}"
                    },
                    {
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                f"Ошибка получения данных почты: \n {msg}"
                            ]
                        ],
                        "range": f"S{number_user}"
                    }
                ])
                continue
            try:
                text_header = value[14]
                text_greeting = value[15]
                text_body = value[16]
            except IndexError as msg:
                app.logger.error(f'Ошибка получения данных текстов для отправки: \n {msg}', exc_info=True)
                values_batch_update_in_google_spreadsheet(SPREADSHEET_ID, [
                    {
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                f"{current_date}"
                            ]
                        ],
                        "range": f"R{number_user}"
                    },
                    {
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                f"Ошибка получения данных текстов для отправки: \n {msg}"
                            ]
                        ],
                        "range": f"S{number_user}"
                    }
                ])
                continue
            try:
                name_employee = value[9]
            except IndexError as msg:
                app.logger.error(f'Ошибка получения данных о сотруднике: \n {msg}', exc_info=True)
                values_batch_update_in_google_spreadsheet(SPREADSHEET_ID, [
                    {
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                f"{current_date}"
                            ]
                        ],
                        "range": f"R{number_user}"
                    },
                    {
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                f"Ошибка получения данных о сотруднике: \n {msg}"
                            ]
                        ],
                        "range": f"S{number_user}"
                    }
                ])
                continue
            try:
                employee_gender = value[13]
            except IndexError as msg:
                app.logger.error(f'Ошибка получения данных пола сотруднике: \n {msg}', exc_info=True)
                values_batch_update_in_google_spreadsheet(SPREADSHEET_ID, [
                    {
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                f"{current_date}"
                            ]
                        ],
                        "range": f"R{number_user}"
                    },
                    {
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                f"Ошибка получения данных пола сотруднике: \n {msg}"
                            ]
                        ],
                        "range": f"S{number_user}"
                    }
                ])
                continue
            try:
                organization = value[7]
            except IndexError as msg:
                app.logger.error(f'Ошибка получения данных организации сотруднике: \n {msg}', exc_info=True)
                values_batch_update_in_google_spreadsheet(SPREADSHEET_ID, [
                    {
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                f"{current_date}"
                            ]
                        ],
                        "range": f"R{number_user}"
                    },
                    {
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                f"Ошибка получения данных организации сотруднике: \n {msg}"
                            ]
                        ],
                        "range": f"S{number_user}"
                    }
                ])
                continue
            if email_one and text_header and text_greeting and text_body and employee_gender:
                pdf_file = AdminPFD({
                    "header": text_header.replace('\n', ' <br />'),
                    "greeting": ' '.join(
                        list(
                            map(replacing_quotes, 
                                text_greeting
                                .replace(' !', '!')
                                .replace('\n', '<br />').split()
                                ))),
                    "body": text_body.replace('\n', '<br />'),
                    "date": datetime.now().strftime('%d.%m.%Y')
                })
                pdf_file.generate_admin_pdf()
                mail_text_body = '' #body письма, которое будет отправляться пользователям
                #subject - тема email письма, отправляемое пользователям
                send_status = send_email(subject='', recipients=[str(email_one), str(email_two)] if email_one and email_two else [str(email_one)], text=True, text_body=mail_text_body, attachment=True, attachments=[{'path': f'{pdf_file.output_path}{pdf_file.id_doc}.pdf', 'name': 'Blagodarstvennoe_pismo_ot_VK_za_' + str(unidecode.unidecode(name_employee)).replace("'", "").replace(" ", "_")}])
                if send_status['status'] == 'error':
                    values_body = [
                        {
                            "majorDimension": "ROWS",
                            "values": [
                                [
                                    f"{current_date}"
                                ]
                            ],
                            "range": f"R{number_user}"
                        },
                        {
                            "majorDimension": "ROWS",
                            "values": [
                                [
                                    f"{send_status['msg']}"
                                ]
                            ],
                            "range": f"S{number_user}"
                        },
                        {
                            "majorDimension": "ROWS",
                            "values": [
                                [
                                    ""
                                ]
                            ],
                            "range": f"T{number_user}"
                        }
                    ]
                    values_batch_update_in_google_spreadsheet(SPREADSHEET_ID, values_body)
                    return
                values_body = [
                    {
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                f"{current_date}"
                            ]
                        ],
                        "range": f"R{number_user}"
                    },
                    {
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                "Доставлено"
                            ]
                        ],
                        "range": f"S{number_user}"
                    },
                    {
                        "majorDimension": "ROWS",
                        "values": [
                            [
                                f"{app.config['URL_PATH_TO_MAIL_PDF']}{pdf_file.id_doc}.pdf"
                            ]
                        ],
                        "range": f"T{number_user}"
                    }
                ]
                values_batch_update_in_google_spreadsheet(SPREADSHEET_ID, values_body)
    return