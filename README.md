# 🚀 Functional Stream Processing Framework

Un framework avanzado de procesamiento de streams basado en mónadas para Python, implementando conceptos de programación funcional pura.

[![Tests](https://img.shields.io/badge/tests-128%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.9+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

## 📋 Tabla de Contenidos

- [Características](#características)
- [Instalación](#instalación)
- [Inicio Rápido](#inicio-rápido)
- [Conceptos Fundamentales](#conceptos-fundamentales)
- [Componentes](#componentes)
- [Ejemplos](#ejemplos)
- [Documentación](#documentación)
- [Testing](#testing)
- [Contribuir](#contribuir)

## ✨ Características

- **🎯 Programación Funcional Pura**: Implementación completa de mónadas, functors y applicatives
- **🌊 Stream Processing**: Procesamiento lazy de datos infinitos con composición funcional
- **🌐 HTTP Integration**: Operaciones HTTP encapsuladas en IO Monad
- **⚠️ Error Handling**: Manejo funcional de errores con Either Monad
- **🔄 Composición**: Pipelines complejos mediante composición de funciones
- **⚡ Lazy Evaluation**: Evaluación diferida para eficiencia
- **🧪 100% Tested**: Suite completa con 128 tests unitarios
- **📝 Type Safe**: Type hints completos con generics

## 📦 Instalación

```bash
# Clonar repositorio
git clone https://github.com/AlanMora/StreamFramework.git
cd StreamFramework

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
pytest tests/ -v
```

## 🚀 Inicio Rápido

### Either Monad - Manejo de Errores

```python
from core import Either

def divide(x, y):
    if y == 0:
        return Either.left("División por cero")
    return Either.right(x / y)

# Pipeline funcional con manejo de errores
result = (
    divide(10, 2)           # Right(5.0)
    .map(lambda x: x * 2)   # Right(10.0)
    .bind(lambda x: divide(x, 3))  # Right(3.33...)
)

print(result)  # Right(3.3333333333333335)
print(result.get_or_else(0))  # 3.3333333333333335
```

### IO Monad - Efectos de I/O Puros

```python
from core import IO, io_write_file, io_read_file

# Composición de efectos (no se ejecuta aún)
pipeline = (
    IO.pure("Hola, Mundo!")
    .map(str.upper)
    .bind(lambda text: io_write_file("/tmp/test.txt", text))
    .bind(lambda _: io_read_file("/tmp/test.txt"))
)

# Ejecución diferida
content = pipeline.run()  # Aquí se ejecutan los efectos
print(content)  # "HOLA, MUNDO!"
```

### Stream Monad - Procesamiento Lazy

```python
from core import Stream

# Stream infinito con lazy evaluation
result = (
    Stream.range(0)              # [0, 1, 2, 3, ...]
    .filter(lambda x: x % 2 == 0)  # [0, 2, 4, 6, ...]
    .map(lambda x: x ** 2)         # [0, 4, 16, 36, ...]
    .take(5)                       # [0, 4, 16, 36, 64]
    .to_list()
)

print(result)  # [0, 4, 16, 36, 64]
```

### Operadores Funcionales

```python
from utils import pipe, compose, curry

# Composición de funciones
pipeline = pipe(
    lambda x: x * 2,
    lambda x: x + 10,
    lambda x: x ** 2
)

print(pipeline(5))  # ((5 * 2) + 10) ** 2 = 400

# Currying
@curry
def add(a, b, c):
    return a + b + c

add10 = add(10)
add10and5 = add10(5)
print(add10and5(3))  # 18
```

## 💡 Conceptos Fundamentales

### Mónadas

Las mónadas son abstracciones que permiten encadenar operaciones de manera funcional. Toda mónada debe cumplir tres leyes:

1. **Identidad Izquierda**: `pure(a).bind(f) == f(a)`
2. **Identidad Derecha**: `m.bind(pure) == m`
3. **Asociatividad**: `m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))`

### Functors

Un functor es una estructura que puede ser mapeada:

```python
# Cualquier tipo que implemente fmap
Stream.of(1, 2, 3).map(lambda x: x * 2)  # [2, 4, 6]
Either.right(5).map(lambda x: x * 2)     # Right(10)
IO.pure(5).map(lambda x: x * 2)          # IO(10)
```

### Applicatives

Permiten aplicar funciones encapsuladas a valores encapsulados:

```python
# pure: envuelve un valor
Stream.pure(42)   # Stream con un elemento
Either.pure(42)   # Right(42)
IO.pure(42)       # IO que retorna 42
```

## 🧩 Componentes

### Core Monads

| Monad | Propósito | Uso Principal |
|-------|-----------|---------------|
| `Either` | Manejo de errores | Operaciones que pueden fallar |
| `IO` | Efectos de I/O | Lectura/escritura, HTTP |
| `Stream` | Procesamiento lazy | Secuencias infinitas, pipelines |

### Utility Functions

```python
from utils import (
    # Composición
    compose, pipe,

    # Currying
    curry, partial,

    # Transformaciones
    fmap, ffilter, freduce,

    # Operadores
    add, multiply, greater_than,

    # Predicados
    is_even, is_positive, is_empty
)
```

## 📚 Ejemplos

### Procesamiento de Logs

```python
from core import Stream, Either
from examples.log_processor import analyze_log_file

# Análisis funcional de logs
stats = analyze_log_file('/var/log/app.log').run()

print(f"Total: {stats['total_entries']}")
print(f"Errores: {stats['errors']}")
print(f"Tasa de error: {stats['error_rate']:.2f}%")
```

### Pipeline de Datos

```python
# Combinación de múltiples mónadas
result = (
    Stream.of(1, 2, 3, 4, 5)
    .map(lambda x: divide(100, x))       # Stream[Either]
    .filter(lambda e: e.is_right)        # Solo exitosos
    .map(lambda e: e._value)             # Extraer valores
    .map(lambda x: round(x, 2))          # Redondear
    .to_list()
)
# [100.0, 50.0, 33.33, 25.0, 20.0]
```

### HTTP Requests con IO Monad

```python
from core import http_get, IO

# Pipeline HTTP funcional
pipeline = (
    http_get("https://api.github.com/users/octocat")
    .map(lambda either: either.map(lambda resp: resp.json()))
    .map(lambda either: either.map(lambda data: data._value['name']))
)

result = pipeline.run()
if result.is_right:
    print(f"Usuario: {result._value}")
```

## 📖 Documentación

- [Tutorial Completo](docs/TUTORIAL.md) - Aprende paso a paso
- [API Reference](docs/API_REFERENCE.md) - Referencia completa
- [Design Rationale](docs/DESIGN_RATIONALE.md) - Decisiones de diseño
- [Ejemplos Avanzados](docs/EXAMPLES.md) - Casos de uso complejos

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Tests específicos
pytest tests/test_monad.py -v      # Either & IO (41 tests)
pytest tests/test_stream.py -v     # Stream (54 tests)
pytest tests/test_io.py -v         # IO helpers (33 tests)

# Con coverage
pytest tests/ --cov=core --cov=utils --cov-report=html

# Verificar leyes monádicas
pytest tests/test_monad.py::TestEitherMonad::test_left_identity -v
```

## 🏗️ Arquitectura

```
StreamFramework/
├── core/
│   ├── monad.py          # Clases base abstractas
│   ├── either.py         # Either Monad (error handling)
│   ├── io_monad.py       # IO Monad (effects)
│   ├── stream.py         # Stream Monad (lazy processing)
│   └── http_stream.py    # HTTP integration
├── utils/
│   └── operators.py      # 50+ functional operators
├── examples/
│   ├── log_processor.py  # Log analysis example
│   ├── http_api.py       # HTTP API example
│   └── realtime_data.py  # Real-time processing
├── tests/
│   ├── test_monad.py     # Monad laws & behavior
│   ├── test_stream.py    # Stream operations
│   └── test_io.py        # IO effects
└── docs/
    ├── TUTORIAL.md
    ├── API_REFERENCE.md
    └── DESIGN_RATIONALE.md
```

## 🎓 Conceptos de FP Implementados

- ✅ **Monads**: Either, IO, Stream
- ✅ **Functors**: fmap implementation
- ✅ **Applicatives**: pure & apply
- ✅ **Pure Functions**: Sin efectos secundarios
- ✅ **Immutability**: Estructuras inmutables
- ✅ **Lazy Evaluation**: Evaluación diferida en Streams
- ✅ **Function Composition**: pipe, compose
- ✅ **Currying**: Aplicación parcial de funciones
- ✅ **Type Safety**: Type hints con generics
- ✅ **Error Handling**: Funcional con Either
- ✅ **Effect Handling**: IO Monad para side effects
- ✅ **Stream Processing**: Procesamiento de secuencias infinitas

## 🤝 Contribuir

Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/amazing`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing`)
5. Abre un Pull Request

### Guidelines

- Mantén las leyes monádicas
- Agrega tests para nuevas features
- Documenta con docstrings
- Usa type hints
- Sigue PEP 8

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

Este framework fue desarrollado como parte de un proyecto académico para explorar conceptos avanzados de programación funcional en Python.

Inspirado por:
- Haskell's Prelude
- Scala's cats/scalaz
- JavaScript's Ramda/Fantasy Land

## 📞 Contacto

- **Autor**: Alan Mora
- **GitHub**: [@AlanMora](https://github.com/AlanMora)
- **Email**: lalomora250396@gmail.com

---

**⭐ Si este proyecto te fue útil, considera darle una estrella en GitHub!**
