import threading
from threading import Thread
from flask_mail import Message
from app import app, mail
from smtplib import SMTPRecipientsRefused

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except SMTPRecipientsRefused as error_msg:
            app.logger.error(f'Ошибка отправки email сообщения: \n\n ОШИБКА: \n {error_msg} \n\n ДАННЫЕ СООБЩЕНИЯ: \n {msg}', exc_info=True)
            return {
                'status': 'error',
                'msg': f'Ошибка отправки \n {error_msg}'
            }
        return {
            'status': 'Ok'
        }
            
class ThreadWithReturnValue(Thread):
    
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return

def send_email(subject: str = app.config['MAIL_DEFAULT_THEME'], sender: str = app.config['MAIL_DEFAULT_SENDER'], recipients: list[str] = [], text: bool = True, text_body: str = '', html: bool = False, html_body: str = '', attachment: bool = False, attachments: list[dict] = []):
    """Функция, отвечающая за отправку email письма пользователям \n
    subject - тема письма\n
    sender - отправитель письма\n
    recipients - получатели письма\n
    text - если True - необходимо передать тело письма\n
    html - если True - необходимо передать html разметку, которая отобразится в письме\n
    attachment - если True - необходимо передать список со словарями, описывающие файлы, необходимые для прикрепления\n
    Пример attachment [{'path': f'47493b0de9b9f53aa2674a7889af0a7176cd360768638716a71619bcdd19777c.pdf', 'name': 'Blagodarstvenoe_pismo'}]
    """
    msg = Message(subject, sender=sender, recipients=recipients)
    if text:
        msg.body = text_body
    if html:
        msg.html = html_body
    if attachment:
        for doc in attachments:
            with app.open_resource(str(doc['path']).replace('app/', '')) as fp:
                msg.attach(f"{doc['name']}.pdf", "doc/pdf", fp.read())
    thread = ThreadWithReturnValue(target=send_async_email, args=(app, msg))
    thread.start()
    return thread.join()
