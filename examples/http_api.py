"""
Ejemplos de uso del framework con HTTP.

🎯 AQUÍ SE VE CÓMO SE USA IO MONAD CON HTTP
"""

from core.http_stream import (
    HttpStream, HttpRequest, HttpMethod,
    fetch_json, fetch_all_json, HttpPipeline,
    http_get, http_post
)
from core.io_monad import IO, io_print
from core.stream import Stream
from core.either import Either
from typing import List, Dict
import time


# ==========================================
# EJEMPLO 1: FETCHING SIMPLE DE API
# ==========================================

def ejemplo_fetch_simple():
    """
    Ejemplo básico: Fetch de una API pública.

    🎯 Muestra cómo IO encapsula la petición HTTP
    """
    print("\n=== EJEMPLO 1: Fetch Simple ===\n")

    # 1. Crear la operación IO (NO se ejecuta todavía)
    fetch_operation = fetch_json('https://api.github.com/users/octocat')

    print("✅ Operación IO creada (aún no ejecutada)")

    # 2. Componer con otras operaciones
    program = (
            io_print("🔄 Fetching datos de GitHub...")
            >> fetch_operation
            .map(lambda either: either.map(lambda data: data.get('name', 'Unknown')))
            .map(lambda either: either.get_or_else('Error fetching'))
            .flat_map(lambda name: io_print(f"👤 Usuario: {name}"))
    )

    print("✅ Pipeline completo creado (aún no ejecutado)")

    # 3. Ejecutar TODO de una vez
    print("\n🚀 Ejecutando pipeline...\n")
    program.run()


# ==========================================
# EJEMPLO 2: PROCESAMIENTO DE MÚLTIPLES APIs
# ==========================================

def ejemplo_multiples_apis():
    """
    Fetches de múltiples APIs y combina resultados.

    🎯 Composición de múltiples operaciones IO
    """
    print("\n=== EJEMPLO 2: Múltiples APIs ===\n")

    # URLs a consultar
    urls = [
        'https://api.github.com/users/torvalds',
        'https://api.github.com/users/gvanrossum',
        'https://api.github.com/users/hadley',
    ]

    # Crear pipeline
    program = (
            io_print("🔄 Fetching datos de múltiples usuarios...")
            >> fetch_all_json(urls)
            .map(lambda results: [
        r.get_or_else({}).get('login', 'Unknown')
        for r in results
    ])
            .flat_map(lambda usernames: io_print(f"👥 Usuarios: {', '.join(usernames)}"))
    )

    # Ejecutar
    program.run()


# ==========================================
# EJEMPLO 3: HTTP STREAM CON TRANSFORMACIONES
# ==========================================

def ejemplo_http_stream():
    """
    Usa HttpStream para procesar múltiples peticiones.

    🎯 Stream + IO trabajando juntos
    """
    print("\n=== EJEMPLO 3: HTTP Stream ===\n")

    # Crear stream de URLs
    repos = ['python/cpython', 'torvalds/linux', 'facebook/react']
    urls = [f'https://api.github.com/repos/{repo}' for repo in repos]

    # Crear HTTP Stream
    stream = (
        HttpStream.from_urls(urls)
        .with_headers({'Accept': 'application/json'})
        .take(3)
    )

    # Ejecutar y procesar
    program = (
            io_print("🔄 Procesando repositorios...\n")
            >> stream.execute()
            .map(lambda response_stream: response_stream.to_list())
            .map(lambda responses: [
        r.get_or_else(None) for r in responses
    ])
            .map(lambda responses: [
        r for r in responses if r and r.is_success()
    ])
            .flat_map(lambda responses:
                      io_print(f"✅ Fetched {len(responses)} repositorios exitosamente")
                      )
    )

    program.run()


# ==========================================
# EJEMPLO 4: PIPELINE DE DATOS CON RETRY
# ==========================================

def ejemplo_con_retry():
    """
    Pipeline con manejo de errores y retry.

    🎯 IO con retry automático
    """
    print("\n=== EJEMPLO 4: Retry Automático ===\n")

    # API que puede fallar
    url = 'https://api.github.com/rate_limit'

    # Crear operación con retry
    fetch_with_retry = (
        fetch_json(url)
        .retry(max_attempts=3)
        .map(lambda either: either.map(lambda data: data.get('rate', {})))
    )

    program = (
            io_print("🔄 Fetching con retry automático...")
            >> fetch_with_retry
            .flat_map(lambda either:
                      either
                      .map(lambda rate: io_print(f"✅ Rate limit: {rate}"))
                      .get_or_else(io_print("❌ Error después de 3 intentos"))
                      )
    )

    program.run()


# ==========================================
# EJEMPLO 5: AGREGACIÓN DE MÚLTIPLES ENDPOINTS
# ==========================================

def ejemplo_agregacion():
    """
    Agrega datos de múltiples endpoints.

    🎯 Composición compleja con IO
    """
    print("\n=== EJEMPLO 5: Agregación de Endpoints ===\n")

    endpoints = {
        'user': 'https://api.github.com/users/octocat',
        'repos': 'https://api.github.com/users/octocat/repos',
    }

    def aggregate_user_data(data: Dict[str, dict]) -> dict:
        """Función pura que agrega los datos."""
        return {
            'name': data['user'].get('name', 'Unknown'),
            'public_repos': data['user'].get('public_repos', 0),
            'repo_count': len(data['repos']),
        }

    program = (
            io_print("🔄 Agregando datos de usuario...")
            >> HttpPipeline.aggregate_endpoints(endpoints, aggregate_user_data)
            .flat_map(lambda either:
                      either
                      .map(lambda summary: io_print(f"📊 Resumen: {summary}"))
                      .get_or_else(io_print("❌ Error en agregación"))
                      )
    )

    program.run()


# ==========================================
# EJEMPLO 6: DATOS PAGINADOS
# ==========================================

def ejemplo_paginacion():
    """
    Fetches de datos paginados.

    🎯 IO manejando paginación automáticamente
    """
    print("\n=== EJEMPLO 6: Datos Paginados ===\n")

    # API paginada (ejemplo ficticio)
    base_url = 'https://api.github.com/users/octocat/repos'

    program = (
            io_print("🔄 Fetching datos paginados...")
            >> HttpPipeline.fetch_paginated(base_url, max_pages=3, page_param='page')
            .map(lambda pages: [p for p in pages if p.is_right])
            .flat_map(lambda pages:
                      io_print(f"✅ Fetched {len(pages)} páginas exitosamente")
                      )
    )

    program.run()


# ==========================================
# EJEMPLO 7: POST REQUEST CON DATOS
# ==========================================

def ejemplo_post_request():
    """
    Envía datos a una API con POST.

    🎯 IO para operaciones POST
    """
    print("\n=== EJEMPLO 7: POST Request ===\n")

    # Datos a enviar
    post_data = {
        'title': 'Test from IO Monad',
        'body': 'This is a test',
        'userId': 1
    }

    # Crear operación POST
    post_operation = http_post(
        'https://jsonplaceholder.typicode.com/posts',
        body=post_data
    )

    program = (
            io_print("📤 Enviando POST request...")
            >> post_operation
            .map(lambda either: either.bind(lambda resp: resp.json()))
            .flat_map(lambda either:
                      either
                      .map(lambda data: io_print(f"✅ Post creado con ID: {data.get('id')}"))
                      .get_or_else(io_print("❌ Error en POST"))
                      )
    )

    program.run()


# ==========================================
# EJEMPLO 8: STREAM PROCESSING REAL-TIME
# ==========================================

def ejemplo_stream_realtime():
    """
    Simula procesamiento de stream en tiempo real.

    🎯 Stream + IO para datos en tiempo real
    """
    print("\n=== EJEMPLO 8: Stream Real-time ===\n")

    # Simular URLs que se generan dinámicamente
    def generate_urls():
        """Generador de URLs."""
        base = 'https://api.github.com/users'
        users = ['octocat', 'torvalds', 'gvanrossum']
        for user in users:
            yield f"{base}/{user}"
            time.sleep(0.5)  # Simular delay

    # Crear stream desde generador
    url_stream = Stream(generate_urls)

    # Procesar stream
    program = (
            io_print("🔄 Procesando stream en tiempo real...\n")
            >> IO(lambda:
                  url_stream
                  .map(lambda url: HttpRequest(url=url))
                  )
            .flat_map(lambda request_stream:
                      HttpStream(request_stream).execute()
                      )
            .map(lambda response_stream: response_stream.to_list())
            .map(lambda responses: [
        r.get_or_else(None) for r in responses if r.is_right
    ])
            .flat_map(lambda valid_responses:
                      io_print(f"\n✅ Procesadas {len(valid_responses)} respuestas")
                      )
    )

    program.run()


# ==========================================
# EJEMPLO 9: ERROR HANDLING COMPLETO
# ==========================================

def ejemplo_error_handling():
    """
    Manejo completo de errores con Either + IO.

    🎯 IO con manejo robusto de errores
    """
    print("\n=== EJEMPLO 9: Error Handling ===\n")

    # URL que puede fallar
    bad_url = 'https://api.github.com/users/nonexistentuser12345'
    good_url = 'https://api.github.com/users/octocat'

    def fetch_with_fallback(primary_url: str, fallback_url: str) -> IO[dict]:
        """Intenta primary, si falla usa fallback."""
        return (
            fetch_json(primary_url)
            .map(lambda either:
                 either.or_else(fetch_json(fallback_url).run())
                 )
            .map(lambda either: either.get_or_else({'error': 'Both failed'}))
        )

    program = (
            io_print("🔄 Fetching con fallback...")
            >> fetch_with_fallback(bad_url, good_url)
            .flat_map(lambda data:
                      io_print(f"✅ Datos: {data.get('login', 'N/A')}")
                      )
    )

    program.run()


# ==========================================
# EJEMPLO 10: COMPOSICIÓN COMPLEJA
# ==========================================

def ejemplo_composicion_compleja():
    """
    Pipeline complejo que combina todo.

    🎯 Composición avanzada de Stream + IO + Either
    """
    print("\n=== EJEMPLO 10: Composición Compleja ===\n")

    # 1. Obtener lista de repos
    # 2. Para cada repo, obtener detalles
    # 3. Filtrar por estrellas
    # 4. Generar reporte

    def get_repos(username: str) -> IO[Either[Exception, list]]:
        """Obtiene repos de un usuario."""
        url = f'https://api.github.com/users/{username}/repos'
        return fetch_json(url).map(lambda e: e.map(lambda d: d[:3]))  # Solo primeros 3

    def get_repo_details(repo_url: str) -> IO[Either[Exception, dict]]:
        """Obtiene detalles de un repo."""
        return fetch_json(repo_url)

    def generate_report(repos: list[dict]) -> str:
        """Genera reporte (función pura)."""
        lines = ["📊 REPORTE DE REPOSITORIOS", "=" * 40]
        for repo in repos:
            stars = repo.get('stargazers_count', 0)
            name = repo.get('name', 'Unknown')
            lines.append(f"⭐ {name}: {stars} estrellas")
        return '\n'.join(lines)

    # Pipeline completo
    program = (
            io_print("🔄 Generando reporte complejo...\n")
            >> get_repos('octocat')
            .map(lambda either: either.get_or_else([]))
            .map(lambda repos: [repo['url'] for repo in repos])
            .flat_map(lambda urls:
                      IO.traverse(urls, get_repo_details)
                      )
            .map(lambda results: [
        r.get_or_else({}) for r in results if r.is_right
    ])
            .map(lambda repos: [
        r for r in repos if r.get('stargazers_count', 0) > 0
    ])
            .map(generate_report)
            .flat_map(io_print)
    )

    program.run()


# ==========================================
# MAIN - EJECUTAR TODOS LOS EJEMPLOS
# ==========================================

if __name__ == "__main__":
    ejemplos = [
        ("Fetch Simple", ejemplo_fetch_simple),
        ("Múltiples APIs", ejemplo_multiples_apis),
        ("HTTP Stream", ejemplo_http_stream),
        ("Con Retry", ejemplo_con_retry),
        ("Agregación", ejemplo_agregacion),
        ("Paginación", ejemplo_paginacion),
        ("POST Request", ejemplo_post_request),
        ("Stream Real-time", ejemplo_stream_realtime),
        ("Error Handling", ejemplo_error_handling),
        ("Composición Compleja", ejemplo_composicion_compleja),
    ]

    print("\n" + "=" * 60)
    print("🚀 FRAMEWORK DE STREAM PROCESSING CON IO MONAD")
    print("=" * 60)

    for i, (nombre, ejemplo) in enumerate(ejemplos, 1):
        print(f"\n[{i}/{len(ejemplos)}] {nombre}")
        input("Presiona ENTER para continuar...")
        try:
            ejemplo()
        except Exception as e:
            print(f"❌ Error: {e}")

        if i < len(ejemplos):
            print("\n" + "-" * 60)

    print("\n" + "=" * 60)
    print("✅ TODOS LOS EJEMPLOS COMPLETADOS")
    print("=" * 60 + "\n")