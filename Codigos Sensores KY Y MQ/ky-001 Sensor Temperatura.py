from machine import Pin
import time
import network
import onewire
import ds18x20
from umqtt.simple import MQTTClient

# Configuración del broker MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = "esp32_client"  
MQTT_SENSOR_TOPIC = "gds0653/ky-001"
MQTT_PORT = 1883

# Configuración del sensor de temperatura KY-001 (DS18B20)
TEMP_PIN = 26  # GPIO26 para el sensor de temperatura
temp_bus = onewire.OneWire(Pin(TEMP_PIN))
temp_sensor = ds18x20.DS18X20(temp_bus)

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
conectar_wifi()

# Conectar a MQTT
client = subscribir()

# Buscar sensores DS18B20
print("Buscando sensores de temperatura...")
roms = temp_sensor.scan()
if len(roms) == 0:
    print("¡No se encontraron sensores! Verificar conexiones")
else:
    print(f"Encontrados {len(roms)} sensores")

# Bucle principal
while True:
    try:
        if len(roms) > 0:
            # Iniciar la conversión de temperatura
            temp_sensor.convert_temp()
            
            # Esperar a que se complete la conversión (750ms)
            time.sleep(1)
            
            # Leer la temperatura del primer sensor encontrado
            temperatura = temp_sensor.read_temp(roms[0])
            
            # Redondear a un decimal
            temperatura = round(temperatura, 1)
            
            # Crear el mensaje
            mensaje = f"{temperatura}"
            
            # Publicar en MQTT
            client.publish(MQTT_SENSOR_TOPIC, mensaje.encode())  # Publicar valor como bytes
            
            # Mostrar en consola
            print(f"[INFO] Temperatura: {temperatura}°C")
            print(f"[INFO] Publicado en {MQTT_SENSOR_TOPIC}: {mensaje}")
            
            # Esperar antes de la siguiente lectura
            time.sleep(2)
            
        else:
            print("[INFO] Buscando sensores...")
            roms = temp_sensor.scan()
            time.sleep(5)
            
    except Exception as e:
        print(f"[ERROR] Error en el loop principal: {e}")
        time.sleep(5)
        try:
            client = subscribir()
        except:
            passO