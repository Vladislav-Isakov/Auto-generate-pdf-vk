from flask_login import current_user
from app import app, db

@app.errorhandler(Exception)
def not_found_error_400(error):
    #app.logger.error(f'Возникла ошибка в контексте аккаунта пользователя с ID: {current_user.vk_id}', exc_info=True)
    pass

@app.errorhandler(404)
def not_found_error_404(error):
    pass

@app.errorhandler(500)
def internal_error_500(error):
    db.session.rollback()
    pass