from machine import Pin
import time
import network
from umqtt.simple import MQTTClient

# Configuración del sensor KY-003 (Efecto Hall)
sensor_pin = Pin(16, Pin.IN, Pin.PULL_UP)  # GPIO16 con resistencia interna de pull-up

# Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# Configuración MQTT
MQTT_CLIENT_ID = "esp32_hall_sensor"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "gds0653/ky-003"

# Variables para control
ultimo_estado = None
ultimo_cambio = 0
DEBOUNCE_TIME = 300  # Tiempo anti-rebote en milisegundos

def conectar_wifi():
    """Conecta el ESP32 a la red WiFi."""
    print("[INFO] Conectando a WiFi...")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
    
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.5)
    
    print("\n[INFO] WiFi Conectada!")
    print(f"[INFO] Dirección IP: {sta_if.ifconfig()[0]}")

def conectar_mqtt():
    """Conecta a MQTT y maneja reconexiones."""
    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
        client.connect()
        print(f"[INFO] Conectado a MQTT en {MQTT_BROKER}")
        return client
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a MQTT: {e}")
        return None

def millis():
    """Retorna el tiempo actual en milisegundos."""
    return time.ticks_ms()

# Conectar a WiFi y MQTT
conectar_wifi()
client = conectar_mqtt()

print("[INFO] Monitoreando el sensor KY-003 (Efecto Hall)")
print("[INFO] Acerca un imán al sensor para detectar el campo magnético")

while True:
    try:
        # Verificar conexión WiFi
        if not network.WLAN(network.STA_IF).isconnected():
            print("[ERROR] WiFi desconectado, reconectando...")
            conectar_wifi()
            client = conectar_mqtt()
            
        # Verificar conexión MQTT
        if client is None:
            print("[ERROR] MQTT desconectado, reconectando...")
            client = conectar_mqtt()
            time.sleep(5)
            continue
            
        # Leer el estado del sensor KY-003
        valor_sensor = sensor_pin.value()
        
        # KY-003 da 0 cuando detecta un imán y 1 cuando no hay imán
        iman_detectado = (valor_sensor == 0)
        
        # Control de cambios para evitar envíos innecesarios
        ahora = millis()
        if ultimo_estado != iman_detectado or (ahora - ultimo_cambio > 5000):
            estado = "no_detectado" if iman_detectado else "detectado"
            client.publish(MQTT_TOPIC, estado)
            print(f"[INFO] Imán: {estado.upper()}")
            
            ultimo_estado = iman_detectado
            ultimo_cambio = ahora
            
    except Exception as e:
        print(f"[ERROR] Error en bucle principal: {e}")
        time.sleep(5)
        
    time.sleep(0.5)  # Pequeña pausa para evitar lecturas excesivas
