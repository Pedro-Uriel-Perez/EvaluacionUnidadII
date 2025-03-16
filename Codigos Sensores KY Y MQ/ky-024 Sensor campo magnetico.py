import time
import network
from machine import Pin
from umqtt.simple import MQTTClient

# Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# Configuración MQTT
MQTT_CLIENT_ID = "esp32_ky025"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "gds0653/ky-024"

# Configuración del sensor KY-025 (Solo Digital)
reed_switch = Pin(34, Pin.IN)  # Salida digital del sensor

# Conectar WiFi
def conectar_wifi():
    print("[INFO] Conectando a WiFi...")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
    
    timeout = 10
    while not sta_if.isconnected() and timeout > 0:
        print(".", end="")
        time.sleep(1)
        timeout -= 1
    
    if sta_if.isconnected():
        print("\n[INFO] WiFi Conectada!")
        print(f"[INFO] Dirección IP: {sta_if.ifconfig()[0]}")
    else:
        print("\n[ERROR] No se pudo conectar a WiFi")

# Conectar a MQTT
def conectar_mqtt():
    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
        client.connect()
        print(f"[INFO] Conectado a MQTT en {MQTT_BROKER}")
        return client
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a MQTT: {e}")
        return None

# Leer el sensor (con filtrado)
def leer_sensor():
    muestras = 5  # Tomar varias muestras para reducir ruido
    detecciones = sum(reed_switch.value() for _ in range(muestras))
    iman_detectado = 1 if detecciones > (muestras // 2) else 0  # Mayoría de lecturas
    return iman_detectado

# Iniciar conexiones
conectar_wifi()
client = conectar_mqtt()

while True:
    try:
        if not client:
            client = conectar_mqtt()
            if not client:
                time.sleep(5)
                continue
        
        # Leer el estado del sensor
        iman_detectado = leer_sensor()
        print(f"[INFO] Imán Detectado: {iman_detectado}")
        
        client.publish(MQTT_TOPIC, str(iman_detectado))
        time.sleep(2)  # Enviar datos cada 2 segundos
    
    except Exception as e:
        print(f"[ERROR] Error en el loop principal: {e}")
        client = None
        time.sleep(5)