from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Urls(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    checks = db.relationship('UrlChecks', backref='url', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


class UrlChecks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.Integer, db.ForeignKey('urls.id'))
    created_at = db.Column(db.DateTime)
    status_code = db.Column(db.Integer)
    h1 = db.Column(db.String)
    description = db.Column(db.String)
    title = db.Column(db.String)
