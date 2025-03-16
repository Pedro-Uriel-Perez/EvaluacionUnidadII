import time
import network
from machine import Pin
from umqtt.simple import MQTTClient

# 📡 Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# 🌐 Configuración MQTT
MQTT_CLIENT_ID = "esp32_ky022"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC_SENSOR = "gds0653/ky-022"

# 📟 Configuración del sensor KY-022 (Receptor IR)
IR_SENSOR_PIN = 14  # Pin digital para el receptor IR
ir_sensor = Pin(IR_SENSOR_PIN, Pin.IN)

# LED para indicación visual
led_onboard = Pin(2, Pin.OUT)

# Variables para control de rebotes y estado
ultimo_estado = None
ultimo_cambio = 0
DEBOUNCE_TIME = 200  # Tiempo anti-rebote en milisegundos

# 🔌 Conectar a WiFi
def conectar_wifi():
    print("[INFO] Conectando a WiFi...")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.5)
    print("\n[INFO] WiFi Conectada!")
    print(f"[INFO] Dirección IP: {sta_if.ifconfig()[0]}")

# 🔄 Conectar a MQTT
def conectar_mqtt():
    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
        client.connect()
        print(f"[INFO] Conectado a MQTT en {MQTT_BROKER}")
        return client
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a MQTT: {e}")
        return None

# Función para obtener tiempo en milisegundos
def millis():
    return time.ticks_ms()

# 🏁 Inicialización
print("[INFO] Iniciando sensor KY-022 (Receptor IR)")
print("[INFO] Este sensor detecta señales infrarrojas de controles remotos")
conectar_wifi()
client = conectar_mqtt()
print("[INFO] Sistema listo. Esperando señales IR...")

# 🔄 Bucle principal
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
            time.sleep(2)
            continue
            
        # Leer estado del sensor IR
        # La mayoría de los receptores IR tienen lógica invertida:
        # LOW (0) = Señal IR detectada, HIGH (1) = No hay señal
        ir_detectado = not ir_sensor.value()  # Invertimos la lógica
        
        # Encender LED cuando se detecta señal IR
        led_onboard.value(0 if ir_detectado else 1)
        
        # Obtener tiempo actual
        ahora = millis()
        
        # Detección con anti-rebote
        if (ir_detectado != ultimo_estado) and (ahora - ultimo_cambio > DEBOUNCE_TIME):
            # Mensaje con el estado
            estado = "DETECTADA" if ir_detectado else "NO DETECTADA"
            mensaje = f'{{"estado":"{estado.lower()}","valor":{0 if ir_detectado else 1}}}'
            
            # Publicar en MQTT
            if client:
                client.publish(MQTT_TOPIC_SENSOR, mensaje)
                print(f"Señal IR {estado}")
            
            ultimo_estado = ir_detectado
            ultimo_cambio = ahora
            
    except Exception as e:
        print(f"[ERROR] Error en el loop principal: {e}")
        client = None
        time.sleep(2)
        
    time.sleep(0.1)  # Pequeña pausa para estabilidad