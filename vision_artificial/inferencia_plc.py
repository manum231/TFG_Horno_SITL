import cv2
from ultralytics import YOLO
from pymodbus.client import ModbusTcpClient
import os

def iniciar_sistema():
    # Conexión al Gemelo Digital (La Planta)
    IP_PLC = '127.0.0.1' 
    PUERTO_PLC = 5020  
    
    print(f"Conectando a la Planta Virtual en {IP_PLC}:{PUERTO_PLC}...")
    cliente_plc = ModbusTcpClient(IP_PLC, port=PUERTO_PLC)
    
    if not cliente_plc.connect():
        print("ERROR: No se pudo conectar a la simulación. Arranca servidor_modbus.py primero.")
        return
    print("Conexión Modbus establecida con éxito.")

    # Cargar la IA
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ruta_pesos = os.path.join(base_dir, "runs", "modelo_fandicosta", "weights", "best.pt")
    modelo = YOLO(ruta_pesos)

    # Diccionario de recetas
    # Los valores se multiplican x10 según tu tabla
    RECETAS = {
        0: {"nombre": "Langostino", "temp": 1800, "vel": 450}, # Clase 0 en YOLO
        1: {"nombre": "Calamar",    "temp": 1800, "vel": 350}, # Clase 1 en YOLO
        2: {"nombre": "Merluza",    "temp": 1800, "vel": 300}, # Clase 2 en YOLO
        3: {"nombre": "Atun",       "temp": 1800, "vel": 200}, # Clase 3 en YOLO
        4: {"nombre": "Emperador",  "temp": 1800, "vel": 150}  # Clase 4 en YOLO
    }

    captura = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    print("\n" + "="*50)
    print("SISTEMA DE VISIÓN Y CONTROL PLC ACTIVO")
    print("="*50)

    ultima_clase_detectada = -1

    while True:
        exito, fotograma = captura.read()
        if not exito: break

        resultados = modelo(fotograma, verbose=False, conf=0.7)
        fotograma_anotado = resultados[0].plot()

        if len(resultados[0].boxes) > 0:
            mejor_deteccion = resultados[0].boxes[0]
            clase_yolo = int(mejor_deteccion.cls.item())
            
            # Solo enviamos comandos Modbus si el producto en cámara cambia
            if clase_yolo != ultima_clase_detectada and clase_yolo in RECETAS:
                receta = RECETAS[clase_yolo]
                
                try:
                    # YOLO deja su sugerencia en el Registro 4 (Buzón)
                    # No ataca directamente al variador por seguridad.
                    cliente_plc.write_register(4, receta["vel"])
                    
                    print(f"Detectado: {receta['nombre'].upper()}")
                    print(f"Sugerencia de Velocidad enviada al buzón: {receta['vel']/10.0} Hz")
                    print("-" * 40)
                    
                    ultima_clase_detectada = clase_yolo
                except Exception as e:
                    print(f"Error Modbus: {e}")

        cv2.imshow("Inspeccion YOLOv8", fotograma_anotado)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    captura.release()
    cv2.destroyAllWindows()
    cliente_plc.close()

if __name__ == "__main__":
    iniciar_sistema()