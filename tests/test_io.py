"""
Tests específicos para IO Monad y operaciones de IO.

Tests enfocados en efectos de entrada/salida y sus helpers.
"""

import pytest
import tempfile
import os
from core.io_monad import (
    IO,
    io_print,
    io_input,
    io_read_file,
    io_write_file,
    io_append_file
)
from core.either import Either


class TestIOHelpers:
    """Tests para helpers de IO."""

    def test_io_read_file(self):
        """Test lectura de archivo."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Hello, World!")
            filepath = f.name

        try:
            content = io_read_file(filepath).run()
            assert content == "Hello, World!"
        finally:
            os.unlink(filepath)

    def test_io_write_file(self):
        """Test escritura de archivo."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            filepath = f.name

        try:
            io_write_file(filepath, "Test content").run()
            with open(filepath, 'r') as f:
                content = f.read()
            assert content == "Test content"
        finally:
            os.unlink(filepath)

    def test_io_append_file(self):
        """Test append a archivo."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Line 1\n")
            filepath = f.name

        try:
            io_append_file(filepath, "Line 2\n").run()
            io_append_file(filepath, "Line 3\n").run()

            with open(filepath, 'r') as f:
                content = f.read()

            assert content == "Line 1\nLine 2\nLine 3\n"
        finally:
            os.unlink(filepath)

    def test_io_read_write_chain(self):
        """Test encadenamiento de read y write."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
            f1.write("Original content")
            source = f1.name

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            dest = f2.name

        try:
            # Pipeline: leer -> transformar -> escribir
            (
                io_read_file(source)
                .map(lambda content: content.upper())
                .bind(lambda content: io_write_file(dest, content))
                .run()
            )

            result = io_read_file(dest).run()
            assert result == "ORIGINAL CONTENT"
        finally:
            os.unlink(source)
            os.unlink(dest)


class TestIOComposition:
    """Tests para composición de IOs."""

    def test_compose_multiple_ios(self):
        """Test composición de múltiples IOs."""
        io1 = IO.pure(5)
        io2 = io1.map(lambda x: x * 2)
        io3 = io2.map(lambda x: x + 3)
        io4 = io3.map(lambda x: x ** 2)

        result = io4.run()
        assert result == 169  # ((5 * 2) + 3) ** 2 = 13 ** 2

    def test_bind_chain(self):
        """Test encadenamiento con bind."""
        result = (
            IO.pure(5)
            .bind(lambda x: IO.pure(x * 2))
            .bind(lambda x: IO.pure(x + 3))
            .bind(lambda x: IO.pure(x ** 2))
            .run()
        )
        assert result == 169

    def test_mixed_map_bind_chain(self):
        """Test mezcla de map y bind."""
        result = (
            IO.pure(5)
            .map(lambda x: x * 2)
            .bind(lambda x: IO.pure(x + 3))
            .map(lambda x: x ** 2)
            .run()
        )
        assert result == 169


class TestIOErrorHandling:
    """Tests para manejo de errores en IO."""

    def test_attempt_with_success(self):
        """Test attempt con operación exitosa."""
        io = IO.pure(42)
        result = io.attempt().run()

        assert result.is_right
        assert result._value == 42

    def test_attempt_with_exception(self):
        """Test attempt con excepción."""
        def failing():
            raise ValueError("Test error")

        io = IO(failing)
        result = io.attempt().run()

        assert result.is_left
        assert isinstance(result._value, ValueError)
        assert str(result._value) == "Test error"

    def test_recover_from_exception(self):
        """Test recover de excepción."""
        def failing():
            raise ValueError("Test error")

        result = IO(failing).recover(lambda e: 42).run()
        assert result == 42

    def test_recover_no_exception(self):
        """Test recover cuando no hay excepción."""
        result = IO.pure(42).recover(lambda e: 0).run()
        assert result == 42

    def test_attempt_then_recover(self):
        """Test attempt seguido de recover en Either."""
        def failing():
            raise ValueError("Test error")

        result = (
            IO(failing)
            .attempt()
            .map(lambda either: either.recover(lambda e: 42))
            .run()
        )

        assert result.is_right
        assert result._value == 42

    def test_error_in_map(self):
        """Test excepción en map."""
        def divide_by_zero(x):
            return x / 0

        with pytest.raises(ZeroDivisionError):
            IO.pure(5).map(divide_by_zero).run()

    def test_error_in_bind(self):
        """Test excepción en bind."""
        def failing_bind(x):
            raise ValueError("Error in bind")

        with pytest.raises(ValueError):
            IO.pure(5).bind(failing_bind).run()


class TestIORetry:
    """Tests para retry en IO."""

    def test_retry_success_first_attempt(self):
        """Test retry exitoso en primer intento."""
        attempts = [0]

        def effect():
            attempts[0] += 1
            return 42

        result = IO(effect).retry(max_attempts=3).run()
        assert result == 42
        assert attempts[0] == 1

    def test_retry_success_after_one_failure(self):
        """Test retry exitoso después de un fallo."""
        attempts = [0]

        def effect():
            attempts[0] += 1
            if attempts[0] == 1:
                raise ValueError("First attempt fails")
            return 42

        result = IO(effect).retry(max_attempts=3).run()
        assert result == 42
        assert attempts[0] == 2

    def test_retry_success_on_last_attempt(self):
        """Test retry exitoso en último intento."""
        attempts = [0]

        def effect():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError("Fail")
            return 42

        result = IO(effect).retry(max_attempts=3).run()
        assert result == 42
        assert attempts[0] == 3

    def test_retry_all_attempts_fail(self):
        """Test retry cuando todos los intentos fallan."""
        attempts = [0]

        def effect():
            attempts[0] += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            IO(effect).retry(max_attempts=3).run()

        assert attempts[0] == 3

    def test_retry_with_different_exceptions(self):
        """Test retry con diferentes excepciones."""
        attempts = [0]

        def effect():
            attempts[0] += 1
            if attempts[0] == 1:
                raise ValueError("First error")
            elif attempts[0] == 2:
                raise TypeError("Second error")
            return 42

        result = IO(effect).retry(max_attempts=3).run()
        assert result == 42
        assert attempts[0] == 3


class TestIOSequenceAndTraverse:
    """Tests para sequence y traverse."""

    def test_sequence_empty_list(self):
        """Test sequence con lista vacía."""
        result = IO.sequence([]).run()
        assert result == []

    def test_sequence_single_io(self):
        """Test sequence con un solo IO."""
        result = IO.sequence([IO.pure(42)]).run()
        assert result == [42]

    def test_sequence_multiple_ios(self):
        """Test sequence con múltiples IOs."""
        ios = [IO.pure(1), IO.pure(2), IO.pure(3)]
        result = IO.sequence(ios).run()
        assert result == [1, 2, 3]

    def test_sequence_with_effects(self):
        """Test sequence con efectos."""
        counter = [0]

        def make_effect(n):
            def effect():
                counter[0] += 1
                return n
            return IO(effect)

        ios = [make_effect(1), make_effect(2), make_effect(3)]
        result = IO.sequence(ios).run()

        assert result == [1, 2, 3]
        assert counter[0] == 3

    def test_traverse_empty_list(self):
        """Test traverse con lista vacía."""
        result = IO.traverse([], lambda x: IO.pure(x * 2)).run()
        assert result == []

    def test_traverse_with_transformation(self):
        """Test traverse con transformación."""
        items = [1, 2, 3, 4, 5]
        result = IO.traverse(items, lambda x: IO.pure(x * 2)).run()
        assert result == [2, 4, 6, 8, 10]

    def test_traverse_with_effects(self):
        """Test traverse con efectos."""
        counter = [0]

        def effect_fn(x):
            def effect():
                counter[0] += 1
                return x * 2
            return IO(effect)

        result = IO.traverse([1, 2, 3], effect_fn).run()
        assert result == [2, 4, 6]
        assert counter[0] == 3


class TestIOFileOperations:
    """Tests para operaciones de archivo."""

    def test_read_nonexistent_file(self):
        """Test lectura de archivo inexistente."""
        with pytest.raises(FileNotFoundError):
            io_read_file("/nonexistent/file.txt").run()

    def test_write_to_invalid_path(self):
        """Test escritura a path inválido."""
        with pytest.raises((FileNotFoundError, PermissionError, OSError)):
            io_write_file("/invalid/path/file.txt", "content").run()

    def test_read_write_encoding(self):
        """Test lectura y escritura con encoding."""
        content = "Hola, ¿cómo estás? 你好"

        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            filepath = f.name

        try:
            io_write_file(filepath, content, encoding='utf-8').run()
            read_content = io_read_file(filepath, encoding='utf-8').run()
            assert read_content == content
        finally:
            os.unlink(filepath)

    def test_read_multiline_file(self):
        """Test lectura de archivo multilínea."""
        content = """Line 1
Line 2
Line 3
Line 4"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(content)
            filepath = f.name

        try:
            read_content = io_read_file(filepath).run()
            assert read_content == content
        finally:
            os.unlink(filepath)


class TestIOPurity:
    """Tests para verificar pureza de IO."""

    def test_io_description_is_pure(self):
        """Test que crear un IO no ejecuta el efecto."""
        executed = [False]

        def effect():
            executed[0] = True
            return 42

        io = IO(effect)
        assert executed[0] is False  # No ejecutado

    def test_io_composition_is_pure(self):
        """Test que componer IOs no ejecuta efectos."""
        executed = []

        def effect1():
            executed.append(1)
            return 10

        def effect2(x):
            executed.append(2)
            return IO(lambda: x * 2)

        io = IO(effect1).bind(effect2)
        assert len(executed) == 0  # No ejecutado

        result = io.run()
        assert len(executed) == 2  # Ejecutado
        assert result == 20

    def test_multiple_runs_independent(self):
        """Test que múltiples runs son independientes."""
        counter = [0]

        def effect():
            counter[0] += 1
            return counter[0]

        io = IO(effect)

        result1 = io.run()
        result2 = io.run()
        result3 = io.run()

        assert result1 == 1
        assert result2 == 2
        assert result3 == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
