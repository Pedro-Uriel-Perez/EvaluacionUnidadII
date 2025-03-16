import time
import network
from machine import Pin
from umqtt.simple import MQTTClient

# Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# Configuración MQTT
MQTT_CLIENT_ID = "esp32_ky034"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "gds0653/ky-034"

# Configuración del LED KY-034
led = Pin(26, Pin.OUT)  # Conectar a la patita larga del KY-034

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
        
        # Encender el LED (cambia de color solo)
        led.value(1)
        print("[INFO] LED ENCENDIDO - Cambiando de colores")
        client.publish(MQTT_TOPIC, "ENCENDIDO")
        time.sleep(7)  # Mantener encendido 7 segundos
        
        # Apagar el LED
        led.value(0)
        print("[INFO] LED APAGADO")
        client.publish(MQTT_TOPIC, "APAGADO")
        time.sleep(7)  # Mantener apagado 7 segundos
    
    except Exception as e:
        print(f"[ERROR] Error en el loop principal: {e}")
        client = None
        time.sleep(5)