from machine import Pin, PWM
import network
import time
from umqtt.robust import MQTTClient
import json

# Configuración WiFi
SSID = "Red-Peter"
PASSWORD = "12345678"

# Configuración MQTT - solo un tema
MQTT_SERVER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = b"gds0643/ky-016"
CLIENT_ID = "ESP32Client_" + str(time.time())

# Configuración de los pines para el LED RGB
LED_R_PIN = 16  # Pin rojo
LED_G_PIN = 17  # Pin verde
LED_B_PIN = 18  # Pin azul

# Frecuencia PWM para los LEDs
PWM_FREQ = 5000

# Configuración del tiempo de actualización
UPDATE_TIME = 2  # Tiempo entre actualizaciones en segundos

# Diccionario de colores básicos
COLORES = {
    "rojo": (1023, 0, 0),
    "verde": (0, 1023, 0),
    "azul": (0, 0, 1023),
    "amarillo": (1023, 1023, 0),
    "magenta": (1023, 0, 1023),
    "cian": (0, 1023, 1023),
    "blanco": (1023, 1023, 1023),
    "apagado": (0, 0, 0)
}

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

def identificar_color(r, g, b):
    """Identifica el nombre del color basado en valores RGB"""
    # Normalizar los valores (0-1)
    r_norm = r / 1023
    g_norm = g / 1023
    b_norm = b / 1023
    
    # Si todos los valores son bajos, está apagado
    if r_norm < 0.1 and g_norm < 0.1 and b_norm < 0.1:
        return "apagado"
    
    # Si todos los valores son altos, es blanco
    if r_norm > 0.9 and g_norm > 0.9 and b_norm > 0.9:
        return "blanco"
    
    # Determinar el color dominante
    if r_norm > 0.7 and g_norm < 0.3 and b_norm < 0.3:
        return "rojo"
    if r_norm < 0.3 and g_norm > 0.7 and b_norm < 0.3:
        return "verde"
    if r_norm < 0.3 and g_norm < 0.3 and b_norm > 0.7:
        return "azul"
    
    # Colores secundarios
    if r_norm > 0.7 and g_norm > 0.7 and b_norm < 0.3:
        return "amarillo"
    if r_norm > 0.7 and g_norm < 0.3 and b_norm > 0.7:
        return "magenta"
    if r_norm < 0.3 and g_norm > 0.7 and b_norm > 0.7:
        return "cian"
    
    # Si no coincide con ninguno de los anteriores
    return "personalizado"

def mensaje_recibido(topic, msg):
    global red_value, green_value, blue_value
    try:
        # Decodificar el mensaje y extraer los valores RGB
        comando = json.loads(msg.decode())
        
        # Si se recibe un mensaje de estado, ignorarlo
        if 'dispositivo' in comando and comando['dispositivo'] == 'led_rgb':
            return
            
        # Si se envía un color por nombre
        if 'color' in comando:
            color_name = comando['color'].lower()
            if color_name in COLORES:
                red_value, green_value, blue_value = COLORES[color_name]
            else:
                print(f"Color no reconocido: {color_name}")
                return
        # Si se envían valores RGB directos
        elif 'r' in comando and 'g' in comando and 'b' in comando:
            red_value = int(comando['r'])
            green_value = int(comando['g'])
            blue_value = int(comando['b'])
        else:
            print("Comando no reconocido")
            return
            
        # Actualizar los LEDs
        pwm_red.duty(red_value)
        pwm_green.duty(green_value)
        pwm_blue.duty(blue_value)
        
        # Identificar el color actual
        color_actual = identificar_color(red_value, green_value, blue_value)
        print(f"Color actualizado: {color_actual} - R:{red_value}, G:{green_value}, B:{blue_value}")
        
    except Exception as e:
        print(f"Error procesando mensaje: {e}")

def conectar_mqtt():
    try:
        client = MQTTClient(CLIENT_ID, MQTT_SERVER, MQTT_PORT, keepalive=60)
        client.set_callback(mensaje_recibido)
        client.connect(clean_session=True)
        client.subscribe(MQTT_TOPIC)
        print("Conectado a MQTT")
        return client
    except Exception as e:
        print(f"Error conectando a MQTT: {e}")
        return None

def main():
    global pwm_red, pwm_green, pwm_blue, red_value, green_value, blue_value
    
    # Inicializar los pines para los LEDs RGB con PWM
    pwm_red = PWM(Pin(LED_R_PIN), freq=PWM_FREQ, duty=0)
    pwm_green = PWM(Pin(LED_G_PIN), freq=PWM_FREQ, duty=0)
    pwm_blue = PWM(Pin(LED_B_PIN), freq=PWM_FREQ, duty=0)
    
    # Valores iniciales (0-1023 para ESP32)
    red_value = 0
    green_value = 0
    blue_value = 0
    
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
            
            # Verificar si hay mensajes entrantes
            client.check_msg()
            
            # Obtener el nombre del color actual
            color_actual = identificar_color(red_value, green_value, blue_value)
            
            # Publicar el estado actual del LED RGB
            contador += 1
            
            # Crear mensaje JSON
            mensaje = {
                "dispositivo": "led_rgb",
                "color": color_actual,
                "r": red_value,
                "g": green_value,
                "b": blue_value,
                "valor": color_actual,  # Guardar el nombre del color como valor
                "contador": contador,
                "timestamp": time.time()
            }
            
            # Publicar estado
            mensaje_json = json.dumps(mensaje)
            client.publish(MQTT_TOPIC, mensaje_json.encode())
            print(f"Estado publicado #{contador} - Color: {color_actual}")
            
            # Esperar tiempo configurado
            time.sleep(UPDATE_TIME)
            
        except Exception as e:
            print(f"Error: {e}")
            client = None
            time.sleep(5)

if __name__ == "__main__":
    main()x	