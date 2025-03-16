from machine import Pin
import time
import network
from umqtt.simple import MQTTClient
import json

# Configuración del sensor fotointerruptor
photo_pin = Pin(16, Pin.IN, Pin.PULL_UP)  # GPIO16 con resistencia pull-up interna
led_pin = Pin(2, Pin.OUT)  # LED integrado en ESP32 para indicación visual

# Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# Configuración MQTT
MQTT_CLIENT_ID = "esp32_photo_interrupter"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "gds0653/photo-interrupter"

# Variables para control
ultimo_estado = None
ultimo_cambio = 0
DEBOUNCE_TIME = 300  # Tiempo anti-rebote en milisegundos
contador = 0
contador_interrupciones = 0  # Contador de número de interrupciones

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

print("[INFO] Iniciando monitoreo del fotointerruptor...")

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
            
        # Leer el estado del fotointerruptor
        # 0 = Interrumpido (Algo bloqueando el haz)
        # 1 = No interrumpido (Haz pasando normalmente)
        raw_state = photo_pin.value()
        
        # Invertir para mejor interpretación 
        # True = Interrumpido (bloqueado), False = No interrumpido (libre)
        is_interrupted = not raw_state
        
        # Actualizar LED para indicación visual
        led_pin.value(1 if is_interrupted else 0)
        
        # Aplicar debounce para lecturas estables
        ahora = millis()
        if (is_interrupted != ultimo_estado) and (ahora - ultimo_cambio > DEBOUNCE_TIME):
            contador += 1
            
            # Si pasamos de no interrumpido a interrumpido, incrementar contador de interrupciones
            if is_interrupted and ultimo_estado is not None:
                contador_interrupciones += 1
            
            mensaje = json.dumps({
                "sensor": "fotointerruptor",
                "valor": 1 if is_interrupted else 0,
                "estado": "interrumpido" if is_interrupted else "libre",
                "contador": contador,
                "interrupciones": contador_interrupciones,
                "timestamp": time.time()
            })
            
            client.publish(MQTT_TOPIC, mensaje)
            print(f"[INFO] #{contador} - Estado: {'INTERRUMPIDO' if is_interrupted else 'LIBRE'}, Total interrupciones: {contador_interrupciones}")
            
            ultimo_estado = is_interrupted
            ultimo_cambio = ahora
            
    except Exception as e:
        print(f"[ERROR] Error en bucle principal: {e}")
        try:
            client = conectar_mqtt()
        except:
            pass
        time.sleep(5)
        
    time.sleep(0.05)  # Pequeña pausa para estabilidad