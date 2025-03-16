from machine import Pin
import time
import network
from umqtt.simple import MQTTClient
import json

# Configuración del sensor de inclinación (interruptor de mercurio KY-017)
tilt_pin = Pin(34, Pin.IN, Pin.PULL_UP)  # GPIO16 con resistencia pull-up

led_pin = Pin(2, Pin.OUT)  

# Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# Configuración MQTT
MQTT_CLIENT_ID = "esp32_tilt_switch_ky017"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "gds0653/ky-017"

# Variables para control de debounce y estado
ultimo_estado = None
ultimo_cambio = 0
DEBOUNCE_TIME = 300  # Tiempo anti-rebote en milisegundos
contador = 0

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

# Bucle principal
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
            
        # Leer sensor de inclinación (0=Inclinado, 1=Vertical)
        # Con pull-up, cuando el sensor está inclinado, el interruptor cierra el circuito
        raw_tilt = tilt_pin.value()
        
        # Invertir para que sea más intuitivo
        tilt_state = not raw_tilt  # True = Inclinado, False = Vertical
        
        # Actualizar LED para visualización física
        led_pin.value(1 if tilt_state else 0)  # Encender LED si está inclinado
        
        # Aplicar debounce para evitar falsas lecturas
        ahora = millis()
        if (tilt_state != ultimo_estado) and (ahora - ultimo_cambio > DEBOUNCE_TIME):
            contador += 1
            
            mensaje = json.dumps({
                "sensor": "inclinacion",
                "valor": 1 if tilt_state else 0,
                "estado": "inclinado" if tilt_state else "vertical",
                "contador": contador,
                "timestamp": time.time()
            })
            
            client.publish(MQTT_TOPIC, mensaje)
            print(f"[INFO] #{contador} - Estado: {'INCLINADO' if tilt_state else 'VERTICAL'}")
            
            ultimo_estado = tilt_state
            ultimo_cambio = ahora
            
    except Exception as e:
        print(f"[ERROR] Error en bucle principal: {e}")
        try:
            client = conectar_mqtt()
        except:
            pass
        time.sleep(5)
        
    time.sleep(0.1)  # Pequeña pausa para estabilidad