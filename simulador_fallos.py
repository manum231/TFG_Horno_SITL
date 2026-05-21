"""
simulador_fallos.py
====================
Módulo de inyección de fallos para validación del sistema de control.
Permite provocar averías controladas en la planta virtual para comprobar
la robustez del controlador PID y los sistemas de seguridad.
 
ARQUITECTURA:
  Este script escribe un código numérico en el Registro Modbus 5,
  que actúa como "buzón de fallos":
    - servidor_modbus.py lo lee y altera la física de la simulación
    - main_plc_automatico.py lo lee y activa las alarmas correspondientes
 
USO:
  Ejecutar como proceso independiente mientras la planta está en marcha.
  Lanzar DESPUÉS de servidor_modbus.py y main_plc_automatico.py.
"""
 
import time
import threading
from pymodbus.client import ModbusTcpClient
 
# Configuración de Red 
IP_PLANTA    = '127.0.0.1'
PUERTO_MODBUS = 5020
REGISTRO_FALLO = 5  # Registro Modbus reservado para el código de fallo activo
 
# Catálogo de Fallos 
CATALOGO_FALLOS = {
    0: {
        "nombre":     "OPERACIÓN NORMAL",
        "descripcion": "Sin fallos activos. Sistema en modo automático nominal.",
        "efecto":     "La planta funciona según los parámetros de diseño.",
        "correctora": "—"
    },
    1: {
        "nombre":     "FALLO SENSOR TEMPERATURA",
        "descripcion": "El termopar del horno queda congelado en su último valor.",
        "efecto":     "El PID ve 20 °C aunque el horno esté caliente, satura potencia al 100%.",
        "correctora": "Enclavamiento por sobretemperatura. Vigilar alarma TH-HIGH."
    },
    2: {
        "nombre":     "FALLO RESISTENCIA CALEFACTORA",
        "descripcion": "La resistencia eléctrica deja de generar calor (K_efectivo = 0).",
        "efecto":     "El horno pierde temperatura lentamente. El PID detecta que no responde.",
        "correctora": "Alarma HEATER-FAULT. Bloquear la cinta hasta diagnosis."
    },
    3: {
        "nombre":     "FALLO VARIADOR DE FRECUENCIA",
        "descripcion": "El variador ignora la consigna de velocidad.",
        "efecto":     "La cinta permanece parada aunque el PLC ordene movimiento.",
        "correctora": "Alarma DRIVE-FAULT. Detener alimentación de producto."
    },
    4: {
        "nombre":     "SOBRETEMPERATURA (FUGA TÉRMICA)",
        "descripcion": "Un fallo en el regulador de tensión inyecta calor adicional.",
        "efecto":     "La temperatura sube por encima del setpoint (> 230 °C).",
        "correctora": "Alarma TH-HIGH. PID corta potencia. Cinta bloqueada por seguridad."
    },
    5: {
        "nombre":     "PARADA DE EMERGENCIA (E-STOP)",
        "descripcion": "Simulación de pulsación del seta de emergencia físico.",
        "efecto":     "Corte inmediato de potencia y cinta. Sistema congelado.",
        "correctora": "Restablecer manualmente desde el panel (opción 0)."
    },
}
 
# Monitor de estado en segundo plano
stop_monitor = threading.Event()
 
def hilo_monitor(cliente):
    """Muestra en tiempo real la temperatura y velocidad de la planta."""
    while not stop_monitor.is_set():
        try:
            lectura = cliente.read_holding_registers(0, 6)
            if not lectura.isError():
                temp  = lectura.registers[1] / 10.0
                vel   = lectura.registers[3] / 10.0
                fallo = lectura.registers[5]
                nombre_fallo = CATALOGO_FALLOS.get(fallo, {}).get("nombre", "DESCONOCIDO")
                barra_temp = "⬆" * int(temp / 10) + "⬇" * (25 - int(temp / 10))
                print(f"\r  Monitor │ Temp: {temp:5.1f}°C [{barra_temp}] │ Cinta: {vel:4.1f}Hz │ FALLO: [{fallo}] {nombre_fallo[:30]:<30}", end="")
        except Exception:
            pass
        time.sleep(1.0)
 
# Interfaz de usuario 
def mostrar_menu():
    print("\n" + "═"*65)
    print("   PANEL DE INYECCIÓN DE FALLOS, VALIDACIÓN DEL SISTEMA")
    print("═"*65)
    for codigo, datos in CATALOGO_FALLOS.items():
        prefijo = "✓" if codigo == 0 else "⚠"
        print(f"\n  [{codigo}] {prefijo}  {datos['nombre']}")
        print(f"       Efecto: {datos['efecto']}")
    print("\n  [i] Información detallada de un fallo")
    print("  [q] Salir y restaurar operación normal")
    print("═"*65)
 
def mostrar_info_fallo(cliente):
    """Muestra la ficha técnica completa de un fallo."""
    codigo_str = input("\n  Introduce el código del fallo (0-5): ").strip()
    try:
        codigo = int(codigo_str)
        if codigo in CATALOGO_FALLOS:
            datos = CATALOGO_FALLOS[codigo]
            print(f"\n FICHA TÉCNICA: {datos['nombre']}")
            print(f" Descripción : {datos['descripcion']}")
            print(f" Efecto      : {datos['efecto']}")
            print(f" Correctora  : {datos['correctora']}")
        else:
            print("  Código fuera de rango.")
    except ValueError:
        print("  Entrada no válida.")
 
def inyectar_fallo():
    print("\n" + "═"*65)
    print("  SIMULADOR DE FALLOS HORNO DE RETRACTILADO FANDICOSTA")
    print("═"*65)
 
    cliente = ModbusTcpClient(IP_PLANTA, port=PUERTO_MODBUS)
    if not cliente.connect():
        print("\n  ERROR: No hay conexión con la planta virtual.")
        print("  Asegúrate de que servidor_modbus.py está en ejecución.\n")
        return
 
    print("  Conexión Modbus establecida.")
    print("  Monitor activo (actualización cada segundo).\n")
 
    # Arrancar el hilo de monitorización
    monitor = threading.Thread(target=hilo_monitor, args=(cliente,), daemon=True)
    monitor.start()
 
    fallo_activo = 0
 
    try:
        while True:
            mostrar_menu()
            print(f"\n  Fallo actualmente activo: [{fallo_activo}] {CATALOGO_FALLOS[fallo_activo]['nombre']}")
            opcion = input("\n  >> Selecciona opción: ").strip().lower()
 
            if opcion == 'q':
                print("\n  Restaurando operación normal antes de salir.")
                cliente.write_register(REGISTRO_FALLO, 0)
                break
 
            elif opcion == 'i':
                stop_monitor.set()   # Pausar monitor para leer bien
                time.sleep(0.2)
                mostrar_info_fallo(cliente)
                stop_monitor.clear()
                monitor = threading.Thread(target=hilo_monitor, args=(cliente,), daemon=True)
                monitor.start()
 
            elif opcion.isdigit() and int(opcion) in CATALOGO_FALLOS:
                codigo = int(opcion)
                stop_monitor.set()
                time.sleep(0.2)
 
                cliente.write_register(REGISTRO_FALLO, codigo)
                fallo_activo = codigo
                datos = CATALOGO_FALLOS[codigo]
 
                if codigo == 0:
                    print("\n SISTEMA RESTAURADO: Operación normal reanudada.")
                else:
                    print(f"\n  FALLO INYECTADO: {datos['nombre']}")
                    print(f"    Observa el monitor y la consola del PID para ver la respuesta.")
                    print(f"    Acción correctora esperada: {datos['correctora']}")
 
                time.sleep(2)
                stop_monitor.clear()
                monitor = threading.Thread(target=hilo_monitor, args=(cliente,), daemon=True)
                monitor.start()
            else:
                print("  Opción no válida. Introduce un número del 0 al 5.")
 
    except KeyboardInterrupt:
        print("\n\n  Interrupción detectada. Restaurando estado normal.")
        cliente.write_register(REGISTRO_FALLO, 0)
    finally:
        stop_monitor.set()
        cliente.close()
        print("  Simulador de fallos cerrado.\n")
 
if __name__ == '__main__':
    inyectar_fallo()