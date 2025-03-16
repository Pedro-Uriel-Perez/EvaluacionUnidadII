from machine import Pin
import time
import network
from umqtt.simple import MQTTClient

# 📡 Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# 📡 Configuración MQTT
MQTT_CLIENT_ID = "esp32"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "gds0653/ky-019"

# Configuración del pin del relé
relevador = Pin(15, Pin.OUT)  # Asegúrate de conectar el relé al pin adecuado

# 📡 Conexión WiFi
def conectar_wifi():
    print("Conectando a WiFi...", end="")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
    
    tiempo_max_espera = 10  # Espera máxima de 10 segundos
    while not sta_if.isconnected() and tiempo_max_espera > 0:
        print(".", end="")
        time.sleep(1)
        tiempo_max_espera -= 1

    if sta_if.isconnected():
        print("\nWiFi Conectada!")
    else:
        print("\nNo se pudo conectar a WiFi")
        reset()  # Reiniciar el ESP32 si no se conecta a WiFi

# 📌 Función para manejar mensajes MQTT (no procesamos mensajes de encendido y apagado)
def llegada_mensaje(topic, msg):
    # No procesamos el mensaje, simplemente manejamos ON y OFF
    pass

# 📌 Función para conectarse a MQTT
def conectar_mqtt():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
    client.set_callback(llegada_mensaje)  # Asignar la función para recibir mensajes
    try:
        client.connect()
        client.subscribe(MQTT_TOPIC)  # Suscribirse al tópico del relé
        print(f"Conectado a MQTT {MQTT_BROKER} y suscrito a {MQTT_TOPIC}")
        return client
    except Exception as e:
        print(f"Error al conectar a MQTT: {e}")
        reset()  # Reiniciar el ESP32 si no se conecta a MQTT

# Conectar a WiFi y MQTT
conectar_wifi()
client = conectar_mqtt()

# Ciclo de encendido y apagado del relé (mantener 3 segundos encendido y 3 segundos apagado)
while True:
    try:
        # Encender el relé durante 3 segundos
        relevador.on()
        print("Relé Encendido")
        client.publish(MQTT_TOPIC, b'ON')  # Publicar estado 'ON'
        
        # Esperar 3 segundos
        time.sleep(3)

        # Apagar el relé durante 3 segundos
        relevador.off()
        print("Relé Apagado")
        client.publish(MQTT_TOPIC, b'OFF')  # Publicar estado 'OFF'
        
        # Esperar otros 3 segundos antes de encender nuevamente
        time.sleep(3)

        # Revisar si hay mensajes en el tópico (sin bloquear el ciclo)
        client.check_msg()
        
    except Exception as e:
        print(f"Error en la lectura del relé: {e}")

    time.sleep(1)  # Revisa los mensajes cada 1 segundo para asegurar que el ciclo no se bloquee