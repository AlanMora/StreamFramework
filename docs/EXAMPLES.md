# 💡 Ejemplos Avanzados

Colección de casos de uso reales y patrones avanzados con el framework.

## Tabla de Contenidos

1. [Data Pipeline ETL](#1-data-pipeline-etl)
2. [Web Scraping Funcional](#2-web-scraping-funcional)
3. [Sistema de Validación](#3-sistema-de-validación)
4. [Event Processing](#4-event-processing)
5. [Caching con Memoización](#5-caching-con-memoización)
6. [Procesamiento de CSV](#6-procesamiento-de-csv)
7. [Rate Limiting](#7-rate-limiting)
8. [Estado Funcional](#8-estado-funcional)

---

## 1. Data Pipeline ETL

Un pipeline completo Extract-Transform-Load usando mónadas.

```python
from core import IO, Stream, Either
from utils import pipe
import json

# ==========================================
# EXTRACT
# ==========================================

def extract_from_api(url):
    """Extrae datos de API"""
    from core import http_get

    return (
        http_get(url)
        .map(lambda either: either.bind(lambda resp: resp.json()))
    )

def extract_from_file(filepath):
    """Extrae datos de archivo JSON"""
    from core import io_read_file

    return (
        io_read_file(filepath)
        .map(lambda content: Either.right(json.loads(content)))
        .attempt()
        .map(lambda either: either.bind(lambda x: x))
    )

# ==========================================
# TRANSFORM
# ==========================================

def clean_record(record):
    """Limpia un registro"""
    return {
        'id': record.get('id'),
        'name': (record.get('name') or '').strip().title(),
        'email': (record.get('email') or '').lower(),
        'age': int(record.get('age', 0))
    }

def validate_record(record):
    """Valida un registro"""
    if not record.get('email') or '@' not in record['email']:
        return Either.left(f"Invalid email: {record}")
    if record.get('age', 0) < 0:
        return Either.left(f"Invalid age: {record}")
    return Either.right(record)

def transform_data(data_either):
    """Transforma el dataset completo"""
    if data_either.is_left:
        return Either.left(data_either._value)

    data = data_either._value

    results = (
        Stream.from_iterable(data)
        .map(clean_record)
        .map(validate_record)
        .filter(lambda e: e.is_right)
        .map(lambda e: e._value)
        .to_list()
    )

    return Either.right(results)

# ==========================================
# LOAD
# ==========================================

def load_to_file(filepath, data_either):
    """Carga datos a archivo"""
    from core import io_write_file

    if data_either.is_left:
        return IO.pure(Either.left(data_either._value))

    data = data_either._value
    content = json.dumps(data, indent=2)

    return (
        io_write_file(filepath, content)
        .map(lambda _: Either.right(f"Loaded {len(data)} records"))
    )

def load_to_database(data_either):
    """Carga datos a base de datos (simulado)"""
    if data_either.is_left:
        return IO.pure(Either.left(data_either._value))

    data = data_either._value

    def insert_records():
        # Simulación de inserción
        print(f"Inserting {len(data)} records to database...")
        return Either.right(f"Inserted {len(data)} records")

    return IO(insert_records)

# ==========================================
# PIPELINE COMPLETO
# ==========================================

def etl_pipeline(source_url, output_file):
    """Pipeline ETL completo"""
    return (
        extract_from_api(source_url)
        .map(transform_data)
        .bind(lambda result: load_to_file(output_file, result))
    )

# Uso
pipeline = etl_pipeline(
    "https://api.example.com/users",
    "/tmp/clean_users.json"
)

result = pipeline.run()
if result.is_right:
    print(result._value)
else:
    print(f"Error: {result._value}")
```

---

## 2. Web Scraping Funcional

Scraping de múltiples páginas con retry y rate limiting.

```python
from core import IO, Stream, Either, http_get
from utils import pipe
import time
from urllib.parse import urljoin

def fetch_page(url, retries=3):
    """Fetch con retry automático"""
    return (
        http_get(url)
        .retry(max_attempts=retries)
    )

def extract_links(html_either):
    """Extrae links de HTML"""
    if html_either.is_left:
        return []

    html = html_either._value.body
    # Simplificado - usar BeautifulSoup en real
    import re
    links = re.findall(r'href="([^"]+)"', html)
    return links

def scrape_site(base_url, max_pages=10):
    """Scrape recursivo de sitio"""
    visited = set()
    to_visit = [base_url]

    def scrape_recursive():
        results = []

        while to_visit and len(visited) < max_pages:
            url = to_visit.pop(0)

            if url in visited:
                continue

            print(f"Scraping: {url}")
            visited.add(url)

            # Fetch página
            page_either = fetch_page(url).run()

            if page_either.is_right:
                # Extraer links
                links = extract_links(page_either)

                # Agregar nuevos links
                for link in links:
                    full_url = urljoin(base_url, link)
                    if full_url.startswith(base_url):
                        to_visit.append(full_url)

                results.append({
                    'url': url,
                    'status': 'success',
                    'links_found': len(links)
                })
            else:
                results.append({
                    'url': url,
                    'status': 'error',
                    'error': str(page_either._value)
                })

            # Rate limiting
            time.sleep(0.5)

        return results

    return IO(scrape_recursive)

# Uso
results = scrape_site("https://example.com", max_pages=5).run()
print(f"Scraped {len(results)} pages")
```

---

## 3. Sistema de Validación

Sistema completo de validación con Either Monad.

```python
from core import Either
from typing import Dict, Any, List
import re

# ==========================================
# VALIDADORES
# ==========================================

def validate_required(field_name, value):
    """Valida campo requerido"""
    if value is None or value == "":
        return Either.left(f"{field_name} es requerido")
    return Either.right(value)

def validate_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return Either.left("Email inválido")
    return Either.right(email)

def validate_min_length(min_len):
    """Retorna validador de longitud mínima"""
    def validator(value):
        if len(str(value)) < min_len:
            return Either.left(f"Debe tener al menos {min_len} caracteres")
        return Either.right(value)
    return validator

def validate_range(min_val, max_val):
    """Retorna validador de rango"""
    def validator(value):
        if not (min_val <= value <= max_val):
            return Either.left(f"Debe estar entre {min_val} y {max_val}")
        return Either.right(value)
    return validator

def validate_pattern(pattern, error_msg):
    """Retorna validador de patrón"""
    def validator(value):
        if not re.match(pattern, str(value)):
            return Either.left(error_msg)
        return Either.right(value)
    return validator

# ==========================================
# COMPOSICIÓN DE VALIDADORES
# ==========================================

def compose_validators(*validators):
    """Compone múltiples validadores"""
    def validate(value):
        result = Either.right(value)
        for validator in validators:
            result = result.bind(validator)
            if result.is_left:
                break
        return result
    return validate

# ==========================================
# VALIDACIÓN DE FORMULARIOS
# ==========================================

class FormValidator:
    def __init__(self):
        self.rules = {}

    def rule(self, field, *validators):
        """Agrega regla de validación"""
        self.rules[field] = compose_validators(*validators)
        return self

    def validate(self, data: Dict[str, Any]) -> Either[Dict, Dict]:
        """Valida el formulario completo"""
        errors = {}
        validated = {}

        for field, validator in self.rules.items():
            value = data.get(field)
            result = validator(value)

            if result.is_left:
                errors[field] = result._value
            else:
                validated[field] = result._value

        if errors:
            return Either.left(errors)
        return Either.right(validated)

# ==========================================
# USO
# ==========================================

# Definir validaciones
validator = FormValidator()
validator.rule(
    'name',
    lambda x: validate_required('name', x),
    validate_min_length(2)
)
validator.rule(
    'email',
    lambda x: validate_required('email', x),
    validate_email
)
validator.rule(
    'age',
    lambda x: validate_required('age', x),
    validate_range(18, 120)
)
validator.rule(
    'username',
    lambda x: validate_required('username', x),
    validate_min_length(3),
    validate_pattern(r'^[a-zA-Z0-9_]+$', 'Solo letras, números y _')
)

# Validar datos
form_data = {
    'name': 'Alan Mora',
    'email': 'alan@example.com',
    'age': 25,
    'username': 'alanmora'
}

result = validator.validate(form_data)

if result.is_right:
    print("✅ Formulario válido:")
    print(result._value)
else:
    print("❌ Errores de validación:")
    for field, error in result._value.items():
        print(f"  {field}: {error}")
```

---

## 4. Event Processing

Sistema de procesamiento de eventos en tiempo real.

```python
from core import Stream, IO
from datetime import datetime
from typing import NamedTuple

# ==========================================
# MODELOS
# ==========================================

class Event(NamedTuple):
    timestamp: datetime
    type: str
    user_id: int
    data: dict

class Alert(NamedTuple):
    level: str
    message: str
    timestamp: datetime

# ==========================================
# PROCESADORES
# ==========================================

def detect_anomalies(events: Stream[Event]) -> Stream[Alert]:
    """Detecta anomalías en eventos"""
    # Ejemplo: más de 5 fallos en ventana
    window_size = 10

    def check_window(window):
        failures = sum(1 for e in window if e.type == 'ERROR')
        if failures >= 5:
            return [Alert(
                level='HIGH',
                message=f'{failures} errores en {window_size} eventos',
                timestamp=datetime.now()
            )]
        return []

    return (
        events
        .chunk(window_size)
        .flat_map(lambda window: Stream.from_iterable(check_window(window)))
    )

def aggregate_metrics(events: Stream[Event]) -> dict:
    """Agrega métricas de eventos"""
    event_list = events.to_list()

    by_type = {}
    by_user = {}

    for event in event_list:
        # Por tipo
        by_type[event.type] = by_type.get(event.type, 0) + 1

        # Por usuario
        by_user[event.user_id] = by_user.get(event.user_id, 0) + 1

    return {
        'total': len(event_list),
        'by_type': by_type,
        'by_user': by_user,
        'period': {
            'start': min(e.timestamp for e in event_list),
            'end': max(e.timestamp for e in event_list)
        }
    }

# ==========================================
# PIPELINE DE EVENTOS
# ==========================================

def process_event_stream(events: list[Event]):
    """Pipeline completo de procesamiento"""
    stream = Stream.from_iterable(events)

    # Pipeline 1: Detección de anomalías
    alerts = detect_anomalies(stream)

    # Pipeline 2: Solo eventos de error
    errors = stream.filter(lambda e: e.type == 'ERROR')

    # Pipeline 3: Métricas
    metrics = aggregate_metrics(stream)

    return {
        'alerts': alerts.to_list(),
        'errors': errors.to_list(),
        'metrics': metrics
    }

# ==========================================
# USO
# ==========================================

# Generar eventos de ejemplo
import random

events = [
    Event(
        timestamp=datetime.now(),
        type=random.choice(['INFO', 'ERROR', 'WARNING']),
        user_id=random.randint(1, 10),
        data={'action': 'click'}
    )
    for _ in range(100)
]

# Procesar
result = process_event_stream(events)

print(f"Alertas: {len(result['alerts'])}")
print(f"Errores: {len(result['errors'])}")
print(f"Métricas: {result['metrics']}")
```

---

## 5. Caching con Memoización

Sistema de caching funcional con memoización.

```python
from core import IO
from utils import memoize
import time
from functools import wraps

# ==========================================
# CACHE DECORATOR
# ==========================================

def cached_io(ttl_seconds=60):
    """Decorator para cachear IOs con TTL"""
    cache = {}

    def decorator(f):
        @wraps(f)
        def wrapper(*args):
            key = str(args)
            now = time.time()

            # Check cache
            if key in cache:
                value, timestamp = cache[key]
                if now - timestamp < ttl_seconds:
                    print(f"✅ Cache HIT: {key}")
                    return IO.pure(value)

            # Cache miss - ejecutar y guardar
            print(f"❌ Cache MISS: {key}")
            io = f(*args)
            result = io.run()
            cache[key] = (result, now)

            return IO.pure(result)

        return wrapper
    return decorator

# ==========================================
# EJEMPLO DE USO
# ==========================================

@cached_io(ttl_seconds=5)
def expensive_query(user_id):
    """Query costoso con caching"""
    def query():
        print(f"Ejecutando query costoso para user {user_id}...")
        time.sleep(2)  # Simula operación lenta
        return {"user_id": user_id, "data": "expensive result"}

    return IO(query)

# Uso
print("Primera llamada:")
result1 = expensive_query(1).run()
print(result1)

print("\nSegunda llamada (inmediata - debería usar cache):")
result2 = expensive_query(1).run()
print(result2)

print("\nTercera llamada (después de 6 segundos - cache expirado):")
time.sleep(6)
result3 = expensive_query(1).run()
print(result3)
```

---

## 6. Procesamiento de CSV

Procesamiento funcional de archivos CSV grandes.

```python
from core import Stream, IO, io_read_file
import csv
from io import StringIO

# ==========================================
# LECTURA DE CSV
# ==========================================

def read_csv_stream(filepath):
    """Lee CSV como stream"""
    def effect():
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return Stream.from_iterable(list(reader))

    return IO(effect)

# ==========================================
# TRANSFORMACIONES
# ==========================================

def clean_row(row):
    """Limpia una fila"""
    return {
        k: v.strip() if isinstance(v, str) else v
        for k, v in row.items()
    }

def convert_types(row):
    """Convierte tipos de datos"""
    return {
        'id': int(row.get('id', 0)),
        'name': str(row.get('name', '')),
        'age': int(row.get('age', 0)),
        'salary': float(row.get('salary', 0.0)),
        'active': row.get('active', 'false').lower() == 'true'
    }

# ==========================================
# ANÁLISIS
# ==========================================

def analyze_csv(filepath):
    """Analiza CSV y retorna estadísticas"""
    return (
        read_csv_stream(filepath)
        .map(lambda stream: (
            stream
            .map(clean_row)
            .map(convert_types)
        ))
        .map(lambda stream: {
            'total_rows': stream.count(),
            'avg_age': stream.map(lambda r: r['age']).reduce(
                lambda acc, x: acc + x, 0
            ) / stream.count(),
            'avg_salary': stream.map(lambda r: r['salary']).reduce(
                lambda acc, x: acc + x, 0
            ) / stream.count(),
            'active_users': stream.filter(
                lambda r: r['active']
            ).count()
        })
    )

# ==========================================
# FILTRADO Y EXPORT
# ==========================================

def filter_and_export(input_file, output_file, filter_fn):
    """Filtra CSV y exporta resultado"""
    def effect():
        # Leer y filtrar
        stream = read_csv_stream(input_file).run()
        filtered = (
            stream
            .map(clean_row)
            .map(convert_types)
            .filter(filter_fn)
            .to_list()
        )

        # Escribir resultado
        with open(output_file, 'w', newline='') as f:
            if filtered:
                writer = csv.DictWriter(f, fieldnames=filtered[0].keys())
                writer.writeheader()
                writer.writerows(filtered)

        return len(filtered)

    return IO(effect)

# Uso
# Filtrar usuarios activos con salario > 50000
result = filter_and_export(
    'users.csv',
    'high_earners.csv',
    lambda row: row['active'] and row['salary'] > 50000
).run()

print(f"Exportados {result} registros")
```

---

## 7. Rate Limiting

Rate limiting funcional para APIs.

```python
from core import IO
import time
from collections import deque

class RateLimiter:
    """Rate limiter basado en token bucket"""

    def __init__(self, max_calls, time_window):
        self.max_calls = max_calls
        self.time_window = time_window  # en segundos
        self.calls = deque()

    def can_proceed(self):
        """Verifica si puede proceder"""
        now = time.time()

        # Remover llamadas fuera de la ventana
        while self.calls and self.calls[0] < now - self.time_window:
            self.calls.popleft()

        # Verificar límite
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True

        return False

    def wait_time(self):
        """Tiempo de espera hasta próxima ventana"""
        if not self.calls:
            return 0

        oldest = self.calls[0]
        wait = self.time_window - (time.time() - oldest)
        return max(0, wait)

def rate_limited(limiter):
    """Decorator para rate limiting"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            def effect():
                while not limiter.can_proceed():
                    wait = limiter.wait_time()
                    print(f"Rate limit - esperando {wait:.2f}s...")
                    time.sleep(wait + 0.1)

                return f(*args, **kwargs).run()

            return IO(effect)
        return wrapper
    return decorator

# Uso
limiter = RateLimiter(max_calls=5, time_window=10)  # 5 llamadas por 10 segundos

@rate_limited(limiter)
def api_call(endpoint):
    """Llamada a API con rate limiting"""
    def effect():
        print(f"Llamando a {endpoint}...")
        return f"Respuesta de {endpoint}"
    return IO(effect)

# Hacer múltiples llamadas (se rate limitará automáticamente)
for i in range(10):
    result = api_call(f"/api/endpoint/{i}").run()
    print(f"  -> {result}")
```

---

## 8. Estado Funcional (State Monad)

Manejo de estado funcional sin mutación.

```python
from core import IO
from typing import NamedTuple, Callable, TypeVar

A = TypeVar('A')
S = TypeVar('S')

class State(NamedTuple):
    """State Monad simplificado"""
    run_state: Callable[[S], tuple[A, S]]

    def map(self, f):
        def new_state(s):
            a, s2 = self.run_state(s)
            return (f(a), s2)
        return State(new_state)

    def bind(self, f):
        def new_state(s):
            a, s2 = self.run_state(s)
            return f(a).run_state(s2)
        return State(new_state)

    @staticmethod
    def pure(value):
        return State(lambda s: (value, s))

    @staticmethod
    def get():
        """Obtiene el estado actual"""
        return State(lambda s: (s, s))

    @staticmethod
    def put(new_state):
        """Establece nuevo estado"""
        return State(lambda s: (None, new_state))

    @staticmethod
    def modify(f):
        """Modifica el estado"""
        return State(lambda s: (None, f(s)))

# Ejemplo: Contador funcional
def increment():
    return State.modify(lambda count: count + 1)

def decrement():
    return State.modify(lambda count: count - 1)

def get_count():
    return State.get()

# Pipeline con estado
computation = (
    increment()
    .bind(lambda _: increment())
    .bind(lambda _: increment())
    .bind(lambda _: get_count())
)

result, final_state = computation.run_state(0)
print(f"Resultado: {result}, Estado final: {final_state}")  # 3, 3
```

---

## 🎯 Conclusión

Estos ejemplos demuestran:

✅ **ETL Pipelines**: Extracción, transformación y carga funcional
✅ **Web Scraping**: Manejo de HTTP con retry y rate limiting
✅ **Validación**: Sistema completo de validación composable
✅ **Event Processing**: Procesamiento de eventos en tiempo real
✅ **Caching**: Memoización y caching con TTL
✅ **CSV Processing**: Procesamiento de archivos grandes
✅ **Rate Limiting**: Control de frecuencia de llamadas
✅ **State Management**: Manejo funcional de estado

Para más información:
- [Tutorial](TUTORIAL.md) - Aprende paso a paso
- [API Reference](API_REFERENCE.md) - Referencia completa
- [Design Rationale](DESIGN_RATIONALE.md) - Decisiones de diseño
