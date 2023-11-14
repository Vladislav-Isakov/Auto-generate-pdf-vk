import time
from datetime import datetime
from app import app, db, login
from flask_login import UserMixin

class User(UserMixin, db.Model):
    """Модель пользователя"""
    id = db.Column(db.Integer, primary_key=True)
    vk_id = db.Column(db.Integer, index=True, unique=True)
    last_seen = db.Column(db.Integer, default=round(time.time()))
    location_of_notifications = db.relationship('location_of_notifications_at_the_user', uselist=False)

    def __repr__(self) -> str:
        return '{}'.format(self.id)
    
    def checking_access_to_the_panel(self):
        return users_with_access_to_the_panel.query.filter_by(vk_id=self.vk_id, access='Выдан').first()

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class users_with_access_to_the_panel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vk_id = db.Column(db.Integer, index=True, unique=True)
    access = db.Column(db.String(32), default='Запрошен')

    def __repr__(self) -> str:
        return '{}'.format(self.id)
    
class location_of_notifications_at_the_user(db.Model):
    """Расположение уведомлений в интерфейсе"""
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(32), default='upper_left_corner')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self) -> str:
        return '{}'.format(self.id)