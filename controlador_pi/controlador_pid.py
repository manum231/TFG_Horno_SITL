class ReguladorPID:
    """
    Implementación de un algoritmo de control PID en tiempo discreto.
    Traduce el error de temperatura en un porcentaje de potencia eléctrica.
    """
    def __init__(self, Kp, Ki, Kd, limite_min=0.0, limite_max=100.0, dt=1.0):
        # Ganancias del controlador
        self.Kp = Kp # Proporcional: Reacciona al error actual
        self.Ki = Ki # Integral: Elimina el error acumulado en el tiempo
        self.Kd = Kd # Derivativo: Frena el impulso si nos acercamos rápido a la meta
        
        self.dt = dt # Ciclo de scan
        
        # Limites de la señal de salida (0% a 100% de potencia)
        self.limite_min = limite_min
        self.limite_max = limite_max
        
        # Variables de memoria para los cálculos iterativos
        self.integral_acumulada = 0.0
        self.error_previo = 0.0

    def calcular_potencia(self, setpoint, valor_actual):
        """
        Calcula la potencia de salida (0-100%) necesaria para alcanzar el setpoint.
        """
        # Calcular el error actual (lo que falta para llegar a la meta)
        error = setpoint - valor_actual
        
        # Término PROPORCIONAL
        P = self.Kp * error
        
        # Término INTEGRAL (acumulación del error a lo largo del tiempo)
        self.integral_acumulada += error * self.dt
        
        # ANTI-WINDUP REAL: Limitar la memoria del acumulador directamente para evitar que la integral crezca sin control cuando el sistema está saturado
        if self.Ki > 0:
            limite_integral_max = self.limite_max / self.Ki
            limite_integral_min = self.limite_min / self.Ki
            
            if self.integral_acumulada > limite_integral_max:
                self.integral_acumulada = limite_integral_max
            elif self.integral_acumulada < limite_integral_min:
                self.integral_acumulada = limite_integral_min
                
        I = self.Ki * self.integral_acumulada
        
        # Evitar que la integral crezca hasta el infinito si hay saturación 
        if I > self.limite_max: I = self.limite_max
        if I < self.limite_min: I = self.limite_min
            
        # Término derivativo (velocidad de cambio del error)
        derivada = (error - self.error_previo) / self.dt
        D = self.Kd * derivada
        
        # Suma total de la acción de control
        potencia_salida = P + I + D
        
        # Saturación (asegurarnos de que no pedimos más del 100% ni menos del 0%)
        if potencia_salida > self.limite_max:
            potencia_salida = self.limite_max
        elif potencia_salida < self.limite_min:
            potencia_salida = self.limite_min
            
        # Guardamos el error actual para la derivada del siguiente ciclo
        self.error_previo = error
        
        return potencia_salida