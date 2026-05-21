import time
from pymodbus.client import ModbusTcpClient
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Configuración del modbus
IP_PLANTA = '127.0.0.1'
PUERTO_MODBUS = 5020

# Configuración de InfluxDB
# Token, organización, bucket
TOKEN_INFLUX = "3tRGyNbsplNPGYGJenV1fCfbAKAztDitOH2Ja67UJT-1N0a6b11Tc_wygp5OrQ9EEv68QmV-vgt_wBOTKzOSOg=="
ORG = "Fandicosta" 
URL = "http://localhost:8086"
BUCKET = "telemetria_fandicosta"

# Nombres de los fallos para que Grafana los muestre legibles
NOMBRES_FALLO = {
    0: "Normal",
    1: "Fallo_Sensor_PT100",
    2: "Fallo_Resistencia",
    3: "Fallo_Variador",
    4: "Sobretemperatura",
    5: "E-Stop",
}

def iniciar_telemetria():
    print("\n" + "="*50)
    print("SISTEMA SCADA INICIADO")
    print("="*50)

    # Conectar al autómata (Modbus)
    cliente_plc = ModbusTcpClient(IP_PLANTA, port=PUERTO_MODBUS)
    if not cliente_plc.connect():
        print("Error: No se puede conectar a la Planta Virtual.")
        return
    print("Conectado a la red Modbus de la planta.")

    # Conectar a InfluxDB
    cliente_db = InfluxDBClient(url=URL, token=TOKEN_INFLUX, org=ORG)
    write_api = cliente_db.write_api(write_options=SYNCHRONOUS)
    print("Conectado a InfluxDB. Inyectando datos...\n")

    try:
        while True:
            # Leemos 6 registros: 0=potencia, 1=temp, 2=consigna_cinta, 3=vel_real, 4=buzon_yolo, 5=codigo_fallo
            lectura = cliente_plc.read_holding_registers(0, 6)
            if not lectura.isError():
                potencia_pid = lectura.registers[0] / 10.0
                temp_real    = lectura.registers[1] / 10.0
                vel_real     = lectura.registers[3] / 10.0
                codigo_fallo = lectura.registers[5]
                nombre_fallo = NOMBRES_FALLO.get(codigo_fallo, f"Fallo_{codigo_fallo}")
 
                punto_datos = (
                    Point("horno_retractilado")
                    .tag("planta", "Fandicosta")
                    .tag("variador", "Siemens_SINAMICS_V20")
                    .tag("fallo_activo", nombre_fallo)      # etiqueta para filtrar en Grafana
                    .field("temperatura_c",  float(temp_real))
                    .field("velocidad_hz",   float(vel_real))
                    .field("potencia_pid",   float(potencia_pid))  # % de potencia del PID
                    .field("codigo_fallo",   int(codigo_fallo))    # código numérico del fallo
                )

                # Escribir en la base de datos
                write_api.write(bucket=BUCKET, org=ORG, record=punto_datos)
                
                indicador = f"FALLO: {nombre_fallo}" if codigo_fallo > 0 else ""
                print(
                    f"\r[BD] Temp:{temp_real:5.1f}°C | "
                    f"PID:{potencia_pid:5.1f}% | "
                    f"Cinta:{vel_real:4.1f}Hz{indicador}",
                    end=""
                )
 
            time.sleep(1.0)
 
    except KeyboardInterrupt:
        print("\nDeteniendo sistema de telemetría.")
    finally:
        cliente_plc.close()
        cliente_db.close()
 
if __name__ == '__main__':
    iniciar_telemetria()