from machine import Pin
import time
import network
from umqtt.simple import MQTTClient

# Configuración del broker MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = "esp32_ky020"
MQTT_SENSOR_TOPIC = "gds0653/ky-020"
MQTT_PORT = 1883

# Configuración de tiempos
INTERVALO_CAMBIO = 3  # Cambiar de estado cada 3 segundos

def conectar_wifi():
    print("Conectando WiFi...", end="")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect('Red-Peter', '12345678')  # Ajusta los datos de tu red
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.3)
    print(" ¡Conectado!")

def subscribir():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT,
                        user=MQTT_USER, password=MQTT_PASSWORD, keepalive=60)
    client.connect()
    print(f"Conectado a {MQTT_BROKER}")
    print(f"Publicando en el tópico {MQTT_SENSOR_TOPIC}")
    return client

# Conectar a WiFi
print("Iniciando SIMULACIÓN de sensor de inclinación KY-020")
conectar_wifi()

# Conectar a MQTT
client = subscribir()

# Estado inicial: vertical (0)
estado_actual = "0"
ultimo_cambio = time.time()

# Publicar estado inicial
client.publish(MQTT_SENSOR_TOPIC, estado_actual)
print(f"Estado inicial: VERTICAL ({estado_actual})")


# Bucle principal
while True:
    try:
        # Verificar si es tiempo de cambiar estado
        ahora = time.time()
        if ahora - ultimo_cambio >= INTERVALO_CAMBIO:
            # Cambiar estado: 0->1 o 1->0
            estado_actual = "1" if estado_actual == "0" else "0"
            ultimo_cambio = ahora
            
            # Publicar nuevo estado
            client.publish(MQTT_SENSOR_TOPIC, estado_actual)
            
            # Mensaje en consola
            if estado_actual == "0":
                print("Sensor VERTICAL (0)")
            else:
                print("Sensor INCLINADO (1)")
        
        # Verificar conexión WiFi
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
        
    time.sleep(0.1)  # Pequeña pausa