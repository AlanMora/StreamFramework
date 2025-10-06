"""
Ejemplo de procesamiento de logs usando Stream Monad.

Demuestra cómo procesar archivos de log de manera funcional,
filtrando, transformando y agregando datos.
"""

from core.stream import Stream
from core.io_monad import IO, io_read_file, io_write_file
from core.either import Either
from utils.operators import pipe, ffilter, fmap, compose
from typing import NamedTuple
from datetime import datetime
import re


# ==========================================
# MODELOS DE DATOS
# ==========================================

class LogEntry(NamedTuple):
    """Representa una entrada de log."""
    timestamp: datetime
    level: str
    message: str
    source: str = "unknown"

    def is_error(self) -> bool:
        """Verifica si es un log de error."""
        return self.level.upper() in ["ERROR", "FATAL", "CRITICAL"]

    def is_warning(self) -> bool:
        """Verifica si es un log de warning."""
        return self.level.upper() == "WARNING"

    def __str__(self) -> str:
        return f"[{self.timestamp}] {self.level}: {self.message}"


# ==========================================
# PARSEADORES
# ==========================================

def parse_log_line(line: str) -> Either[str, LogEntry]:
    """
    Parsea una línea de log.

    Formato esperado:
    2024-01-15 10:30:45 ERROR Database connection failed

    Returns:
        Either[str, LogEntry]
    """
    # Pattern: YYYY-MM-DD HH:MM:SS LEVEL Message
    pattern = r'(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\s+(\w+)\s+(.+)'
    match = re.match(pattern, line.strip())

    if not match:
        return Either.left(f"Invalid log format: {line}")

    try:
        timestamp_str, level, message = match.groups()
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

        return Either.right(LogEntry(
            timestamp=timestamp,
            level=level,
            message=message
        ))
    except Exception as e:
        return Either.left(f"Parse error: {str(e)}")


# ==========================================
# PROCESADORES DE STREAMS
# ==========================================

def read_log_file(filepath: str) -> IO[Stream[str]]:
    """
    Lee un archivo de log y retorna un Stream de líneas.

    Args:
        filepath: Ruta al archivo de log

    Returns:
        IO[Stream[str]]
    """
    def effect():
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return Stream.from_iterable(lines)

    return IO(effect)


def filter_errors(logs: Stream[LogEntry]) -> Stream[LogEntry]:
    """Filtra solo logs de error."""
    return logs.filter(lambda log: log.is_error())


def filter_by_keyword(keyword: str):
    """Retorna una función que filtra logs por keyword."""
    def filter_fn(logs: Stream[LogEntry]) -> Stream[LogEntry]:
        return logs.filter(lambda log: keyword.lower() in log.message.lower())
    return filter_fn


def group_by_level(logs: Stream[LogEntry]) -> dict[str, list[LogEntry]]:
    """
    Agrupa logs por nivel.

    Returns:
        Diccionario con nivel como key y lista de logs como value
    """
    result = {}
    for log in logs:
        level = log.level.upper()
        if level not in result:
            result[level] = []
        result[level].append(log)
    return result


def count_by_level(logs: Stream[LogEntry]) -> dict[str, int]:
    """
    Cuenta logs por nivel.

    Returns:
        Diccionario con nivel como key y conteo como value
    """
    return {
        level: len(entries)
        for level, entries in group_by_level(logs).items()
    }


# ==========================================
# PIPELINE DE ANÁLISIS
# ==========================================

def analyze_log_file(filepath: str) -> IO[dict]:
    """
    Analiza un archivo de log y retorna estadísticas.

    Pipeline:
    1. Leer archivo
    2. Parsear líneas
    3. Filtrar líneas inválidas
    4. Generar estadísticas

    Returns:
        IO[dict] con estadísticas del log
    """
    def effect():
        # Leer archivo
        lines = read_log_file(filepath).run()

        # Parsear líneas
        parsed = lines.map(parse_log_line)

        # Filtrar solo los que parsearon correctamente (Right)
        valid_logs = Stream.from_iterable([
            result._value
            for result in parsed
            if result.is_right
        ])

        # Calcular estadísticas
        all_logs = valid_logs.to_list()
        total = len(all_logs)

        # Recrear stream para múltiples operaciones
        log_stream = Stream.from_iterable(all_logs)

        errors = log_stream.filter(lambda log: log.is_error()).count()
        warnings = log_stream.filter(lambda log: log.is_warning()).count()

        # Conteo por nivel
        level_counts = count_by_level(Stream.from_iterable(all_logs))

        return {
            'total_entries': total,
            'errors': errors,
            'warnings': warnings,
            'level_counts': level_counts,
            'error_rate': (errors / total * 100) if total > 0 else 0
        }

    return IO(effect)


def extract_errors_to_file(input_file: str, output_file: str) -> IO[int]:
    """
    Extrae solo los errores de un log a un nuevo archivo.

    Returns:
        IO[int] con el número de errores extraídos
    """
    def effect():
        # Leer y parsear
        lines = read_log_file(input_file).run()
        parsed = lines.map(parse_log_line)

        # Filtrar solo errores
        errors = Stream.from_iterable([
            result._value
            for result in parsed
            if result.is_right and result._value.is_error()
        ])

        # Convertir a texto
        error_lines = errors.map(str).to_list()

        # Escribir archivo
        content = '\n'.join(error_lines)
        io_write_file(output_file, content).run()

        return len(error_lines)

    return IO(effect)


def find_frequent_errors(filepath: str, top_n: int = 10) -> IO[list[tuple[str, int]]]:
    """
    Encuentra los errores más frecuentes.

    Returns:
        IO[list[tuple[str, int]]] con (mensaje, frecuencia)
    """
    def effect():
        # Leer y parsear
        lines = read_log_file(filepath).run()
        parsed = lines.map(parse_log_line)

        # Filtrar errores
        errors = Stream.from_iterable([
            result._value
            for result in parsed
            if result.is_right and result._value.is_error()
        ])

        # Contar frecuencias
        frequency = {}
        for error in errors:
            msg = error.message
            frequency[msg] = frequency.get(msg, 0) + 1

        # Ordenar por frecuencia
        sorted_errors = sorted(
            frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_errors[:top_n]

    return IO(effect)


# ==========================================
# EJEMPLOS DE USO
# ==========================================

def example_basic_analysis():
    """Ejemplo básico de análisis de logs."""
    print("=== Análisis de Logs ===\n")

    # Crear archivo de ejemplo
    sample_log = """2024-01-15 10:30:45 INFO Application started
2024-01-15 10:30:46 DEBUG Loading configuration
2024-01-15 10:30:47 ERROR Database connection failed
2024-01-15 10:30:48 WARNING Cache miss for key: user_123
2024-01-15 10:30:49 ERROR Failed to authenticate user
2024-01-15 10:30:50 INFO Request processed successfully
2024-01-15 10:30:51 ERROR Database connection failed
2024-01-15 10:30:52 CRITICAL System shutdown initiated"""

    io_write_file('/tmp/sample.log', sample_log).run()

    # Analizar
    stats = analyze_log_file('/tmp/sample.log').run()

    print("Estadísticas:")
    print(f"  Total de entradas: {stats['total_entries']}")
    print(f"  Errores: {stats['errors']}")
    print(f"  Warnings: {stats['warnings']}")
    print(f"  Tasa de error: {stats['error_rate']:.2f}%")
    print("\nConteo por nivel:")
    for level, count in sorted(stats['level_counts'].items()):
        print(f"  {level}: {count}")


def example_extract_errors():
    """Ejemplo de extracción de errores."""
    print("\n=== Extracción de Errores ===\n")

    # Extraer errores
    error_count = extract_errors_to_file(
        '/tmp/sample.log',
        '/tmp/errors.log'
    ).run()

    print(f"Errores extraídos: {error_count}")
    print("\nContenido de errors.log:")

    content = io_read_file('/tmp/errors.log').run()
    print(content)


def example_frequent_errors():
    """Ejemplo de errores más frecuentes."""
    print("\n=== Errores Más Frecuentes ===\n")

    frequent = find_frequent_errors('/tmp/sample.log', top_n=5).run()

    print("Top 5 errores:")
    for i, (msg, count) in enumerate(frequent, 1):
        print(f"{i}. [{count}x] {msg}")


def example_functional_pipeline():
    """Ejemplo usando composición funcional."""
    print("\n=== Pipeline Funcional ===\n")

    # Pipeline funcional
    result = (
        read_log_file('/tmp/sample.log')
        .run()
        .map(parse_log_line)
        .filter(lambda e: e.is_right)
        .map(lambda e: e._value)
        .filter(lambda log: log.is_error())
        .map(lambda log: log.message)
        .distinct()
        .to_list()
    )

    print("Mensajes de error únicos:")
    for msg in result:
        print(f"  - {msg}")


if __name__ == "__main__":
    example_basic_analysis()
    example_extract_errors()
    example_frequent_errors()
    example_functional_pipeline()
