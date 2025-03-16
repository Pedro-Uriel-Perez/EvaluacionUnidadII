from machine import Pin, ADC
import time
import network
from umqtt.simple import MQTTClient

# Configuración del broker MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = "esp32_ky039"
MQTT_SENSOR_TOPIC = "gds0653/ky-039"
MQTT_PORT = 1883

# Configuración del sensor de pulso KY-039
PULSE_ANALOG_PIN = 34  # Pin ADC para la lectura analógica (S del sensor)

# Configuración de ADC para lectura analógica
adc = ADC(Pin(PULSE_ANALOG_PIN))
adc.atten(ADC.ATTN_11DB)  # Configuración para rango 0-3.3V
adc.width(ADC.WIDTH_12BIT)  # Resolución de 12 bits (0-4095)

# Variables para control
ultimo_envio = 0
INTERVALO_ENVIO = 1000  # Enviar datos cada 1 segundo (ms)
TIEMPO_MUESTREO = 50    # Tiempo entre muestras (ms)
buffer_valores = []     # Buffer para almacenar lecturas
VENTANA_MUESTRAS = 20   # Número de muestras para detectar pulsos

# Variables para cálculo de BPM
ultimo_pulso = 0        # Tiempo del último pulso detectado
pulsos = []             # Lista para almacenar intervalos entre pulsos
bpm = 0                 # Valor BPM calculado
umbral_superior = 2500  # Valor inicial para umbral superior
umbral_inferior = 1500  # Valor inicial para umbral inferior
estado_pulso = False    # True si estamos por encima del umbral

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

# Función para calcular BPM a partir de intervalos entre pulsos
def calcular_bpm(intervalos):
    if not intervalos:
        return 0
    
    # Calcular BPM basado en el promedio de intervalos
    intervalo_promedio = sum(intervalos) / len(intervalos)
    return int(60000 / intervalo_promedio)  # 60000 ms = 1 minuto

# Conectar a WiFi
print("Iniciando sensor de pulso KY-039")
print("Coloque su dedo en el sensor para detectar pulsos cardíacos")
conectar_wifi()

# Conectar a MQTT
client = subscribir()

print("Sistema listo! Monitoreando pulso cardíaco...")

# Bucle principal
ultimo_tiempo_muestreo = 0
while True:
    try:
        # Obtener tiempo actual
        ahora = millis()
        
        # Tomar una muestra cada TIEMPO_MUESTREO
        if ahora - ultimo_tiempo_muestreo >= TIEMPO_MUESTREO:
            # Leer valor del sensor
            valor = adc.read()
            
            # Agregar al buffer y mantener tamaño
            buffer_valores.append(valor)
            if len(buffer_valores) > VENTANA_MUESTRAS:
                buffer_valores.pop(0)
            
            # Si tenemos suficientes muestras, podemos detectar pulsos
            if len(buffer_valores) == VENTANA_MUESTRAS:
                # Calcular promedio y ajustar umbrales dinámicamente
                promedio = sum(buffer_valores) / len(buffer_valores)
                umbral_superior = promedio + 100
                umbral_inferior = promedio - 100
                
                # Detectar pulso (cuando la señal cruza hacia arriba el umbral)
                if valor > umbral_superior and not estado_pulso:
                    estado_pulso = True
                    
                    # Calcular intervalo desde el último pulso
                    if ultimo_pulso > 0:
                        intervalo = ahora - ultimo_pulso
                        
                        # Solo considerar intervalos razonables (30-250 BPM)
                        if 240 < intervalo < 2000:
                            pulsos.append(intervalo)
                            
                            # Limitar el array a los últimos 10 pulsos
                            if len(pulsos) > 10:
                                pulsos.pop(0)
                            
                            # Calcular BPM
                            bpm = calcular_bpm(pulsos)
                    
                    ultimo_pulso = ahora
                
                # Detectar cuando la señal baja por debajo del umbral
                elif valor < umbral_inferior and estado_pulso:
                    estado_pulso = False
            
            ultimo_tiempo_muestreo = ahora
        
        # Publicar datos periódicamente
        if ahora - ultimo_envio >= INTERVALO_ENVIO:
            # Solo publicar si tenemos un BPM válido
            if bpm > 0:
                # Crear mensaje: valor actual, BPM
                mensaje = f"{valor},{bpm}"
                
                # Publicar en MQTT
                client.publish(MQTT_SENSOR_TOPIC, mensaje.encode())
                
                # Mostrar información en consola
                print(f"[INFO] Valor: {valor} | BPM: {bpm}")
                print(f"[INFO] Publicado en {MQTT_SENSOR_TOPIC}: {mensaje}")
            else:
                # Publicar solo el valor si no hay BPM calculado aún
                mensaje = f"{valor},0"
                client.publish(MQTT_SENSOR_TOPIC, mensaje.encode())
                print(f"[INFO] Esperando pulsos... Valor: {valor}")
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
            
    time.sleep(0.01)  # Pequeña pausa