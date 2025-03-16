import time
import network
from machine import Pin, ADC
from umqtt.simple import MQTTClient

# Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# Configuración MQTT
MQTT_CLIENT_ID = "esp32_mq04"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "gds0653/mq-04"

# Configuración del MQ-04 (Sensor de metano/gas natural)
MQ04_ANALOG_PIN = 34  # Pin ADC para la lectura analógica
MQ04_DIGITAL_PIN = 14  # Pin digital para detección de umbral

# Configuración ADC para lectura analógica
adc = ADC(Pin(MQ04_ANALOG_PIN))
adc.atten(ADC.ATTN_11DB)  # Configuración para rango 0-3.3V
adc.width(ADC.WIDTH_12BIT)  # Resolución de 12 bits (0-4095)

# Configuración del pin digital (para detección de umbral)
digital_sensor = Pin(MQ04_DIGITAL_PIN, Pin.IN)

# LED para indicación visual
led_onboard = Pin(2, Pin.OUT)

# Variables para control
ultimo_valor = 0
ultimo_estado_digital = None
ultimo_envio = 0
INTERVALO_ENVIO = 2000  # Enviar datos cada 2 segundos
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
print("Iniciando sensor MQ-04 (Metano/Gas Natural)")
print("¡IMPORTANTE! El sensor necesita tiempo de calentamiento (~3 minutos)")
conectar_wifi()
client = conectar_mqtt()

# Tiempo de calentamiento del sensor
print("Calentando el sensor MQ-04...")
for i in range(30, 0, -1):
    print(f"Tiempo restante: {i} segundos")
    led_onboard.value(i % 2)  # Parpadear LED durante calentamiento
    time.sleep(1)

print("¡Sensor listo! Monitoreando gas metano/natural...")
led_onboard.value(0)  # Apagar LED después del calentamiento

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
        
        # Leer valores del sensor MQ-04
        valor_analogico = adc.read()  # Valor analógico (0-4095)
        valor_digital = not digital_sensor.value()  # Normalmente activo en LOW
        
        # Convertir valor analógico a voltaje (aproximado)
        voltaje = valor_analogico * 3.3 / 4095
        
        # LED indicador para alerta
        led_onboard.value(1 if valor_digital else 0)
        
        # Obtener tiempo actual
        ahora = millis()
        
        # Determinar si es momento de enviar datos
        cambio_significativo = abs(valor_analogico - ultimo_valor) > UMBRAL_CAMBIO
        cambio_digital = valor_digital != ultimo_estado_digital
        tiempo_envio = ahora - ultimo_envio > INTERVALO_ENVIO
        
        if cambio_significativo or cambio_digital or tiempo_envio:
            # Crear mensaje con formato JSON
            mensaje = '{"valor":' + str(valor_analogico) + ',"alerta":' + str(1 if valor_digital else 0) + '}'
            
            # Publicar en MQTT
            client.publish(MQTT_TOPIC, mensaje)
            
            # Actualizar consola
            estado = "¡ALERTA! Gas detectado" if valor_digital else "Normal"
            print(f"Estado: {estado} | Valor: {valor_analogico} | Voltaje: {voltaje:.2f}V")
            
            # Actualizar últimos valores
            ultimo_valor = valor_analogico
            ultimo_estado_digital = valor_digital
            ultimo_envio = ahora
            
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)
        
    time.sleep(0.1)  # Pequeña pausa