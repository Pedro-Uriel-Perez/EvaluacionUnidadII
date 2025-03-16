import time
import network
from machine import Pin
from umqtt.simple import MQTTClient

# 📡 Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# 🌐 Configuración MQTT
MQTT_CLIENT_ID = "esp32_ky032"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC_SENSOR = "gds0653/ky-032"

# 🛑 Configuración del sensor KY-032
SENSOR_PIN = 27  # Pin de salida del KY-032
sensor = Pin(SENSOR_PIN, Pin.IN)

# 🔌 Conectar a WiFi
def conectar_wifi():
    print("[INFO] Conectando a WiFi...")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)

    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.5)

    print("\n[INFO] WiFi Conectada!")
    print(f"[INFO] Dirección IP: {sta_if.ifconfig()[0]}")

# 🔄 Conectar a MQTT
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
conectar_wifi()
client = conectar_mqtt()

while True:
    try:
        # Leer estado del sensor KY-032
        sensor_estado = sensor.value()  # 0 = Obstáculo detectado, 1 = No hay obstáculo

        # Publicar en MQTT
        if client:
            client.publish(MQTT_TOPIC_SENSOR, str(sensor_estado))
            print(f"[INFO] Publicado en {MQTT_TOPIC_SENSOR}: {sensor_estado}")

        # Esperar antes de la próxima lectura
        time.sleep(0.5)

    except Exception as e:
        print(f"[ERROR] Error en el loop principal: {e}")
        client = None
        time.sleep(5)