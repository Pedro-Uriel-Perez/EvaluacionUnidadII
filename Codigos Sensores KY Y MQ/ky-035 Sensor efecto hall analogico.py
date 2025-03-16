import time
import network
from machine import Pin, ADC
from umqtt.simple import MQTTClient

# Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# Configuración MQTT
MQTT_CLIENT_ID = "esp32_ky035"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "gds0653/ky-035"

# Configuración del KY-035 (Sensor de efecto Hall analógico)
HALL_ANALOG_PIN = 34  # Pin ADC para la lectura analógica (verificar en ESP32)
HALL_DIGITAL_PIN = 14  # Pin digital para detección de umbral (si el módulo lo tiene)

# Configuración ADC para lectura analógica
adc = ADC(Pin(HALL_ANALOG_PIN))
adc.atten(ADC.ATTN_11DB)  # Configuración para rango 0-3.3V
adc.width(ADC.WIDTH_12BIT)  # Resolución de 12 bits (0-4095)

# Configuración del pin digital (para módulos que incluyen salida digital)
try:
    digital_sensor = Pin(HALL_DIGITAL_PIN, Pin.IN)
    digital_disponible = True
except:
    digital_disponible = False

# LED para indicación visual
led_onboard = Pin(2, Pin.OUT)

# Variables para control
ultimo_valor = 0
ultimo_estado_digital = None
ultimo_envio = 0
INTERVALO_ENVIO = 1000  # Enviar datos cada 1 segundo
UMBRAL_CAMBIO = 100  # Enviar si el valor cambia más de esto

# Conectar a WiFi
def conectar_wifi():
    print("Conectando a WiFi...")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.5)
    print("\nWiFi Conectada!")

# Conectar a MQTT
def conectar_mqtt():
    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
        client.connect()
        print("Conectado a MQTT")
        return client
    except Exception as e:
        print(f"Error conectando a MQTT: {e}")
        return None

# Función para obtener tiempo en milisegundos
def millis():
    return time.ticks_ms()

# Inicialización
print("Iniciando sensor KY-035 (Sensor de efecto Hall analógico)")
print("Este sensor detecta campos magnéticos")
conectar_wifi()
client = conectar_mqtt()

print("Sistema listo! Acerque un imán al sensor...")

# Bucle principal
while True:
    try:
        # Verificar conexión WiFi y MQTT
        if not network.WLAN(network.STA_IF).isconnected() or client is None:
            print("Reconectando...")
            conectar_wifi()
            client = conectar_mqtt()
            time.sleep(2)
            continue
        
        # Leer valores del sensor KY-035
        valor_analogico = adc.read()  # Valor analógico (0-4095)
        
        # Leer valor digital si está disponible
        if digital_disponible:
            valor_digital = digital_sensor.value()
            led_onboard.value(valor_digital)  # LED refleja estado digital
        else:
            # Si no hay pin digital, usar un umbral en el valor analógico
            # para encender/apagar el LED
            umbral = 2047  # Mitad del rango (0-4095)
            valor_digital = valor_analogico > umbral
            led_onboard.value(1 if valor_digital else 0)
        
        # Obtener tiempo actual
        ahora = millis()
        
        # Determinar si es momento de enviar datos
        cambio_significativo = abs(valor_analogico - ultimo_valor) > UMBRAL_CAMBIO
        cambio_digital = digital_disponible and (valor_digital != ultimo_estado_digital)
        tiempo_envio = ahora - ultimo_envio > INTERVALO_ENVIO
        
        if cambio_significativo or cambio_digital or tiempo_envio:
            # Enviar el valor analógico como texto
            valor_a_enviar = str(valor_analogico)
            
            # Publicar en MQTT
            client.publish(MQTT_TOPIC, valor_a_enviar)
            
            # Actualizar consola
            estado = "DETECTADO" if valor_digital else "NO DETECTADO"
            print(f"Campo magnético: {estado} (Valor: {valor_analogico})")
            
            # Actualizar últimos valores
            ultimo_valor = valor_analogico
            ultimo_estado_digital = valor_digital
            ultimo_envio = ahora
            
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)
        
    time.sleep(0.1)  # Pequeña pausa