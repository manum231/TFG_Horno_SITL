# TFG Horno SITL — Sistema de Automatización IIoT para Horno de Retractilado

Trabajo Fin de Grado — Grado en Ingeniería en Sistemas Inteligentes  
Universidad Intercontinental de la Empresa · 2026  
Autor: Manuel Mora Rivas

---

## Descripción

Sistema de automatización e IIoT diseñado y validado en entorno Software-in-the-Loop (SITL) para un horno de retractilado industrial. El proyecto integra cuatro tecnologías en una arquitectura distribuida:

- Control PID discreto con anti-windup para mantenimiento de temperatura a 180 ºC
- Gemelo digital del horno (modelo FOPDT) y la cinta transportadora (variador de frecuencia)
- Visión artificial YOLOv8n para identificación automática de producto y gestión de recetas
- SCADA en tiempo real con InfluxDB y Grafana
- Módulo de inyección de fallos para validación de robustez (5 modos de avería)

Toda la comunicación entre módulos se realiza mediante Modbus TCP/IP.

---

## Estructura del proyecto

```
TFG_Horno_SITL/
├── controlador_pi/
│   ├── controlador_pid.py       # Clase ReguladorPID discreto con anti-windup
│   └── main_plc_automatico.py   # Controlador PID + enclavamiento + alarmas
├── simulador_planta/
│   ├── modelo_horno.py          # Modelos HornoFOPDT y MotorCinta
│   └── servidor_modbus.py       # Gemelo digital + servidor Modbus TCP/IP
├── vision_artificial/
│   ├── inferencia_plc.py        # YOLOv8n en tiempo real + escritura Modbus
│   ├── capturar_dataset.py      # Herramienta de captura de dataset
│   ├── preparar_dataset.py      # Organización train/val + data.yaml
│   └── entrenar_yolo.py         # Entrenamiento YOLOv8n (50 épocas)
├── grafana/
│   └── telemetria_scada.py      # Agente SCADA → InfluxDB a 1 Hz
├── maquetas/                    # Diseños draw.io de los 5 productos Fandicosta
├── lanzador_tfg.py              # Orquestador del sistema completo
├── simulador_fallos.py          # Inyección de fallos controlada (Registro 5)
├── requirements.txt
└── yolov8n.pt                   # Pesos base YOLOv8 Nano
```

---

## Mapa de registros Modbus

| Registro | Descripción | Productor | Consumidor |
|---|---|---|---|
| 0 | Potencia PID (×10) | PID | Gemelo digital |
| 1 | Temperatura real (×10) | Gemelo digital | PID / SCADA |
| 2 | Consigna cinta (×10) | PID | Gemelo digital |
| 3 | Velocidad real (×10) | Gemelo digital | PID / SCADA |
| 4 | Buzón YOLO (×10) | YOLOv8 | PID |
| 5 | Código de fallo (0-5) | Simulador fallos | Gemelo / PID |

---

## Instalación

### Requisitos previos

- Python 3.10 o superior
- InfluxDB v2 instalado en local ([docs.influxdata.com](https://docs.influxdata.com/influxdb/v2/))
- Grafana instalado en local ([grafana.com](https://grafana.com/docs/grafana/latest/))

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/manum231/TFG_Horno_SITL.git
cd TFG_Horno_SITL

# 2. Crear y activar el entorno virtual
python -m venv entorno_tfg
entorno_tfg\Scripts\activate       # Windows
source entorno_tfg/bin/activate    # Linux / macOS

# 3. Instalar dependencias
pip install -r requirements.txt
```

---

## Uso

### Arranque completo del sistema

```bash
python lanzador_tfg.py
```

Arranca en secuencia: gemelo digital → PID → telemetría SCADA → visión artificial.

### Inyección de fallos (terminal separada)

```bash
python simulador_fallos.py
```

| Código | Fallo |
|---|---|
| 0 | Operación normal |
| 1 | Fallo sensor PT100 |
| 2 | Fallo resistencia calefactora |
| 3 | Fallo variador de frecuencia |
| 4 | Sobretemperatura (fuga térmica) |
| 5 | Parada de emergencia (E-Stop) |

### Entrenamiento del modelo de visión (opcional)

```bash
# 1. Capturar imágenes de las maquetas
python vision_artificial/capturar_dataset.py

# 2. Preparar el dataset (80/20 train/val)
python vision_artificial/preparar_dataset.py

# 3. Entrenar YOLOv8n
python vision_artificial/entrenar_yolo.py
```

---

## Recetas de producción

| Producto | Clase YOLO | Velocidad cinta |
|---|---|---|
| Langostino Austral | 0 | 45 Hz |
| Calamar Patagónico | 1 | 35 Hz |
| Merluza del Cabo | 2 | 30 Hz |
| Atún Aleta Amarilla | 3 | 20 Hz |
| Filete de Emperador | 4 | 15 Hz |

---

## Tecnologías

- [pymodbus](https://github.com/pymodbus-dev/pymodbus) — Comunicaciones Modbus TCP/IP
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) — Detección de objetos en tiempo real
- [OpenCV](https://opencv.org/) — Captura de cámara y visualización
- [InfluxDB](https://www.influxdata.com/) — Base de datos de series temporales
- [Grafana](https://grafana.com/) — Dashboard de monitorización

---

## Licencia

Proyecto académico — Universidad Intercontinental de la Empresa · 2026
