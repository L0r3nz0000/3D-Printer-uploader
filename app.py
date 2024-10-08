import os
from flask import Flask, flash, request, redirect, render_template, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User
from sqlalchemy.exc import IntegrityError
from flask_wtf.csrf import CSRFProtect, CSRFError
from forms import LoginForm, RegistrationForm, PermissionForm, UploadForm
import time
import socket
import psutil
from _3d_printer import Printer

# Funzione per ottenere la dimensione in formato leggibile
def get_human_readable_size(size_bytes):
  return psutil._common.bytes2human(size_bytes)

UPLOAD_FOLDER = './models/'

def get_models():
  return [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f)) and f.endswith('.gcode')]

ALLOWED_EXTENSIONS = {"stl", "obj", "3mf", "amf", "ply", "wrl", "fbx", "dae", "gcode"}
PORT = '/dev/ttyUSB0' # porta seriale stampante

printer = Printer(PORT)
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

csrf = CSRFProtect(app)

db.init_app(app)

def allowed_file(filename):
  return '.' in filename and \
    filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
  return render_template('error.html', error_message=e.description), 400

@app.route('/get_percentage', methods=['GET'])
def get_percentage():
  return printer.get_percentage() if not printer.completed else "Completed"

@app.route('/monitor', methods=['GET', 'POST'])
def monitor():
  return render_template('monitor.html')

@app.route('/stop', methods=['POST'])
def stop():
  if session.get('can_stop'):
    printer.stop_print()
  else:
    flash('You are not allowed to interrupt the current print', 'danger')
    return redirect(url_for('home'))

@app.route('/remove/<int:id>', methods=['POST'])
@csrf.exempt
def remove(id):
  if session.get('can_delete'):
    models = get_models()
    if id <= len(models) and id > 0:
      filename = models[id-1]
      path = os.path.join(UPLOAD_FOLDER, filename)
      os.remove(path)
      return redirect('/home')
    else:
      flash('Parameter ID out of range', 'danger')
      return redirect(url_for('home'))
  else:
    flash('You are not allowed to remove models', 'danger')
    return redirect(url_for('home'))

@app.route('/print/<int:id>', methods=['POST'])
@csrf.exempt
def print(id):
  if not session.get('can_print'):
    flash('You are not allowed to start a print', 'danger')
    return redirect(url_for('home'))
  
  models = get_models()
  if id <= len(models) and id > 0:
    filename = models[id-1]

    gcode_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if gcode_path.endswith('.gcode'):
      if os.path.exists(gcode_path):
        if not printer.start_print(gcode_path):  # Inizia la stampa
          return redirect(url_for('monitor'))
        else:
          flash('Controlla il collegamento con la stampante e riprova', 'warning')
          return redirect(url_for('home'))
      else:
        flash(f'File: {gcode_path} not found', 'danger')
        return redirect(url_for('home'))
    else:
      flash(f'File: {gcode_path} is not a gcode', 'danger')
      return redirect(url_for('home'))
  else:
    flash('Parameter ID out of range', 'danger')
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
  form = RegistrationForm()
  if form.validate_on_submit():
    hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
    new_user = User(username=form.username.data, password=hashed_password, is_admin=False, can_print=False, can_upload=False, can_view=True, can_delete=False)

    try:
      db.session.add(new_user)
      db.session.commit()
      flash('Registration successful! You can now log in.', 'success')
      return redirect('/login')
    except IntegrityError:
      db.session.rollback()  # Rollback the session to avoid corruption
      flash('Username already exists. Please choose a different username.', 'danger')

  return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
  form = LoginForm(request.form)
  if request.method == 'POST':
    if form.validate_on_submit():
      user = User.query.filter_by(username=form.username.data).first()

      if user and check_password_hash(user.password, form.password.data):
        session['user_id'] = user.id
        session['is_admin'] = user.is_admin
        session['can_view'] = user.can_view
        session['can_upload'] = user.can_upload
        session['can_print'] = user.can_print
        session['can_delete'] = user.can_delete
        flash('Login successful!', 'success')
        return redirect('/home')
      else:
        flash('Invalid username or password', 'danger')
  
  return render_template('login.html', form=form)

@app.route('/users', methods=['GET', 'POST'])
def users():
  if not session.get('is_admin'):
    flash('You do not have access to this page.', 'danger')
    return redirect('/home')
  
  form = PermissionForm()
  users = User.query.all()
  
  if request.method == 'POST':
    user_id = request.form.get('user_id')
    user = User.query.get(user_id)
    
    if user:
      user.is_admin = 'is_admin' in request.form
      user.can_print = 'can_print' in request.form
      user.can_upload = 'can_upload' in request.form
      user.can_view = 'can_view' in request.form
      user.can_delete = 'can_delete' in request.form
      user.can_stop = 'can_stop' in request.form
      db.session.commit()
      flash(f'Permissions updated for {user.username}', 'success')
  
  return render_template('users.html', users=users, form=form)

@app.route('/logout')
def logout():
  session.pop('user_id', None)
  session.pop('is_admin', None)
  flash('You have been logged out.', 'success')
  return redirect('/login')

@app.route('/upload', methods=['POST'])
def upload():
  if not session.get('can_upload'):
    flash('User not allowed to load models', 'danger')
    return redirect(url_for('home'))
  # controlla se nella post c'è il file
  if 'file' not in request.files:
    flash('No file part', 'warning')
    return redirect(url_for('home'))
  file = request.files['file']

  # se l'utente non sceglie un file, il browser
  # carica un file vuoto senza nome.
  if file.filename == '':
    flash('No selected file', 'warning')
    return redirect(request.url)
  
  if file and allowed_file(file.filename):
    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

  return redirect(url_for('home'))

@app.route('/', methods=['GET'])
@app.route('/home', methods=['GET'])
@csrf.exempt
def home():
  if 'user_id' not in session:
    return redirect('/login')

  files = get_models()
  upload_form = UploadForm()
  user = User.query.get(session['user_id'])

  data = []
  for i, file in enumerate(files):
    bytes_size = os.path.getsize(os.path.join(UPLOAD_FOLDER, file))
    data.append({'id': i+1, 'name': file, 'size': get_human_readable_size(bytes_size)})

  return render_template('home.html', user=user, form=upload_form, data=data, is_admin=session.get('is_admin'))

if __name__ == "__main__":
  app.run(host="0.0.0.0")