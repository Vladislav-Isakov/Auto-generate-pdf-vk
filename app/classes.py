import pdfkit
from flask import render_template
from app import app
import secrets

class PDF:
    #путь до wkhtmltopdf на ПК/Машине
    path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
    options = {
        "orientation": "portrait",
        "page-size": "A4",
        "margin-top": "0px",
        "margin-right": "0px",
        "margin-bottom": "0px",
        "margin-left": "0px",
        "encoding": "UTF-8"
    }
    
    def generate_pdf(self, template: str = "pdf/mail.html", data: dict = {}, output_path: str = "app/static/generate_pdf/"):
        print(output_path)
        return pdfkit.from_string(render_template(template, data=data), output_path=output_path, options=self.options, cover_first=True, configuration=self.config)

    
class AdminPFD(PDF):

    template = "pdf/mail.html"
    output_path = "app/static/generate_pdf/mail/"

    def __init__(self, data) -> None:
        self.data = data

    def generate_admin_pdf(self):
        self.id_doc = secrets.token_hex(nbytes=16)
        return super().generate_pdf(self.template, self.data, self.output_path+f'{self.id_doc}.pdf')