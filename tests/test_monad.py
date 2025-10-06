"""
Tests para las mónadas base.

Verifica que las implementaciones cumplan con las leyes monádicas.
"""

import pytest
from core.monad import Monad
from core.either import Either
from core.io_monad import IO


# ==========================================
# TESTS PARA EITHER MONAD
# ==========================================

class TestEitherMonad:
    """Tests para Either Monad."""

    def test_either_right_creation(self):
        """Test creación de Right."""
        result = Either.right(42)
        assert result.is_right
        assert not result.is_left
        assert result._value == 42

    def test_either_left_creation(self):
        """Test creación de Left."""
        result = Either.left("error")
        assert result.is_left
        assert not result.is_right
        assert result._value == "error"

    def test_either_pure(self):
        """Test de pure (unit)."""
        result = Either.pure(42)
        assert result.is_right
        assert result._value == 42

    # Ley 1: Identidad izquierda
    # pure(a).bind(f) == f(a)
    def test_left_identity(self):
        """Ley de identidad izquierda."""
        value = 5
        f = lambda x: Either.right(x * 2)

        left_side = Either.pure(value).bind(f)
        right_side = f(value)

        assert left_side._value == right_side._value
        assert left_side.is_right == right_side.is_right

    # Ley 2: Identidad derecha
    # m.bind(pure) == m
    def test_right_identity(self):
        """Ley de identidad derecha."""
        m = Either.right(42)

        result = m.bind(Either.pure)

        assert result._value == m._value
        assert result.is_right == m.is_right

    # Ley 3: Asociatividad
    # m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))
    def test_associativity(self):
        """Ley de asociatividad."""
        m = Either.right(5)
        f = lambda x: Either.right(x * 2)
        g = lambda x: Either.right(x + 3)

        left_side = m.bind(f).bind(g)
        right_side = m.bind(lambda x: f(x).bind(g))

        assert left_side._value == right_side._value

    def test_map_on_right(self):
        """Test map en Right."""
        result = Either.right(5).map(lambda x: x * 2)
        assert result.is_right
        assert result._value == 10

    def test_map_on_left(self):
        """Test map en Left (debe propagar el error)."""
        result = Either.left("error").map(lambda x: x * 2)
        assert result.is_left
        assert result._value == "error"

    def test_bind_on_right(self):
        """Test bind en Right."""
        result = Either.right(5).bind(lambda x: Either.right(x * 2))
        assert result.is_right
        assert result._value == 10

    def test_bind_on_left(self):
        """Test bind en Left (debe propagar el error)."""
        result = Either.left("error").bind(lambda x: Either.right(x * 2))
        assert result.is_left
        assert result._value == "error"

    def test_get_or_else_on_right(self):
        """Test get_or_else en Right."""
        result = Either.right(42).get_or_else(0)
        assert result == 42

    def test_get_or_else_on_left(self):
        """Test get_or_else en Left."""
        result = Either.left("error").get_or_else(0)
        assert result == 0

    def test_or_else_on_right(self):
        """Test or_else en Right."""
        result = Either.right(42).or_else(Either.right(0))
        assert result.is_right
        assert result._value == 42

    def test_or_else_on_left(self):
        """Test or_else en Left."""
        result = Either.left("error").or_else(Either.right(42))
        assert result.is_right
        assert result._value == 42

    def test_recover_on_left(self):
        """Test recover en Left."""
        result = Either.left("error").recover(lambda e: f"Recovered from {e}")
        assert result.is_right
        assert result._value == "Recovered from error"

    def test_recover_on_right(self):
        """Test recover en Right (no debe hacer nada)."""
        result = Either.right(42).recover(lambda e: 0)
        assert result.is_right
        assert result._value == 42

    def test_chaining_operations(self):
        """Test encadenamiento de operaciones."""
        result = (
            Either.right(5)
            .map(lambda x: x * 2)
            .bind(lambda x: Either.right(x + 3))
            .map(lambda x: x * 10)
        )
        assert result.is_right
        assert result._value == 130  # ((5 * 2) + 3) * 10

    def test_error_propagation(self):
        """Test propagación de errores en cadena."""
        result = (
            Either.right(5)
            .map(lambda x: x * 2)
            .bind(lambda x: Either.left("error"))
            .map(lambda x: x + 3)  # No se ejecuta
        )
        assert result.is_left
        assert result._value == "error"

    def test_map_exception_handling(self):
        """Test manejo de excepciones en map."""
        def divide_by_zero(x):
            return x / 0

        result = Either.right(5).map(divide_by_zero)
        assert result.is_left
        assert isinstance(result._value, Exception)


# ==========================================
# TESTS PARA IO MONAD
# ==========================================

class TestIOMonad:
    """Tests para IO Monad."""

    def test_io_pure(self):
        """Test de pure (unit)."""
        io = IO.pure(42)
        assert io.run() == 42

    def test_io_execution_deferred(self):
        """Test que la ejecución es diferida."""
        executed = []

        def effect():
            executed.append(1)
            return 42

        io = IO(effect)
        assert len(executed) == 0  # No ejecutado aún

        result = io.run()
        assert len(executed) == 1  # Ejecutado
        assert result == 42

    def test_io_map(self):
        """Test map en IO."""
        io = IO.pure(5).map(lambda x: x * 2)
        assert io.run() == 10

    def test_io_bind(self):
        """Test bind en IO."""
        io = IO.pure(5).bind(lambda x: IO.pure(x * 2))
        assert io.run() == 10

    def test_io_flat_map(self):
        """Test flat_map (alias de bind)."""
        io = IO.pure(5).flat_map(lambda x: IO.pure(x * 2))
        assert io.run() == 10

    # Ley 1: Identidad izquierda
    def test_left_identity(self):
        """Ley de identidad izquierda."""
        value = 5
        f = lambda x: IO.pure(x * 2)

        left_side = IO.pure(value).bind(f).run()
        right_side = f(value).run()

        assert left_side == right_side

    # Ley 2: Identidad derecha
    def test_right_identity(self):
        """Ley de identidad derecha."""
        m = IO.pure(42)

        result = m.bind(IO.pure).run()

        assert result == m.run()

    # Ley 3: Asociatividad
    def test_associativity(self):
        """Ley de asociatividad."""
        m = IO.pure(5)
        f = lambda x: IO.pure(x * 2)
        g = lambda x: IO.pure(x + 3)

        left_side = m.bind(f).bind(g).run()
        right_side = m.bind(lambda x: f(x).bind(g)).run()

        assert left_side == right_side

    def test_chaining_operations(self):
        """Test encadenamiento de operaciones."""
        result = (
            IO.pure(5)
            .map(lambda x: x * 2)
            .bind(lambda x: IO.pure(x + 3))
            .map(lambda x: x * 10)
            .run()
        )
        assert result == 130

    def test_attempt_success(self):
        """Test attempt con éxito."""
        io = IO.pure(42)
        result = io.attempt().run()

        assert result.is_right
        assert result._value == 42

    def test_attempt_failure(self):
        """Test attempt con excepción."""
        def failing_effect():
            raise ValueError("test error")

        io = IO(failing_effect)
        result = io.attempt().run()

        assert result.is_left
        assert isinstance(result._value, ValueError)

    def test_recover_success(self):
        """Test recover cuando no hay error."""
        io = IO.pure(42)
        result = io.recover(lambda e: 0).run()
        assert result == 42

    def test_recover_failure(self):
        """Test recover cuando hay error."""
        def failing_effect():
            raise ValueError("test error")

        io = IO(failing_effect)
        result = io.recover(lambda e: 0).run()
        assert result == 0

    def test_retry_success_first_attempt(self):
        """Test retry exitoso en primer intento."""
        io = IO.pure(42)
        result = io.retry(max_attempts=3).run()
        assert result == 42

    def test_retry_success_after_failures(self):
        """Test retry exitoso después de fallos."""
        attempts = [0]

        def effect():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError("fail")
            return 42

        io = IO(effect)
        result = io.retry(max_attempts=5).run()
        assert result == 42
        assert attempts[0] == 3

    def test_retry_all_attempts_fail(self):
        """Test retry cuando todos los intentos fallan."""
        def failing_effect():
            raise ValueError("fail")

        io = IO(failing_effect)

        with pytest.raises(ValueError):
            io.retry(max_attempts=3).run()

    def test_sequence(self):
        """Test sequence de IOs."""
        ios = [IO.pure(1), IO.pure(2), IO.pure(3)]
        result = IO.sequence(ios).run()
        assert result == [1, 2, 3]

    def test_traverse(self):
        """Test traverse."""
        items = [1, 2, 3]
        result = IO.traverse(items, lambda x: IO.pure(x * 2)).run()
        assert result == [2, 4, 6]

    def test_multiple_runs_execute_effect_multiple_times(self):
        """Test que run() ejecuta el efecto cada vez."""
        counter = [0]

        def effect():
            counter[0] += 1
            return counter[0]

        io = IO(effect)

        assert io.run() == 1
        assert io.run() == 2
        assert io.run() == 3


# ==========================================
# TESTS DE INTEGRACIÓN
# ==========================================

class TestMonadIntegration:
    """Tests de integración entre mónadas."""

    def test_io_with_either(self):
        """Test IO que retorna Either."""
        def risky_operation():
            return Either.right(42)

        io = IO(risky_operation)
        result = io.run()

        assert result.is_right
        assert result._value == 42

    def test_io_attempt_returns_either(self):
        """Test que attempt retorna IO[Either]."""
        io = IO.pure(42)
        result = io.attempt().run()

        assert isinstance(result, Either)
        assert result.is_right

    def test_complex_pipeline(self):
        """Test pipeline complejo combinando IO y Either."""
        def process_value(x):
            if x < 0:
                return Either.left("Negative value")
            return Either.right(x * 2)

        result = (
            IO.pure(5)
            .map(lambda x: x + 3)
            .bind(lambda x: IO(lambda: process_value(x)))
            .run()
        )

        assert result.is_right
        assert result._value == 16


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
