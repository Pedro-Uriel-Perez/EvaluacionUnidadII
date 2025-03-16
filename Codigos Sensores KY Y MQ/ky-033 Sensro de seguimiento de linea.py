import time
import network
from machine import Pin
from umqtt.simple import MQTTClient

# Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# Configuración MQTT
MQTT_CLIENT_ID = "esp32_ky033"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "gds0653/ky-033"

# Configuración del KY-033 (Sensor de seguimiento de línea)
SENSOR_PIN = 14  # Pin digital para el sensor
sensor = Pin(SENSOR_PIN, Pin.IN)

# LED para indicación visual
led_onboard = Pin(2, Pin.OUT)

# Variables para control
ultimo_estado = None
ultimo_cambio = 0
DEBOUNCE_TIME = 300  # Tiempo anti-rebote en milisegundos
ultimo_envio = 0
INTERVALO_ENVIO = 5000  # Enviar estado cada 5 segundos si no hay cambios

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

# Función para obtener tiempo en milisegundos
def millis():
    return time.ticks_ms()

# Inicialización
print("Iniciando sensor KY-033 (Seguimiento de línea)")
conectar_wifi()
client = conectar_mqtt()

# Publicar estado inicial
if client:
    valor_inicial = "1" if sensor.value() else "0"
    client.publish(MQTT_TOPIC, valor_inicial)
    ultimo_estado = sensor.value()
    print(f"Estado inicial: {'LÍNEA DETECTADA (1)' if ultimo_estado else 'SIN LÍNEA (0)'}")

print("Sistema listo! Esperando detección...")

# Bucle principal
while True:
    try:
        # Verificar conexión WiFi y MQTT
        if not network.WLAN(network.STA_IF).isconnected() or client is None:
            print("Reconectando...")
            conectar_wifi()
            client = conectar_mqtt()
            time.sleep(2)
            continue
        
        # Leer estado del sensor
        # Nota: el valor puede ser invertido según el sensor específico y la superficie
        # KY-033 típicamente: 
        # - 1 (HIGH) = Superficie clara/reflectante o sin obstáculo
        # - 0 (LOW) = Superficie oscura/no reflectante o con obstáculo
        estado_actual = sensor.value()
        
        # LED indicador
        led_onboard.value(estado_actual)
        
        # Obtener tiempo actual
        ahora = millis()
        
        # Detectar cambio de estado con anti-rebote
        if estado_actual != ultimo_estado and ahora - ultimo_cambio > DEBOUNCE_TIME:
            # Crear valor para MQTT (1 o 0)
            valor = "1" if estado_actual else "0"
            
            # Publicar en MQTT
            client.publish(MQTT_TOPIC, valor)
            
            # Mostrar en consola
            if estado_actual:
                print("LÍNEA DETECTADA (1)")
            else:
                print("SIN LÍNEA (0)")
            
            # Actualizar variables de estado
            ultimo_estado = estado_actual
            ultimo_cambio = ahora
            ultimo_envio = ahora
            
        # Enviar periódicamente el estado actual como heartbeat
        elif ahora - ultimo_envio > INTERVALO_ENVIO:
            valor = "1" if estado_actual else "0"
            client.publish(MQTT_TOPIC, valor)
            if estado_actual:
                print("Heartbeat: LÍNEA DETECTADA (1)")
            else:
                print("Heartbeat: SIN LÍNEA (0)")
            ultimo_envio = ahora
            
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)
        
    time.sleep(0.1)  # Pequeña pausa