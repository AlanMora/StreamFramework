from typing import TypeVar, Generic, Callable, Iterator, Iterable
from .monad import Monad
from .io_monad import IO
from .either import Either
import itertools

A = TypeVar('A')
B = TypeVar('B')


class Stream(Monad[A], Generic[A]):
    """
    Mónada Stream para procesamiento lazy de secuencias.

    Características:
    - Evaluación perezosa (lazy)
    - Composición funcional
    - Manejo de streams infinitos
    """

    def __init__(self, source: Callable[[], Iterator[A]]):
        """
        Args:
            source: Función que produce un iterador
        """
        self._source = source

    def __iter__(self) -> Iterator[A]:
        """Permite iterar sobre el stream."""
        return self._source()

    def map(self, f: Callable[[A], B]) -> 'Stream[B]':
        """Transforma cada elemento del stream."""

        def new_source():
            return map(f, self._source())

        return Stream(new_source)

    def bind(self, f: Callable[[A], 'Stream[B]']) -> 'Stream[B]':
        """Flat map sobre el stream."""

        def new_source():
            for item in self._source():
                for sub_item in f(item):
                    yield sub_item

        return Stream(new_source)

    def flat_map(self, f: Callable[[A], 'Stream[B]']) -> 'Stream[B]':
        """Alias de bind."""
        return self.bind(f)

    @staticmethod
    def pure(value: A) -> 'Stream[A]':
        """Crea un stream con un solo elemento."""
        return Stream(lambda: iter([value]))

    @staticmethod
    def of(*values: A) -> 'Stream[A]':
        """Crea un stream de múltiples valores."""
        return Stream(lambda: iter(values))

    @staticmethod
    def from_iterable(iterable: Iterable[A]) -> 'Stream[A]':
        """Crea un stream desde un iterable."""
        return Stream(lambda: iter(iterable))

    @staticmethod
    def range(start: int, stop: int = None, step: int = 1) -> 'Stream[int]':
        """Crea un stream de números."""
        if stop is None:
            return Stream(lambda: itertools.count(start, step))
        else:
            return Stream(lambda: iter(range(start, stop, step)))

    @staticmethod
    def repeat(value: A, times: int = None) -> 'Stream[A]':
        """Repite un valor times veces (infinito si times=None)."""
        if times is None:
            return Stream(lambda: itertools.repeat(value))
        else:
            return Stream(lambda: itertools.repeat(value, times))

    # ==========================================
    # OPERACIONES DE TRANSFORMACIÓN
    # ==========================================

    def filter(self, predicate: Callable[[A], bool]) -> 'Stream[A]':
        """Filtra elementos según un predicado."""

        def new_source():
            return filter(predicate, self._source())

        return Stream(new_source)

    def take(self, n: int) -> 'Stream[A]':
        """Toma los primeros n elementos."""

        def new_source():
            return itertools.islice(self._source(), n)

        return Stream(new_source)

    def skip(self, n: int) -> 'Stream[A]':
        """Salta los primeros n elementos."""

        def new_source():
            it = self._source()
            for _ in range(n):
                next(it, None)
            return it

        return Stream(new_source)

    def take_while(self, predicate: Callable[[A], bool]) -> 'Stream[A]':
        """Toma elementos mientras el predicado sea True."""

        def new_source():
            return itertools.takewhile(predicate, self._source())

        return Stream(new_source)

    def drop_while(self, predicate: Callable[[A], bool]) -> 'Stream[A]':
        """Descarta elementos mientras el predicado sea True."""

        def new_source():
            return itertools.dropwhile(predicate, self._source())

        return Stream(new_source)

    def distinct(self) -> 'Stream[A]':
        """Elimina duplicados consecutivos."""

        def new_source():
            seen = set()
            for item in self._source():
                if item not in seen:
                    seen.add(item)
                    yield item

        return Stream(new_source)

    def chunk(self, size: int) -> 'Stream[list[A]]':
        """Agrupa elementos en chunks de tamaño size."""

        def new_source():
            it = self._source()
            while True:
                chunk = list(itertools.islice(it, size))
                if not chunk:
                    break
                yield chunk

        return Stream(new_source)

    # ==========================================
    # OPERACIONES TERMINALES
    # ==========================================

    def reduce(self, f: Callable[[B, A], B], initial: B) -> B:
        """Reduce el stream a un valor único."""
        result = initial
        for item in self._source():
            result = f(result, item)
        return result

    def fold_left(self, f: Callable[[B, A], B], initial: B) -> B:
        """Alias de reduce."""
        return self.reduce(f, initial)

    def to_list(self) -> list[A]:
        """Materializa el stream en una lista."""
        return list(self._source())

    def count(self) -> int:
        """Cuenta los elementos del stream."""
        return sum(1 for _ in self._source())

    def for_each(self, f: Callable[[A], None]) -> None:
        """Ejecuta una función por cada elemento (efecto secundario)."""
        for item in self._source():
            f(item)

    def find(self, predicate: Callable[[A], bool]) -> Either[str, A]:
        """Encuentra el primer elemento que cumple el predicado."""
        for item in self._source():
            if predicate(item):
                return Either.right(item)
        return Either.left("No element found")

    def exists(self, predicate: Callable[[A], bool]) -> bool:
        """Verifica si existe algún elemento que cumple el predicado."""
        return any(predicate(item) for item in self._source())

    def all(self, predicate: Callable[[A], bool]) -> bool:
        """Verifica si todos los elementos cumplen el predicado."""
        return all(predicate(item) for item in self._source())

    # ==========================================
    # COMBINADORES
    # ==========================================

    def zip(self, other: 'Stream[B]') -> 'Stream[tuple[A, B]]':
        """Combina dos streams en tuplas."""

        def new_source():
            return zip(self._source(), other._source())

        return Stream(new_source)

    def concat(self, other: 'Stream[A]') -> 'Stream[A]':
        """Concatena dos streams."""

        def new_source():
            return itertools.chain(self._source(), other._source())

        return Stream(new_source)

    def flatten(self: 'Stream[Iterable[B]]') -> 'Stream[B]':
        """Aplana un stream de iterables."""

        def new_source():
            for items in self._source():
                for item in items:
                    yield item

        return Stream(new_source)

    def __repr__(self) -> str:
        return "Stream(<lazy>)"