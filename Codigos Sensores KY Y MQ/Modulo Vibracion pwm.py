from machine import Pin
import time
import network
from umqtt.simple import MQTTClient

# Configuración del broker MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = "esp32_client"  # Asegúrate de que no esté vacío
MQTT_SENSOR_TOPIC = "gds0653/pwm"
MQTT_PORT = 1883

# Configuración del motor de vibración
motor = Pin(26, Pin.OUT)  # GPIO26 controla el motor (IN)


def conectar_wifi():
    print("Conectando WiFi...", end="")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect('Red-Peter', '12345678')  # Ingresa la contraseña si es necesario
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.3)  # Corregido
    print(" ¡Conectado!")


def subscribir():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT,
                        user=MQTT_USER, password=MQTT_PASSWORD, keepalive=60)
    client.connect()
    print(f"Conectado a {MQTT_BROKER}")
    print(f"Suscrito al tópico {MQTT_SENSOR_TOPIC}")
    return client


# Conectar a WiFi
conectar_wifi()

# Conectar a MQTT
client = subscribir()

# Bucle principal
while True:
    try:
        # Activar el motor de vibración
        motor.value(1)
        mensaje = "Motor activado"
        client.publish(MQTT_SENSOR_TOPIC, mensaje.encode())  # Publicar valor como bytes
        print(f"[INFO] Publicado en {MQTT_SENSOR_TOPIC}: {mensaje}")

        time.sleep(3)  # Vibrar durante 3 segundos

        # Apagar el motor de vibración
        motor.value(0)
        mensaje = "Motor desactivado"
        client.publish(MQTT_SENSOR_TOPIC, mensaje.encode())  # Publicar valor como bytes
        print(f"[INFO] Publicado en {MQTT_SENSOR_TOPIC}: {mensaje}")

        time.sleep(3)  # Esperar antes de repetir el ciclo

    except Exception as e:
        print(f"[ERROR] Error en el loop principal: {e}")
        client = None  # En caso de error, desconectar MQTT