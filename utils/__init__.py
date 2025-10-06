"""
Utils module - Operadores funcionales y utilidades.

Exporta funciones de alto nivel para programación funcional.
"""

from .operators import (
    # Composición
    compose,
    pipe,

    # Currying y aplicación parcial
    curry,
    partial,

    # Transformaciones
    fmap,
    ffilter,
    freduce,
    flatten,
    flat_map,

    # Operadores matemáticos
    add,
    subtract,
    multiply,
    divide,
    power,
    modulo,

    # Operadores de comparación
    equals,
    not_equals,
    greater_than,
    less_than,
    greater_or_equal,
    less_or_equal,

    # Utilidades
    identity,
    const,
    flip,
    tap,
    memoize,

    # Predicados
    is_even,
    is_odd,
    is_positive,
    is_negative,
    is_zero,
    is_empty,
    is_none,
    is_not_none,
)

__all__ = [
    # Composición
    'compose',
    'pipe',

    # Currying
    'curry',
    'partial',

    # Transformaciones
    'fmap',
    'ffilter',
    'freduce',
    'flatten',
    'flat_map',

    # Operadores matemáticos
    'add',
    'subtract',
    'multiply',
    'divide',
    'power',
    'modulo',

    # Operadores de comparación
    'equals',
    'not_equals',
    'greater_than',
    'less_than',
    'greater_or_equal',
    'less_or_equal',

    # Utilidades
    'identity',
    'const',
    'flip',
    'tap',
    'memoize',

    # Predicados
    'is_even',
    'is_odd',
    'is_positive',
    'is_negative',
    'is_zero',
    'is_empty',
    'is_none',
    'is_not_none',
]
