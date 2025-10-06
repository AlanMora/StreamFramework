from typing import TypeVar, Generic, Callable, Any
from .monad import Monad
from .either import Either

A = TypeVar('A')
B = TypeVar('B')


class IO(Monad[A], Generic[A]):
    """
    Mónada IO que encapsula operaciones de entrada/salida.

    Características:
    - Lazy evaluation (ejecución diferida)
    - Composición funcional
    - Separación entre descripción y ejecución
    """

    def __init__(self, effect: Callable[[], A]):
        """
        Args:
            effect: Función sin argumentos que produce el efecto
        """
        self._effect = effect

    def run(self) -> A:
        """
        Ejecuta el efecto IO. ¡Única función impura!

        Returns:
            Resultado de ejecutar el efecto
        """
        return self._effect()

    def unsafe_run(self) -> A:
        """Alias de run() que hace explícito que es impuro."""
        return self.run()

    def map(self, f: Callable[[A], B]) -> 'IO[B]':
        """
        Functor map: Transforma el resultado del efecto.
        """

        def new_effect():
            result = self._effect()
            return f(result)

        return IO(new_effect)

    def bind(self, f: Callable[[A], 'IO[B]']) -> 'IO[B]':
        """
        Bind monádico: Encadena operaciones IO.
        También conocido como flat_map o >>=
        """

        def new_effect():
            result = self._effect()
            next_io = f(result)
            return next_io.run()

        return IO(new_effect)

    def flat_map(self, f: Callable[[A], 'IO[B]']) -> 'IO[B]':
        """Alias de bind."""
        return self.bind(f)

    @staticmethod
    def pure(value: A) -> 'IO[A]':
        """Envuelve un valor puro en IO."""
        return IO(lambda: value)

    def attempt(self) -> 'IO[Either[Exception, A]]':
        """
        Captura excepciones y las convierte en Either.

        Returns:
            IO[Either[Exception, A]]
        """

        def effect():
            try:
                result = self._effect()
                return Either.right(result)
            except Exception as e:
                return Either.left(e)

        return IO(effect)

    def recover(self, handler: Callable[[Exception], A]) -> 'IO[A]':
        """
        Maneja errores y se recupera con un valor alternativo.
        """

        def effect():
            try:
                return self._effect()
            except Exception as e:
                return handler(e)

        return IO(effect)

    def retry(self, max_attempts: int = 3) -> 'IO[A]':
        """
        Reintenta la operación hasta max_attempts veces.
        """

        def effect():
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return self._effect()
                except Exception as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        raise e
            raise last_exception

        return IO(effect)

    @staticmethod
    def sequence(io_list: list['IO[A]']) -> 'IO[list[A]]':
        """
        Ejecuta una lista de IOs y retorna IO con lista de resultados.
        """

        def effect():
            return [io.run() for io in io_list]

        return IO(effect)

    @staticmethod
    def traverse(items: list[A], f: Callable[[A], 'IO[B]']) -> 'IO[list[B]]':
        """
        Mapea cada item a una IO y las ejecuta todas.
        """
        return IO.sequence([f(item) for item in items])

    def __repr__(self) -> str:
        return f"IO(<effect>)"


# CONSTRUCTORES DE IO COMUNES

def io_print(message: str) -> IO[None]:
    """IO que imprime un mensaje."""
    return IO(lambda: print(message))


def io_input(prompt: str = "") -> IO[str]:
    """IO que lee input del usuario."""
    return IO(lambda: input(prompt))


def io_read_file(filepath: str, encoding: str = 'utf-8') -> IO[str]:
    """IO que lee un archivo."""

    def effect():
        with open(filepath, 'r', encoding=encoding) as f:
            return f.read()

    return IO(effect)


def io_write_file(filepath: str, content: str, encoding: str = 'utf-8') -> IO[None]:
    """IO que escribe en un archivo."""

    def effect():
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)

    return IO(effect)


def io_append_file(filepath: str, content: str, encoding: str = 'utf-8') -> IO[None]:
    """IO que agrega contenido a un archivo."""

    def effect():
        with open(filepath, 'a', encoding=encoding) as f:
            f.write(content)

    return IO(effect)