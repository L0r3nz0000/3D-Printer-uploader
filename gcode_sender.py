import serial
import time

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
        time.sleep(0.005)
            
    # Chiudi la connessione seriale
    ser.close()
    print("Connessione chiusa")
      
  except Exception as e:
    print(f"Errore: {e}")

send_gcode('models/Chain_Guide.gcode', '/dev/ttyUSB0')