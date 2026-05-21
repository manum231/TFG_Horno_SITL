import numpy as np
import matplotlib.pyplot as plt

class HornoFOPDT:
    """
    Simulador termodinámico de un horno de retractilado.
    Utiliza un modelo de Primer Orden con Tiempo Muerto (FOPDT).
    """
    def __init__(self, K=2.5, tau=120.0, theta=30.0, dt=1.0, T_amb=20.0):
        # Parámetros característicos de la planta
        self.K = K # Ganancia estática (ºC / % potencia)
        self.tau = tau # Constante de tiempo (inercia térmica en segundos)
        self.theta = theta # Tiempo muerto (retardo de las resistencias en segundos)
        self.dt = dt # Paso de simulación (segundos)
        self.T_amb = T_amb # Temperatura ambiente (ºC)
        
        # Estado inicial
        self.T_actual = self.T_amb
        
        # Buffer circular para simular el retardo físico (tiempo muerto)
        pasos_retardo = int(max(1, self.theta / self.dt))
        self.historial_potencia = [0.0] * pasos_retardo

    def actualizar_temperatura(self, potencia_aplicada):
        """
        Calcula la nueva temperatura tras 1 paso de tiempo (dt).
        Utiliza integración numérica por el método de Euler.
        """
        # Obtener la potencia que se aplicó hace 'theta' segundos
        potencia_efectiva = self.historial_potencia.pop(0)
        
        # Guardar la potencia actual para el futuro
        self.historial_potencia.append(potencia_aplicada)
        
        # Ecuación diferencial discretizada (Euler)
        derivada = (self.K * potencia_efectiva - (self.T_actual - self.T_amb)) / self.tau
        self.T_actual = self.T_actual + (derivada * self.dt)
        
        return self.T_actual
    
class MotorCinta:
    """
    Simulador cinemático de una cinta transportadora accionada por un 
    motor asíncrono y gobernada por un variador de frecuencia (ej. ATV320).
    Modela las rampas de aceleración y deceleración.
    """
    def __init__(self, rampa_acc=5.0, rampa_dec=5.0, dt=1.0):
        # Parámetros del variador
        self.rampa_acc = rampa_acc # Aceleración en Hz por segundo
        self.rampa_dec = rampa_dec # Deceleración en Hz por segundo
        self.dt = dt # Paso de simulación (segundos)
        
        # Estado inicial
        self.velocidad_actual = 0.0 # Velocidad en Hz (0 a 50 Hz)

    def actualizar_velocidad(self, consigna_hz):
        """
        Calcula la velocidad real del motor en el instante actual, 
        limitada por las rampas del variador de frecuencia.
        """
        # Si la velocidad actual es menor que la deseada, aceleramos
        if self.velocidad_actual < consigna_hz:
            self.velocidad_actual += self.rampa_acc * self.dt
            # Evitamos pasarnos de la consigna
            if self.velocidad_actual > consigna_hz:
                self.velocidad_actual = consigna_hz
                
        # Si la velocidad actual es mayor que la deseada, frenamos
        elif self.velocidad_actual > consigna_hz:
            self.velocidad_actual -= self.rampa_dec * self.dt
            # Evitamos frenar de más
            if self.velocidad_actual < consigna_hz:
                self.velocidad_actual = consigna_hz
                
        return self.velocidad_actual

# probar el modelo con una simulación simple
if __name__ == '__main__':
    # Instanciamos el horno y el motor de la cinta
    horno = HornoFOPDT()
    motor = MotorCinta(rampa_acc=10.0, rampa_dec=10.0) # El variador acelerará a 10 Hz por segundo
    
    tiempo_total = 600 # 10 minutos de simulación
    tiempos = np.arange(0, tiempo_total, horno.dt)
    temperaturas = []
    velocidades = []
    
    for t in tiempos:
        # Lógica del Horno: Se enciende al 80% de potencia en el segundo 50
        potencia = 80.0 if t >= 50 else 0.0
        temp = horno.actualizar_temperatura(potencia)
        temperaturas.append(temp)
        
        # Lógica del Motor: Le pedimos ir a 50Hz (velocidad máxima) en el segundo 150
        consigna_vel = 50.0 if t >= 150 else 0.0
        vel = motor.actualizar_velocidad(consigna_vel)
        velocidades.append(vel)
        
    # Visualización Doble (Temperatura y Velocidad)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # Gráfica Superior: Temperatura del Horno
    ax1.plot(tiempos, temperaturas, 'r-', linewidth=2, label='Temperatura (ºC)')
    ax1.axhline(y=20, color='gray', linestyle='--', label='Temp. Ambiente')
    ax1.set_title('Respuesta Térmica - Horno de Retractilado Virtual')
    ax1.set_ylabel('Temperatura (ºC)')
    ax1.grid(True)
    ax1.legend()
    
    # Gráfica Inferior: Velocidad de la Cinta (Variador)
    ax2.plot(tiempos, velocidades, 'b-', linewidth=2, label='Velocidad del Motor (Hz)')
    ax2.set_title('Respuesta Cinemática - Variador de Frecuencia de la Cinta')
    ax2.set_xlabel('Tiempo (s)')
    ax2.set_ylabel('Frecuencia (Hz)')
    ax2.grid(True)
    ax2.legend()
    
    plt.tight_layout()
    plt.show()