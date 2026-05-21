import cv2
import os
import time

def inicializar_carpetas():
    """Crea la estructura de carpetas necesaria para el dataset de YOLO."""
    ruta_base = os.path.join(os.path.dirname(__file__), "dataset")
    os.makedirs(os.path.join(ruta_base, "images"), exist_ok=True)
    return os.path.join(ruta_base, "images")

def capturar_rafaga(captura, ruta_imagenes, id_producto, nombre_producto, num_fotos=30):
    """Toma una ráfaga de fotos de un producto específico."""
    print(f"\nINICIANDO CAPTURA: {nombre_producto}")
    print(f"Mueve lentamente la caja mientras se toman las {num_fotos} fotos...")
    
    # Pausa de 2 segundos para colocar la caja antes de empezar
    time.sleep(2) 
    
    fotos_tomadas = 0
    while fotos_tomadas < num_fotos:
        exito, fotograma = captura.read()
        if not exito:
            print("Error al leer la cámara.")
            break

        # Guardar la imagen con el formato: producto_ID_timestamp.jpg
        nombre_archivo = f"producto_{id_producto}_{int(time.time()*1000)}.jpg"
        ruta_archivo = os.path.join(ruta_imagenes, nombre_archivo)
        cv2.imwrite(ruta_archivo, fotograma)
        
        fotos_tomadas += 1
        print(f"Captura {fotos_tomadas}/{num_fotos} guardada: {nombre_archivo}")
        
        # Mostrar el fotograma en la ventana con un texto superpuesto
        cv2.putText(fotograma, f"GRABANDO {nombre_producto}: {fotos_tomadas}/{num_fotos}", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("Captura de Dataset (YOLOv8)", fotograma)
        
        # Pequeña pausa entre fotos para que te dé tiempo a mover la caja
        cv2.waitKey(150)

    print(f"RÁFAGA COMPLETADA PARA {nombre_producto}")

def iniciar_recoleccion():
    ruta_imagenes = inicializar_carpetas()
    print("Iniciando cámara")
    captura = cv2.VideoCapture(0)

    if not captura.isOpened():
        print("Error: No se pudo acceder a la webcam.")
        return

    nombres_productos = {
        '1': "Langostino (Sostenible)",
        '2': "Calamar (Esencial)",
        '3': "Merluza (Esencial)",
        '4': "Atun (Skinpack)",
        '5': "Emperador (Embolsado)"
    }

    print("\n" + "="*50)
    print(" PANEL DE CONTROL DE CAPTURA - CREACIÓN DE DATASET")
    print("="*50)
    print("Coloca un producto frente a la cámara y pulsa su número (1-5)")
    print("Pulsa 'q' para salir del programa.")
    print("="*50)

    while True:
        exito, fotograma = captura.read()
        if not exito: break

        cv2.putText(fotograma, "ESPERANDO ORDEN (1-5) | 'q' para salir", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Captura de Dataset (YOLOv8)", fotograma)

        tecla = cv2.waitKey(1) & 0xFF
        
        if tecla == ord('q'):
            print("Cerrando programa de captura.")
            break
        elif chr(tecla) in nombres_productos:
            id_prod = chr(tecla)
            capturar_rafaga(captura, ruta_imagenes, id_prod, nombres_productos[id_prod])

    captura.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    iniciar_recoleccion()