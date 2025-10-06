from typing import TypeVar, Generic, Callable, Union
from .monad import Monad

A = TypeVar('A')
B = TypeVar('B')
E = TypeVar('E')


class Either(Monad[A], Generic[E, A]):
    """
    Mónada Either para manejo de errores funcional.

    Representa un valor que puede ser:
    - Left(error): Contiene un error
    - Right(value): Contiene un valor exitoso
    """

    def __init__(self, value: Union[E, A], is_right: bool):
        self._value = value
        self._is_right = is_right

    @property
    def is_right(self) -> bool:
        """Retorna True si es Right (éxito)."""
        return self._is_right

    @property
    def is_left(self) -> bool:
        """Retorna True si es Left (error)."""
        return not self._is_right

    def bind(self, f: Callable[[A], 'Either[E, B]']) -> 'Either[E, B]':
        """
        Si es Right, aplica f. Si es Left, propaga el error.
        """
        if self._is_right:
            return f(self._value)
        else:
            return Either(self._value, False)

    def map(self, f: Callable[[A], B]) -> 'Either[E, B]':
        """
        Si es Right, aplica f al valor. Si es Left, propaga el error.
        """
        if self._is_right:
            try:
                return Either(f(self._value), True)
            except Exception as e:
                return Either(e, False)
        else:
            return Either(self._value, False)

    @staticmethod
    def pure(value: A) -> 'Either[E, A]':
        """Crea un Right con el valor."""
        return Either(value, True)

    @staticmethod
    def left(error: E) -> 'Either[E, A]':
        """Crea un Left con un error."""
        return Either(error, False)

    @staticmethod
    def right(value: A) -> 'Either[E, A]':
        """Crea un Right con un valor."""
        return Either(value, True)

    def get_or_else(self, default: A) -> A:
        """Obtiene el valor o retorna un default si es Left."""
        return self._value if self._is_right else default

    def or_else(self, alternative: 'Either[E, A]') -> 'Either[E, A]':
        """Si es Left, retorna la alternativa. Si es Right, retorna self."""
        return self if self._is_right else alternative

    def recover(self, f: Callable[[E], A]) -> 'Either[E, A]':
        """
        Si es Left, aplica f al error para recuperarse.
        Si es Right, retorna self.
        """
        if self.is_left:
            try:
                return Either(f(self._value), True)
            except Exception as e:
                return Either(e, False)
        else:
            return self

    def __repr__(self) -> str:
        if self._is_right:
            return f"Right({self._value})"
        else:
            return f"Left({self._value})"