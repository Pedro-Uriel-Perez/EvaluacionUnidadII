from machine import Pin
import time
import network
from umqtt.simple import MQTTClient

# Configuración del broker MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = "esp32_ky012"
MQTT_TOPIC_STATUS = "gds0653/ky-012"  # Tema para publicar estado
MQTT_PORT = 1883

# Configuración del buzzer KY-012
BUZZER_PIN = 26  # Pin digital para controlar el buzzer
buzzer = Pin(BUZZER_PIN, Pin.OUT)

# Configuración de tiempos
TIEMPO_ENCENDIDO = 1    # Tiempo que el buzzer está encendido (segundos)
TIEMPO_APAGADO = 4      # Tiempo que el buzzer está apagado (segundos)

# Estado inicial: apagado
buzzer.value(0)
estado_actual = "0"

def conectar_wifi():
    print("Conectando WiFi...", end="")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect('Red-Peter', '12345678')
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.3)
    print(" ¡Conectado!")

def subscribir():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT,
                        user=MQTT_USER, password=MQTT_PASSWORD, keepalive=60)
    client.connect()
    print(f"Conectado a MQTT, publicando en {MQTT_TOPIC_STATUS}")
    return client

# Conectar a WiFi
print("Iniciando control automático de buzzer KY-012")
conectar_wifi()

# Conectar a MQTT
client = subscribir()

# Publicar estado inicial
client.publish(MQTT_TOPIC_STATUS, estado_actual)
print(f"Estado inicial: {estado_actual} (Buzzer apagado)")

print(f"Sistema listo! Buzzer sonará cada {TIEMPO_ENCENDIDO + TIEMPO_APAGADO} segundos")
print(f"  - Encendido: {TIEMPO_ENCENDIDO} segundos")
print(f"  - Apagado: {TIEMPO_APAGADO} segundos")

ultimo_cambio = time.time()

# Bucle principal
while True:
    try:
        # Verificar si hay que cambiar el estado
        ahora = time.time()
        
        # Si está apagado y pasó el tiempo de apagado, encender
        if estado_actual == "0" and ahora - ultimo_cambio >= TIEMPO_APAGADO:
            # Encender buzzer
            buzzer.value(1)
            estado_actual = "1"
            ultimo_cambio = ahora
            
            # Publicar nuevo estado
            client.publish(MQTT_TOPIC_STATUS, estado_actual)
            print(f"Estado cambiado: {estado_actual} (Buzzer encendido)")
            
        # Si está encendido y pasó el tiempo de encendido, apagar
        elif estado_actual == "1" and ahora - ultimo_cambio >= TIEMPO_ENCENDIDO:
            # Apagar buzzer
            buzzer.value(0)
            estado_actual = "0"
            ultimo_cambio = ahora
            
            # Publicar nuevo estado
            client.publish(MQTT_TOPIC_STATUS, estado_actual)
            print(f"Estado cambiado: {estado_actual} (Buzzer apagado)")
        
        # Si se pierde la conexión, reconectar
        if not network.WLAN(network.STA_IF).isconnected():
            print("Reconectando WiFi...")
            conectar_wifi()
            client = subscribir()
        
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
        try:
            client = subscribir()
        except:
            pass
    
    time.sleep(0.1)  # Pequeña pausa para no saturar CPU