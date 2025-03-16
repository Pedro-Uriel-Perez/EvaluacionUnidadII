from machine import Pin, ADC
import network
import time
from umqtt.robust import MQTTClient
import json
import urequests  # Usar para hacer solicitudes HTTP

# Configuración WiFi
SSID = "Red-Peter"
PASSWORD = "12345678"

# Configuración MQTT
MQTT_SERVER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = b"gds0643/ky-028"
CLIENT_ID = "ESP32Client_" + str(time.time())

# Configuración del sensor KY-028
TEMP_DIGITAL_PIN = 16    # Pin para la salida digital
TEMP_ANALOG_PIN = 32     # Pin para la salida analógica (ADC)

# Configuración del tiempo de muestreo
SAMPLE_TIME = 2   # Tiempo entre muestras en segundos

# URL del servidor que recibe los datos
SERVER_URL = "http://tu-servidor.com/api/insert_temperature"  # Cambia por tu URL de API

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Conectando a WiFi...')
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.5)
            print('.', end='')
    print('\nConectado a WiFi')
    print('Dirección IP:', wlan.ifconfig()[0])

def conectar_mqtt():
    try:
        client = MQTTClient(CLIENT_ID, MQTT_SERVER, MQTT_PORT, keepalive=60)
        client.connect(clean_session=True)
        print("Conectado a MQTT")
        return client
    except Exception as e:
        print(f"Error conectando a MQTT: {e}")
        return None

def enviar_datos_a_base_de_datos(temperatura):
    try:
        # Crear los datos que se enviarán a la base de datos
        datos = {
            "sensor_id": 3,  # Ajusta el ID del sensor según tu base de datos
            "user_id": 1,    # Ajusta el ID de usuario según tu base de datos
            "value": temperatura  # Aquí se usa la temperatura calculada
        }
        
        # Hacer la solicitud HTTP POST para insertar los datos
        response = urequests.post(SERVER_URL, json=datos)
        
        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            print("Temperatura guardada correctamente en la base de datos.")
        else:
            print(f"Error al guardar la temperatura: {response.status_code}")
        response.close()
    except Exception as e:
        print(f"Error al enviar los datos a la base de datos: {e}")

def main():
    # Inicializar pines del sensor
    temp_digital = Pin(TEMP_DIGITAL_PIN, Pin.IN)
    temp_analog = ADC(Pin(TEMP_ANALOG_PIN))
    temp_analog.atten(ADC.ATTN_11DB)  # Configurar para rango completo 0-3.3V
    
    # Conectar a WiFi
    conectar_wifi()
    
    # Iniciar cliente MQTT
    client = None
    contador = 0
    
    while True:
        try:
            # Reconectar MQTT si es necesario
            if client is None:
                client = conectar_mqtt()
                if client is None:
                    time.sleep(5)
                    continue
            
            # Leer sensor - salida digital (0=frío, 1=caliente respecto al umbral ajustado)
            umbral_superado = temp_digital.value()
            
            # Leer valor analógico (0-4095)
            valor_analogico = temp_analog.read()
            
            # Convertir a una temperatura aproximada (ajustar según calibración)
            # Fórmula simplificada, necesita calibración para mayor precisión
            temperatura_aprox = (valor_analogico / 4095) * 100  # Temperatura en °C (aproximada)
            
            contador += 1
            
            # Crear mensaje JSON para MQTT
            mensaje = {
                "sensor": "temperatura",
                "valor_digital": umbral_superado,
                "valor_analogico": valor_analogico,
                "temperatura_aprox": round(temperatura_aprox, 1),
                "estado": "caliente" if umbral_superado else "frio",
                "contador": contador,
                "timestamp": time.time()
            }
            
            # Publicar datos en MQTT
            mensaje_json = json.dumps(mensaje)
            client.publish(MQTT_TOPIC, mensaje_json.encode())
            print(f"Enviado #{contador} - Temperatura: {round(temperatura_aprox, 1)}°C, Estado: {'Caliente' if umbral_superado else 'Frío'}")
            
            # Enviar datos a la base de datos
            enviar_datos_a_base_de_datos(round(temperatura_aprox, 1))  # Se envía la temperatura real
            
            # Esperar tiempo de muestreo configurado
            time.sleep(SAMPLE_TIME)
            
        except Exception as e:
            print(f"Error: {e}")
            client = None
            time.sleep(5)

if __name__ == "__main__":
    main()