# Auto-generate-pdf-vk - В чём суть проекта?
⋅⋅⋅ Вам нужно отправлять множество PDF файлов, но делать это руками долго и не эффективно? Тогда автогенерация PDF вам в этом поможет.
⋅⋅⋅ С помощью многопоточности и асинхронности фреймворка достигается высокая скороть отправки файлов с письмами на почту пользователей.

## Используемый фреймворк Flask
⋅⋅⋅ Flask асинхронный, тем самым обращение к API сервисов или отправка файлов через API становится быстрее.
⋅⋅⋅ В проекте используется Flask версии 2.3.2, учитывайте это при реализации логики.
⋅⋅⋅ По умолчанию в проекте используется режим дебагинга - debug, если вы собираетесь разворачивать проект на своей машине, отключите данный режим в модуле run.py

## Многопоточность
⋅⋅⋅ Использование многопоточности ускоряет IO-bound(ввод-вывод) процессы, так мы обходим GIL - глобальную блокировку итерпритатора, т.к Python под капотом выполняет только один поток байт-код Python одновременно.
-- Многопоточность используется в модуле mail.py - для отправки писем на почты пользователей.

## Откуда берутся данные для отправки?
⋅⋅⋅ Данные: имя пользователя, фамилия, заголовок, тело текст в PFD файле и т.д. берутся из Google Sheets.
⋅⋅⋅ Вам необходимо создать гугл-таблицу, наполнить её данными. В конфигурации проекта config.py, указать в атрибуте TABLE_LETTERS_TO_MANAGERS_SPREADSHEET_ID класса вставить ID таблицы.
⋅⋅⋅ Пример ID таблицы, у нас есть ссылка вида https://docs.google.com/spreadsheets/d/1NsXDHSDPlVdf7gbNxC4Gib/edit#gid=0 - ID таблицы будет = 1NsXDHSDPlVdf7gbNxC4Gib

## Настройка конфигурации
⋅⋅⋅ Заходим в модуль config.py и следуем инструкции:
⋅⋅* Измените SECRET_KEY на любой, сложный ключ - для безопасности WEB-приложения. Можете сгенирировать hex строку в консоли, с помощью команды: 
```python
python -c 'import secrets; print(secrets.token_hex())'
```
⋅⋅* В атрибуте MAIL_USERNAME указываем email с которого будут отправляться письма.
⋅⋅* MAIL_PASSWORD - указываем пароль для внешних сервисов, сгенерировать его можно [тут](https://account.mail.ru/user/2-step-auth/passwords?back_url=https%3A%2F%2Fid.mail.ru%2Fsecurity).
⋅⋅* MAIL_DEFAULT_SENDER - указываем почту, с которой будут отправляться письма, в случае если не передадим её в функцию для отправки письма, будет использована почта по умолчанию.
⋅⋅* MAIL_DEFAULT_THEME - указываем тему письма по умолчанию, если не передадим её в функцию для отправки письма - будет использоваться она.
⋅⋅* Если будете заливать скрипт на свою машину, раскоментируйте атрибуты: SESSION_COOKIE_SECURE, REMEMBER_COOKIE_SECURE, SESSION_COOKIE_HTTPONLY, REMEMBER_COOKIE_HTTPONLY, SESSION_COOKIE_SAMESITE - они нужны для безопасности вашего WEB-приложения - Flask.

## Необходимые столбцы в гугл-таблице:
| A        | B           | C  | D | E        | F           | G  | H | I        | F           |
| :-------------: |:-------------:| :-----:| :-------------: |:-------------:| :-----:| :-------------: |:-------------:| :-----:| :-----:|
| Почта пользователя на которую будет отправлено письмо | Второстепенная почта (не обязательно) | Пол пользователя (М/Ж) | Текст для хедера в PDF файле | Текст для приветствия - над основным текстом в PDF файле | Основной текст для PDF файла | Время отправки письма | Статус доставки письма - Письмо будет доставлено, установится статус "Доставлено" | Ссылка для скачивания сгенерированного файла с машины | Чек-бокс, если чек-бокс нажат, письмо будет отправлено, если нет - система не сгенерирует файл и не отправит его на почту пользователя |


## Необходимые настройки в проекте
⋅⋅* Перейдите в модуль app/classes.py, в классе PDF, укажите путь до exe файла генератора PDF, скачать его можно [тут](https://wkhtmltopdf.org/downloads.html).
⋅⋅* Перейдите в модуль app/functions.py, в функции AutoSendingEmailsAdmin, измените переменные на свои:
range - название листа в таблице с которого будут читаться данные.
email_one - номер столбца, где будут основные email пользователей.
email_two - номер столбца, где будут вторичные email пользователей (необязательно).
text_header - номер столбца, где будет текст хеадера для PDF файла, в правом левом углу.
text_greeting - номер столбца, где будет приветственный текст, находится над основным текстом в PDF файле.
text_body - номер столбца, где будет основной текст - наполнение в PDF файле.
employee_gender - номер столбца, где будет пол получателя
mail_text_body - текст в email письме, которое будет отправлено с прикреплённым PDF файлом.

## Ошибки при отправке писем
⋅⋅⋅ Если во время отправки писем на почты пользователей, возникнет ошибка, она запишется в файл логов, папка /logs
⋅⋅⋅ Ошибки возникают чаще всего, в случае если email пользователя невалидный.
