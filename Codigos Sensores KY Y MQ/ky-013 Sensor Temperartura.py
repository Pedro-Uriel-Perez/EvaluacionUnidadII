import time
import network
from machine import Pin
import random  # Importar módulo para generar números aleatorios
from umqtt.simple import MQTTClient

# 📡 Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# 🌐 Configuración MQTT
MQTT_CLIENT_ID = "esp32_temp_sensor"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "gds0653/ky-013"  # Tema MQTT para el sensor KY-013

# 🔌 Función para conectar a WiFi
def conectar_wifi():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
    for _ in range(20):
        if sta_if.isconnected():
            print("\n[INFO] WiFi Conectada!")
            print(f"[INFO] IP: {sta_if.ifconfig()[0]}")
            return True
        print(".", end="")
        time.sleep(0.5)
    print("\n[ERROR] No se pudo conectar a WiFi")
    return False

# 🔄 Función para conectar a MQTT
def conectar_mqtt():
    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
        client.connect()
        print(f"[INFO] Conectado a MQTT en {MQTT_BROKER}")
        return client
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a MQTT: {e}")
        return None

# 🏁 Bucle principal
if conectar_wifi():
    client = conectar_mqtt()
else:
    client = None

while True:
    try:
        if not network.WLAN(network.STA_IF).isconnected():
            print("[WARNING] WiFi desconectado. Intentando reconectar...")
            if conectar_wifi():
                client = conectar_mqtt()

        # Generar un valor aleatorio de temperatura entre 20 y 30 grados Celsius
        temperature = random.uniform(20.0, 30.0)
        print(f"[INFO] Temperatura generada aleatoriamente: {temperature:.2f}°C")

        # Publicar la temperatura en MQTT
        if client:
            client.publish(MQTT_TOPIC, str(temperature).encode())  # Publica la temperatura en el tema MQTT
            print(f"[INFO] Publicado en {MQTT_TOPIC}: {temperature:.2f}°C")

        # Esperar antes de la siguiente lectura
        time.sleep(2)

    except Exception as e:
        print(f"[ERROR] Error en el loop principal: {e}")
        client = None  # Intentará reconectar en la siguiente iteración
        time.sleep(5)
