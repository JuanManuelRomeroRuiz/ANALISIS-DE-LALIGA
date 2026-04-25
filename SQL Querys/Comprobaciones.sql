-- Total de equipos
SELECT id, nombre, ciudad, estadio, fundacion FROM equipos ORDER BY nombre;

-- API_id del betis
SELECT id, nombre, api_id FROM equipos WHERE nombre ILIKE '%betis%';

-- Total de jugadores
SELECT COUNT(*) FROM jugadores;

-- Total de partidos
SELECT COUNT(*) FROM partidos;

-- Ver algunos partidos con nombres de equipos
SELECT 
    p.id,
    p.fecha,
    e1.nombre AS local,
    e2.nombre AS visitante,
    p.goles_local,
    p.goles_visitante,
    p.jornada,
    p.temporada,
    p.estado
FROM partidos p
JOIN equipos e1 ON p.equipo_local = e1.id
JOIN equipos e2 ON p.equipo_visitante = e2.id
ORDER BY p.fecha
LIMIT 10;

--Total de eventos
SELECT COUNT(*) FROM eventos;

-- Ver algunos eventos
SELECT 
    p.fecha,
    p.temporada,
    COUNT(e.partido_id) AS num_eventos
FROM partidos p
LEFT JOIN eventos e ON p.id = e.partido_id
GROUP BY p.fecha, p.temporada
ORDER BY p.fecha;

-- Ver eventos por tipo
SELECT tipo_evento, COUNT(*) 
FROM eventos 
GROUP BY tipo_evento 
ORDER BY COUNT(*) DESC;

-- Total de estadisticas
SELECT COUNT(*) FROM estadisticas_jugador_partido;

-- Ver estadisticas
SELECT 
    p.fecha,
    p.temporada,
    p.posesion_local,
    p.posesion_visitante,
    p.tiros_local,
    p.tiros_visitante,
    p.corners_local,
    p.corners_visitante,
    p.faltas_local,
    p.faltas_visitante
FROM partidos p
WHERE posesion_local IS NOT NULL
ORDER BY p.fecha;