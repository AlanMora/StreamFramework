"""
Tests para Stream Monad.

Verifica operaciones lazy, transformaciones y combinadores de streams.
"""

import pytest
from core.stream import Stream
from core.either import Either


class TestStreamCreation:
    """Tests para creación de streams."""

    def test_pure(self):
        """Test creación con pure."""
        stream = Stream.pure(42)
        result = stream.to_list()
        assert result == [42]

    def test_of_single_value(self):
        """Test creación con of (un valor)."""
        stream = Stream.of(42)
        result = stream.to_list()
        assert result == [42]

    def test_of_multiple_values(self):
        """Test creación con of (múltiples valores)."""
        stream = Stream.of(1, 2, 3, 4, 5)
        result = stream.to_list()
        assert result == [1, 2, 3, 4, 5]

    def test_from_iterable(self):
        """Test creación desde iterable."""
        stream = Stream.from_iterable([1, 2, 3, 4, 5])
        result = stream.to_list()
        assert result == [1, 2, 3, 4, 5]

    def test_range_with_stop(self):
        """Test creación con range (con stop)."""
        stream = Stream.range(0, 5)
        result = stream.to_list()
        assert result == [0, 1, 2, 3, 4]

    def test_range_with_step(self):
        """Test creación con range (con step)."""
        stream = Stream.range(0, 10, 2)
        result = stream.to_list()
        assert result == [0, 2, 4, 6, 8]

    def test_range_infinite(self):
        """Test creación con range infinito."""
        stream = Stream.range(0)
        result = stream.take(5).to_list()
        assert result == [0, 1, 2, 3, 4]

    def test_repeat_finite(self):
        """Test repeat finito."""
        stream = Stream.repeat("x", 3)
        result = stream.to_list()
        assert result == ["x", "x", "x"]

    def test_repeat_infinite(self):
        """Test repeat infinito."""
        stream = Stream.repeat("x")
        result = stream.take(5).to_list()
        assert result == ["x", "x", "x", "x", "x"]


class TestStreamTransformations:
    """Tests para transformaciones de streams."""

    def test_map(self):
        """Test map."""
        stream = Stream.of(1, 2, 3, 4, 5)
        result = stream.map(lambda x: x * 2).to_list()
        assert result == [2, 4, 6, 8, 10]

    def test_filter(self):
        """Test filter."""
        stream = Stream.of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
        result = stream.filter(lambda x: x % 2 == 0).to_list()
        assert result == [2, 4, 6, 8, 10]

    def test_bind(self):
        """Test bind (flat_map)."""
        stream = Stream.of(1, 2, 3)
        result = stream.bind(lambda x: Stream.of(x, x * 2)).to_list()
        assert result == [1, 2, 2, 4, 3, 6]

    def test_flat_map(self):
        """Test flat_map (alias de bind)."""
        stream = Stream.of(1, 2, 3)
        result = stream.flat_map(lambda x: Stream.of(x, x * 2)).to_list()
        assert result == [1, 2, 2, 4, 3, 6]

    def test_take(self):
        """Test take."""
        stream = Stream.range(0)
        result = stream.take(5).to_list()
        assert result == [0, 1, 2, 3, 4]

    def test_skip(self):
        """Test skip."""
        stream = Stream.of(1, 2, 3, 4, 5)
        result = stream.skip(2).to_list()
        assert result == [3, 4, 5]

    def test_take_while(self):
        """Test take_while."""
        stream = Stream.of(1, 2, 3, 4, 5, 6, 7, 8)
        result = stream.take_while(lambda x: x < 5).to_list()
        assert result == [1, 2, 3, 4]

    def test_drop_while(self):
        """Test drop_while."""
        stream = Stream.of(1, 2, 3, 4, 5, 6, 7, 8)
        result = stream.drop_while(lambda x: x < 5).to_list()
        assert result == [5, 6, 7, 8]

    def test_distinct(self):
        """Test distinct."""
        stream = Stream.of(1, 2, 2, 3, 3, 3, 4, 5, 5)
        result = stream.distinct().to_list()
        assert result == [1, 2, 3, 4, 5]

    def test_chunk(self):
        """Test chunk."""
        stream = Stream.of(1, 2, 3, 4, 5, 6, 7, 8)
        result = stream.chunk(3).to_list()
        assert result == [[1, 2, 3], [4, 5, 6], [7, 8]]


class TestStreamTerminalOperations:
    """Tests para operaciones terminales."""

    def test_to_list(self):
        """Test to_list."""
        stream = Stream.of(1, 2, 3, 4, 5)
        result = stream.to_list()
        assert result == [1, 2, 3, 4, 5]

    def test_count(self):
        """Test count."""
        stream = Stream.of(1, 2, 3, 4, 5)
        result = stream.count()
        assert result == 5

    def test_reduce(self):
        """Test reduce."""
        stream = Stream.of(1, 2, 3, 4, 5)
        result = stream.reduce(lambda acc, x: acc + x, 0)
        assert result == 15

    def test_fold_left(self):
        """Test fold_left (alias de reduce)."""
        stream = Stream.of(1, 2, 3, 4, 5)
        result = stream.fold_left(lambda acc, x: acc + x, 0)
        assert result == 15

    def test_for_each(self):
        """Test for_each."""
        results = []
        stream = Stream.of(1, 2, 3, 4, 5)
        stream.for_each(lambda x: results.append(x * 2))
        assert results == [2, 4, 6, 8, 10]

    def test_find_found(self):
        """Test find cuando encuentra."""
        stream = Stream.of(1, 2, 3, 4, 5)
        result = stream.find(lambda x: x > 3)
        assert result.is_right
        assert result._value == 4

    def test_find_not_found(self):
        """Test find cuando no encuentra."""
        stream = Stream.of(1, 2, 3, 4, 5)
        result = stream.find(lambda x: x > 10)
        assert result.is_left

    def test_exists_true(self):
        """Test exists cuando existe."""
        stream = Stream.of(1, 2, 3, 4, 5)
        result = stream.exists(lambda x: x == 3)
        assert result is True

    def test_exists_false(self):
        """Test exists cuando no existe."""
        stream = Stream.of(1, 2, 3, 4, 5)
        result = stream.exists(lambda x: x > 10)
        assert result is False

    def test_all_true(self):
        """Test all cuando todos cumplen."""
        stream = Stream.of(2, 4, 6, 8, 10)
        result = stream.all(lambda x: x % 2 == 0)
        assert result is True

    def test_all_false(self):
        """Test all cuando no todos cumplen."""
        stream = Stream.of(1, 2, 3, 4, 5)
        result = stream.all(lambda x: x % 2 == 0)
        assert result is False


class TestStreamCombinators:
    """Tests para combinadores de streams."""

    def test_zip(self):
        """Test zip."""
        s1 = Stream.of(1, 2, 3)
        s2 = Stream.of('a', 'b', 'c')
        result = s1.zip(s2).to_list()
        assert result == [(1, 'a'), (2, 'b'), (3, 'c')]

    def test_zip_different_lengths(self):
        """Test zip con diferentes longitudes."""
        s1 = Stream.of(1, 2, 3, 4, 5)
        s2 = Stream.of('a', 'b', 'c')
        result = s1.zip(s2).to_list()
        assert result == [(1, 'a'), (2, 'b'), (3, 'c')]

    def test_concat(self):
        """Test concat."""
        s1 = Stream.of(1, 2, 3)
        s2 = Stream.of(4, 5, 6)
        result = s1.concat(s2).to_list()
        assert result == [1, 2, 3, 4, 5, 6]

    def test_flatten(self):
        """Test flatten."""
        stream = Stream.of([1, 2], [3, 4], [5, 6])
        result = stream.flatten().to_list()
        assert result == [1, 2, 3, 4, 5, 6]


class TestStreamLaziness:
    """Tests para verificar lazy evaluation."""

    def test_map_is_lazy(self):
        """Test que map es lazy."""
        executed = []

        def track_execution(x):
            executed.append(x)
            return x * 2

        stream = Stream.of(1, 2, 3, 4, 5)
        mapped = stream.map(track_execution)

        # No se ejecuta hasta materializar
        assert len(executed) == 0

        result = mapped.to_list()
        assert len(executed) == 5
        assert result == [2, 4, 6, 8, 10]

    def test_filter_is_lazy(self):
        """Test que filter es lazy."""
        executed = []

        def track_execution(x):
            executed.append(x)
            return x % 2 == 0

        stream = Stream.of(1, 2, 3, 4, 5)
        filtered = stream.filter(track_execution)

        assert len(executed) == 0

        result = filtered.to_list()
        assert len(executed) == 5

    def test_take_stops_early(self):
        """Test que take detiene la evaluación temprano."""
        executed = []

        def track_execution(x):
            executed.append(x)
            return x

        stream = Stream.range(0, 100).map(track_execution)
        result = stream.take(5).to_list()

        # Solo debe haber ejecutado 5 elementos
        assert len(executed) == 5
        assert result == [0, 1, 2, 3, 4]

    def test_infinite_stream_with_take(self):
        """Test stream infinito con take."""
        stream = Stream.range(0)  # Infinito
        result = stream.map(lambda x: x * 2).take(5).to_list()
        assert result == [0, 2, 4, 6, 8]


class TestStreamMonadLaws:
    """Tests para verificar leyes monádicas."""

    def test_left_identity(self):
        """Ley: pure(a).bind(f) == f(a)"""
        value = 5
        f = lambda x: Stream.of(x, x * 2)

        left = Stream.pure(value).bind(f).to_list()
        right = f(value).to_list()

        assert left == right

    def test_right_identity(self):
        """Ley: m.bind(pure) == m"""
        m = Stream.of(1, 2, 3)

        result = m.bind(Stream.pure).to_list()
        expected = m.to_list()

        assert result == expected

    def test_associativity(self):
        """Ley: m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))"""
        m = Stream.of(1, 2, 3)
        f = lambda x: Stream.of(x, x * 2)
        g = lambda x: Stream.of(x + 1)

        left = m.bind(f).bind(g).to_list()
        right = m.bind(lambda x: f(x).bind(g)).to_list()

        assert left == right


class TestStreamChaining:
    """Tests para encadenamiento complejo de operaciones."""

    def test_complex_pipeline(self):
        """Test pipeline complejo."""
        result = (
            Stream.range(1, 21)
            .filter(lambda x: x % 2 == 0)  # Pares: [2,4,6,8,10,12,14,16,18,20]
            .map(lambda x: x * 2)           # [4,8,12,16,20,24,28,32,36,40]
            .take(5)                        # [4,8,12,16,20]
            .to_list()
        )
        assert result == [4, 8, 12, 16, 20]

    def test_nested_flat_map(self):
        """Test flat_map anidado."""
        result = (
            Stream.of(1, 2, 3)
            .flat_map(lambda x: Stream.of(x, x * 2))
            .flat_map(lambda x: Stream.of(x, x + 1))
            .to_list()
        )
        # 1 -> [1, 2] -> [1, 2, 2, 3]
        # 2 -> [2, 4] -> [2, 3, 4, 5]
        # 3 -> [3, 6] -> [3, 4, 6, 7]
        assert result == [1, 2, 2, 3, 2, 3, 4, 5, 3, 4, 6, 7]

    def test_fibonacci_stream(self):
        """Test generación de Fibonacci usando streams."""
        def fibonacci():
            a, b = 0, 1
            while True:
                yield a
                a, b = b, a + b

        result = Stream(fibonacci).take(10).to_list()
        assert result == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

    def test_primes_stream(self):
        """Test generación de números primos."""
        def is_prime(n):
            if n < 2:
                return False
            for i in range(2, int(n ** 0.5) + 1):
                if n % i == 0:
                    return False
            return True

        result = (
            Stream.range(2, 50)
            .filter(is_prime)
            .to_list()
        )
        assert result == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]


class TestStreamEdgeCases:
    """Tests para casos borde."""

    def test_empty_stream(self):
        """Test stream vacío."""
        stream = Stream.from_iterable([])
        assert stream.to_list() == []
        assert stream.count() == 0

    def test_single_element_stream(self):
        """Test stream con un solo elemento."""
        stream = Stream.pure(42)
        assert stream.to_list() == [42]
        assert stream.count() == 1

    def test_take_more_than_available(self):
        """Test take con más elementos de los disponibles."""
        stream = Stream.of(1, 2, 3)
        result = stream.take(10).to_list()
        assert result == [1, 2, 3]

    def test_skip_more_than_available(self):
        """Test skip con más elementos de los disponibles."""
        stream = Stream.of(1, 2, 3)
        result = stream.skip(10).to_list()
        assert result == []

    def test_take_zero(self):
        """Test take con 0 elementos."""
        stream = Stream.of(1, 2, 3)
        result = stream.take(0).to_list()
        assert result == []

    def test_reduce_empty_stream(self):
        """Test reduce en stream vacío."""
        stream = Stream.from_iterable([])
        result = stream.reduce(lambda acc, x: acc + x, 0)
        assert result == 0

    def test_find_in_empty_stream(self):
        """Test find en stream vacío."""
        stream = Stream.from_iterable([])
        result = stream.find(lambda x: True)
        assert result.is_left


class TestStreamReusability:
    """Tests para verificar reutilización de streams."""

    def test_stream_can_be_iterated_multiple_times(self):
        """Test que un stream puede iterarse múltiples veces."""
        stream = Stream.of(1, 2, 3)

        result1 = stream.to_list()
        result2 = stream.to_list()
        result3 = stream.to_list()

        assert result1 == [1, 2, 3]
        assert result2 == [1, 2, 3]
        assert result3 == [1, 2, 3]

    def test_transformed_stream_can_be_reused(self):
        """Test que streams transformados pueden reutilizarse."""
        stream = Stream.of(1, 2, 3).map(lambda x: x * 2)

        result1 = stream.to_list()
        result2 = stream.to_list()

        assert result1 == [2, 4, 6]
        assert result2 == [2, 4, 6]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
