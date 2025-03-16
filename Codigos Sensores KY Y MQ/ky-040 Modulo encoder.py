from machine import Pin
import time
import network
from umqtt.simple import MQTTClient

# Configuración del broker MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = "esp32_ky040"
MQTT_SENSOR_TOPIC = "gds0653/ky-040"
MQTT_PORT = 1883

# Configuración del módulo encoder KY-040
CLK_PIN = 26  # Pin CLK del encoder
DT_PIN = 25   # Pin DT del encoder
SW_PIN = 27   # Pin SW del encoder (botón)

# Configuración de pines
clk = Pin(CLK_PIN, Pin.IN, Pin.PULL_UP)
dt = Pin(DT_PIN, Pin.IN, Pin.PULL_UP)
sw = Pin(SW_PIN, Pin.IN, Pin.PULL_UP)

# Variables para control
contador = 0           # Valor del contador
clk_ultimo = clk.value()  # Último estado del pin CLK
sw_ultimo = 1          # Último estado del botón
ultimo_envio = 0       # Tiempo del último envío MQTT
ultimo_cambio = 0      # Tiempo del último cambio
DEBOUNCE_TIME = 50     # Tiempo anti-rebote en ms

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
print("Iniciando módulo encoder KY-040")
conectar_wifi()

# Conectar a MQTT
client = subscribir()

print("Sistema listo! Gire el encoder o presione el botón...")

# Bucle principal
while True:
    try:
        # Obtener tiempo actual
        ahora = millis()
        
        # Leer el estado actual del CLK
        clk_actual = clk.value()
        
        # Verificar si el CLK ha cambiado (esto ocurre cuando el encoder rota)
        if clk_actual != clk_ultimo:
            # Si el pin DT difiere del pin CLK, encoder rotando en sentido horario
            if dt.value() != clk_actual:
                contador += 1
                direccion = "CW"  # Clockwise (sentido horario)
            else:
                contador -= 1
                direccion = "CCW"  # Counter-clockwise (sentido antihorario)
                
            # Publicar en MQTT
            mensaje = f"ROT,{contador},{direccion}"
            client.publish(MQTT_SENSOR_TOPIC, mensaje.encode())
            
            # Mostrar información en consola
            print(f"[INFO] Encoder rotado: {direccion} | Contador: {contador}")
            print(f"[INFO] Publicado en {MQTT_SENSOR_TOPIC}: {mensaje}")
            
            # Actualizar último estado de CLK
            clk_ultimo = clk_actual
            ultimo_envio = ahora
        
        # Verificar si el botón ha sido presionado (el botón es normalmente HIGH)
        sw_actual = sw.value()
        
        # Si el botón cambia de estado y pasó el tiempo de debounce
        if sw_actual != sw_ultimo and (ahora - ultimo_cambio) > DEBOUNCE_TIME:
            # Si el botón está presionado (LOW)
            if sw_actual == 0:
                # Publicar en MQTT
                mensaje = f"BTN,{contador},PRESS"
                client.publish(MQTT_SENSOR_TOPIC, mensaje.encode())
                
                # Mostrar información en consola
                print(f"[INFO] Botón presionado | Contador: {contador}")
                print(f"[INFO] Publicado en {MQTT_SENSOR_TOPIC}: {mensaje}")
                
                # Opcional: Resetear contador al presionar botón
                # contador = 0
            
            # Actualizar último estado y tiempo del botón
            sw_ultimo = sw_actual
            ultimo_cambio = ahora
            ultimo_envio = ahora
            
    except Exception as e:
        print(f"[ERROR] Error en el loop principal: {e}")
        # Intentar reconectar
        time.sleep(5)
        try:
            client = subscribir()
        except:
            pass
            
    time.sleep(0.001)  # Pequeña pausa para no saturar CPU