import requests
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
import os
import time

print("Iniciando script...")

# Cargar variables del .env
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Configuración API
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY
}

# Configuración base de datos
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def test_conexion():
    try:
        conn = get_connection()
        print("Conexion a TimescaleDB correcta")
        conn.close()
    except Exception as e:
        print(f"Error de conexion: {e}")

def test_api():
    response = requests.get(f"{BASE_URL}/status", headers=HEADERS)
    data = response.json()
    if response.status_code == 200:
        restantes = data['response']['requests']['current']
        limite = data['response']['requests']['limit_day']
        print(f"API conectada correctamente")
        print(f"Peticiones usadas hoy: {restantes}/{limite}")
    else:
        print(f"Error en la API: {data}")


#OBTENER EQUIPOS DE LA API

def scrape_equipos():
    print("\n--- Scraping equipos ---")
    conn = get_connection()
    cur = conn.cursor()

    for temporada in ["2023", "2024"]:
        print(f"Obteniendo equipos de la temporada {temporada}...")
        response = requests.get(
            f"{BASE_URL}/teams",
            headers=HEADERS,
            params={"league": 140, "season": temporada}
        )
        data = response.json()

        equipos = data.get("response", [])
        print(f"Equipos encontrados: {len(equipos)}")

        for item in equipos:
            equipo = item["team"]
            sede = item["venue"]

            cur.execute("""
                INSERT INTO equipos (nombre, nombre_corto, ciudad, estadio, capacidad_est, fundacion, api_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (api_id) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    nombre_corto = EXCLUDED.nombre_corto,
                    ciudad = EXCLUDED.ciudad,
                    estadio = EXCLUDED.estadio,
                    capacidad_est = EXCLUDED.capacidad_est,
                    fundacion = EXCLUDED.fundacion
            """, (
                equipo.get("name"),
                equipo.get("code"),
                sede.get("city"),
                sede.get("name"),
                sede.get("capacity"),
                equipo.get("founded"),
                equipo.get("id")
            ))

        conn.commit()
        print(f"Equipos de {temporada} guardados correctamente")
        time.sleep(1)  # Pausa para no saturar la API

    cur.close()
    conn.close()
    print("--- Equipos completado ---\n")

# OBTENER JUGADORES DE LA API

def scrape_jugadores():
    print("\n--- Scraping jugadores del Betis ---")
    conn = get_connection()
    cur = conn.cursor()

    BETIS_API_ID = 543

    for temporada in ["2023", "2024"]:
        print(f"Obteniendo jugadores del Betis temporada {temporada}...")
        pagina = 1
        total_jugadores = 0

        while True:
            response = requests.get(
                f"{BASE_URL}/players",
                headers=HEADERS,
                params={"league": 140, "season": temporada, "team": BETIS_API_ID, "page": pagina}
            )
            data = response.json()
            jugadores = data.get("response", [])

            if not jugadores:
                break

            for item in jugadores:
                jugador = item["player"]
                stats = item["statistics"][0] if item["statistics"] else {}

                cur.execute("SELECT id FROM equipos WHERE api_id = %s", (BETIS_API_ID,))
                equipo_row = cur.fetchone()
                equipo_id = equipo_row[0] if equipo_row else None

                cur.execute("""
                    INSERT INTO jugadores (nombre, posicion, nacionalidad, fecha_nac, altura_cm, peso_kg, equipo_id, api_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (api_id) DO UPDATE SET
                        nombre = EXCLUDED.nombre,
                        posicion = EXCLUDED.posicion,
                        nacionalidad = EXCLUDED.nacionalidad,
                        fecha_nac = EXCLUDED.fecha_nac,
                        altura_cm = EXCLUDED.altura_cm,
                        peso_kg = EXCLUDED.peso_kg,
                        equipo_id = EXCLUDED.equipo_id
                """, (
                    jugador.get("name"),
                    stats.get("games", {}).get("position"),
                    jugador.get("nationality"),
                    jugador.get("birth", {}).get("date"),
                    int(jugador.get("height", "0 cm").replace(" cm", "")) if jugador.get("height") else None,
                    int(jugador.get("weight", "0 kg").replace(" kg", "")) if jugador.get("weight") else None,
                    equipo_id,
                    jugador.get("id")
                ))
                total_jugadores += 1

            conn.commit()
            total_paginas = data.get("paging", {}).get("total", 1)
            print(f"Temporada {temporada} - Pagina {pagina}/{total_paginas} procesada")

            if pagina >= total_paginas:
                break

            pagina += 1
            time.sleep(1)

        print(f"Total jugadores guardados para {temporada}: {total_jugadores}")

    cur.close()
    conn.close()
    print("--- Jugadores completado ---\n")

# OBTENER PARTIDOS DE LA API

def scrape_partidos():
    print("\n--- Scraping partidos del Betis ---")
    conn = get_connection()
    cur = conn.cursor()

    BETIS_API_ID = 543

    for temporada in ["2023", "2024"]:
        print(f"Obteniendo partidos del Betis temporada {temporada}...")

        response = requests.get(
            f"{BASE_URL}/fixtures",
            headers=HEADERS,
            params={"league": 140, "season": temporada, "team": BETIS_API_ID}
        )
        data = response.json()
        partidos = data.get("response", [])
        print(f"Partidos encontrados: {len(partidos)}")

        for item in partidos:
            fixture = item["fixture"]
            teams = item["teams"]
            goals = item["goals"]
            score = item["score"]

            # Buscar ids internos de los equipos
            cur.execute("SELECT id FROM equipos WHERE api_id = %s", (teams["home"]["id"],))
            local_row = cur.fetchone()
            cur.execute("SELECT id FROM equipos WHERE api_id = %s", (teams["away"]["id"],))
            visitante_row = cur.fetchone()

            local_id = local_row[0] if local_row else None
            visitante_id = visitante_row[0] if visitante_row else None

            cur.execute("""
                INSERT INTO partidos (fecha, equipo_local, equipo_visitante, goles_local, goles_visitante, jornada, temporada, estadio, arbitro, estado, api_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (api_id) DO UPDATE SET
                    goles_local = EXCLUDED.goles_local,
                    goles_visitante = EXCLUDED.goles_visitante,
                    estado = EXCLUDED.estado
            """, (
                fixture.get("date"),
                local_id,
                visitante_id,
                goals.get("home"),
                goals.get("away"),
                item["league"].get("round", "").replace("Regular Season - ", ""),
                f"{temporada}/{int(temporada)+1}",
                fixture.get("venue", {}).get("name"),
                fixture.get("referee"),
                fixture.get("status", {}).get("long"),
                fixture.get("id")
            ))

        conn.commit()
        print(f"Partidos de {temporada} guardados correctamente")
        time.sleep(1)

    cur.close()
    conn.close()
    print("--- Partidos completado ---\n")

# OBTENER EVENTOS DE LA API

def scrape_eventos():
    print("\n--- Scraping eventos ---")
    conn = get_connection()
    cur = conn.cursor()

    # Obtener todos los partidos de la BD
    cur.execute("SELECT id, api_id, fecha FROM partidos ORDER BY fecha")
    partidos = cur.fetchall()
    print(f"Total partidos a procesar: {len(partidos)}")

    for i, (partido_id, partido_api_id, fecha) in enumerate(partidos):
        print(f"Procesando partido {i+1}/{len(partidos)} (api_id: {partido_api_id})...")

        response = requests.get(
            f"{BASE_URL}/fixtures/events",
            headers=HEADERS,
            params={"fixture": partido_api_id}
        )
        data = response.json()
        eventos = data.get("response", [])

        for evento in eventos:
            equipo_api_id = evento.get("team", {}).get("id")
            jugador_api_id = evento.get("player", {}).get("id")
            jugador_rel_api_id = evento.get("assist", {}).get("id")

            # Buscar ids internos
            cur.execute("SELECT id FROM equipos WHERE api_id = %s", (equipo_api_id,))
            equipo_row = cur.fetchone()
            equipo_id = equipo_row[0] if equipo_row else None

            cur.execute("SELECT id FROM jugadores WHERE api_id = %s", (jugador_api_id,))
            jugador_row = cur.fetchone()
            jugador_id = jugador_row[0] if jugador_row else None

            cur.execute("SELECT id FROM jugadores WHERE api_id = %s", (jugador_rel_api_id,))
            jugador_rel_row = cur.fetchone()
            jugador_rel_id = jugador_rel_row[0] if jugador_rel_row else None

            minuto = evento.get("time", {}).get("elapsed")
            minuto_extra = evento.get("time", {}).get("extra")
            tipo = evento.get("type", "").lower().replace(" ", "_")
            detalle = evento.get("detail")
            comentarios = evento.get("comments")

            cur.execute("""
                INSERT INTO eventos (tiempo, partido_id, jugador_id, equipo_id, tipo_evento, minuto, minuto_extra, descripcion, es_penalti, es_propia_meta, jugador_rel_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                fecha,
                partido_id,
                jugador_id,
                equipo_id,
                tipo,
                minuto,
                minuto_extra,
                detalle,
                detalle == "Penalty" if tipo == "goal" else False,
                detalle == "Own Goal" if tipo == "goal" else False,
                jugador_rel_id
            ))

        conn.commit()
        print(f"  -> {len(eventos)} eventos guardados")
        time.sleep(0.5)

    cur.close()
    conn.close()
    print("--- Eventos completado ---\n")

# OBTENER ESTADISTICAS POR JUGADOR

def scrape_estadisticas():
    print("\n--- Scraping estadisticas por jugador ---")
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, api_id, fecha FROM partidos ORDER BY fecha")
    partidos = cur.fetchall()
    print(f"Total partidos a procesar: {len(partidos)}")

    for i, (partido_id, partido_api_id, fecha) in enumerate(partidos):
        print(f"Procesando partido {i+1}/{len(partidos)} (api_id: {partido_api_id})...")

        response = requests.get(
            f"{BASE_URL}/fixtures/players",
            headers=HEADERS,
            params={"fixture": partido_api_id}
        )
        data = response.json()
        equipos = data.get("response", [])

        total = 0
        for equipo_data in equipos:
            equipo_api_id = equipo_data.get("team", {}).get("id")

            cur.execute("SELECT id FROM equipos WHERE api_id = %s", (equipo_api_id,))
            equipo_row = cur.fetchone()
            equipo_id = equipo_row[0] if equipo_row else None

            for player_data in equipo_data.get("players", []):
                jugador = player_data.get("player", {})
                stats = player_data.get("statistics", [{}])[0]

                jugador_api_id = jugador.get("id")
                cur.execute("SELECT id FROM jugadores WHERE api_id = %s", (jugador_api_id,))
                jugador_row = cur.fetchone()
                jugador_id = jugador_row[0] if jugador_row else None

                games = stats.get("games", {})
                shots = stats.get("shots", {})
                goals = stats.get("goals", {})
                passes = stats.get("passes", {})
                tackles = stats.get("tackles", {})
                duels = stats.get("duels", {})
                cards = stats.get("cards", {})
                fouls = stats.get("fouls", {})

                cur.execute("""
                    INSERT INTO estadisticas_jugador_partido (
                        tiempo, partido_id, jugador_id, equipo_id,
                        minutos_jugados, titular,
                        goles, asistencias, disparos, disparos_puerta,
                        xg, xg_asistencia,
                        pases, pases_completados, precision_pases, pases_clave,
                        entradas, intercepciones,
                        duelos_ganados, duelos_totales,
                        tarjetas_amarillas, tarjetas_rojas,
                        faltas_cometidas, faltas_recibidas,
                        valoracion
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s, %s,
                        %s, %s, %s, %s,
                        %s, %s,
                        %s, %s, %s, %s,
                        %s, %s,
                        %s, %s,
                        %s, %s,
                        %s, %s,
                        %s
                    )
                """, (
                    fecha, partido_id, jugador_id, equipo_id,
                    games.get("minutes"),
                    games.get("captain") is not None,
                    goals.get("total") or 0,
                    goals.get("assists") or 0,
                    shots.get("total") or 0,
                    shots.get("on") or 0,
                    goals.get("saves"),
                    None,
                    passes.get("total") or 0,
                    passes.get("accuracy") or 0,
                    float(passes.get("accuracy") or 0),
                    passes.get("key") or 0,
                    tackles.get("total") or 0,
                    tackles.get("interceptions") or 0,
                    duels.get("won") or 0,
                    duels.get("total") or 0,
                    cards.get("yellow") or 0,
                    cards.get("red") or 0,
                    fouls.get("committed") or 0,
                    fouls.get("drawn") or 0,
                    float(games.get("rating") or 0) if games.get("rating") else None
                ))
                total += 1

        conn.commit()
        print(f"  -> {total} registros guardados")
        time.sleep(0.5)

    cur.close()
    conn.close()
    print("--- Estadisticas completado ---\n")

# OBTENER ESTADISTICAS POR PARTIDO

def scrape_estadisticas_partido():
    print("\n--- Scraping estadisticas de partidos ---")
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, api_id FROM partidos ORDER BY fecha")
    partidos = cur.fetchall()
    print(f"Total partidos a procesar: {len(partidos)}")

    for i, (partido_id, partido_api_id) in enumerate(partidos):
        print(f"Procesando partido {i+1}/{len(partidos)} (api_id: {partido_api_id})...")

        response = requests.get(
            f"{BASE_URL}/fixtures/statistics",
            headers=HEADERS,
            params={"fixture": partido_api_id}
        )
        data = response.json()
        equipos = data.get("response", [])

        if not equipos:
            print(f"  -> Sin datos")
            time.sleep(0.5)
            continue

        stats_local = {}
        stats_visit = {}

        # Obtener ids de equipos del partido
        cur.execute("SELECT equipo_local, equipo_visitante FROM partidos WHERE id = %s", (partido_id,))
        partido_row = cur.fetchone()
        local_id, visitante_id = partido_row

        for equipo_data in equipos:
            equipo_api_id = equipo_data.get("team", {}).get("id")
            cur.execute("SELECT id FROM equipos WHERE api_id = %s", (equipo_api_id,))
            equipo_row = cur.fetchone()
            equipo_id = equipo_row[0] if equipo_row else None

            stats = {}
            for stat in equipo_data.get("statistics", []):
                stats[stat["type"]] = stat["value"]

            if equipo_id == local_id:
                stats_local = stats
            else:
                stats_visit = stats

        def parse_pct(val):
            if val is None:
                return None
            if isinstance(val, str):
                return float(val.replace("%", ""))
            return float(val)

        cur.execute("""
            UPDATE partidos SET
                posesion_local      = %s,
                posesion_visitante  = %s,
                tiros_local         = %s,
                tiros_visitante     = %s,
                tiros_puerta_local  = %s,
                tiros_puerta_visit  = %s,
                corners_local       = %s,
                corners_visitante   = %s,
                faltas_local        = %s,
                faltas_visitante    = %s
            WHERE id = %s
        """, (
            parse_pct(stats_local.get("Ball Possession")),
            parse_pct(stats_visit.get("Ball Possession")),
            stats_local.get("Total Shots"),
            stats_visit.get("Total Shots"),
            stats_local.get("Shots on Goal"),
            stats_visit.get("Shots on Goal"),
            stats_local.get("Corner Kicks"),
            stats_visit.get("Corner Kicks"),
            stats_local.get("Fouls"),
            stats_visit.get("Fouls"),
            partido_id
        ))

        conn.commit()
        print(f"  -> Estadisticas guardadas")
        time.sleep(0.5)

    cur.close()
    conn.close()
    print("--- Estadisticas de partidos completado ---\n")


if __name__ == "__main__":
    print("Ejecutando tests...")
    test_conexion()
    test_api()
    scrape_equipos()
    scrape_jugadores()
    scrape_partidos()
    scrape_eventos()
    scrape_estadisticas()
    scrape_estadisticas_partido()