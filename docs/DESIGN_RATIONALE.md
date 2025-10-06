# 🏗️ Design Rationale

Explicación detallada de las decisiones de diseño e implementación del framework.

## Tabla de Contenidos

1. [Filosofía del Framework](#filosofía-del-framework)
2. [Por qué Mónadas](#por-qué-mónadas)
3. [Decisiones de Implementación](#decisiones-de-implementación)
4. [Trade-offs](#trade-offs)
5. [Comparación con Otros Frameworks](#comparación-con-otros-frameworks)

---

## Filosofía del Framework

### Principios Fundamentales

El framework fue diseñado siguiendo estos principios core:

#### 1. **Pureza Funcional**

```python
# ❌ Enfoque imperativo (con side effects)
def process_data(data):
    print("Processing...")  # Side effect
    result = []
    for item in data:
        result.append(item * 2)
    return result

# ✅ Enfoque funcional (sin side effects)
def process_data(data):
    return Stream.from_iterable(data).map(lambda x: x * 2)
```

**Razón**: Las funciones puras son:
- Más fáciles de testear
- Más fáciles de razonar
- Componibles
- Thread-safe por defecto

#### 2. **Composición sobre Herencia**

```python
# ✅ Composición de mónadas
pipeline = (
    IO.pure(data)
    .map(transform)
    .bind(process)
    .map(format_output)
)
```

**Razón**:
- Más flexible que jerarquías de clases
- Evita el problema del "diamond inheritance"
- Permite mezclar comportamientos dinámicamente

#### 3. **Lazy Evaluation**

```python
# El stream no se evalúa hasta .to_list()
stream = (
    Stream.range(0)  # Infinito!
    .map(expensive_operation)
    .filter(condition)
    .take(10)
    .to_list()  # Solo ahora se ejecuta
)
```

**Razón**:
- Permite trabajar con secuencias infinitas
- Solo computa lo necesario
- Eficiente en memoria

#### 4. **Type Safety**

```python
from typing import TypeVar, Generic

A = TypeVar('A')
B = TypeVar('B')

class Stream(Generic[A]):
    def map(self, f: Callable[[A], B]) -> 'Stream[B]':
        ...
```

**Razón**:
- Detecta errores en tiempo de diseño
- Mejor IDE support (autocomplete)
- Documentación automática

---

## Por qué Mónadas

### El Problema que Resuelven

Las mónadas resuelven el problema de **componer operaciones con contexto**.

#### Problema 1: Manejo de Errores

```python
# ❌ Sin mónadas: try/except anidados
try:
    result1 = operation1()
    try:
        result2 = operation2(result1)
        try:
            result3 = operation3(result2)
            return result3
        except Exception as e:
            handle_error(e)
    except Exception as e:
        handle_error(e)
except Exception as e:
    handle_error(e)

# ✅ Con Either Monad: pipeline limpio
result = (
    operation1()
    .bind(operation2)
    .bind(operation3)
)
```

#### Problema 2: Side Effects

```python
# ❌ Sin mónadas: side effects inmediatos
def process():
    data = read_file()  # Lee ahora
    transformed = transform(data)
    write_file(transformed)  # Escribe ahora
    return result

# ✅ Con IO Monad: descripción vs ejecución
def process():
    return (
        io_read_file("input.txt")
        .map(transform)
        .bind(lambda data: io_write_file("output.txt", data))
    )

pipeline = process()  # Solo descripción
pipeline.run()  # Ahora sí ejecuta
```

#### Problema 3: Procesamiento de Secuencias

```python
# ❌ Sin mónadas: materialización inmediata
data = range(1000000)
filtered = [x for x in data if condition(x)]  # Crea lista
mapped = [f(x) for x in filtered]  # Otra lista
result = list(mapped[:10])  # Solo necesitamos 10!

# ✅ Con Stream Monad: lazy evaluation
result = (
    Stream.range(0, 1000000)
    .filter(condition)
    .map(f)
    .take(10)  # Solo evalúa 10 elementos
    .to_list()
)
```

### Las Tres Leyes Monádicas

Implementamos las leyes para garantizar comportamiento consistente:

```python
# Ley 1: Identidad Izquierda
# pure(a).bind(f) == f(a)
assert Stream.pure(5).bind(lambda x: Stream.of(x * 2)).to_list() == \
       Stream.of(5 * 2).to_list()

# Ley 2: Identidad Derecha
# m.bind(pure) == m
stream = Stream.of(1, 2, 3)
assert stream.bind(Stream.pure).to_list() == stream.to_list()

# Ley 3: Asociatividad
# m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))
m = Stream.of(1, 2, 3)
f = lambda x: Stream.of(x, x * 2)
g = lambda x: Stream.of(x + 1)

left = m.bind(f).bind(g).to_list()
right = m.bind(lambda x: f(x).bind(g)).to_list()
assert left == right
```

**Por qué son importantes**:
- Garantizan comportamiento predecible
- Permiten refactorizar con confianza
- Hacen el código razonable matemáticamente

---

## Decisiones de Implementación

### 1. Either vs Result/Option

**Decisión**: Implementar `Either[E, A]` en lugar de `Result[T, E]` y `Option[T]` separados.

**Razones**:
- ✅ Mayor flexibilidad (tipo de error personalizable)
- ✅ Más cercano a Haskell/Scala
- ✅ Un tipo para gobernarlos a todos

**Trade-off**:
- ❌ Un poco más verboso que `Option[T]` para casos simples

```python
# Either es más general
Either[str, int]  # Error como string, valor como int
Either[Exception, Data]  # Error como excepción
Either[None, int]  # Funciona como Option[int]

# vs tener tipos separados
Option[int]  # Solo para ausencia de valor
Result[int, str]  # Siempre específico
```

### 2. IO Monad con run() explícito

**Decisión**: Requiere llamada explícita a `.run()` para ejecutar efectos.

**Razones**:
- ✅ Separación clara entre descripción y ejecución
- ✅ Previene efectos accidentales
- ✅ Facilita testing (puedes testear la descripción sin ejecutar)

```python
# Descripción (pura)
pipeline = (
    io_read_file("input.txt")
    .map(process)
    .bind(lambda data: io_write_file("output.txt", data))
)

# En tests: puedes inspeccionar el pipeline sin ejecutarlo

# Ejecución (impura)
result = pipeline.run()
```

**Alternativa considerada**: Auto-ejecución con `await` (estilo async/await)
- ❌ Requeriría Python 3.5+
- ❌ Menos explícito
- ❌ Mezcla conceptos async con FP

### 3. Stream con Lazy Evaluation

**Decisión**: Streams son completamente lazy, solo se evalúan al materializarlos.

**Implementación**:

```python
class Stream:
    def __init__(self, source: Callable[[], Iterator[A]]):
        self._source = source  # Función, no iterador

    def map(self, f):
        def new_source():
            return map(f, self._source())  # Lazy
        return Stream(new_source)
```

**Razones**:
- ✅ Permite streams infinitos
- ✅ Eficiente en memoria
- ✅ Solo computa lo necesario

**Trade-off**:
- ❌ Puede ser menos intuitivo para principiantes
- ❌ Múltiples materializaciones re-evalúan el stream

### 4. Type Hints con Generics

**Decisión**: Usar TypeVars y Generic completos.

```python
A = TypeVar('A')
B = TypeVar('B')

class Monad(Generic[A]):
    def map(self, f: Callable[[A], B]) -> 'Monad[B]':
        ...
```

**Razones**:
- ✅ Type safety en tiempo de diseño
- ✅ Mejor experiencia en IDEs
- ✅ Documentación automática

**Trade-off**:
- ❌ Sintaxis más verbosa
- ❌ Requiere Python 3.9+ para algunas features

### 5. Currying con Decorator

**Decisión**: Implementar currying como decorator en lugar de transformación automática.

```python
@curry
def add(a, b, c):
    return a + b + c

add(1)(2)(3)  # Curried
add(1, 2, 3)  # También funciona
```

**Razones**:
- ✅ Opt-in (el usuario elige cuándo usar)
- ✅ Soporte para ambos estilos
- ✅ Pythonic

**Alternativa considerada**: Currying automático (estilo Haskell)
- ❌ Muy diferente al estilo Python
- ❌ Confuso para usuarios nuevos

---

## Trade-offs

### Performance vs Expresividad

```python
# Más expresivo pero un poco más lento
result = (
    Stream.range(0, 1000000)
    .map(lambda x: x * 2)
    .filter(lambda x: x > 100)
    .take(10)
    .to_list()
)

# Más rápido pero menos expresivo
result = []
for i in range(1000000):
    x = i * 2
    if x > 100:
        result.append(x)
        if len(result) == 10:
            break
```

**Decisión**: Priorizar expresividad y composabilidad.

**Justificación**:
- En la mayoría de casos, la diferencia es negligible
- El código es más mantenible
- Optimizaciones prematuras son la raíz de todo mal
- Cuando el performance importa, usa herramientas apropiadas (NumPy, etc.)

### Compatibilidad con Python "Normal"

```python
# Interoperabilidad con código imperativo
traditional_list = [1, 2, 3, 4, 5]
stream = Stream.from_iterable(traditional_list)

# Vuelta a Python normal
result_list = stream.map(lambda x: x * 2).to_list()
```

**Decisión**: Máxima interoperabilidad.

**Razones**:
- Facilita adopción gradual
- No necesitas reescribir todo
- Funciona con librerías existentes

### Legibilidad vs Concisión

```python
# Más conciso (estilo Haskell)
result = stream >>= f >>= g >>= h

# Más legible (nuestro estilo)
result = (
    stream
    .bind(f)
    .bind(g)
    .bind(h)
)
```

**Decisión**: Priorizar legibilidad.

**Razones**:
- Python valora la legibilidad
- Operators como `>>=` son raros en Python
- Explícito es mejor que implícito (Zen of Python)

---

## Comparación con Otros Frameworks

### vs. PyMonad

| Característica | Stream Framework | PyMonad |
|---------------|------------------|---------|
| Leyes Monádicas | ✅ Testeadas | ✅ Testeadas |
| Type Hints | ✅ Completos | ❌ Limitados |
| Lazy Streams | ✅ Sí | ❌ No |
| IO Monad | ✅ Sí | ❌ No |
| Documentación | ✅ Extensa | ⚠️ Básica |
| Currying | ✅ Decorator | ✅ Manual |

### vs. returns (dry-python)

| Característica | Stream Framework | returns |
|---------------|------------------|---------|
| Either/Result | ✅ Either | ✅ Result |
| IO Monad | ✅ Sí | ✅ Sí |
| Streams | ✅ Lazy | ❌ No |
| Railway-oriented | ⚠️ Via Either | ✅ Explícito |
| Decorators | ⚠️ Básico | ✅ Avanzado |
| Learning Curve | ⚠️ Media | ⚠️ Alta |

### vs. toolz/fn.py

| Característica | Stream Framework | toolz |
|---------------|------------------|--------|
| Mónadas | ✅ Sí | ❌ No |
| Lazy Evaluation | ✅ Streams | ✅ Iterators |
| Functional Utils | ✅ 50+ | ✅ 100+ |
| Type Safety | ✅ Generics | ❌ No |
| Composición | ✅ Monádica | ✅ Funciones |

**Nuestro nicho**:
- Educativo: aprender FP y mónadas
- Expresivo: código declarativo y legible
- Type-safe: aprovecha el sistema de tipos de Python

---

## Lecciones Aprendidas

### 1. Python no es Haskell

**Lección**: No intentar forzar sintaxis de Haskell en Python.

```python
# ❌ Intentar replicar Haskell
result = pure(5) >>= f >>= g >>= h

# ✅ Idiomático en Python
result = (
    Stream.pure(5)
    .bind(f)
    .bind(g)
    .bind(h)
)
```

### 2. Documentación es Clave

**Lección**: FP puede ser intimidante. Documentación clara es esencial.

- Docstrings detallados
- Ejemplos en cada función
- Tutorial paso a paso
- Explicación de conceptos

### 3. Testing de Leyes Monádicas

**Lección**: Tests normales no son suficientes. Hay que testear las leyes.

```python
def test_left_identity(self):
    """pure(a).bind(f) == f(a)"""
    value = 5
    f = lambda x: Stream.of(x * 2)

    left = Stream.pure(value).bind(f).to_list()
    right = f(value).to_list()

    assert left == right
```

### 4. Interoperabilidad es Importante

**Lección**: El framework debe jugar bien con código Python normal.

```python
# ✅ Fácil entrada y salida
input_list = [1, 2, 3]
output_list = (
    Stream.from_iterable(input_list)
    .map(lambda x: x * 2)
    .to_list()
)
```

---

## Conclusión

El diseño del framework balances:
- **Pureza funcional** vs **pragmatismo Python**
- **Expresividad** vs **performance**
- **Type safety** vs **simplicidad**
- **Teoría** vs **practicidad**

El resultado es un framework que:
- ✅ Enseña conceptos de FP
- ✅ Es útil en proyectos reales
- ✅ Se integra con Python existente
- ✅ Mantiene correctitud matemática

Para más detalles, ver:
- [Tutorial](TUTORIAL.md) - Cómo usar el framework
- [API Reference](API_REFERENCE.md) - Referencia completa
- [Examples](EXAMPLES.md) - Casos de uso reales
