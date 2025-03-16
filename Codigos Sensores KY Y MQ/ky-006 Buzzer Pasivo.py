from machine import Pin, PWM
import time
import network
from umqtt.simple import MQTTClient
import json

# Configuración del Buzzer Pasivo con PWM
buzzer = PWM(Pin(27))  # Usando el pin 27 
buzzer.duty(0)  # Inicialmente apagado

# Verificación inicial
buzzer.freq(1000)  # Tono de 1000 Hz
buzzer.duty(512)   # Volumen medio
print("[TEST] Probando buzzer")
time.sleep(1)
buzzer.duty(0)
print("[TEST] Prueba finalizada")

# Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# Configuración MQTT
MQTT_CLIENT_ID = "esp32_buzzer_pasivo"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "gds0653/ky-006"  # Mantén el mismo tópico que usabas antes

# Variables para control
estado_buzzer = False
ultimo_cambio = 0
contador = 0
intervalo_cambio = 5000  # 5 segundos

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

print("[INFO] Buzzer pasivo inicializado")

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
        
        # Alternar estado cada 5 segundos
        tiempo_actual = millis()
        if tiempo_actual - ultimo_cambio >= intervalo_cambio:
            # Alternar estado
            estado_buzzer = not estado_buzzer
            
            # Activar o desactivar el buzzer
            if estado_buzzer:
                buzzer.freq(1000)  # Tono de 1000 Hz
                buzzer.duty(512)   # Volumen medio
            else:
                buzzer.duty(0)     # Apagar
            
            # Preparar mensaje - enviar exactamente como antes
            estado = "encendido" if estado_buzzer else "apagado"
            
            # Este formato era el que funcionaba antes
            client.publish(MQTT_TOPIC, estado)
            print(f"[INFO] Buzzer {estado.upper()}")
            
            ultimo_cambio = tiempo_actual
            
    except Exception as e:
        print(f"[ERROR] Error en bucle principal: {e}")
        try:
            client = conectar_mqtt()
        except:
            pass
        time.sleep(5)
        
    time.sleep(0.1)  # Pequeña pausa para estabilidad