from machine import Pin, ADC
import time
import network
from umqtt.simple import MQTTClient

# Configuración del broker MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = "esp32_sensor"
MQTT_SENSOR_TOPIC = "gds0653/ky-036"
MQTT_PORT = 1883

# Configuración del sensor analógico
ANALOG_PIN = 34  # Pin ADC para la lectura analógica (A0 del sensor)

# Configuración de ADC para lectura analógica
adc = ADC(Pin(ANALOG_PIN))
adc.atten(ADC.ATTN_0DB)  # Configuración para rango 0-1V para mayor sensibilidad
adc.width(ADC.WIDTH_12BIT)  # Resolución de 12 bits (0-4095)

# Variables para control
ultimo_envio = 0
INTERVALO_ENVIO = 1000  # Enviar datos cada 1 segundo (ms)

def conectar_wifi():
    print("Conectando WiFi...", end="")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect('Red-Peter', '12345678')
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.3)
    print(" ¡Conectado!")
    print(f"Dirección IP: {sta_if.ifconfig()[0]}")

def subscribir():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT,
                        user=MQTT_USER, password=MQTT_PASSWORD, keepalive=60)
    client.connect()
    print(f"Conectado a {MQTT_BROKER}")
    print(f"Publicando en el tópico {MQTT_SENSOR_TOPIC}")
    return client

# Función para obtener tiempo en milisegundos
def millis():
    return time.ticks_ms()

# Conectar a WiFi
print("Iniciando sensor analógico en pin 34")
conectar_wifi()

# Conectar a MQTT
client = subscribir()

print("Sistema listo! Monitoreando valores del sensor...")

# Tomar algunas lecturas iniciales para estabilizar
for _ in range(5):
    adc.read()
    time.sleep(0.1)

# Bucle principal
while True:
    try:
        # Realizar múltiples lecturas y promediar para estabilidad
        total = 0
        muestras = 10
        for _ in range(muestras):
            total += adc.read()
            time.sleep(0.01)
        
        valor_analogico = total // muestras  # Valor promedio
        
        # Obtener tiempo actual
        ahora = millis()
        
        # Publicar datos periódicamente
        if ahora - ultimo_envio >= INTERVALO_ENVIO:
            # Publicar en MQTT solo el valor analógico como string
            mensaje = str(valor_analogico)
            
            # Publicar en MQTT
            client.publish(MQTT_SENSOR_TOPIC, mensaje.encode())
            
            # Mostrar información en consola
            print(f"[INFO] Valor del sensor: {valor_analogico}")
            print(f"[INFO] Publicado en {MQTT_SENSOR_TOPIC}: {mensaje}")
            
            ultimo_envio = ahora
            
    except Exception as e:
        print(f"[ERROR] Error en el loop principal: {e}")
        # Intentar reconectar
        time.sleep(5)
        try:
            client = subscribir()
        except:
            pass
            
    time.sleep(0.1)  # Pequeña pausa