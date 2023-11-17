from app import app, db

@app.errorhandler(400)
def not_found_error_400(error):
    pass

@app.errorhandler(404)
def not_found_error_404(error):
    pass

@app.errorhandler(500)
def internal_error_500(error):
    db.session.rollback()
    pass