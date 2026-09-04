from datetime import datetime

from extensions import db


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    created_on = db.Column(db.DateTime,default=datetime.utcnow)
