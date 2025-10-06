"""
Ejemplo de procesamiento de datos en tiempo real.

 Stream + IO para análisis de datos en vivo
"""

from core.stream import Stream
from core.io_monad import IO, io_print
from core.http_stream import fetch_json
from core.either import Either
from dataclasses import dataclass
from datetime import datetime
from typing import List
import time
import random


@dataclass
class SensorData:
    """Datos de un sensor."""
    timestamp: datetime
    temperature: float
    humidity: float
    sensor_id: str


@dataclass
class Alert:
    """Alerta generada."""
    level: str  # WARNING, CRITICAL
    message: str
    timestamp: datetime


class RealtimeProcessor:
    """
    Procesador de datos en tiempo real usando Stream + IO.

     CASO DE USO: Monitoreo de sensores IoT
    """

    @staticmethod
    def simulate_sensor_stream(duration_seconds: int = 10) -> Stream[SensorData]:
        """
        Simula un stream de datos de sensores.

        Args:
            duration_seconds: Duración de la simulación

        Returns:
            Stream[SensorData]
        """

        def sensor_generator():
            """Generador de datos de sensores."""
            start_time = time.time()
            sensor_ids = ['SENSOR_001', 'SENSOR_002', 'SENSOR_003']

            while time.time() - start_time < duration_seconds:
                # Generar dato aleatorio
                data = SensorData(
                    timestamp=datetime.now(),
                    temperature=random.uniform(15.0, 35.0),
                    humidity=random.uniform(30.0, 80.0),
                    sensor_id=random.choice(sensor_ids)
                )
                yield data
                time.sleep(0.5)  # Frecuencia de lectura

        return Stream(sensor_generator)

    @staticmethod
    def detect_anomalies(data: SensorData) -> Either[str, Alert]:
        """
        Detecta anomalías en los datos (función pura).

        Returns:
            Either[str, Alert] - Left si no hay anomalía, Right si hay
        """
        # Umbrales
        TEMP_CRITICAL = 30.0
        TEMP_WARNING = 25.0
        HUMIDITY_CRITICAL = 70.0

        if data.temperature > TEMP_CRITICAL:
            return Either.right(Alert(
                level='CRITICAL',
                message=f'Temperatura crítica: {data.temperature:.1f}°C en {data.sensor_id}',
                timestamp=data.timestamp
            ))
        elif data.temperature > TEMP_WARNING:
            return Either.right(Alert(
                level='WARNING',
                message=f'Temperatura alta: {data.temperature:.1f}°C en {data.sensor_id}',
                timestamp=data.timestamp
            ))
        elif data.humidity > HUMIDITY_CRITICAL:
            return Either.right(Alert(
                level='CRITICAL',
                message=f'Humedad crítica: {data.humidity:.1f}% en {data.sensor_id}',
                timestamp=data.timestamp
            ))
        else:
            return Either.left('Normal')

    @staticmethod
    def log_alert(alert: Alert) -> IO[None]:
        """
        Registra una alerta (operación IO).

         IO para efectos secundarios (logging)
        """
        symbol = '[!]' if alert.level == 'CRITICAL' else '[!]'
        return io_print(f"{symbol} [{alert.level}] {alert.message}")

    @staticmethod
    def save_to_database(data: SensorData) -> IO[None]:
        """
        Simula guardar datos en base de datos.

         IO para persistencia
        """

        def effect():
            # Simular escritura en DB
            # print(f" Guardando en DB: {data.sensor_id} - {data.temperature:.1f}°C")
            pass  # En producción, aquí iría la escritura real

        return IO(effect)

    @staticmethod
    def send_alert_notification(alert: Alert) -> IO[Either[Exception, None]]:
        """
        Envía notificación de alerta (ej: webhook, email).

         IO para HTTP POST (notificación)
        """

        def effect():
            try:
                # En producción, enviaría a un webhook real
                # response = requests.post('https://alerts.example.com/notify', ...)
                print(f" Notificación enviada: {alert.message}")
                return Either.right(None)
            except Exception as e:
                return Either.left(e)

        return IO(effect)

    @classmethod
    def process_realtime(cls, duration: int = 10) -> IO[None]:
        """
        Pipeline completo de procesamiento en tiempo real.

         COMPOSICIÓN COMPLETA: Stream + IO + Either

        Flujo:
        1. Leer stream de sensores
        2. Guardar cada lectura en DB
        3. Detectar anomalías
        4. Si hay alerta, loggear y notificar
        5. Generar estadísticas
        """

        def effect():
            print(f"\n Iniciando monitoreo por {duration} segundos...\n")

            # Contadores
            total_readings = 0
            total_alerts = 0

            # Obtener stream
            sensor_stream = cls.simulate_sensor_stream(duration)

            # Procesar cada dato
            for data in sensor_stream:
                total_readings += 1

                # Guardar en DB (IO)
                cls.save_to_database(data).run()

                # Detectar anomalías (puro)
                anomaly_result = cls.detect_anomalies(data)

                # Si hay alerta
                if anomaly_result.is_right:
                    alert = anomaly_result.get_or_else(None)
                    if alert:
                        total_alerts += 1

                        # Loggear alerta (IO)
                        cls.log_alert(alert).run()

                        # Enviar notificación crítica (IO)
                        if alert.level == 'CRITICAL':
                            cls.send_alert_notification(alert).run()

                # Mostrar lectura normal
                else:
                    print(f" {data.sensor_id}: {data.temperature:.1f}°C, {data.humidity:.1f}%")

            # Resumen final
            print(f"\n{'=' * 60}")
            print(f" RESUMEN DEL MONITOREO")
            print(f"{'=' * 60}")
            print(f"Total de lecturas: {total_readings}")
            print(f"Total de alertas: {total_alerts}")
            print(f"Tasa de alertas: {(total_alerts / total_readings * 100):.1f}%")
            print(f"{'=' * 60}\n")

        return IO(effect)


# ==========================================
# EJEMPLO DE USO
# ==========================================

def ejemplo_monitoring():
    """Ejecuta el sistema de monitoreo."""
    print("\n" + "=" * 60)
    print("  SISTEMA DE MONITOREO EN TIEMPO REAL")
    print("=" * 60)

    # Crear y ejecutar el pipeline
    monitoring_program = RealtimeProcessor.process_realtime(duration=10)
    monitoring_program.run()


if __name__ == "__main__":
    ejemplo_monitoring()