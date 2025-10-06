"""
Stream Framework - Core Module

Framework de procesamiento de streams basado en mónadas.
"""

from .monad import Monad, Functor, Applicative
from .io_monad import IO, io_print, io_input, io_read_file, io_write_file, io_append_file
from .either import Either
from .stream import Stream
from .http_stream import (
    HttpStream,
    HttpRequest,
    HttpResponse,
    HttpMethod,
    http_get,
    http_post,
    http_put,
    http_delete,
    http_request
)

__version__ = '1.0.0'

__all__ = [
    # Monad base
    'Monad',
    'Functor',
    'Applicative',

    # IO Monad
    'IO',
    'io_print',
    'io_input',
    'io_read_file',
    'io_write_file',
    'io_append_file',

    # Either Monad
    'Either',

    # Stream
    'Stream',

    # HTTP
    'HttpStream',
    'HttpRequest',
    'HttpResponse',
    'HttpMethod',
    'http_get',
    'http_post',
    'http_put',
    'http_delete',
    'http_request',
]