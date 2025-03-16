from machine import Pin
import time
import network
from umqtt.simple import MQTTClient

# Configuración de pines
laser_pin = Pin(16, Pin.OUT)    # GPIO16 para el láser
boton_pin = Pin(4, Pin.IN)      # GPIO4 para el botón

# Configuración WiFi
WIFI_SSID = "DESKTOP-BVQOQ56 7592"
WIFI_PASSWORD = "Popeye08"

# Configuración MQTT
MQTT_CLIENT_ID = "esp32_laser_ky008"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC_SENSOR = "postgres/sensors"    # Publicar estado del botón
MQTT_TOPIC_ACTUATOR = "postgres/actuator" # Publicar estado del láser

# Variables de control
ultimo_estado_boton = None
ultimo_estado_laser = None
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

        # Leer estado del botón
        estado_boton = boton_pin.value()

        # Encender o apagar el láser según el botón
        laser_pin.value(estado_boton)  # Si el botón es 1, el láser se enciende

        # Solo publicar si los estados cambiaron
        if estado_boton != ultimo_estado_boton:
            mensaje_boton = f"{estado_boton}"
            client.publish(MQTT_TOPIC_SENSOR, mensaje_boton)
            print(f"[INFO] Publicado en {MQTT_TOPIC_SENSOR}: {mensaje_boton}")
            ultimo_estado_boton = estado_boton
        
        if estado_boton != ultimo_estado_laser:
            mensaje_laser = f"{estado_boton}"
            client.publish(MQTT_TOPIC_ACTUATOR, mensaje_laser)
            print(f"[INFO] Publicado en {MQTT_TOPIC_ACTUATOR}: {mensaje_laser}")
            ultimo_estado_laser = estado_boton

        # Si hay demasiados errores, reiniciar conexiones
        if errores_conexion >= 10:
            print("[ERROR] Demasiados errores, reiniciando conexiones...")
            conectar_wifi()
            client = conectar_mqtt()
            errores_conexion = 0

    except Exception as e:
        print(f"[ERROR] Error en el loop principal: {e}")
        client = None

    time.sleep(0.1)  # Pequeña pausa para estabilidad

