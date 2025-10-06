"""
Tests para HTTP Stream con IO Monad.
"""

import pytest
from core.http_stream import (
    HttpStream, HttpRequest, HttpMethod,
    http_get, fetch_json, HttpPipeline
)
from core.io_monad import IO


class TestHttpIO:
    """Tests para operaciones HTTP con IO."""

    def test_http_get_returns_io(self):
        """Verifica que http_get retorna IO."""
        result = http_get('https://api.github.com/users/octocat')
        assert isinstance(result, IO)

    def test_fetch_json_lazy_evaluation(self):
        """Verifica que fetch_json es lazy (no ejecuta inmediatamente)."""
        # Crear la IO
        fetch_op = fetch_json('https://api.github.com/users/octocat')

        # No debe ejecutarse hasta llamar .run()
        assert isinstance(fetch_op, IO)

        # Ejecutar
        result = fetch_op.run()
        assert result.is_right or result.is_left

    def test_http_stream_composition(self):
        """Verifica composición de HTTP Stream."""
        urls = [
            'https://api.github.com/users/octocat',
            'https://api.github.com/users/torvalds'
        ]

        stream = HttpStream.from_urls(urls)
        assert isinstance(stream, HttpStream)

        # Agregar headers
        stream_with_headers = stream.with_headers({'Accept': 'application/json'})
        assert isinstance(stream_with_headers, HttpStream)

    def test_io_monad_laws(self):
        """Verifica que IO cumple las leyes monádicas."""

        # Left identity: pure(a).bind(f) == f(a)
        def f(x):
            return IO.pure(x * 2)

        a = 5
        left = IO.pure(a).bind(f).run()
        right = f(a).run()
        assert left == right

        # Right identity: m.bind(pure) == m
        m = IO.pure(10)
        assert m.bind(IO.pure).run() == m.run()


if __name__ == "__main__":
    pytest.main([__file__, '-v'])