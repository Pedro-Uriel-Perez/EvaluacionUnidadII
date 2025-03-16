from machine import Pin, ADC
import time
import network
from umqtt.simple import MQTTClient

# Configuración del sensor de sonido (4 pines, usando salida analógica)
sensor_pin = ADC(Pin(34))  # Pin donde conectaste la salida analógica del sensor de sonido
sensor_pin.atten(ADC.ATTN_0DB)  # Configuración para un rango de 0 a 1.1V (ajustable según el sensor)

# Configuración WiFi (tu red doméstica)
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# Configuración MQTT
MQTT_CLIENT_ID = "esp32_sensor_sonido_pequeno_analogico"
MQTT_BROKER = "broker.emqx.io"  # Cambia a la IP de tu broker MQTT
MQTT_PORT = 1883
MQTT_TOPIC_PUB = "gds0653/ky-037"  # Topic para el sensor de sonido pequeño (analógico)
MQTT_TOPIC_SUB = "postgres/sensors"

# Variables para almacenar el último valor leído del sensor
ultimo_valor = None
umbral_cambio = 200  # Umbral para considerar un cambio significativo (ajustado a 500)

# Función para conectar a WiFi
def conectar_wifi():
    print("Conectando a WiFi...", end="")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.3)
    print("\nWiFi Conectada!")

# Función para suscribirse al broker MQTT
def subscribir():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
    client.set_callback(llegada_mensaje)
    client.connect()
    client.subscribe(MQTT_TOPIC_SUB)
    print(f"Conectado a {MQTT_BROKER}, suscrito a {MQTT_TOPIC_SUB}")
    return client

# Función para recibir mensajes MQTT (aunque no se usa en este caso)
def llegada_mensaje(topic, msg):
    print(f"Mensaje recibido en {topic}: {msg}")

# Conectar a WiFi
conectar_wifi()

# Conectar al broker MQTT
client = subscribir()

# Ciclo infinito para leer el sensor de sonido y enviar datos solo cuando haya un cambio significativo
while True:
    client.check_msg()  # Revisar si hay mensajes en el topic de control
    try:
        # Leer el valor del sensor de sonido (0-1023 si es un ADC de 10 bits)
        valor_sonido = sensor_pin.read()

        # Solo publicamos si el cambio en el valor es significativo (más de 500)
        if ultimo_valor is None or abs(valor_sonido - ultimo_valor) > umbral_cambio:
            mensaje = f"{valor_sonido}"
            print(f"Publicando: {mensaje}")
            client.publish(MQTT_TOPIC_PUB, mensaje)  # Publicamos el nivel de sonido
            ultimo_valor = valor_sonido  # Actualizamos el último valor leído

    except OSError as e:
        print("Error al leer el sensor:", e)

    time.sleep(1)  # Esperamos 1 segundo antes de leer nuevamente el sensor