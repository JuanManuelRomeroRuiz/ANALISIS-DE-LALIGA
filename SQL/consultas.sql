-- 1. Posesión media del Betis por temporada
SELECT temporada,
    ROUND(AVG(posesion_local)::numeric, 1) AS posesion_media
FROM partidos
WHERE posesion_local IS NOT NULL
GROUP BY temporada
ORDER BY temporada;

-- 2. Evolución de tiros por partido a lo largo del tiempo
SELECT time_bucket('1 month', fecha) AS mes,
    ROUND(AVG(tiros_local)::numeric, 1) AS tiros_media
FROM partidos
WHERE tiros_local IS NOT NULL
GROUP BY mes
ORDER BY mes;

-- 3. Goles marcados por el Betis por temporada
SELECT temporada,
    SUM(CASE WHEN equipo_local = (SELECT id FROM equipos WHERE nombre ILIKE '%betis%') 
        THEN goles_local ELSE goles_visitante END) AS goles_marcados,
    SUM(CASE WHEN equipo_local = (SELECT id FROM equipos WHERE nombre ILIKE '%betis%') 
        THEN goles_visitante ELSE goles_local END) AS goles_recibidos
FROM partidos
GROUP BY temporada
ORDER BY temporada;

-- 4. En qué minutos marca más goles el Betis
SELECT 
    minuto,
    COUNT(*) AS goles
FROM eventos
WHERE tipo_evento = 'goal'
AND equipo_id = (SELECT id FROM equipos WHERE nombre ILIKE '%betis%')
GROUP BY minuto
ORDER BY goles DESC
LIMIT 10;

-- 5. Rendimiento local vs visitante
SELECT
    CASE WHEN equipo_local = (SELECT id FROM equipos WHERE nombre ILIKE '%betis%')
        THEN 'Local' ELSE 'Visitante' END AS condicion,
    COUNT(*) AS partidos,
    ROUND(AVG(CASE WHEN equipo_local = (SELECT id FROM equipos WHERE nombre ILIKE '%betis%')
        THEN goles_local ELSE goles_visitante END)::numeric, 2) AS goles_marcados_media,
    ROUND(AVG(posesion_local)::numeric, 1) AS posesion_media
FROM partidos
WHERE posesion_local IS NOT NULL
GROUP BY condicion;

-- 6. Jugadores del Betis con mejor valoración media
SELECT 
    j.nombre,
    ROUND(AVG(e.valoracion)::numeric, 2) AS valoracion_media,
    COUNT(*) AS partidos_jugados
FROM estadisticas_jugador_partido e
JOIN jugadores j ON e.jugador_id = j.id
WHERE e.equipo_id = (SELECT id FROM equipos WHERE nombre ILIKE '%betis%')
AND e.valoracion IS NOT NULL
GROUP BY j.nombre
HAVING COUNT(*) >= 3
ORDER BY valoracion_media DESC
LIMIT 10;

-- 7. Tarjetas por mes usando time_bucket
SELECT 
    time_bucket('1 month', tiempo) AS mes,
    COUNT(*) AS tarjetas
FROM eventos
WHERE tipo_evento = 'card'
GROUP BY mes
ORDER BY mes;

-- 8. Evolución de la valoración de Isco partido a partido
SELECT 
    p.fecha,
    p.temporada,
    e.valoracion,
    e.minutos_jugados
FROM estadisticas_jugador_partido e
JOIN partidos p ON e.partido_id = p.id
JOIN jugadores j ON e.jugador_id = j.id
WHERE j.nombre ILIKE '%isco%'
ORDER BY p.fecha;

-- 9. Comparativa de rendimiento de Isco entre temporadas
SELECT 
    p.temporada,
    ROUND(AVG(e.valoracion)::numeric, 2) AS valoracion_media,
    ROUND(AVG(e.minutos_jugados)::numeric, 0) AS minutos_media,
    SUM(e.goles) AS goles_totales,
    SUM(e.asistencias) AS asistencias_totales
FROM estadisticas_jugador_partido e
JOIN partidos p ON e.partido_id = p.id
JOIN jugadores j ON e.jugador_id = j.id
WHERE j.nombre ILIKE '%isco%'
GROUP BY p.temporada
ORDER BY p.temporada;

-- 10. Primeros y últimos eventos de cada partido (first y last de TimescaleDB)
SELECT 
    p.fecha,
    first(e.tipo_evento, e.minuto) AS primer_evento,
    last(e.tipo_evento, e.minuto) AS ultimo_evento,
    COUNT(*) AS total_eventos
FROM eventos e
JOIN partidos p ON e.partido_id = p.id
GROUP BY p.fecha
ORDER BY p.fecha;

-- 11. Rendimiento del Betis por rival
SELECT 
    CASE 
        WHEN p.equipo_local = (SELECT id FROM equipos WHERE nombre ILIKE '%betis%')
        THEN e2.nombre
        ELSE e1.nombre
    END AS rival,
    COUNT(*) AS partidos,
    ROUND(AVG(CASE WHEN p.equipo_local = (SELECT id FROM equipos WHERE nombre ILIKE '%betis%')
        THEN p.goles_local ELSE p.goles_visitante END)::numeric, 2) AS goles_marcados_media,
    ROUND(AVG(CASE WHEN p.equipo_local = (SELECT id FROM equipos WHERE nombre ILIKE '%betis%')
        THEN p.goles_visitante ELSE p.goles_local END)::numeric, 2) AS goles_recibidos_media
FROM partidos p
JOIN equipos e1 ON p.equipo_local = e1.id
JOIN equipos e2 ON p.equipo_visitante = e2.id
WHERE p.equipo_local = (SELECT id FROM equipos WHERE nombre ILIKE '%betis%')
   OR p.equipo_visitante = (SELECT id FROM equipos WHERE nombre ILIKE '%betis%')
GROUP BY rival
ORDER BY goles_marcados_media DESC;