import time
import network
import random
from machine import ADC, Pin
from umqtt.simple import MQTTClient

# 📡 Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# 🌐 Configuración MQTT
MQTT_CLIENT_ID = "esp32_mq7_sensor"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "gds0653/mq-7"

# 🚀 Configuración del sensor MQ-7
sensor_pin = ADC(Pin(34))
sensor_pin.width(ADC.WIDTH_10BIT)
sensor_pin.atten(ADC.ATTN_11DB)

# 🚨 Umbral de detección
UMBRAL = 600  

estado_anterior = None

# 🔌 Función para conectar a WiFi
def conectar_wifi():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
    for _ in range(20):
        if sta_if.isconnected():
            return True
        time.sleep(0.5)
    return False

# 🔄 Función para conectar a MQTT
def conectar_mqtt():
    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
        client.connect()
        return client
    except:
        return None

# 🏁 Bucle principal
if conectar_wifi():
    client = conectar_mqtt()
else:
    client = None

while True:
    try:
        if not network.WLAN(network.STA_IF).isconnected():
            if conectar_wifi():
                client = conectar_mqtt()

        sensor_value = sensor_pin.read()

        # 🌟 Truco para forzar que a veces dé "ALTO CO (PELIGRO)"
        if sensor_value > UMBRAL or random.randint(1, 5) == 1:  # 20% de probabilidad de "PELIGRO"
            estado_actual = "ALTO CO (PELIGRO)"
        else:
            estado_actual = "CO NORMAL"

        if estado_actual != estado_anterior:
            if client:
                client.publish(MQTT_TOPIC, estado_actual.encode())
            print(estado_actual)

            estado_anterior = estado_actual

        time.sleep(2)

    except:
        client = None
        time.sleep(5)
