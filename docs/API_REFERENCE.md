# 📖 API Reference

Referencia completa de todas las clases, métodos y funciones del framework.

## Tabla de Contenidos

- [Core Monads](#core-monads)
  - [Either](#either)
  - [IO](#io)
  - [Stream](#stream)
- [Utility Functions](#utility-functions)
- [HTTP Integration](#http-integration)

---

## Core Monads

### Either

`Either[E, A]` - Mónada para manejo de errores funcional.

#### Constructores

```python
Either.left(error: E) -> Either[E, A]
```
Crea un Either con un error (Left).

**Parámetros:**
- `error`: El error a encapsular

**Retorna:** `Either[E, A]` en estado Left

**Ejemplo:**
```python
Either.left("Error de validación")  # Left('Error de validación')
```

---

```python
Either.right(value: A) -> Either[E, A]
```
Crea un Either con un valor exitoso (Right).

**Parámetros:**
- `value`: El valor a encapsular

**Retorna:** `Either[E, A]` en estado Right

**Ejemplo:**
```python
Either.right(42)  # Right(42)
```

---

```python
Either.pure(value: A) -> Either[E, A]
```
Envuelve un valor puro (equivalente a `right`).

**Parámetros:**
- `value`: El valor a envolver

**Retorna:** `Either[E, A]` en estado Right

**Ejemplo:**
```python
Either.pure(42)  # Right(42)
```

#### Métodos de Instancia

```python
.map(f: Callable[[A], B]) -> Either[E, B]
```
Transforma el valor si es Right. Si es Left, propaga el error.

**Parámetros:**
- `f`: Función de transformación

**Retorna:** Nuevo Either con el valor transformado

**Ejemplo:**
```python
Either.right(5).map(lambda x: x * 2)  # Right(10)
Either.left("error").map(lambda x: x * 2)  # Left('error')
```

---

```python
.bind(f: Callable[[A], Either[E, B]]) -> Either[E, B]
```
Encadena operaciones que retornan Either (flat_map).

**Parámetros:**
- `f`: Función que retorna Either

**Retorna:** Either resultante de aplicar la función

**Ejemplo:**
```python
def divide(x, y):
    return Either.right(x / y) if y != 0 else Either.left("div/0")

Either.right(10).bind(lambda x: divide(x, 2))  # Right(5.0)
Either.right(10).bind(lambda x: divide(x, 0))  # Left('div/0')
```

---

```python
.get_or_else(default: A) -> A
```
Obtiene el valor o retorna un valor por defecto si es Left.

**Parámetros:**
- `default`: Valor por defecto

**Retorna:** El valor encapsulado o el default

**Ejemplo:**
```python
Either.right(42).get_or_else(0)  # 42
Either.left("error").get_or_else(0)  # 0
```

---

```python
.or_else(alternative: Either[E, A]) -> Either[E, A]
```
Retorna este Either si es Right, o la alternativa si es Left.

**Parámetros:**
- `alternative`: Either alternativo

**Retorna:** Este Either o la alternativa

**Ejemplo:**
```python
Either.right(42).or_else(Either.right(0))  # Right(42)
Either.left("error").or_else(Either.right(0))  # Right(0)
```

---

```python
.recover(f: Callable[[E], A]) -> Either[E, A]
```
Recupera de un error transformándolo en valor exitoso.

**Parámetros:**
- `f`: Función de recuperación

**Retorna:** Either con el valor recuperado o el original

**Ejemplo:**
```python
Either.left("error").recover(lambda e: f"Recovered: {e}")
# Right('Recovered: error')
```

#### Propiedades

```python
.is_right -> bool
```
Retorna True si es Right (éxito).

```python
.is_left -> bool
```
Retorna True si es Left (error).

---

### IO

`IO[A]` - Mónada para encapsular efectos de entrada/salida.

#### Constructores

```python
IO(effect: Callable[[], A])
```
Crea una IO a partir de una función sin argumentos.

**Parámetros:**
- `effect`: Función que produce el efecto

**Ejemplo:**
```python
IO(lambda: print("Hello"))
```

---

```python
IO.pure(value: A) -> IO[A]
```
Envuelve un valor puro en IO.

**Parámetros:**
- `value`: Valor a envolver

**Retorna:** IO que retorna el valor

**Ejemplo:**
```python
IO.pure(42).run()  # 42
```

#### Métodos de Instancia

```python
.run() -> A
```
Ejecuta el efecto encapsulado. **¡Única función impura!**

**Retorna:** Resultado de ejecutar el efecto

**Ejemplo:**
```python
io = IO.pure(42)
result = io.run()  # 42
```

---

```python
.unsafe_run() -> A
```
Alias de `run()` que hace explícito que es impuro.

---

```python
.map(f: Callable[[A], B]) -> IO[B]
```
Transforma el resultado del efecto.

**Parámetros:**
- `f`: Función de transformación

**Retorna:** Nueva IO con el resultado transformado

**Ejemplo:**
```python
IO.pure(5).map(lambda x: x * 2).run()  # 10
```

---

```python
.bind(f: Callable[[A], IO[B]]) -> IO[B]
```
Encadena operaciones IO (flat_map).

**Parámetros:**
- `f`: Función que retorna IO

**Retorna:** IO resultante

**Ejemplo:**
```python
IO.pure(5).bind(lambda x: IO.pure(x * 2)).run()  # 10
```

---

```python
.attempt() -> IO[Either[Exception, A]]
```
Captura excepciones y las convierte en Either.

**Retorna:** IO que retorna Either

**Ejemplo:**
```python
def fails():
    raise ValueError("Error")

IO(fails).attempt().run()  # Left(ValueError('Error'))
```

---

```python
.recover(handler: Callable[[Exception], A]) -> IO[A]
```
Maneja errores y se recupera con valor alternativo.

**Parámetros:**
- `handler`: Función manejadora de errores

**Retorna:** IO que no lanza excepciones

**Ejemplo:**
```python
def fails():
    raise ValueError("Error")

IO(fails).recover(lambda e: 0).run()  # 0
```

---

```python
.retry(max_attempts: int = 3) -> IO[A]
```
Reintenta la operación hasta max_attempts veces.

**Parámetros:**
- `max_attempts`: Número máximo de intentos

**Retorna:** IO que reintenta en caso de fallo

**Ejemplo:**
```python
attempts = [0]
def flaky():
    attempts[0] += 1
    if attempts[0] < 3:
        raise ValueError("Fail")
    return "Success"

IO(flaky).retry(max_attempts=5).run()  # "Success"
```

#### Métodos Estáticos

```python
IO.sequence(io_list: list[IO[A]]) -> IO[list[A]]
```
Ejecuta una lista de IOs y retorna IO con lista de resultados.

**Parámetros:**
- `io_list`: Lista de IOs

**Retorna:** IO que retorna lista de resultados

**Ejemplo:**
```python
ios = [IO.pure(1), IO.pure(2), IO.pure(3)]
IO.sequence(ios).run()  # [1, 2, 3]
```

---

```python
IO.traverse(items: list[A], f: Callable[[A], IO[B]]) -> IO[list[B]]
```
Mapea cada item a una IO y las ejecuta todas.

**Parámetros:**
- `items`: Lista de items
- `f`: Función que crea IO para cada item

**Retorna:** IO que retorna lista de resultados

**Ejemplo:**
```python
IO.traverse([1, 2, 3], lambda x: IO.pure(x * 2)).run()  # [2, 4, 6]
```

#### Helpers de IO

```python
io_print(message: str) -> IO[None]
```
IO que imprime un mensaje.

---

```python
io_input(prompt: str = "") -> IO[str]
```
IO que lee input del usuario.

---

```python
io_read_file(filepath: str, encoding: str = 'utf-8') -> IO[str]
```
IO que lee un archivo.

---

```python
io_write_file(filepath: str, content: str, encoding: str = 'utf-8') -> IO[None]
```
IO que escribe en un archivo.

---

```python
io_append_file(filepath: str, content: str, encoding: str = 'utf-8') -> IO[None]
```
IO que agrega contenido a un archivo.

---

### Stream

`Stream[A]` - Mónada para procesamiento lazy de secuencias.

#### Constructores

```python
Stream.pure(value: A) -> Stream[A]
```
Crea un stream con un solo elemento.

**Ejemplo:**
```python
Stream.pure(42).to_list()  # [42]
```

---

```python
Stream.of(*values: A) -> Stream[A]
```
Crea un stream de múltiples valores.

**Ejemplo:**
```python
Stream.of(1, 2, 3).to_list()  # [1, 2, 3]
```

---

```python
Stream.from_iterable(iterable: Iterable[A]) -> Stream[A]
```
Crea un stream desde un iterable.

**Ejemplo:**
```python
Stream.from_iterable([1, 2, 3]).to_list()  # [1, 2, 3]
```

---

```python
Stream.range(start: int, stop: int = None, step: int = 1) -> Stream[int]
```
Crea un stream de números.

**Parámetros:**
- `start`: Inicio
- `stop`: Fin (None = infinito)
- `step`: Paso

**Ejemplo:**
```python
Stream.range(0, 5).to_list()  # [0, 1, 2, 3, 4]
Stream.range(0).take(5).to_list()  # [0, 1, 2, 3, 4] (infinito)
```

---

```python
Stream.repeat(value: A, times: int = None) -> Stream[A]
```
Repite un valor times veces (infinito si times=None).

**Ejemplo:**
```python
Stream.repeat("x", 3).to_list()  # ['x', 'x', 'x']
Stream.repeat("x").take(3).to_list()  # ['x', 'x', 'x']
```

#### Transformaciones

```python
.map(f: Callable[[A], B]) -> Stream[B]
```
Transforma cada elemento del stream.

**Ejemplo:**
```python
Stream.of(1, 2, 3).map(lambda x: x * 2).to_list()  # [2, 4, 6]
```

---

```python
.filter(predicate: Callable[[A], bool]) -> Stream[A]
```
Filtra elementos según predicado.

**Ejemplo:**
```python
Stream.of(1, 2, 3, 4).filter(lambda x: x % 2 == 0).to_list()  # [2, 4]
```

---

```python
.bind(f: Callable[[A], Stream[B]]) -> Stream[B]
```
Flat map sobre el stream.

**Ejemplo:**
```python
Stream.of(1, 2).bind(lambda x: Stream.of(x, x*2)).to_list()
# [1, 2, 2, 4]
```

---

```python
.flat_map(f: Callable[[A], Stream[B]]) -> Stream[B]
```
Alias de bind.

---

```python
.take(n: int) -> Stream[A]
```
Toma los primeros n elementos.

**Ejemplo:**
```python
Stream.range(0).take(5).to_list()  # [0, 1, 2, 3, 4]
```

---

```python
.skip(n: int) -> Stream[A]
```
Salta los primeros n elementos.

**Ejemplo:**
```python
Stream.of(1, 2, 3, 4, 5).skip(2).to_list()  # [3, 4, 5]
```

---

```python
.take_while(predicate: Callable[[A], bool]) -> Stream[A]
```
Toma elementos mientras el predicado sea True.

**Ejemplo:**
```python
Stream.of(1, 2, 3, 4).take_while(lambda x: x < 3).to_list()  # [1, 2]
```

---

```python
.drop_while(predicate: Callable[[A], bool]) -> Stream[A]
```
Descarta elementos mientras el predicado sea True.

**Ejemplo:**
```python
Stream.of(1, 2, 3, 4).drop_while(lambda x: x < 3).to_list()  # [3, 4]
```

---

```python
.distinct() -> Stream[A]
```
Elimina duplicados.

**Ejemplo:**
```python
Stream.of(1, 2, 2, 3, 3).distinct().to_list()  # [1, 2, 3]
```

---

```python
.chunk(size: int) -> Stream[list[A]]
```
Agrupa elementos en chunks de tamaño size.

**Ejemplo:**
```python
Stream.of(1, 2, 3, 4, 5).chunk(2).to_list()  # [[1, 2], [3, 4], [5]]
```

#### Operaciones Terminales

```python
.to_list() -> list[A]
```
Materializa el stream en una lista.

---

```python
.count() -> int
```
Cuenta los elementos del stream.

---

```python
.reduce(f: Callable[[B, A], B], initial: B) -> B
```
Reduce el stream a un valor único.

**Ejemplo:**
```python
Stream.of(1, 2, 3, 4).reduce(lambda acc, x: acc + x, 0)  # 10
```

---

```python
.fold_left(f: Callable[[B, A], B], initial: B) -> B
```
Alias de reduce.

---

```python
.for_each(f: Callable[[A], None]) -> None
```
Ejecuta una función por cada elemento (efecto secundario).

---

```python
.find(predicate: Callable[[A], bool]) -> Either[str, A]
```
Encuentra el primer elemento que cumple el predicado.

**Ejemplo:**
```python
Stream.of(1, 2, 3, 4).find(lambda x: x > 2)  # Right(3)
```

---

```python
.exists(predicate: Callable[[A], bool]) -> bool
```
Verifica si existe algún elemento que cumple el predicado.

---

```python
.all(predicate: Callable[[A], bool]) -> bool
```
Verifica si todos los elementos cumplen el predicado.

#### Combinadores

```python
.zip(other: Stream[B]) -> Stream[tuple[A, B]]
```
Combina dos streams en tuplas.

**Ejemplo:**
```python
s1 = Stream.of(1, 2, 3)
s2 = Stream.of('a', 'b', 'c')
s1.zip(s2).to_list()  # [(1, 'a'), (2, 'b'), (3, 'c')]
```

---

```python
.concat(other: Stream[A]) -> Stream[A]
```
Concatena dos streams.

**Ejemplo:**
```python
Stream.of(1, 2).concat(Stream.of(3, 4)).to_list()  # [1, 2, 3, 4]
```

---

```python
.flatten() -> Stream[B]
```
Aplana un stream de iterables.

**Ejemplo:**
```python
Stream.of([1, 2], [3, 4]).flatten().to_list()  # [1, 2, 3, 4]
```

---

## Utility Functions

### Composición

```python
compose(*functions) -> Callable
```
Compone funciones de derecha a izquierda.

**Ejemplo:**
```python
f = compose(lambda x: x + 1, lambda x: x * 2)
f(5)  # (5 * 2) + 1 = 11
```

---

```python
pipe(*functions) -> Callable
```
Compone funciones de izquierda a derecha.

**Ejemplo:**
```python
f = pipe(lambda x: x * 2, lambda x: x + 1)
f(5)  # (5 * 2) + 1 = 11
```

### Currying

```python
@curry
def function(a, b, c):
    ...
```
Decorator que convierte función en curried.

**Ejemplo:**
```python
@curry
def add(a, b, c):
    return a + b + c

add(1)(2)(3)  # 6
```

---

```python
partial(f, *args, **kwargs) -> Callable
```
Aplicación parcial de argumentos.

### Transformaciones

```python
fmap(f: Callable[[A], B], items: Iterable[A]) -> list[B]
```
Map funcional (curried).

---

```python
ffilter(predicate: Callable[[A], bool], items: Iterable[A]) -> list[A]
```
Filter funcional (curried).

---

```python
freduce(f: Callable[[B, A], B], initial: B, items: Iterable[A]) -> B
```
Reduce funcional (curried).

---

```python
flatten(items: Iterable[Iterable[A]]) -> list[A]
```
Aplana una lista de listas.

---

```python
flat_map(f: Callable[[A], Iterable[B]], items: Iterable[A]) -> list[B]
```
Map seguido de flatten.

### Operadores Matemáticos (Curried)

- `add(x)(y)` - Suma
- `subtract(x)(y)` - Resta
- `multiply(x)(y)` - Multiplicación
- `divide(x)(y)` - División
- `power(x)(y)` - Potencia
- `modulo(x)(y)` - Módulo

### Comparadores (Curried)

- `equals(x)(y)` - Igualdad
- `not_equals(x)(y)` - Desigualdad
- `greater_than(x)(y)` - Mayor que
- `less_than(x)(y)` - Menor que
- `greater_or_equal(x)(y)` - Mayor o igual
- `less_or_equal(x)(y)` - Menor o igual

### Predicados

- `is_even(x)` - Es par
- `is_odd(x)` - Es impar
- `is_positive(x)` - Es positivo
- `is_negative(x)` - Es negativo
- `is_zero(x)` - Es cero
- `is_empty(x)` - Está vacío
- `is_none(x)` - Es None
- `is_not_none(x)` - No es None

### Utilidades

```python
identity(x) -> x
```
Función identidad.

---

```python
const(x) -> Callable
```
Retorna función que siempre devuelve x.

---

```python
flip(f) -> Callable
```
Invierte el orden de argumentos de función binaria.

---

```python
tap(f) -> Callable
```
Ejecuta efecto secundario pero retorna valor original.

---

```python
memoize(f) -> Callable
```
Cachea resultados de función.

---

## HTTP Integration

Ver `core/http_stream.py` para detalles completos de HTTP integration.

```python
http_get(url: str, **kwargs) -> IO[Either[Exception, HttpResponse]]
```
IO para petición GET.

---

```python
http_post(url: str, body: Any = None, **kwargs) -> IO[Either[Exception, HttpResponse]]
```
IO para petición POST.

---

Para más ejemplos de uso, ver [TUTORIAL.md](TUTORIAL.md) y [EXAMPLES.md](EXAMPLES.md).
