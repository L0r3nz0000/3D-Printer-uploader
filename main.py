import os
from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename
import serial
import time
import socket

def get_local_ip():
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect(("8.8.8.8", 80))
  addr = s.getsockname()[0]
  s.close()
  return addr

UPLOAD_FOLDER = 'models/'
ALLOWED_EXTENSIONS = {"stl", "obj", "3mf", "amf", "ply", "wrl", "fbx", "dae", "gcode"}
PORT = '/dev/ttyUSB0' # porta seriale stampante

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
  return '.' in filename and \
    filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS

def send_gcode(file_path, port, baud_rate=115200):
  try:
    # Apre la connessione seriale
    ser = serial.Serial(port, baud_rate)
    print(f"Connesso alla porta {port} con baud rate {baud_rate}")
    
    # Legge il file G-code
    with open(file_path, 'r') as file:
      lines = file.readlines()
    
    # Invia ogni linea del file G-code alla stampante
    for line in lines:
      line = line.strip()
      if line and not line.startswith(';'):  # Ignora linee vuote o commenti
        ser.write((line + '\n').encode())
        print(f"Inviato: {line}")
        
        # Attendi la risposta della stampante
        response = ser.readline().decode().strip()
        print(f"Risposta: {response}")
        
        # Piccolo ritardo per evitare di inviare troppi comandi contemporameamente alla stampante
        time.sleep(0.1)
            
    # Chiudi la connessione seriale
    ser.close()
    print("Connessione chiusa")
      
  except Exception as e:
    print(f"Errore: {e}")

@app.route('/print/<file>', methods=['GET'])
def print(file):
  filename = secure_filename(file)
  gcode_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
  
  if gcode_path.endswith('.gcode'):
    if os.path.exists(gcode_path):
      send_gcode(gcode_path, PORT)
      return "<html>Printing...</html>"
    else:
      return f"<html><h1>File: \"{gcode_path}\" not found</h1></html>"
  else:
    return f"<html><h1>File: \"{file}\" is not a gcode</h1></html>"
  
@app.route('/', methods=['GET', 'POST'])
def upload_file():
  if request.method == 'POST':
    # check if the post request has the file part
    if 'file' not in request.files:
      flash('No file part')
      return redirect(request.url)
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
      flash('No selected file')
      return redirect(request.url)
    if file and allowed_file(file.filename):
      filename = secure_filename(file.filename)
      path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
      file.save(path)
      return render_template('success.html', path=path)
  return render_template('index.html')

if __name__ == "__main__":
  app.run(host="0.0.0.0")