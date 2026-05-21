import subprocess
import time
import sys
import os

def encontrar_archivo(nombre_archivo, ruta_base="."):
    """Busca un archivo recursivamente en todas las subcarpetas."""
    for raiz, directorios, archivos in os.walk(ruta_base):
        # Ignora carpetas del entorno virtual y caches para ir rápido
        if 'entorno_tfg' in raiz or '__pycache__' in raiz or '.git' in raiz:
            continue
        if nombre_archivo in archivos:
            return os.path.join(raiz, nombre_archivo)
    return None

def iniciar_planta_completa():
    print("\n" + "="*50)
    print(" INICIANDO HORNO RETRACTILADO")
    print("="*50)

    # Búsqueda automática de los módulos instalados
    print("Escaneando directorios en busca de los módulos de control y SCADA.")
    ruta_servidor = encontrar_archivo("servidor_modbus.py")
    ruta_pid = encontrar_archivo("main_plc_automatico.py")
    ruta_camara = encontrar_archivo("inferencia_plc.py")
    ruta_telemetria = encontrar_archivo("telemetria_scada.py")

    faltan_archivos = False
    if not ruta_servidor:
        print("ERROR: No encuentro 'servidor_modbus.py'")
        faltan_archivos = True
    if not ruta_pid:
        print("ERROR: No encuentro 'main_plc_automatico.py'")
        faltan_archivos = True
    if not ruta_camara:
        print("ERROR: No encuentro 'inferencia_plc.py'")
        faltan_archivos = True
    if not ruta_telemetria:
        print("ERROR: No encuentro 'telemetria_scada.py'")
        faltan_archivos = True

    if faltan_archivos:
        print("\nDeteniendo arranque: Comprueba la ubicación y nombre de los archivos.")
        return

    procesos = []

    try:
        # Secuencia de arranque del horno
        print(f"\n[1/4] Levantando el Gemelo Digital -> {ruta_servidor}")
        p_servidor = subprocess.Popen([sys.executable, ruta_servidor])
        procesos.append(p_servidor)
        time.sleep(2) # Esperar para abrir el puerto Modbus

        print(f"[2/4] Iniciando el Controlador PID Térmico -> {ruta_pid}")
        p_pid = subprocess.Popen([sys.executable, ruta_pid])
        procesos.append(p_pid)
        time.sleep(2) # Esperar para cargar la interfaz gráfica

        print(f"[3/4] Activando Sonda de Telemetría SCADA -> {ruta_telemetria}")
        p_telemetria = subprocess.Popen([sys.executable, ruta_telemetria])
        procesos.append(p_telemetria)
        time.sleep(1)

        print(f"[4/4] Activando Visión Artificial (YOLOv8) -> {ruta_camara}")
        p_camara = subprocess.Popen([sys.executable, ruta_camara])
        procesos.append(p_camara)

        print("\nTODA LA LÍNEA DE PRODUCCIÓN ESTÁ OPERATIVA.")
        print(">> Los datos del motor Siemens SINAMICS V20 se están enviando a InfluxDB.")
        print(">> Pulsa 'q' en la ventana de la cámara para salir de YOLO.")
        print(">> O pulsa ENTER en esta consola para apagar el horno.\n")

        input() 

    except KeyboardInterrupt:
        print("\nApagado manual detectado.")
    finally:
        print("\n APAGANDO LOS SISTEMAS Y LIBERANDO PUERTOS DE RED.")
        for p in procesos:
            p.terminate() 
        print("Línea de producción detenida.")

if __name__ == "__main__":
    iniciar_planta_completa()