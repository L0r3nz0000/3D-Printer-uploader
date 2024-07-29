import serial
import time

class Printer:
  def __init__(self, port, baud_rate=115200):
    self.port = port
    self.baud_rate = baud_rate

    # Apre la connessione seriale
    self.ser = serial.Serial(port, baud_rate)
    
    self.percentage = 0.000
    self.completed = False

  def get_percentage(self):
    return str(self.percentage)#+"%"
  
  def stop_print(self):
    self.ser.write("M112\n".encode()) # Invia il comando di stop forzato
    response = self.ser.readline().decode().strip()
    print(f"Risposta: {response}")

    self.ser.write("G28\n".encode())  # Invia il comando di auto home
    response = self.ser.readline().decode().strip()
    print(f"Risposta: {response}")

    self.ser.close()

  def start_print(self, file_path):
    try:
      print(f"Connesso alla porta {self.port} con baud rate {self.baud_rate}")
      
      # Legge il file G-code
      with open(file_path, 'r') as file:
        lines = file.readlines()
      
      # Invia ogni linea del file G-code alla stampante
      for i, line in enumerate(lines):
        line = line.strip()
        if line and not line.startswith(';'):  # Ignora linee vuote o commenti
          self.ser.write((line + '\n').encode())
          print(f"Inviato: {line}")
          
          # Attendi la risposta della stampante
          response = self.ser.readline().decode().strip()
          print(f"Risposta: {response}")

          self.precentage = round(i / len(lines) * 100, 3)
          # Piccolo ritardo per evitare di inviare troppi comandi contemporameamente alla stampante
          time.sleep(0.005)
          
      # Chiudi la connessione seriale
      self.ser.close()
      self.completed = True
      print("Stampa completata")
        
    except Exception as e:
      print(f"Errore: {e}")