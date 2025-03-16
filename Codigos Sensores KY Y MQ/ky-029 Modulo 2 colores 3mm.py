import time
import network
from machine import Pin
from umqtt.simple import MQTTClient

# Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# Configuración MQTT
MQTT_CLIENT_ID = "esp32_ky029"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "gds0653/ky-029"

# Configuración del KY-029 (LED de dos colores)
RED_PIN = 12    # Pin para el LED rojo
GREEN_PIN = 14  # Pin para el LED verde

# Configurar pines como salida
led_rojo = Pin(RED_PIN, Pin.OUT)
led_verde = Pin(GREEN_PIN, Pin.OUT)

# Variable para seguir el estado actual
estado_actual = "1"  # Comenzamos con rojo
ultimo_cambio = 0
INTERVALO_CAMBIO = 2000  # Alternar cada 2 segundos (ms)

# Conectar a WiFi
def conectar_wifi():
    print("Conectando a WiFi...")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.5)
    print("\nWiFi Conectada!")

# Conectar a MQTT
def conectar_mqtt():
    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
        client.connect()
        print("Conectado a MQTT")
        return client
    except:
        print("Error conectando a MQTT")
        return None

# Función para obtener tiempo actual en ms
def millis():
    return time.ticks_ms()

# Función para cambiar el estado del LED
def cambiar_estado():
    global estado_actual
    
    if estado_actual == "1":  # Si está en rojo, cambiar a verde
        led_rojo.value(0)
        led_verde.value(1)
        estado_actual = "2"
        print("LED: VERDE (2)")
    else:  # Si está en verde, cambiar a rojo
        led_rojo.value(1)
        led_verde.value(0)
        estado_actual = "1"
        print("LED: ROJO (1)")
    
    # Publicar el nuevo estado en MQTT
    if client:
        client.publish(MQTT_TOPIC, estado_actual)

# Inicialización
print("Iniciando sistema...")
conectar_wifi()
client = conectar_mqtt()

# Iniciar con rojo
led_rojo.value(1)
led_verde.value(0)

# Publicar estado inicial
if client:
    client.publish(MQTT_TOPIC, "1")
    print("Estado inicial: ROJO (1)")

print("Sistema listo! Alternando automáticamente entre ROJO y VERDE...")

# Bucle principal - alterna automáticamente
while True:
    try:
        # Verificar tiempo para cambio
        ahora = millis()
        if ahora - ultimo_cambio >= INTERVALO_CAMBIO:
            cambiar_estado()
            ultimo_cambio = ahora
        
        # Verificar conexión MQTT
        if client is None:
            print("Reconectando a MQTT...")
            client = conectar_mqtt()
            time.sleep(1)
        
    except Exception as e:
        print(f"Error: {e}")
        client = None
        time.sleep(1)
        
    time.sleep(0.1)