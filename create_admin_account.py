from werkzeug.security import generate_password_hash
from app import db, app
from models import User

username = input('Username for admin account >> ')
password = input(f'Password for {username} >> ')

if password == input(f'Confirm password for {username} >> '):
  hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
  admin = User(username=username, password=hashed_password, is_admin=True, can_print=True, can_upload=True, can_view=True, can_delete=True, can_stop=True)
  
  with app.app_context():
    try:
      db.session.add(admin)
      db.session.commit()
      print('Admin account succesfully created, you can now log in at http://127.0.0.1:5000/login')
    except Exception as e:
      print(e)