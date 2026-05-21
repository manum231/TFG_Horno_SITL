from ultralytics import YOLO
import os

def entrenar_modelo():
    # Buscamos la ruta del archivo data.yaml
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ruta_yaml = os.path.join(base_dir, "yolo_dataset", "data.yaml")

    print("\n" + "="*50)
    print("INICIANDO EL ENTRENAMIENTO DE LA RED NEURONAL")
    print("="*50)
    print(f"Archivo de configuración: {ruta_yaml}")

    # Cargamos el modelo base (YOLOv8 Nano)
    model = YOLO('yolov8n.pt') 

    # Lanzamos el entrenamiento
    model.train(
        data=ruta_yaml,
        epochs=50, # Número de veces que la IA verá todo el dataset completo
        imgsz=640, # Resolución estándar a la que redimensionará las fotos
        batch=16, # Paquetes de 16 imágenes simultáneas
        project=os.path.join(base_dir, 'runs'), # Carpeta principal donde se guardará todo
        name='modelo_fandicosta', # Nombre de la subcarpeta de resultados
        plots=True # Genera gráficas de rendimiento
    )

    print("\nENTRENAMIENTO FINALIZADO.")
    print("Los pesos están en la carpeta: vision_artificial/runs/modelo_fandicosta/weights/best.pt")

if __name__ == "__main__":
    entrenar_modelo()