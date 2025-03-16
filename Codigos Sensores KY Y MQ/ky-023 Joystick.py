import time
import network
import json
from machine import Pin, ADC
from umqtt.simple import MQTTClient

# 📡 Configuración WiFi
WIFI_SSID = "Red-Peter"
WIFI_PASSWORD = "12345678"

# 🌐 Configuración MQTT
MQTT_CLIENT_ID = "esp32_ky023"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC_SENSOR = "gds0653/ky-023"

# 🕹️ Configuración del sensor KY-023 (Joystick)
# Pines analógicos para los ejes X e Y
JOYSTICK_X_PIN = 32  # Pin ADC para el eje X
JOYSTICK_Y_PIN = 33  # Pin ADC para el eje Y
JOYSTICK_BTN_PIN = 14  # Pin para el botón del joystick

# Configuración ADC para los ejes X e Y
adc_x = ADC(Pin(JOYSTICK_X_PIN))
adc_y = ADC(Pin(JOYSTICK_Y_PIN))
adc_x.atten(ADC.ATTN_11DB)  # Configuración para rango 0-3.3V
adc_y.atten(ADC.ATTN_11DB)  # Configuración para rango 0-3.3V
adc_x.width(ADC.WIDTH_12BIT)  # Resolución de 12 bits (0-4095)
adc_y.width(ADC.WIDTH_12BIT)  # Resolución de 12 bits (0-4095)

# Configuración del botón (generalmente activo en LOW)
btn = Pin(JOYSTICK_BTN_PIN, Pin.IN, Pin.PULL_UP)

# LED para indicación visual
led_onboard = Pin(2, Pin.OUT)

# Variables para control
ultimo_tiempo_publicacion = 0
INTERVALO_PUBLICACION = 200  # Publicar cada 200ms cuando hay cambios
ultimo_estado = "CENTRO"
ultimo_btn = None
UMBRAL_CAMBIO = 100  # Umbral para detectar movimientos

# 🔌 Conectar a WiFi
def conectar_wifi():
    print("[INFO] Conectando a WiFi...")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.5)
    print("\n[INFO] WiFi Conectada!")
    print(f"[INFO] Dirección IP: {sta_if.ifconfig()[0]}")

# 🔄 Conectar a MQTT
def conectar_mqtt():
    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
        client.connect()
        print(f"[INFO] Conectado a MQTT en {MQTT_BROKER}")
        return client
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a MQTT: {e}")
        return None

# Función para obtener tiempo en milisegundos
def millis():
    return time.ticks_ms()

# 🏁 Inicialización
print("[INFO] Iniciando sensor KY-023 (Joystick)")
conectar_wifi()
client = conectar_mqtt()
print("[INFO] Mueva el joystick o presione el botón")

# Valores de calibración - ajustar según tu joystick
X_CENTRO = 2047  # Valor en reposo aproximado
Y_CENTRO = 2047  # Valor en reposo aproximado
ZONA_MUERTA = 400  # Zona muerta alrededor del centro (aumentada para menos sensibilidad)

# 🔄 Bucle principal
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
            time.sleep(2)
            continue
            
        # Leer valores del joystick
        valor_x = adc_x.read()  # Lee eje X (0-4095)
        valor_y = adc_y.read()  # Lee eje Y (0-4095)
        valor_btn = not btn.value()  # Lee botón (normalmente activo en LOW)
        
        # Encender LED cuando se presiona el botón
        led_onboard.value(valor_btn)
        
        # Determinar estado del joystick como texto
        estado_actual = "CENTRO"
        
        # Verificar primero el botón
        if valor_btn:
            estado_actual = "PRESIONADO"
        else:
            # Si no está presionado, revisar posición
            if abs(valor_x - X_CENTRO) > ZONA_MUERTA or abs(valor_y - Y_CENTRO) > ZONA_MUERTA:
                # Priorizar el eje con mayor desviación
                if abs(valor_x - X_CENTRO) > abs(valor_y - Y_CENTRO):
                    # Movimiento horizontal dominante
                    if valor_x > X_CENTRO:
                        estado_actual = "DERECHA"
                    else:
                        estado_actual = "IZQUIERDA"
                else:
                    # Movimiento vertical dominante
                    if valor_y > Y_CENTRO:
                        estado_actual = "ABAJO"
                    else:
                        estado_actual = "ARRIBA"
            else:
                # En centro pero no presionado
                estado_actual = "LIBERADO"
        
        # Obtener tiempo actual
        ahora = millis()
        
        # Publicar si cambia el estado o pasó suficiente tiempo
        cambio_estado = estado_actual != ultimo_estado
        tiempo_publicar = ahora - ultimo_tiempo_publicacion > INTERVALO_PUBLICACION
        
        if cambio_estado and tiempo_publicar:
            # Crear mensaje con el estado como texto
            mensaje = json.dumps({"estado": estado_actual})
            
            # Publicar en MQTT
            if client:
                client.publish(MQTT_TOPIC_SENSOR, mensaje)
                print(f"Joystick: {estado_actual}")
            
            # Actualizar estado anterior
            ultimo_estado = estado_actual
            ultimo_tiempo_publicacion = ahora
            
    except Exception as e:
        print(f"[ERROR] Error en el loop principal: {e}")
        client = None
        time.sleep(2)
        
    time.sleep(0.05)  # Pequeña pausa para estabilidad