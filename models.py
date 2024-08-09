from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(150), unique=True, nullable=False)
  password = db.Column(db.String(150), nullable=False)
  is_admin = db.Column(db.Boolean, default=False)
  can_print = db.Column(db.Boolean, default=False)
  can_upload = db.Column(db.Boolean, default=False)
  can_view = db.Column(db.Boolean, default=False)
  can_delete = db.Column(db.Boolean, default=False)

  def __repr__(self):
    return f'<User {self.username}>'
