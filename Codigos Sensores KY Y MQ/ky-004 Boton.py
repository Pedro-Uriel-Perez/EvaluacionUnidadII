from machine import Pin
import time
import network
from umqtt.simple import MQTTClient

# Configuración de pines con resistencia pull-up interna
boton_pin = Pin(16, Pin.IN, Pin.PULL_UP)  # GPIO16 para el botón con pull-up

# Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# Configuración MQTT
MQTT_CLIENT_ID = "esp32_boton_sensor"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC_SENSOR = "gds0653/ky-004"    # Publicar estado del botón

# Variables de control
ultimo_estado_boton = None
ultimo_cambio = 0
DEBOUNCE_TIME = 200  # Tiempo anti-rebote en milisegundos
errores_conexion = 0

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
    global errores_conexion
    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
        client.connect()
        print(f"[INFO] Conectado a MQTT en {MQTT_BROKER}")
        errores_conexion = 0
        return client
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a MQTT: {e}")
        errores_conexion += 1
        return None

def millis():
    """Devuelve el tiempo actual en milisegundos."""
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
            
        # Leer estado del botón (invertido porque usamos pull-up)
        estado_boton_raw = boton_pin.value()
        estado_boton = 1 if estado_boton_raw == 0 else 0  # Invertimos la lógica
        
        # Técnica anti-rebote
        tiempo_actual = millis()
        if (estado_boton != ultimo_estado_boton) and (tiempo_actual - ultimo_cambio > DEBOUNCE_TIME):
            mensaje_boton = f"{estado_boton}"
            client.publish(MQTT_TOPIC_SENSOR, mensaje_boton)
            print(f"[INFO] Publicado en {MQTT_TOPIC_SENSOR}: {mensaje_boton}")
            ultimo_estado_boton = estado_boton
            ultimo_cambio = tiempo_actual
        
        # Si hay demasiados errores, reiniciar conexiones
        if errores_conexion >= 10:
            print("[ERROR] Demasiados errores, reiniciando conexiones...")
            conectar_wifi()
            client = conectar_mqtt()
            errores_conexion = 0
            
    except Exception as e:
        print(f"[ERROR] Error en el loop principal: {e}")
        client = None
        
    time.sleep(0.01)  # Pequeña pausa para estabilidad