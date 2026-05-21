import time
import threading
import logging
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

# Importamos la física de nuestra planta desde el otro archivo
from modelo_horno import HornoFOPDT, MotorCinta 

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# Variable global para acceder a la memoria Modbus desde cualquier hilo
contexto_servidor = None

def ciclo_de_scan(horno, motor, dt):
    """
    Rutina de ejecución en segundo plano (Hilo secundario).
    Emula el ciclo de scan de la planta física resolviendo las ecuaciones 
    de estado en tiempo discreto y actualizando el mapa de registros.
    """
    global contexto_servidor
    
    # Temperatura congelada para el fallo de sensor (último valor válido conocido)
    temp_sensor_congelada = horno.T_amb

    while True:
        if contexto_servidor is not None:
            # Acceder al bloque de Holding Registers (Función Modbus 3)
            # En configuraciones single=True, el ID del esclavo por defecto es 0
            contexto = contexto_servidor[0]
            
            # fase de lectura: Leer las órdenes de la Raspberry Pi (Registros 0 a 5)
            # getValues(function_code, address, count)
            valores_memoria = contexto.getValues(3, 0, 6) 
            
            # El Registro 0 contiene la potencia solicitada por el PID (escalada x10)
            orden_potencia = valores_memoria[0] / 10.0
            
            # El Registro 2 contiene la velocidad solicitada al variador (escalada x10)
            orden_velocidad = valores_memoria[2] / 10.0

            # El Registro 5 contiene el código de fallo activo
            codigo_fallo    = valores_memoria[5]
            
            if codigo_fallo == 1:
                # FALLO SENSOR: el horno sigue calentándose físicamente,
                # pero publicamos la temperatura ambiente como si el sensor leyera mal.
                horno.actualizar_temperatura(orden_potencia) # física real (oculta)
                temp_publicar = horno.T_amb # dato falso al PLC
                vel_real = motor.actualizar_velocidad(orden_velocidad)
                log_fallo = "SENSOR-FAULT"
 
            elif codigo_fallo == 2:
                # FALLO RESISTENCIA: la resistencia no transfiere calor (K=0 transitorio).
                # Simulamos pasando potencia 0 al modelo térmico.
                temp_publicar = horno.actualizar_temperatura(0.0)
                vel_real      = motor.actualizar_velocidad(orden_velocidad)
                log_fallo = "HEATER-FAULT"
 
            elif codigo_fallo == 3:
                # FALLO VARIADOR: ignoramos la consigna de velocidad → cinta a 0.
                temp_publicar = horno.actualizar_temperatura(orden_potencia)
                vel_real      = motor.actualizar_velocidad(0.0)   # ignorar orden
                log_fallo = "DRIVE-FAULT"
 
            elif codigo_fallo == 4:
                # SOBRETEMPERATURA: fuga térmica, añadimos potencia extra al modelo.
                temp_publicar = horno.actualizar_temperatura(orden_potencia + 60.0)
                vel_real      = motor.actualizar_velocidad(orden_velocidad)
                log_fallo = "OVERHEAT-FAULT"
 
            elif codigo_fallo == 5:
                # E-STOP: corte total (ni calor ni movimiento).
                temp_publicar = horno.actualizar_temperatura(0.0)
                vel_real      = motor.actualizar_velocidad(0.0)
                log_fallo = "E-STOP"
 
            else:
                # OPERACIÓN NORMAL
                temp_publicar = horno.actualizar_temperatura(orden_potencia)
                vel_real      = motor.actualizar_velocidad(orden_velocidad)
                log_fallo = None
 
            if log_fallo:
                print(f"\r  [PLANTA] {log_fallo} activo │ T_pub={temp_publicar:.1f}°C │ V={vel_real:.1f}Hz    ", end="")
 
            # Fase de escritura: Publicar la temperatura actual y la velocidad real en los registros 1 y 3 respectivamente
            contexto.setValues(3, 1, [int(temp_publicar * 10)])
            contexto.setValues(3, 3, [int(vel_real * 10)])
 
        time.sleep(dt)

def iniciar_servidor_planta():
    """
    Inicializa la arquitectura de red y lanza la simulación física concurrente.
    """
    global contexto_servidor
    
    print("Iniciando Gemelo Digital de la Planta (Horno + Cinta)")
    
    # Instanciar los modelos físicos (Δt = 1.0 segundos)
    paso_tiempo = 1.0
    horno = HornoFOPDT(dt=paso_tiempo)
    motor = MotorCinta(rampa_acc=5.0, rampa_dec=5.0, dt=paso_tiempo)
    
    # Configurar la memoria del Servidor Modbus (10 registros inicializados a 0)
    bloque_registros = ModbusSequentialDataBlock(0, [0] * 10)
    contexto_esclavo = ModbusSlaveContext(di=None, co=None, hr=bloque_registros, ir=None)
    contexto_servidor = ModbusServerContext(slaves=contexto_esclavo, single=True)
    
    # Lanzar el ciclo de scan en un hilo paralelo
    hilo_fisica = threading.Thread(target=ciclo_de_scan, args=(horno, motor, paso_tiempo))
    hilo_fisica.daemon = True # Permite que el hilo se destruya al cerrar el programa
    hilo_fisica.start()
    
    # Arrancar el servicio de red bloqueante
    puerto_red = 5020
    print(f"Servidor Modbus a la escucha en localhost, Puerto: {puerto_red}")
    print("Planta en ejecución. Esperando comandos de la Raspberry Pi")
    
    StartTcpServer(
        context=contexto_servidor,
        address=("0.0.0.0", puerto_red)
    )

if __name__ == "__main__":
    iniciar_servidor_planta()