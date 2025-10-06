"""
Suite completa de tests para el framework.
"""

import pytest
from core.monad import Monad
from core.io_monad import IO, io_print, io_read_file, io_write_file
from core.either import Either
from core.stream import Stream
from core.http_stream import HttpStream, fetch_json, HttpRequest, HttpMethod
import tempfile
import os


# ==========================================
# TESTS DE MONAD BASE
# ==========================================

class TestMonadLaws:
    """Verifica que todas las mónadas cumplen las leyes monádicas."""

    def test_io_left_identity(self):
        """Left identity: pure(a).bind(f) == f(a)"""
        a = 42
        f = lambda x: IO.pure(x * 2)

        left = IO.pure(a).bind(f).run()
        right = f(a).run()

        assert left == right

    def test_io_right_identity(self):
        """Right identity: m.bind(pure) == m"""
        m = IO.pure(100)

        left = m.bind(IO.pure).run()
        right = m.run()

        assert left == right

    def test_io_associativity(self):
        """Associativity: m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))"""
        m = IO.pure(5)
        f = lambda x: IO.pure(x + 3)
        g = lambda x: IO.pure(x * 2)

        left = m.bind(f).bind(g).run()
        right = m.bind(lambda x: f(x).bind(g)).run()

        assert left == right

    def test_either_left_identity(self):
        """Either Left identity"""
        a = 42
        f = lambda x: Either.right(x * 2)

        left = Either.pure(a).bind(f)
        right = f(a)

        assert left._value == right._value

    def test_stream_functor_identity(self):
        """Functor identity: fmap(id) == id"""
        stream = Stream.of(1, 2, 3)
        identity = lambda x: x

        result = stream.map(identity).to_list()
        expected = stream.to_list()

        assert result == expected

    def test_stream_functor_composition(self):
        """Functor composition: fmap(f . g) == fmap(f) . fmap(g)"""
        stream = Stream.of(1, 2, 3)
        f = lambda x: x + 1
        g = lambda x: x * 2

        # fmap(f . g)
        left = stream.map(lambda x: f(g(x))).to_list()

        # fmap(f) . fmap(g)
        right = stream.map(g).map(f).to_list()

        assert left == right


# ==========================================
# TESTS DE IO MONAD
# ==========================================

class TestIOMonad:
    """Tests para IO Monad."""

    def test_io_pure(self):
        """Test IO.pure"""
        value = 42
        io = IO.pure(value)
        assert io.run() == value

    def test_io_map(self):
        """Test IO.map"""
        io = IO.pure(5)
        result = io.map(lambda x: x * 2).run()
        assert result == 10

    def test_io_bind(self):
        """Test IO.bind"""
        io = IO.pure(5)
        result = io.bind(lambda x: IO.pure(x + 3)).run()
        assert result == 8

    def test_io_composition(self):
        """Test composición de múltiples operaciones IO"""
        program = (
            IO.pure(10)
            .map(lambda x: x + 5)
            .bind(lambda x: IO.pure(x * 2))
            .map(lambda x: x - 10)
        )

        assert program.run() == 20

    def test_io_sequence(self):
        """Test IO.sequence"""
        ios = [IO.pure(1), IO.pure(2), IO.pure(3)]
        result = IO.sequence(ios).run()
        assert result == [1, 2, 3]

    def test_io_traverse(self):
        """Test IO.traverse"""
        items = [1, 2, 3]
        f = lambda x: IO.pure(x * 2)
        result = IO.traverse(items, f).run()
        assert result == [2, 4, 6]

    def test_io_file_operations(self):
        """Test operaciones de archivo con IO"""
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name

        try:
            # Pipeline de escritura y lectura
            content = "Hello, IO Monad!"

            program = (
                    io_write_file(temp_path, content)
                    >> io_read_file(temp_path)
            )

            result = program.run()
            assert result == content

        finally:
            # Limpiar
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_io_attempt(self):
        """Test IO.attempt para manejo de errores"""
        # IO que falla
        io_fail = IO(lambda: 1 / 0)
        result = io_fail.attempt().run()

        assert result.is_left
        assert isinstance(result._value, ZeroDivisionError)

        # IO que tiene éxito
        io_success = IO.pure(42)
        result = io_success.attempt().run()

        assert result.is_right
        assert result._value == 42

    def test_io_recover(self):
        """Test IO.recover"""
        io_fail = IO(lambda: 1 / 0)
        result = io_fail.recover(lambda e: 0).run()

        assert result == 0

    def test_io_retry(self):
        """Test IO.retry"""
        counter = {'attempts': 0}

        def flaky_operation():
            counter['attempts'] += 1
            if counter['attempts'] < 3:
                raise ValueError("Fail")
            return "Success"

        io = IO(flaky_operation)
        result = io.retry(max_attempts=3).run()

        assert result == "Success"
        assert counter['attempts'] == 3

    def test_io_lazy_evaluation(self):
        """Verifica que IO no ejecuta hasta .run()"""
        executed = {'flag': False}

        def effect():
            executed['flag'] = True
            return 42

        io = IO(effect)

        # No debe ejecutarse todavía
        assert executed['flag'] is False

        # Ejecutar
        io.run()
        assert executed['flag'] is True


# ==========================================
# TESTS DE EITHER MONAD
# ==========================================

class TestEitherMonad:
    """Tests para Either Monad."""

    def test_either_right(self):
        """Test Either.right"""
        either = Either.right(42)
        assert either.is_right
        assert either._value == 42

    def test_either_left(self):
        """Test Either.left"""
        either = Either.left("Error")
        assert either.is_left
        assert either._value == "Error"

    def test_either_map_right(self):
        """Test map en Right"""
        either = Either.right(5)
        result = either.map(lambda x: x * 2)

        assert result.is_right
        assert result._value == 10

    def test_either_map_left(self):
        """Test map en Left (propaga error)"""
        either = Either.left("Error")
        result = either.map(lambda x: x * 2)

        assert result.is_left
        assert result._value == "Error"

    def test_either_bind_right(self):
        """Test bind en Right"""
        either = Either.right(5)
        result = either.bind(lambda x: Either.right(x + 3))

        assert result.is_right
        assert result._value == 8

    def test_either_bind_left(self):
        """Test bind en Left (propaga error)"""
        either = Either.left("Error")
        result = either.bind(lambda x: Either.right(x + 3))

        assert result.is_left
        assert result._value == "Error"

    def test_either_get_or_else(self):
        """Test get_or_else"""
        right = Either.right(42)
        left = Either.left("Error")

        assert right.get_or_else(0) == 42
        assert left.get_or_else(0) == 0

    def test_either_or_else(self):
        """Test or_else"""
        right = Either.right(42)
        left = Either.left("Error")
        alternative = Either.right(100)

        assert right.or_else(alternative)._value == 42
        assert left.or_else(alternative)._value == 100

    def test_either_recover(self):
        """Test recover"""
        left = Either.left("Error")
        result = left.recover(lambda e: 0)

        assert result.is_right
        assert result._value == 0


# ==========================================
# TESTS DE STREAM MONAD
# ==========================================

class TestStreamMonad:
    """Tests para Stream Monad."""

    def test_stream_of(self):
        """Test Stream.of"""
        stream = Stream.of(1, 2, 3)
        result = stream.to_list()
        assert result == [1, 2, 3]

    def test_stream_from_iterable(self):
        """Test Stream.from_iterable"""
        stream = Stream.from_iterable([1, 2, 3, 4])
        result = stream.to_list()
        assert result == [1, 2, 3, 4]

    def test_stream_map(self):
        """Test Stream.map"""
        stream = Stream.of(1, 2, 3)
        result = stream.map(lambda x: x * 2).to_list()
        assert result == [2, 4, 6]

    def test_stream_filter(self):
        """Test Stream.filter"""
        stream = Stream.of(1, 2, 3, 4, 5)
        result = stream.filter(lambda x: x % 2 == 0).to_list()
        assert result == [2, 4]

    def test_stream_take(self):
        """Test Stream.take"""
        stream = Stream.range(0, 100)
        result = stream.take(5).to_list()
        assert result == [0, 1, 2, 3, 4]

    def test_stream_skip(self):
        """Test Stream.skip"""
        stream = Stream.of(1, 2, 3, 4, 5)
        result = stream.skip(2).to_list()
        assert result == [3, 4, 5]

    def test_stream_reduce(self):
        """Test Stream.reduce"""
        stream = Stream.of(1, 2, 3, 4)
        result = stream.reduce(lambda acc, x: acc + x, 0)
        assert result == 10

    def test_stream_chunk(self):
        """Test Stream.chunk"""
        stream = Stream.range(0, 10)
        result = stream.chunk(3).to_list()
        assert result == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]

    def test_stream_zip(self):
        """Test Stream.zip"""
        s1 = Stream.of(1, 2, 3)
        s2 = Stream.of('a', 'b', 'c')
        result = s1.zip(s2).to_list()
        assert result == [(1, 'a'), (2, 'b'), (3, 'c')]

    def test_stream_concat(self):
        """Test Stream.concat"""
        s1 = Stream.of(1, 2, 3)
        s2 = Stream.of(4, 5, 6)
        result = s1.concat(s2).to_list()
        assert result == [1, 2, 3, 4, 5, 6]

    def test_stream_distinct(self):
        """Test Stream.distinct"""
        stream = Stream.of(1, 2, 2, 3, 3, 3, 4)
        result = stream.distinct().to_list()
        assert result == [1, 2, 3, 4]

    def test_stream_find(self):
        """Test Stream.find"""
        stream = Stream.of(1, 2, 3, 4, 5)

        # Found
        result = stream.find(lambda x: x > 3)
        assert result.is_right
        assert result._value == 4

        # Not found
        result = stream.find(lambda x: x > 10)
        assert result.is_left

    def test_stream_exists(self):
        """Test Stream.exists"""
        stream = Stream.of(1, 2, 3, 4, 5)

        assert stream.exists(lambda x: x == 3) is True
        assert stream.exists(lambda x: x > 10) is False

    def test_stream_all(self):
        """Test Stream.all"""
        stream = Stream.of(2, 4, 6, 8)

        assert stream.all(lambda x: x % 2 == 0) is True

        stream2 = Stream.of(2, 3, 4)
        assert stream2.all(lambda x: x % 2 == 0) is False

    def test_stream_lazy_evaluation(self):
        """Verifica evaluación perezosa"""
        executed = []

        def track_execution(x):
            executed.append(x)
            return x * 2

        stream = Stream.of(1, 2, 3, 4, 5)
        mapped_stream = stream.map(track_execution)

        # No debe ejecutarse todavía
        assert len(executed) == 0

        # Tomar solo 2 elementos
        result = mapped_stream.take(2).to_list()

        # Solo debe haber procesado 2 elementos
        assert result == [2, 4]
        assert executed == [1, 2]

    def test_stream_infinite(self):
        """Test stream infinito"""
        # Stream infinito de números
        infinite = Stream.range(0)

        # Tomar solo primeros 5
        result = infinite.take(5).to_list()
        assert result == [0, 1, 2, 3, 4]

    def test_stream_composition(self):
        """Test composición compleja de operaciones"""
        result = (
            Stream.range(0, 20)
            .filter(lambda x: x % 2 == 0)  # Pares
            .map(lambda x: x * 2)  # Duplicar
            .skip(2)  # Saltar primeros 2
            .take(5)  # Tomar 5
            .reduce(lambda acc, x: acc + x, 0)  # Sumar
        )

        # [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
        # [0, 4, 8, 12, 16, 20, 24, 28, 32, 36]
        # [8, 12, 16, 20, 24]
        # sum = 80
        assert result == 80


# ==========================================
# TESTS DE HTTP STREAM
# ==========================================

class TestHttpStream:
    """Tests para HTTP Stream con IO."""

    def test_http_request_is_io(self):
        """Verifica que las peticiones HTTP retornan IO"""
        io_result = fetch_json('https://api.github.com/users/octocat')
        assert isinstance(io_result, IO)

    def test_http_stream_creation(self):
        """Test creación de HttpStream"""
        urls = ['https://api.github.com/users/octocat']
        stream = HttpStream.from_urls(urls)
        assert isinstance(stream, HttpStream)

    def test_http_stream_with_headers(self):
        """Test agregar headers a HttpStream"""
        stream = HttpStream.from_urls(['https://api.github.com'])
        stream_with_headers = stream.with_headers({'Accept': 'application/json'})
        assert isinstance(stream_with_headers, HttpStream)

    def test_http_stream_with_auth(self):
        """Test agregar autenticación"""
        stream = HttpStream.from_urls(['https://api.github.com'])
        stream_with_auth = stream.with_auth('token123')
        assert isinstance(stream_with_auth, HttpStream)

    @pytest.mark.integration
    def test_http_fetch_integration(self):
        """Test de integración real con GitHub API"""
        program = fetch_json('https://api.github.com/users/octocat')
        result = program.run()

        # Debe retornar Either
        assert isinstance(result, Either)

        # Si es successful, debe contener datos
        if result.is_right:
            data = result._value
            assert 'login' in data
            assert data['login'] == 'octocat'

    @pytest.mark.integration
    def test_http_stream_execute_integration(self):
        """Test ejecución de HttpStream con API real"""
        urls = [
            'https://api.github.com/users/octocat',
            'https://api.github.com/users/torvalds'
        ]

        stream = HttpStream.from_urls(urls)
        io_stream = stream.execute()

        # Debe retornar IO
        assert isinstance(io_stream, IO)

        # Ejecutar
        response_stream = io_stream.run()
        responses = response_stream.to_list()

        # Debe tener 2 respuestas
        assert len(responses) == 2


# ==========================================
# TESTS DE INTEGRACIÓN COMPLETA
# ==========================================

class TestIntegration:
    """Tests de integración del framework completo."""

    def test_complete_pipeline(self):
        """Test pipeline completo: Stream + IO + Either"""
        # Crear datos
        numbers = [1, 2, 3, 4, 5]

        # Pipeline
        result = (
            Stream.from_iterable(numbers)
            .map(lambda x: x * 2)
            .filter(lambda x: x > 5)
            .reduce(lambda acc, x: acc + x, 0)
        )

        # [2, 4, 6, 8, 10] -> [6, 8, 10] -> sum = 24
        assert result == 24

    def test_io_with_either(self):
        """Test integración IO + Either"""

        def safe_divide(x, y):
            if y == 0:
                return Either.left("Division by zero")
            return Either.right(x / y)

        program = (
            IO.pure((10, 2))
            .map(lambda t: safe_divide(t[0], t[1]))
        )

        result = program.run()
        assert result.is_right
        assert result._value == 5.0

    def test_stream_with_io(self):
        """Test Stream procesando operaciones IO"""
        # Crear archivos temporales
        temp_files = []
        for i in range(3):
            f = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
            f.write(f"Content {i}")
            f.close()
            temp_files.append(f.name)

        try:
            # Stream que lee archivos
            file_stream = Stream.from_iterable(temp_files)

            # Leer cada archivo y recolectar contenidos
            contents = []
            for filepath in file_stream:
                content = io_read_file(filepath).run()
                contents.append(content)

            assert len(contents) == 3
            assert all('Content' in c for c in contents)

        finally:
            # Limpiar
            for filepath in temp_files:
                if os.path.exists(filepath):
                    os.remove(filepath)

    def test_error_propagation(self):
        """Test propagación de errores a través del pipeline"""

        def risky_operation(x):
            if x == 0:
                raise ValueError("Zero not allowed")
            return 10 / x

        # Pipeline con error
        result = (
            Stream.of(5, 2, 0, 1)
            .map(lambda x: Either.right(x).map(risky_operation))
            .to_list()
        )

        # Primeros 2 deben ser Right
        assert result[0].is_right
        assert result[1].is_right

        # Tercero debe ser Left (error)
        assert result[2].is_left

        # Cuarto debe ser Right
        assert result[3].is_right


# ==========================================
# TESTS DE PERFORMANCE
# ==========================================

class TestPerformance:
    """Tests de performance y memoria."""

    def test_large_stream_memory(self):
        """Verifica que streams grandes no consuman toda la memoria"""
        # Stream de 1 millón de elementos
        large_stream = Stream.range(0, 1_000_000)

        # Procesar solo primeros 100
        result = (
            large_stream
            .filter(lambda x: x % 2 == 0)
            .take(100)
            .to_list()
        )

        # Debe procesar solo lo necesario
        assert len(result) == 100
        assert result[0] == 0
        assert result[99] == 198

    def test_io_composition_no_early_execution(self):
        """Verifica que IO no ejecuta hasta .run()"""
        execution_count = {'count': 0}

        def effect():
            execution_count['count'] += 1
            return 42

        # Crear pipeline complejo
        io = (
            IO(effect)
            .map(lambda x: x + 1)
            .bind(lambda x: IO(lambda: x * 2))
            .map(lambda x: x - 5)
        )

        # No debe haberse ejecutado
        assert execution_count['count'] == 0

        # Ejecutar
        result = io.run()

        # Debe ejecutarse una sola vez
        assert execution_count['count'] == 1
        assert result == 79  # (42 + 1) * 2 - 5


# ==========================================
# EJECUTAR TESTS
# ==========================================

if __name__ == "__main__":
    # Ejecutar todos los tests
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-m', 'not integration'  # Excluir tests de integración por defecto
    ])

    # Para ejecutar tests de integración:
    # pytest test_complete.py -v -m integration