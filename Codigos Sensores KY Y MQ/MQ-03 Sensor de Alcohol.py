import time
import network
from machine import Pin, ADC
from umqtt.simple import MQTTClient

# 📡 Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# 🌐 Configuración MQTT
MQTT_CLIENT_ID = "esp32_mq3"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC_SENSOR = "gds0653/mq-3"

# 🍺 Configuración del sensor MQ-3 (Alcohol)
MQ3_ANALOG_PIN = 34  # Pin ADC para lectura analógica
MQ3_DIGITAL_PIN = 14  # Pin digital para detección de umbral

# Configuración de ADC del ESP32 para el MQ-3
adc = ADC(Pin(MQ3_ANALOG_PIN))
adc.atten(ADC.ATTN_11DB)  # Configuración para rango 0-3.3V
adc.width(ADC.WIDTH_12BIT)  # Resolución de 12 bits (0-4095)

# Pin digital (umbral de alarma)
digital_sensor = Pin(MQ3_DIGITAL_PIN, Pin.IN)

# LED para indicación visual
led_onboard = Pin(2, Pin.OUT)

# Variable para almacenar el último estado enviado
ultimo_estado = None

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

# 🏁 Inicialización
print("[INFO] Iniciando sensor MQ-3 (Alcohol)")
print("[INFO] Calentando sensor...")
led_onboard.value(1)  # Encender LED durante calentamiento
conectar_wifi()
client = conectar_mqtt()
time.sleep(10)  # Tiempo de calentamiento reducido
led_onboard.value(0)
print("[INFO] ¡Sensor listo!")

# 🔄 Bucle principal
while True:
    try:
        # Leer sensor (invertir lógica si es necesario según tu hardware)
        valor_digital = not digital_sensor.value()  # Adaptado para detección activa en LOW
        
        # Activar LED basado en la lectura digital
        led_onboard.value(valor_digital)
        
        # Convertir a formato binario simple
        estado = "1" if valor_digital else "0"  # 1 = detectado, 0 = no detectado
        
        # Publicar solo si hay cambio o cada 5 segundos
        if estado != ultimo_estado:
            if client:
                client.publish(MQTT_TOPIC_SENSOR, estado)
                
                if estado == "1":
                    print("[ALERTA] Alcohol detectado! Publicado: 1")
                else:
                    print("[INFO] Sin detección. Publicado: 0")
                    
                ultimo_estado = estado
        
    except Exception as e:
        print(f"[ERROR] {e}")
        # Intentar reconectar MQTT si hay error
        try:
            client = conectar_mqtt()
        except:
            pass
    
    time.sleep(0.2)  # Respuesta rápida