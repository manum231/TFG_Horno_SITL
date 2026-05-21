import time
from pymodbus.client import ModbusTcpClient
from controlador_pid import ReguladorPID
#import matplotlib.pyplot as plt

IP_PLANTA = '127.0.0.1'
PUERTO_MODBUS = 5020
CONSIGNA_HORNO_FIJA = 180.0  # El horno siempre a 180ºC 

# Umbrales de alarma 
UMBRAL_TEMP_ALTA    = 230.0   # °C — sobretemperatura
UMBRAL_TEMP_BAJA    = 20.5    # °C — sensor probablemente roto (valor ambiente)
UMBRAL_PID_SATURADO = 95.0    # %  — PID al límite sin efecto → posible fallo de resistencia
CICLOS_SIN_RESPUESTA = 30     # s  — tiempo para declarar fallo de resistencia
 
def detectar_alarmas(temp, potencia, vel_consigna, vel_real, codigo_fallo, historial_temp, ciclos_pid_sat):
    """
    Analiza el estado del proceso y devuelve una lista de alarmas activas.
    Distingue entre alarmas de proceso (detectadas por el PLC) y fallos
    declarados explícitamente desde el simulador.
    """
    alarmas = []
 
    # Alarmas detectadas por lógica del proceso 
 
    # A1: Sobretemperatura, riesgo de quemar el producto
    if temp > UMBRAL_TEMP_ALTA:
        alarmas.append("AL-01 SOBRETEMPERATURA: T > {:.0f}°C".format(UMBRAL_TEMP_ALTA))
 
    # A2: Temperatura sospechosamente baja mientras el PID empuja al máximo (indica sensor roto o resistencia fundida)
    if temp <= UMBRAL_TEMP_BAJA and potencia > 50.0:
        alarmas.append("AL-02 SENSOR PT100 SOSPECHOSO: lectura anómalamente baja")
 
    # A3: PID saturado sin respuesta térmica (resistencia averiada)
    if ciclos_pid_sat >= CICLOS_SIN_RESPUESTA:
        alarmas.append("AL-03 RESISTENCIA SIN RESPUESTA: PID saturado {}s sin efecto".format(
            CICLOS_SIN_RESPUESTA))
 
    # A4: Motor no responde a la consigna
    if vel_consigna > 10 and vel_real < 1.0:
        alarmas.append("AL-04 VARIADOR SIN RESPUESTA: consigna activa pero cinta parada")
 
    # Alarmas declaradas por el simulador de fallos
    if codigo_fallo == 5:
        alarmas.append("AL-05 E-STOP ACTIVO: Parada de emergencia — rearme manual requerido")
 
    return alarmas

def ejecutar_pid_automatico():
    print("\n" + "="*60)
    print(" CEREBRO PID - MANTENIMIENTO TÉRMICO (180ºC)")
    print("="*60)
    
    # Inicializar control y comunicaciones
    pid_horno = ReguladorPID(Kp=1.2, Ki=0.02, Kd=0.5, dt=1.0)
    cliente = ModbusTcpClient(IP_PLANTA, port=PUERTO_MODBUS)
    
    if not cliente.connect():
        print("Error: Planta virtual no detectada. Arranca servidor_modbus.py")
        return

    # Preparar Gráfica en tiempo real
    #plt.ion()
    #fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    #fig.suptitle('Supervisión del Horno Fandicosta (PID + Variador)')
    #tiempos, temps, vels = [], [], []

    print("\nEncendiendo quemadores. Horno en ciclo autónomo.")
    print("Esperando órdenes de velocidad desde la cámara (YOLOv8).")
    print("-" * 60)

    tiempo_actual = 0
    ciclos_pid_sat   = 0  # Contador para detectar resistencia sin respuesta
    alarmas_previas  = set() # Para notificar solo cuando cambia el estado

    try:
        while True:
            # LECTURA DE SENSORES Y BUZONES
            # Leemos 6 registros de golpe (del 0 al 5)
            lectura = cliente.read_holding_registers(0, 6)
            if lectura.isError(): continue
                
            temp_real      = lectura.registers[1] / 10.0
            vel_real       = lectura.registers[3] / 10.0
            buzon_yolo     = lectura.registers[4] # Lo que pide la cámara
            codigo_fallo   = lectura.registers[5] 
            
            # EJECUCIÓN DEL PID TÉRMICO
            # En E-Stop o fallo de sensor, no ejecutamos el PID normalmente
            if codigo_fallo == 5:
                potencia = 0.0  # Corte total
            else:
                potencia = pid_horno.calcular_potencia(CONSIGNA_HORNO_FIJA, temp_real)
 
            # Contador de saturación (para detectar resistencia rota)
            if potencia >= UMBRAL_PID_SATURADO and temp_real < CONSIGNA_HORNO_FIJA - 20:
                ciclos_pid_sat += 1
            else:
                ciclos_pid_sat = 0
            
            # LÓGICA DE ENCLAVAMIENTO (INTERLOCK)
            # Permitimos un margen de error térmico de 2 grados (178.0 ºC)
            # En E-Stop, bloqueamos siempre la cinta
            if codigo_fallo == 5:
                consigna_cinta = 0
                estado = "E-STOP: TODO PARADO"
            elif temp_real >= 178.0:
                consigna_cinta = buzon_yolo
                estado = "TEMPERATURA ÓPTIMA: Cinta Habilitada"
            else:
                consigna_cinta = 0
                estado = "CALENTANDO: Cinta Bloqueada por Seguridad"
            
            # ESCRITURA EN LOS ACTUADORES
            cliente.write_register(0, int(potencia * 10))
            cliente.write_register(2, consigna_cinta) # Mandamos la orden final al variador

            # Sistema de alarmas 
            alarmas_activas = detectar_alarmas(
                temp=temp_real,
                potencia=potencia,
                vel_consigna=consigna_cinta / 10.0,
                vel_real=vel_real,
                codigo_fallo=codigo_fallo,
                historial_temp=None, # Extensible
                ciclos_pid_sat=ciclos_pid_sat
            )
 
            set_alarmas = set(alarmas_activas)
            alarmas_nuevas = set_alarmas - alarmas_previas
            alarmas_resueltas = alarmas_previas - set_alarmas
 
            for al in alarmas_nuevas:
                print(f"\n ALARMA ACTIVA [{tiempo_actual}s]")
                print(f" {al}")
                print(f" {'═'*40}")
 
            for al in alarmas_resueltas:
                etiqueta = al.split(":")[0].strip()
                print(f"\n ALARMA RESUELTA [{tiempo_actual}s]: {etiqueta} Volviendo a normal")
 
            alarmas_previas = set_alarmas
            
            # GRÁFICAS 
            #tiempos.append(tiempo_actual)
            #temps.append(temp_real)
            #vels.append(vel_real)
            
            #if len(tiempos) > 60: 
                #tiempos.pop(0)
                #temps.pop(0)
                #vels.pop(0)

            #ax1.clear()
            #ax1.plot(tiempos, temps, 'r-', label='Temperatura (ºC)')
            #ax1.axhline(y=180, color='k', linestyle='--', label='Consigna (180ºC)')
            #ax1.legend()
            #ax1.set_ylabel('ºC')
            #ax1.grid(True)

            #ax2.clear()
            #ax2.plot(tiempos, vels, 'b-', label='Velocidad Cinta (Hz)')
            #ax2.legend()
            #ax2.set_ylabel('Hz')
            #ax2.set_xlabel('Tiempo (s)')
            #ax2.grid(True)

            #plt.pause(0.01)
            
            # Telemetría en consola 
            indicador_fallo = f" [FALLO:{codigo_fallo}]" if codigo_fallo > 0 else ""
            print(
                f"\r[{tiempo_actual:03d}s] {estado:<42} | "
                f"T:{temp_real:5.1f}°C | PID:{potencia:5.1f}% | "
                f"Cinta:{vel_real:4.1f}Hz{indicador_fallo}",
                end=""
            )
 
            tiempo_actual += 1
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print("\nDeteniendo línea de producción.")
    finally:
        cliente.write_register(0, 0)
        cliente.write_register(2, 0) # Apagar todo al salir
        cliente.close()

if __name__ == '__main__':
    ejecutar_pid_automatico()