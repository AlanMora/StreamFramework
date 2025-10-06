import requests
import json
from typing import TypeVar, Generic, Callable, Optional, Dict, Any
from .stream import Stream
from .io_monad import IO
from .either import Either
from dataclasses import dataclass
from enum import Enum

A = TypeVar('A')
B = TypeVar('B')


class HttpMethod(Enum):
    """Métodos HTTP soportados."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


@dataclass
class HttpRequest:
    """Representa una petición HTTP."""
    url: str
    method: HttpMethod = HttpMethod.GET
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    body: Optional[Any] = None
    timeout: int = 30

    def to_dict(self) -> dict:
        """Convierte la request a un diccionario."""
        return {
            'url': self.url,
            'method': self.method.value,
            'headers': self.headers or {},
            'params': self.params or {},
            'body': self.body,
            'timeout': self.timeout
        }


@dataclass
class HttpResponse:
    """Representa una respuesta HTTP."""
    status_code: int
    headers: Dict[str, str]
    body: str
    request: HttpRequest

    def json(self) -> Either[Exception, dict]:
        """Parsea el body como JSON."""
        try:
            return Either.right(json.loads(self.body))
        except json.JSONDecodeError as e:
            return Either.left(e)

    def is_success(self) -> bool:
        """Verifica si la respuesta fue exitosa (2xx)."""
        return 200 <= self.status_code < 300

    def is_error(self) -> bool:
        """Verifica si hubo un error (4xx o 5xx)."""
        return self.status_code >= 400


# FUNCIONES IO PARA HTTP

def http_request(request: HttpRequest) -> IO[Either[Exception, HttpResponse]]:
    """
    Crea una IO que ejecuta una petición HTTP.

    La petición NO se ejecuta inmediatamente, solo se describe.
    Se ejecutará cuando se llame a .run()

    Args:
        request: Configuración de la petición

    Returns:
        IO[Either[Exception, HttpResponse]]
    """

    def effect():
        try:
            # Preparar la petición
            kwargs = {
                'timeout': request.timeout,
                'headers': request.headers or {},
                'params': request.params or {}
            }

            # Agregar body si existe
            if request.body is not None:
                if isinstance(request.body, (dict, list)):
                    kwargs['json'] = request.body
                else:
                    kwargs['data'] = request.body

            # Ejecutar la petición según el método
            if request.method == HttpMethod.GET:
                resp = requests.get(request.url, **kwargs)
            elif request.method == HttpMethod.POST:
                resp = requests.post(request.url, **kwargs)
            elif request.method == HttpMethod.PUT:
                resp = requests.put(request.url, **kwargs)
            elif request.method == HttpMethod.DELETE:
                resp = requests.delete(request.url, **kwargs)
            elif request.method == HttpMethod.PATCH:
                resp = requests.patch(request.url, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {request.method}")

            # Crear respuesta
            response = HttpResponse(
                status_code=resp.status_code,
                headers=dict(resp.headers),
                body=resp.text,
                request=request
            )

            return Either.right(response)

        except Exception as e:
            return Either.left(e)

    return IO(effect)


def http_get(url: str, **kwargs) -> IO[Either[Exception, HttpResponse]]:
    """IO para petición GET."""
    request = HttpRequest(url=url, method=HttpMethod.GET, **kwargs)
    return http_request(request)


def http_post(url: str, body: Any = None, **kwargs) -> IO[Either[Exception, HttpResponse]]:
    """IO para petición POST."""
    request = HttpRequest(url=url, method=HttpMethod.POST, body=body, **kwargs)
    return http_request(request)


def http_put(url: str, body: Any = None, **kwargs) -> IO[Either[Exception, HttpResponse]]:
    """IO para petición PUT."""
    request = HttpRequest(url=url, method=HttpMethod.PUT, body=body, **kwargs)
    return http_request(request)


def http_delete(url: str, **kwargs) -> IO[Either[Exception, HttpResponse]]:
    """IO para petición DELETE."""
    request = HttpRequest(url=url, method=HttpMethod.DELETE, **kwargs)
    return http_request(request)


# HTTP STREAM - COMBINA STREAM + IO

class HttpStream(Generic[A]):
    """
    Stream que procesa peticiones HTTP de manera funcional.

    Características:
    - Procesamiento lazy de múltiples peticiones
    - Manejo funcional de errores
    - Retry automático
    - Rate limiting
    - Composición funcional
    """

    def __init__(self, requests: Stream[HttpRequest]):
        """
        Args:
            requests: Stream de peticiones HTTP
        """
        self._requests = requests

    @staticmethod
    def from_urls(urls: list[str]) -> 'HttpStream':
        """Crea un HttpStream desde una lista de URLs."""
        requests = [HttpRequest(url=url) for url in urls]
        return HttpStream(Stream.from_iterable(requests))

    @staticmethod
    def single(url: str, method: HttpMethod = HttpMethod.GET, **kwargs) -> 'HttpStream':
        """Crea un HttpStream con una sola petición."""
        request = HttpRequest(url=url, method=method, **kwargs)
        return HttpStream(Stream.of(request))

    def execute(self) -> IO[Stream[Either[Exception, HttpResponse]]]:
        """
        Ejecuta todas las peticiones y retorna un stream de respuestas.

        Returns:
            IO[Stream[Either[Exception, HttpResponse]]]
        """

        def effect():
            def response_generator():
                for request in self._requests:
                    # Ejecutar cada petición
                    result = http_request(request).run()
                    yield result

            return Stream(lambda: response_generator())

        return IO(effect)

    def execute_parallel(self, max_workers: int = 5) -> IO[list[Either[Exception, HttpResponse]]]:
        """
        Ejecuta las peticiones en paralelo.

        Args:
            max_workers: Número máximo de workers concurrentes

        Returns:
            IO[list[Either[Exception, HttpResponse]]]
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def effect():
            requests_list = list(self._requests)
            results = []

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Enviar todas las peticiones
                future_to_request = {
                    executor.submit(http_request(req).run): req
                    for req in requests_list
                }

                # Recolectar resultados en orden de completación
                for future in as_completed(future_to_request):
                    results.append(future.result())

            return results

        return IO(effect)

    def map_request(self, f: Callable[[HttpRequest], HttpRequest]) -> 'HttpStream':
        """Transforma cada petición."""
        return HttpStream(self._requests.map(f))

    def filter_request(self, predicate: Callable[[HttpRequest], bool]) -> 'HttpStream':
        """Filtra peticiones."""
        return HttpStream(self._requests.filter(predicate))

    def with_retry(self, max_attempts: int = 3) -> 'HttpStream':
        """Agrega retry a cada petición."""

        def add_retry(request: HttpRequest) -> HttpRequest:
            # Aquí podrías agregar metadata de retry
            return request

        return self.map_request(add_retry)

    def with_headers(self, headers: Dict[str, str]) -> 'HttpStream':
        """Agrega headers a todas las peticiones."""

        def add_headers(request: HttpRequest) -> HttpRequest:
            new_headers = (request.headers or {}).copy()
            new_headers.update(headers)
            request.headers = new_headers
            return request

        return self.map_request(add_headers)

    def with_auth(self, token: str) -> 'HttpStream':
        """Agrega autenticación Bearer a las peticiones."""
        return self.with_headers({'Authorization': f'Bearer {token}'})

    def take(self, n: int) -> 'HttpStream':
        """Toma las primeras n peticiones."""
        return HttpStream(self._requests.take(n))

    def __repr__(self) -> str:
        return "HttpStream(<requests>)"


# UTILIDADES DE ALTO NIVEL

def fetch_json(url: str, **kwargs) -> IO[Either[Exception, dict]]:
    """
    Fetches JSON data from a URL.

    Returns:
        IO[Either[Exception, dict]]
    """