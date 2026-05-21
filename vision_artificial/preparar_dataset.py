import os
import shutil
import random

def preparar_dataset():
    # detectamos la ruta base del proyecto (donde está este script)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construimos las rutas origen dinámicamente
    ruta_imagenes = os.path.join(base_dir, "dataset", "images")
    ruta_etiquetas = os.path.join(base_dir, "etiquetas_descargadas")
    
    # Rutas destino
    ruta_base_yolo = os.path.join(base_dir, "yolo_dataset")
    carpetas = [
        os.path.join(ruta_base_yolo, "images", "train"),
        os.path.join(ruta_base_yolo, "images", "val"),
        os.path.join(ruta_base_yolo, "labels", "train"),
        os.path.join(ruta_base_yolo, "labels", "val")
    ]
    
    for carpeta in carpetas:
        os.makedirs(carpeta, exist_ok=True)

    # Comprobaciones de seguridad
    if not os.path.exists(ruta_imagenes):
        print(f"Error: No encuentro la carpeta de imágenes en:\n{ruta_imagenes}")
        return
        
    if not os.path.exists(ruta_etiquetas):
        print(f"Error: No encuentro la carpeta de etiquetas en:\n{ruta_etiquetas}")
        print("Asegúrate de 'etiquetas_descargadas' esta dentro de 'vision_artificial'")
        return

    # Cogemos todas las imágenes
    imagenes = [f for f in os.listdir(ruta_imagenes) if f.endswith('.jpg')]
    # Mezclarlas aleatoriamente para que los conjuntos sean heterogéneos
    random.shuffle(imagenes) 

    # Calcular el corte (80% Train / 20% Val)
    corte = int(len(imagenes) * 0.8)
    train_imgs = imagenes[:corte]
    val_imgs = imagenes[corte:]

    def mover_archivos(lista_imgs, subcarpeta):
        contador = 0
        for img in lista_imgs:
            txt = img.replace('.jpg', '.txt')
            
            ruta_img_origen = os.path.join(ruta_imagenes, img)
            ruta_txt_origen = os.path.join(ruta_etiquetas, txt)
            
            # Solo copiamos si la foto tiene su etiqueta correspondiente
            if os.path.exists(ruta_txt_origen):
                ruta_img_destino = os.path.join(ruta_base_yolo, "images", subcarpeta, img)
                ruta_txt_destino = os.path.join(ruta_base_yolo, "labels", subcarpeta, txt)
                
                shutil.copy(ruta_img_origen, ruta_img_destino)
                shutil.copy(ruta_txt_origen, ruta_txt_destino)
                contador += 1
        return contador

    print("Ensamblando conjunto de Entrenamiento (Train)")
    total_train = mover_archivos(train_imgs, "train")
    
    print("Ensamblando conjunto de Validación (Val)")
    total_val = mover_archivos(val_imgs, "val")

    # Generar el archivo de configuración data.yaml
    ruta_absoluta = os.path.abspath(ruta_base_yolo).replace("\\", "/")
    
    yaml_content = f"""path: {ruta_absoluta}
train: images/train
val: images/val

nc: 5
names: ['langostino', 'calamar', 'merluza', 'atun', 'emperador']
"""
    with open(os.path.join(ruta_base_yolo, "data.yaml"), "w") as f:
        f.write(yaml_content)

    print("\n" + "="*50)
    print("DATASET PREPARADO CON ÉXITO")
    print("="*50)
    print(f"Imágenes en Entrenamiento: {total_train}")
    print(f"Imágenes en Validación: {total_val}")
    print("Archivo data.yaml generado correctamente.")

if __name__ == "__main__":
    preparar_dataset()