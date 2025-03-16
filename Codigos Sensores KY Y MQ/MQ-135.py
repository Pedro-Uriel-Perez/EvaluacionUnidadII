from machine import Pin, ADC
import time
import network
from umqtt.simple import MQTTClient

# Configuración del broker MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = "esp32_mq135"
MQTT_SENSOR_TOPIC = "gds0653/mq-135"
MQTT_PORT = 1883

# Configuración del sensor MQ-135 (Calidad del Aire) - SOLO ANALÓGICO
MQ135_ANALOG_PIN = 34  # Pin ADC para la lectura analógica

# Configuración de ADC para lectura analógica
adc = ADC(Pin(MQ135_ANALOG_PIN))
adc.atten(ADC.ATTN_11DB)  # Configuración para rango 0-3.3V
adc.width(ADC.WIDTH_12BIT)  # Resolución de 12 bits (0-4095)

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
print("Iniciando sensor MQ-135 (Calidad del Aire) - Solo Analógico")
print("¡IMPORTANTE! El sensor necesita tiempo de calentamiento (hasta 24h para precisión máxima)")
print("Para pruebas básicas, 5 minutos de calentamiento son suficientes")
conectar_wifi()

# Conectar a MQTT
client = subscribir()

# Tiempo de calentamiento del sensor (versión reducida para pruebas)
print("Calentando el sensor MQ-135...")
for i in range(60, 0, -1):
    if i % 10 == 0:
        print(f"Tiempo restante: {i} segundos")
    time.sleep(1)

print("¡Sensor listo para pruebas básicas!")
print("Nota: Para mayor precisión, el sensor debería estabilizarse durante más tiempo")

# Bucle principal
while True:
    try:
        # Leer valor analógico del sensor MQ-135
        valor_analogico = adc.read()  # Valor analógico (0-4095)
        
        # Publicar valor como string
        mensaje = str(valor_analogico)
        client.publish(MQTT_SENSOR_TOPIC, mensaje.encode())
        
        # Mostrar en consola con interpretación básica
        if valor_analogico < 1000:
            calidad = "Buena"
        elif valor_analogico < 1800:
            calidad = "Moderada"
        else:
            calidad = "Pobre"
            
        print(f"[INFO] Valor MQ-135: {valor_analogico} - Calidad del aire: {calidad}")
        print(f"[INFO] Publicado en {MQTT_SENSOR_TOPIC}: {mensaje}")
        
        # Esperar antes de la siguiente lectura
        time.sleep(2)
        
    except Exception as e:
        print(f"[ERROR] Error en el loop principal: {e}")
        time.sleep(5)
        try:
            client = subscribir()
        except:
            pass