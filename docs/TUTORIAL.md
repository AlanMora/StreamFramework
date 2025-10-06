# 📚 Tutorial Completo: Functional Stream Framework

Bienvenido al tutorial completo del framework. Aprenderás desde los conceptos básicos hasta técnicas avanzadas de programación funcional.

## 📋 Tabla de Contenidos

1. [Introducción a la Programación Funcional](#1-introducción-a-la-programación-funcional)
2. [Either Monad: Manejo de Errores](#2-either-monad-manejo-de-errores)
3. [IO Monad: Efectos Puros](#3-io-monad-efectos-puros)
4. [Stream Monad: Procesamiento Lazy](#4-stream-monad-procesamiento-lazy)
5. [Operadores Funcionales](#5-operadores-funcionales)
6. [Composición Avanzada](#6-composición-avanzada)
7. [Casos de Uso Reales](#7-casos-de-uso-reales)

---

## 1. Introducción a la Programación Funcional

### ¿Qué es una Mónada?

Una **mónada** es un patrón de diseño funcional que encapsula valores y permite encadenar operaciones de manera composable.

**Las 3 operaciones esenciales**:

```python
# 1. pure: envuelve un valor
monad = Monad.pure(42)

# 2. map: transforma el valor interno
monad.map(lambda x: x * 2)

# 3. bind (flat_map): encadena operaciones monádicas
monad.bind(lambda x: Monad.pure(x + 1))
```

**Las 3 leyes monádicas** que deben cumplirse:

```python
# Ley 1: Identidad Izquierda
Monad.pure(a).bind(f) == f(a)

# Ley 2: Identidad Derecha
m.bind(Monad.pure) == m

# Ley 3: Asociatividad
m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))
```

---

## 2. Either Monad: Manejo de Errores

### ¿Por qué Either?

En programación funcional, no usamos excepciones. En su lugar, representamos el éxito o fallo como valores:

- `Right(valor)`: Éxito
- `Left(error)`: Fallo

### Ejemplo Básico

```python
from core import Either

def divide(x, y):
    """División segura que retorna Either"""
    if y == 0:
        return Either.left("Error: División por cero")
    return Either.right(x / y)

# Uso
result = divide(10, 2)
print(result)  # Right(5.0)

result = divide(10, 0)
print(result)  # Left('Error: División por cero')
```

### Map y Bind

```python
# Map: transforma el valor exitoso
result = Either.right(5).map(lambda x: x * 2)
print(result)  # Right(10)

# Map en Left no hace nada (propaga el error)
result = Either.left("error").map(lambda x: x * 2)
print(result)  # Left('error')

# Bind: encadena operaciones que retornan Either
result = (
    Either.right(10)
    .bind(lambda x: divide(x, 2))  # Right(5.0)
    .bind(lambda x: divide(x, 0))  # Left('Error: División por cero')
    .map(lambda x: x + 100)        # No se ejecuta
)
print(result)  # Left('Error: División por cero')
```

### Recuperación de Errores

```python
# get_or_else: valor por defecto
value = Either.left("error").get_or_else(42)
print(value)  # 42

value = Either.right(10).get_or_else(42)
print(value)  # 10

# or_else: Either alternativo
result = Either.left("error").or_else(Either.right(42))
print(result)  # Right(42)

# recover: transformar el error
result = Either.left("error").recover(lambda e: f"Recuperado: {e}")
print(result)  # Right('Recuperado: error')
```

### Caso Práctico: Validación

```python
from core import Either

def validate_age(age):
    if age < 0:
        return Either.left("Edad no puede ser negativa")
    if age < 18:
        return Either.left("Debe ser mayor de edad")
    return Either.right(age)

def validate_email(email):
    if '@' not in email:
        return Either.left("Email inválido")
    return Either.right(email)

# Pipeline de validación
result = (
    validate_age(25)
    .map(lambda age: {"age": age})
    .bind(lambda data: validate_email("user@example.com")
          .map(lambda email: {**data, "email": email}))
)

if result.is_right:
    print(f"Usuario válido: {result._value}")
else:
    print(f"Error de validación: {result._value}")
```

---

## 3. IO Monad: Efectos Puros

### El Problema de los Side Effects

En programación funcional, queremos separar la **descripción** de los efectos de su **ejecución**.

```python
# ❌ Impuro: se ejecuta inmediatamente
def impure():
    print("Efecto ejecutado!")  # Side effect
    return 42

result = impure()  # Ya ejecutó el efecto

# ✅ Puro: se describe pero no se ejecuta
from core import IO

def pure():
    return IO(lambda: print("Efecto ejecutado!"))

io = pure()  # No se ejecutó nada aún
io.run()     # Ahora sí se ejecuta
```

### Creación de IO

```python
from core import IO

# pure: envuelve un valor
io = IO.pure(42)
print(io)  # IO(<effect>)
print(io.run())  # 42

# Constructor directo
io = IO(lambda: 5 + 3)
print(io.run())  # 8
```

### Composición de Efectos

```python
from core import IO, io_write_file, io_read_file

# Map: transforma el resultado
io = (
    IO.pure(5)
    .map(lambda x: x * 2)
    .map(lambda x: x + 3)
)
print(io.run())  # 13

# Bind: encadena IOs
pipeline = (
    IO.pure("Hola, Mundo!")
    .map(str.upper)
    .bind(lambda text: io_write_file("/tmp/test.txt", text))
    .bind(lambda _: io_read_file("/tmp/test.txt"))
    .map(str.lower)
)

result = pipeline.run()
print(result)  # "hola, mundo!"
```

### Manejo de Errores en IO

```python
from core import IO

# attempt: captura excepciones
def risky_operation():
    return 10 / 0

io = IO(risky_operation).attempt()
result = io.run()

if result.is_left:
    print(f"Error capturado: {result._value}")
# Error capturado: division by zero

# recover: recuperarse de errores
io = IO(risky_operation).recover(lambda e: 0)
print(io.run())  # 0

# retry: reintentar en caso de fallo
attempts = [0]

def flaky_operation():
    attempts[0] += 1
    if attempts[0] < 3:
        raise ValueError("Fallo temporal")
    return "Éxito!"

io = IO(flaky_operation).retry(max_attempts=5)
print(io.run())  # "Éxito!"
print(f"Intentos: {attempts[0]}")  # 3
```

### Caso Práctico: Pipeline de Archivos

```python
from core import IO, io_read_file, io_write_file

def process_log_file(input_path, output_path):
    """Pipeline funcional de procesamiento de archivo"""
    return (
        io_read_file(input_path)
        .map(lambda content: content.split('\n'))
        .map(lambda lines: [line for line in lines if 'ERROR' in line])
        .map(lambda errors: '\n'.join(errors))
        .bind(lambda errors: io_write_file(output_path, errors))
        .map(lambda _: "Procesamiento completado")
    )

# Uso (descripción, no ejecución)
pipeline = process_log_file('/var/log/app.log', '/tmp/errors.log')

# Ejecutar
result = pipeline.run()
print(result)
```

---

## 4. Stream Monad: Procesamiento Lazy

### ¿Qué es Lazy Evaluation?

Los Streams **no calculan los valores hasta que se necesitan**. Esto permite trabajar con secuencias infinitas.

```python
from core import Stream

# Creación de streams
s1 = Stream.of(1, 2, 3, 4, 5)
s2 = Stream.from_iterable([1, 2, 3])
s3 = Stream.range(0, 10)      # [0, 1, 2, ..., 9]
s4 = Stream.range(0)          # [0, 1, 2, ...] infinito!
s5 = Stream.repeat("x", 5)    # ["x", "x", "x", "x", "x"]
```

### Transformaciones Lazy

```python
# Map: transforma cada elemento
result = Stream.of(1, 2, 3).map(lambda x: x * 2).to_list()
# [2, 4, 6]

# Filter: filtra elementos
result = Stream.of(1, 2, 3, 4, 5).filter(lambda x: x % 2 == 0).to_list()
# [2, 4]

# FlatMap: map + flatten
result = (
    Stream.of(1, 2, 3)
    .flat_map(lambda x: Stream.of(x, x * 2))
    .to_list()
)
# [1, 2, 2, 4, 3, 6]
```

### Take y Skip

```python
# Take: toma los primeros N
Stream.range(0).take(5).to_list()
# [0, 1, 2, 3, 4]

# Skip: salta los primeros N
Stream.of(1, 2, 3, 4, 5).skip(2).to_list()
# [3, 4, 5]

# Take while: mientras se cumpla condición
Stream.of(1, 2, 3, 4, 5).take_while(lambda x: x < 4).to_list()
# [1, 2, 3]

# Drop while: descarta mientras se cumpla
Stream.of(1, 2, 3, 4, 5).drop_while(lambda x: x < 4).to_list()
# [4, 5]
```

### Operaciones Terminales

```python
# to_list: materializa el stream
Stream.of(1, 2, 3).to_list()
# [1, 2, 3]

# reduce: acumula
Stream.of(1, 2, 3, 4, 5).reduce(lambda acc, x: acc + x, 0)
# 15

# count: cuenta elementos
Stream.of(1, 2, 3).count()
# 3

# find: busca primer elemento
Stream.of(1, 2, 3, 4, 5).find(lambda x: x > 3)
# Right(4)

# exists: verifica existencia
Stream.of(1, 2, 3).exists(lambda x: x == 2)
# True

# all: verifica que todos cumplan
Stream.of(2, 4, 6).all(lambda x: x % 2 == 0)
# True
```

### Combinadores

```python
# Zip: combina dos streams
s1 = Stream.of(1, 2, 3)
s2 = Stream.of('a', 'b', 'c')
s1.zip(s2).to_list()
# [(1, 'a'), (2, 'b'), (3, 'c')]

# Concat: concatena streams
Stream.of(1, 2, 3).concat(Stream.of(4, 5, 6)).to_list()
# [1, 2, 3, 4, 5, 6]

# Flatten: aplana stream de iterables
Stream.of([1, 2], [3, 4], [5, 6]).flatten().to_list()
# [1, 2, 3, 4, 5, 6]

# Chunk: agrupa en bloques
Stream.of(1, 2, 3, 4, 5).chunk(2).to_list()
# [[1, 2], [3, 4], [5]]
```

### Caso Práctico: Números Primos

```python
from core import Stream

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

# Primeros 10 números primos
primes = (
    Stream.range(2)              # Infinito desde 2
    .filter(is_prime)            # Solo primos
    .take(10)                    # Primeros 10
    .to_list()
)
print(primes)
# [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]

# Suma de primos menores a 100
sum_primes = (
    Stream.range(2, 100)
    .filter(is_prime)
    .reduce(lambda acc, x: acc + x, 0)
)
print(sum_primes)  # 1060
```

---

## 5. Operadores Funcionales

### Composición de Funciones

```python
from utils import compose, pipe

# Compose: derecha a izquierda (como matemáticas)
add1 = lambda x: x + 1
mult2 = lambda x: x * 2
square = lambda x: x ** 2

# f(g(h(x)))
f = compose(square, add1, mult2)
print(f(5))  # square(add1(mult2(5))) = square(add1(10)) = square(11) = 121

# Pipe: izquierda a derecha (más intuitivo)
g = pipe(mult2, add1, square)
print(g(5))  # square(add1(mult2(5))) = ((5*2)+1)^2 = 121
```

### Currying

```python
from utils import curry

# Convierte función de múltiples args en cadena de funciones
@curry
def add(a, b, c):
    return a + b + c

# Uso normal
print(add(1, 2, 3))  # 6

# Aplicación parcial
add1 = add(1)
add1and2 = add1(2)
print(add1and2(3))  # 6

# Útil para crear funciones especializadas
add10 = add(10)
add10and5 = add10(5)
print(add10and5(3))  # 18
```

### Transformaciones Funcionales

```python
from utils import fmap, ffilter, freduce

# fmap: map curried
double = fmap(lambda x: x * 2)
print(double([1, 2, 3]))  # [2, 4, 6]

# ffilter: filter curried
evens = ffilter(lambda x: x % 2 == 0)
print(evens([1, 2, 3, 4, 5]))  # [2, 4]

# freduce: reduce curried
sum_all = freduce(lambda acc, x: acc + x, 0)
print(sum_all([1, 2, 3, 4, 5]))  # 15
```

### Operadores Curried

```python
from utils import add, multiply, greater_than, is_even

# Operadores matemáticos
add5 = add(5)
print(add5(10))  # 15

mult3 = multiply(3)
print(mult3(7))  # 21

# Comparadores
gt10 = greater_than(10)
print(gt10(15))  # True
print(gt10(5))   # False

# Predicados
numbers = [1, 2, 3, 4, 5, 6]
print(list(filter(is_even, numbers)))  # [2, 4, 6]
```

---

## 6. Composición Avanzada

### Combinando Mónadas

```python
from core import Stream, Either, IO

# Stream de Either
def safe_divide(x, y):
    if y == 0:
        return Either.left(f"División por cero: {x}/{y}")
    return Either.right(x / y)

results = (
    Stream.of((10, 2), (20, 4), (30, 0), (40, 5))
    .map(lambda pair: safe_divide(pair[0], pair[1]))
    .filter(lambda e: e.is_right)
    .map(lambda e: e._value)
    .to_list()
)
print(results)  # [5.0, 5.0, 8.0]
```

### IO con Either

```python
from core import IO

def risky_io_operation():
    """IO que puede fallar"""
    return (
        IO(lambda: 10 / 0)
        .attempt()  # IO[Either[Exception, A]]
    )

# Manejo del resultado
result = risky_io_operation().run()
if result.is_left:
    print(f"Error: {result._value}")
else:
    print(f"Éxito: {result._value}")
```

### Pipeline Completo

```python
from core import Stream, IO, io_read_file
from utils import pipe

def process_numbers(filename):
    """Pipeline completo: IO + Stream + Either"""
    return (
        io_read_file(filename)
        .map(lambda content: content.split('\n'))
        .map(lambda lines: Stream.from_iterable(lines))
        .map(lambda stream: (
            stream
            .map(str.strip)
            .filter(lambda x: x.isdigit())
            .map(int)
            .filter(lambda x: x > 0)
            .map(lambda x: x ** 2)
            .take(10)
            .to_list()
        ))
    )

# Uso
io = process_numbers('/tmp/numbers.txt')
result = io.run()
print(result)
```

---

## 7. Casos de Uso Reales

### Caso 1: Procesamiento de Logs

```python
from core import Stream, Either
from examples.log_processor import parse_log_line, read_log_file

# Analizar logs
log_stream = (
    read_log_file('/var/log/app.log')
    .run()
    .map(parse_log_line)
    .filter(lambda e: e.is_right)
    .map(lambda e: e._value)
)

# Estadísticas
errors = log_stream.filter(lambda log: log.is_error()).count()
warnings = log_stream.filter(lambda log: log.is_warning()).count()

print(f"Errores: {errors}, Warnings: {warnings}")
```

### Caso 2: Validación de Datos

```python
from core import Either

class User:
    def __init__(self, name, email, age):
        self.name = name
        self.email = email
        self.age = age

def validate_user(data):
    """Validación funcional con Either"""
    return (
        validate_name(data.get('name'))
        .bind(lambda name:
            validate_email(data.get('email'))
            .bind(lambda email:
                validate_age(data.get('age'))
                .map(lambda age: User(name, email, age))
            )
        )
    )

def validate_name(name):
    if not name or len(name) < 2:
        return Either.left("Nombre inválido")
    return Either.right(name)

def validate_email(email):
    if not email or '@' not in email:
        return Either.left("Email inválido")
    return Either.right(email)

def validate_age(age):
    if age is None or age < 18:
        return Either.left("Debe ser mayor de edad")
    return Either.right(age)

# Uso
result = validate_user({
    'name': 'Alan',
    'email': 'alan@example.com',
    'age': 25
})

if result.is_right:
    user = result._value
    print(f"Usuario válido: {user.name}")
else:
    print(f"Error: {result._value}")
```

### Caso 3: ETL Pipeline

```python
from core import Stream, IO

def extract():
    """Extraer datos de fuente"""
    return IO(lambda: [
        {'id': 1, 'value': 100},
        {'id': 2, 'value': 200},
        {'id': 3, 'value': 300},
    ])

def transform(data):
    """Transformar datos"""
    return (
        Stream.from_iterable(data)
        .filter(lambda x: x['value'] > 150)
        .map(lambda x: {**x, 'value': x['value'] * 1.1})
        .to_list()
    )

def load(data):
    """Cargar datos"""
    return IO(lambda: print(f"Cargados {len(data)} registros"))

# Pipeline ETL
pipeline = (
    extract()
    .map(transform)
    .bind(lambda data: load(data).map(lambda _: data))
)

result = pipeline.run()
print(result)
```

---

## 🎯 Conclusión

Has aprendido:

✅ Conceptos fundamentales de programación funcional
✅ Either Monad para manejo de errores
✅ IO Monad para efectos puros
✅ Stream Monad para procesamiento lazy
✅ Operadores funcionales y composición
✅ Casos de uso reales

**Siguiente paso**: Explora la [API Reference](API_REFERENCE.md) para conocer todas las funciones disponibles.

**Recursos adicionales**:
- [Ejemplos Avanzados](EXAMPLES.md)
- [Design Rationale](DESIGN_RATIONALE.md)
