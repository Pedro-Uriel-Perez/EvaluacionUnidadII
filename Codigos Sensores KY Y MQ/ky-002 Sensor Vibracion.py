from machine import Pin
import network
import time
from umqtt.robust import MQTTClient
import json

# Configuración WiFi
SSID = "Red-Peter"
PASSWORD = "12345678"

# Configuración MQTT
MQTT_SERVER = "broker.emqx.io"  
MQTT_PORT = 1883
MQTT_TOPIC = b"gds0643/ich/main"
CLIENT_ID = "ESP32Client_" + str(time.time())

# Configuración del sensor
SIGNAL_PIN = 16    # Pin para recibir la señal (S)

# Configuración del tiempo de muestreo
SAMPLE_TIME = 2   # Tiempo entre muestras en segundos

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Conectando a WiFi...')
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.5)
            print('.', end='')
    print('\nConectado a WiFi')
    print('Dirección IP:', wlan.ifconfig()[0])

def conectar_mqtt():
    try:
        client = MQTTClient(CLIENT_ID, MQTT_SERVER, MQTT_PORT, keepalive=60)
        client.connect(clean_session=True)
        print("Conectado a MQTT")
        return client
    except Exception as e:
        print(f"Error conectando a MQTT: {e}")
        return None

def main():
    # Inicializar pines
    vibration_sensor = Pin(SIGNAL_PIN, Pin.IN)
    
    # Conectar a WiFi
    conectar_wifi()
    
    # Iniciar cliente MQTT
    client = None
    contador = 0
    
    while True:
        try:
            # Reconectar MQTT si es necesario
            if client is None:
                client = conectar_mqtt()
                if client is None:
                    time.sleep(5)
                    continue
            
            # Leer sensor - para KY-002: 0=sin vibración, 1=vibración detectada
            vibration_detected = vibration_sensor.value()
            contador += 1
            
            # Crear mensaje JSON
            mensaje = {
                "sensor": "vibracion",
                "valor": vibration_detected,
                "estado": "activo" if vibration_detected == 1 else "inactivo",
                "contador": contador,
                "timestamp": time.time()
            }
            
            # Publicar datos
            mensaje_json = json.dumps(mensaje)
            client.publish(MQTT_TOPIC, mensaje_json.encode())
            print(f"Enviado #{contador} - Vibración: {'Detectada' if vibration_detected else 'No detectada'}, Valor: {vibration_detected}")
            
            # Esperar tiempo de muestreo configurado
            time.sleep(SAMPLE_TIME)
            
        except Exception as e:
            print(f"Error: {e}")
            client = None
            time.sleep(5)

if __name__ == "__main__":
    main()