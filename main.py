import os
from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename
import time
import socket
import gcode_sender
import psutil

# Funzione per ottenere dimensione leggibile
def get_human_readable_size(size_bytes):
  return psutil._common.bytes2human(size_bytes)

def get_models():
  base_path = 'models/'
  return [f for f in os.listdir(base_path) if os.path.isfile(os.path.join(base_path, f)) and f.endswith('.gcode')]

UPLOAD_FOLDER = 'models/'
ALLOWED_EXTENSIONS = {"stl", "obj", "3mf", "amf", "ply", "wrl", "fbx", "dae", "gcode"}
PORT = '/dev/ttyUSB0' # porta seriale stampante

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
  return '.' in filename and \
    filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS

@app.route('/monitor', methods=['GET', 'POST'])
def monitor():
  return "printing..."

@app.route('/remove/<int:id>', methods=['POST'])
def remove(id):
  models = get_models()
  if id <= len(models) and id > 0:
    filename = models[id-1]
    path = os.path.join('models/', filename)
    os.remove(path)
    return redirect('/')
  else:
    return render_template('error.html', error_code="Parameter ID out of range")

@app.route('/print/<int:id>', methods=['POST'])
def print(id):
  models = get_models()
  if id <= len(models) and id > 0:
    filename = models[id-1]

    gcode_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if gcode_path.endswith('.gcode'):
      if os.path.exists(gcode_path):
        gcode_sender.send(gcode_path, PORT)  # Inizia la stampa
        #return redirect('/monitor')
      else:
        return f"<html><h1>File: \"{gcode_path}\" not found</h1></html>"
    else:
      return f"<html><h1>File: \"{filename}\" is not a gcode</h1></html>"
  else:
    return render_template('error.html', error_code="Parameter ID out of range")

  
@app.route('/', methods=['GET', 'POST'])
def upload_file():
  if request.method == 'POST':
    # controlla se nella post c'è il file
    if 'file' not in request.files:
      flash('No file part')
      return redirect(request.url)
    file = request.files['file']

    # se l'utente non sceglie un file, il browser carica
    # un file vuoto senza nome.
    if file.filename == '':
      flash('No selected file')
      return redirect(request.url)
    
    if file and allowed_file(file.filename):
      filename = secure_filename(file.filename)
      path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
      file.save(path)
    

  if request.method == 'GET':
    base_path = 'models/'
    files = get_models()

    data = []
    for i, file in enumerate(files):
      bytes_size = os.path.getsize(os.path.join(base_path, file))
      data.append({'id': i+1, 'name': file, 'size': get_human_readable_size(bytes_size)})

    return render_template('index.html', data=data)

if __name__ == "__main__":
  app.run(host="0.0.0.0")