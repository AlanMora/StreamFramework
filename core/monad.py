from typing import TypeVar, Generic, Callable
from abc import ABC, abstractmethod

A = TypeVar('A')
B = TypeVar('B')


class Monad(ABC, Generic[A]):
    """
    Clase base abstracta para todas las mónadas.

    Leyes que debe cumplir toda mónada:
    1. Identidad izquierda: pure(a).bind(f) == f(a)
    2. Identidad derecha: m.bind(pure) == m
    3. Asociatividad: m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))
    """

    @abstractmethod
    def bind(self, f: Callable[[A], 'Monad[B]']) -> 'Monad[B]':
        """
        Operación fundamental de mónada (también llamada flat_map o >>=).

        Args:
            f: Función que toma un valor y devuelve una mónada

        Returns:
            Nueva mónada con la operación aplicada
        """
        pass

    @abstractmethod
    def map(self, f: Callable[[A], B]) -> 'Monad[B]':
        """
        Functor map: Aplica una función al valor encapsulado.

        Args:
            f: Función pura a aplicar

        Returns:
            Nueva mónada con el valor transformado
        """
        pass

    @staticmethod
    @abstractmethod
    def pure(value: A) -> 'Monad[A]':
        """
        Unit/Return: Envuelve un valor puro en la mónada.

        Args:
            value: Valor a envolver

        Returns:
            Mónada conteniendo el valor
        """
        pass

    def __rshift__(self, other: 'Monad[B]') -> 'Monad[B]':
        """
        Operador >> para encadenar operaciones monádicas.
        Ejecuta esta mónada, descarta el resultado, ejecuta la siguiente.
        """
        return self.bind(lambda _: other)


class Functor(ABC, Generic[A]):
    """Protocolo Functor: estructura que puede ser mapeada."""

    @abstractmethod
    def fmap(self, f: Callable[[A], B]) -> 'Functor[B]':
        """Aplica una función al contenido."""
        pass


class Applicative(Functor[A], ABC):
    """
    Protocolo Applicative: Functor que puede aplicar funciones
    encapsuladas a valores encapsulados.
    """

    @staticmethod
    @abstractmethod
    def pure(value: A) -> 'Applicative[A]':
        """Envuelve un valor puro."""
        pass

    @abstractmethod
    def apply(self, ff: 'Applicative[Callable[[A], B]]') -> 'Applicative[B]':
        """
        Aplica una función encapsulada a un valor encapsulado.

        Args:
            ff: Applicative conteniendo una función

        Returns:
            Applicative con el resultado
        """
        pass