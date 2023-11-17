import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = "secret-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
#    SESSION_COOKIE_SECURE = True
#    REMEMBER_COOKIE_SECURE = True
#    SESSION_COOKIE_HTTPONLY = True # необязательно, т.к по умолчанию в сессии стоит True
#    REMEMBER_COOKIE_HTTPONLY = True
#    SESSION_COOKIE_SAMESITE="Lax"
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024
    SCOPES_GOOGLE = ["https://www.googleapis.com/auth/spreadsheets"]
    URL_PATH_TO_MAIL_PDF = "http://127.0.0.1:5000/pdf/mail/"
    TABLE_LETTERS_TO_MANAGERS_SPREADSHEET_ID = "" #id гугл-таблицы (получается из ссылки на таблицу)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.mail.ru'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or '' #email с которого будут отправляться письма с генерированными pdf файлами
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or '' #пароль от email почты
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or '' #email с которого по умолчанию будут отправляться письма
    MAIL_DEFAULT_THEME = 'Письмо от внешнего сервиса' #тема - заголовок письма по умолчанию
    MAIL_ASCII_ATTACHMENTS = True