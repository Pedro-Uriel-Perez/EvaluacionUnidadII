import time
import network
from machine import Pin, ADC
from umqtt.simple import MQTTClient

# Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# Configuración MQTT
MQTT_CLIENT_ID = "esp32_mq2"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "gds0653/mq-2"

# Configuración del sensor MQ2 (Gas)
mq2_sensor = ADC(Pin(34))  # Pin analógico del sensor
mq2_sensor.atten(ADC.ATTN_11DB)  # Ajuste para rango completo de 3.3V

# Conectar WiFi
def conectar_wifi():
    print("[INFO] Conectando a WiFi...")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
    
    timeout = 10  # Tiempo máximo de espera en segundos
    while not sta_if.isconnected() and timeout > 0:
        print(".", end="")
        time.sleep(1)
        timeout -= 1
    
    if sta_if.isconnected():
        print("\n[INFO] WiFi Conectada!")
        print(f"[INFO] Dirección IP: {sta_if.ifconfig()[0]}")
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

# Leer valor del sensor MQ2
def leer_gas():
    valor = mq2_sensor.read()
    gas_ppm = (valor / 4095) * 1000  # Conversión aproximada a PPM
    return gas_ppm

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
        
        # Leer el valor del sensor
        gas_ppm = leer_gas()
        print(f"[INFO] Concentración de gas: {gas_ppm:.2f} PPM")
        client.publish(MQTT_TOPIC, str(gas_ppm))
        time.sleep(2)
    
    except Exception as e:
        print(f"[ERROR] Error en el loop principal: {e}")
        client = None
        time.sleep(5)
