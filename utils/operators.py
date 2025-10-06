"""
Operadores funcionales y utilidades de composición.

Proporciona funciones de alto nivel para trabajar con programación funcional,
incluyendo composición, currying, y operadores de transformación.
"""

from typing import TypeVar, Callable, Any, Iterable
from functools import reduce, wraps
import operator as op

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')


# COMPOSICIÓN DE FUNCIONES

def compose(*functions: Callable) -> Callable:
    """
    Compone funciones de derecha a izquierda.

    compose(f, g, h)(x) == f(g(h(x)))

    Example:
        >>> add1 = lambda x: x + 1
        >>> mult2 = lambda x: x * 2
        >>> f = compose(add1, mult2)
        >>> f(5)  # (5 * 2) + 1
        11
    """
    def composed(x):
        return reduce(lambda acc, f: f(acc), reversed(functions), x)
    return composed


def pipe(*functions: Callable) -> Callable:
    """
    Compone funciones de izquierda a derecha.

    pipe(f, g, h)(x) == h(g(f(x)))

    Example:
        >>> add1 = lambda x: x + 1
        >>> mult2 = lambda x: x * 2
        >>> f = pipe(add1, mult2)
        >>> f(5)  # (5 + 1) * 2
        12
    """
    def piped(x):
        return reduce(lambda acc, f: f(acc), functions, x)
    return piped


# CURRYING Y APLICACIÓN PARCIAL

def curry(f: Callable) -> Callable:
    """
    Convierte una función de múltiples argumentos en una cadena de funciones
    de un argumento.

    Example:
        >>> @curry
        ... def add(x, y, z):
        ...     return x + y + z
        >>> add(1)(2)(3)
        6
        >>> add_10 = add(10)
        >>> add_10(5)(3)
        18
    """
    @wraps(f)
    def curried(*args, **kwargs):
        if len(args) + len(kwargs) >= f.__code__.co_argcount:
            return f(*args, **kwargs)
        return lambda *more_args, **more_kwargs: curried(
            *(args + more_args),
            **{**kwargs, **more_kwargs}
        )
    return curried


def partial(f: Callable, *args, **kwargs) -> Callable:
    """
    Aplicación parcial de argumentos a una función.

    Example:
        >>> def greet(greeting, name):
        ...     return f"{greeting}, {name}!"
        >>> say_hello = partial(greet, "Hello")
        >>> say_hello("World")
        'Hello, World!'
    """
    def wrapper(*more_args, **more_kwargs):
        return f(*args, *more_args, **{**kwargs, **more_kwargs})
    return wrapper


# TRANSFORMACIONES DE LISTAS

@curry
def fmap(f: Callable[[A], B], items: Iterable[A]) -> list[B]:
    """
    Map funcional (curried).

    Example:
        >>> fmap(lambda x: x * 2, [1, 2, 3])
        [2, 4, 6]
        >>> double = fmap(lambda x: x * 2)
        >>> double([1, 2, 3])
        [2, 4, 6]
    """
    return list(map(f, items))


@curry
def ffilter(predicate: Callable[[A], bool], items: Iterable[A]) -> list[A]:
    """
    Filter funcional (curried).

    Example:
        >>> ffilter(lambda x: x > 2, [1, 2, 3, 4])
        [3, 4]
        >>> greater_than_2 = ffilter(lambda x: x > 2)
        >>> greater_than_2([1, 2, 3, 4])
        [3, 4]
    """
    return list(filter(predicate, items))


@curry
def freduce(f: Callable[[B, A], B], initial: B, items: Iterable[A]) -> B:
    """
    Reduce funcional (curried).

    Example:
        >>> freduce(lambda acc, x: acc + x, 0, [1, 2, 3, 4])
        10
        >>> sum_all = freduce(lambda acc, x: acc + x, 0)
        >>> sum_all([1, 2, 3, 4])
        10
    """
    return reduce(f, items, initial)


def flatten(items: Iterable[Iterable[A]]) -> list[A]:
    """
    Aplana una lista de listas.

    Example:
        >>> flatten([[1, 2], [3, 4], [5]])
        [1, 2, 3, 4, 5]
    """
    return [item for sublist in items for item in sublist]


def flat_map(f: Callable[[A], Iterable[B]], items: Iterable[A]) -> list[B]:
    """
    Map seguido de flatten.

    Example:
        >>> flat_map(lambda x: [x, x * 2], [1, 2, 3])
        [1, 2, 2, 4, 3, 6]
    """
    return flatten(map(f, items))


# OPERADORES MATEMÁTICOS FUNCIONALES

@curry
def add(x: int, y: int) -> int:
    """Suma curried."""
    return x + y


@curry
def subtract(x: int, y: int) -> int:
    """Resta curried."""
    return x - y


@curry
def multiply(x: int, y: int) -> int:
    """Multiplicación curried."""
    return x * y


@curry
def divide(x: float, y: float) -> float:
    """División curried."""
    return x / y


@curry
def power(x: float, y: float) -> float:
    """Potencia curried."""
    return x ** y


@curry
def modulo(x: int, y: int) -> int:
    """Módulo curried."""
    return x % y


# OPERADORES DE COMPARACIÓN

@curry
def equals(x: Any, y: Any) -> bool:
    """Igualdad curried."""
    return x == y


@curry
def not_equals(x: Any, y: Any) -> bool:
    """Desigualdad curried."""
    return x != y


@curry
def greater_than(x: Any, y: Any) -> bool:
    """Mayor que curried."""
    return x > y


@curry
def less_than(x: Any, y: Any) -> bool:
    """Menor que curried."""
    return x < y


@curry
def greater_or_equal(x: Any, y: Any) -> bool:
    """Mayor o igual curried."""
    return x >= y


@curry
def less_or_equal(x: Any, y: Any) -> bool:
    """Menor o igual curried."""
    return x <= y


# UTILIDADES

def identity(x: A) -> A:
    """
    Función identidad.

    Example:
        >>> identity(5)
        5
    """
    return x


def const(x: A) -> Callable[[Any], A]:
    """
    Retorna una función que siempre devuelve x.

    Example:
        >>> always_5 = const(5)
        >>> always_5(1)
        5
        >>> always_5("anything")
        5
    """
    return lambda _: x


def flip(f: Callable[[A, B], C]) -> Callable[[B, A], C]:
    """
    Invierte el orden de los argumentos de una función binaria.

    Example:
        >>> def divide(x, y):
        ...     return x / y
        >>> flipped_divide = flip(divide)
        >>> flipped_divide(2, 10)  # 10 / 2
        5.0
    """
    @wraps(f)
    def flipped(b: B, a: A) -> C:
        return f(a, b)
    return flipped


def tap(f: Callable[[A], Any]) -> Callable[[A], A]:
    """
    Ejecuta un efecto secundario pero retorna el valor original.
    Útil para debugging en pipelines.

    Example:
        >>> result = pipe(
        ...     lambda x: x * 2,
        ...     tap(lambda x: print(f"Debug: {x}")),
        ...     lambda x: x + 1
        ... )(5)
        Debug: 10
        >>> result
        11
    """
    def tapped(x: A) -> A:
        f(x)
        return x
    return tapped


def memoize(f: Callable) -> Callable:
    """
    Memoiza una función (cachea resultados).

    Example:
        >>> @memoize
        ... def expensive_computation(n):
        ...     print(f"Computing for {n}")
        ...     return n * n
        >>> expensive_computation(5)
        Computing for 5
        25
        >>> expensive_computation(5)  # No recomputa
        25
    """
    cache = {}

    @wraps(f)
    def memoized(*args):
        if args not in cache:
            cache[args] = f(*args)
        return cache[args]

    return memoized


# PREDICADOS COMUNES

def is_even(x: int) -> bool:
    """Verifica si un número es par."""
    return x % 2 == 0


def is_odd(x: int) -> bool:
    """Verifica si un número es impar."""
    return x % 2 != 0


def is_positive(x: float) -> bool:
    """Verifica si un número es positivo."""
    return x > 0


def is_negative(x: float) -> bool:
    """Verifica si un número es negativo."""
    return x < 0


def is_zero(x: float) -> bool:
    """Verifica si un número es cero."""
    return x == 0


def is_empty(x: Iterable) -> bool:
    """Verifica si un iterable está vacío."""
    try:
        return len(x) == 0
    except TypeError:
        return not any(True for _ in x)


def is_none(x: Any) -> bool:
    """Verifica si un valor es None."""
    return x is None


def is_not_none(x: Any) -> bool:
    """Verifica si un valor no es None."""
    return x is not None
