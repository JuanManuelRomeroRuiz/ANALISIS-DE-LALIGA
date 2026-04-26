CREATE TABLE equipos (
    id              SERIAL PRIMARY KEY,
    nombre          TEXT NOT NULL,
    nombre_corto    TEXT,
    ciudad          TEXT,
    estadio         TEXT,
    capacidad_est   INT,
    fundacion       INT,
    entrenador      TEXT,
    api_id          INT UNIQUE
);

CREATE TABLE jugadores (
    id              SERIAL PRIMARY KEY,
    nombre          TEXT NOT NULL,
    posicion        TEXT,
    nacionalidad    TEXT,
    fecha_nac       DATE,
    altura_cm       INT,
    peso_kg         INT,
    dorsal          INT,
    pie_dominante   TEXT,
    equipo_id       INT REFERENCES equipos(id),
    api_id          INT UNIQUE
);

CREATE TABLE partidos (
    id                  SERIAL PRIMARY KEY,
    fecha               TIMESTAMPTZ NOT NULL,
    equipo_local        INT REFERENCES equipos(id),
    equipo_visitante    INT REFERENCES equipos(id),
    goles_local         INT DEFAULT 0,
    goles_visitante     INT DEFAULT 0,
    jornada             INT,
    temporada           TEXT,
    estadio             TEXT,
    arbitro             TEXT,
    estado              TEXT,
    posesion_local      FLOAT,
    posesion_visitante  FLOAT,
    tiros_local         INT,
    tiros_visitante     INT,
    tiros_puerta_local  INT,
    tiros_puerta_visit  INT,
    corners_local       INT,
    corners_visitante   INT,
    faltas_local        INT,
    faltas_visitante    INT,
    xg_local            FLOAT,
    xg_visitante        FLOAT,
    api_id              INT UNIQUE
);

CREATE TABLE eventos (
    tiempo          TIMESTAMPTZ NOT NULL,
    partido_id      INT REFERENCES partidos(id),
    jugador_id      INT REFERENCES jugadores(id),
    equipo_id       INT REFERENCES equipos(id),
    tipo_evento     TEXT NOT NULL,
    minuto          INT,
    minuto_extra    INT,
    descripcion     TEXT,
    xg              FLOAT,
    es_penalti      BOOLEAN,
    es_propia_meta  BOOLEAN,
    jugador_rel_id  INT REFERENCES jugadores(id)
);

SELECT create_hypertable('eventos', 'tiempo');

CREATE TABLE estadisticas_jugador_partido (
    tiempo              TIMESTAMPTZ NOT NULL,
    partido_id          INT REFERENCES partidos(id),
    jugador_id          INT REFERENCES jugadores(id),
    equipo_id           INT REFERENCES equipos(id),
    minutos_jugados     INT,
    titular             BOOLEAN,
    goles               INT DEFAULT 0,
    asistencias         INT DEFAULT 0,
    disparos            INT DEFAULT 0,
    disparos_puerta     INT DEFAULT 0,
    xg                  FLOAT,
    xg_asistencia       FLOAT,
    pases               INT,
    pases_completados   INT,
    precision_pases     FLOAT,
    pases_clave         INT,
    entradas            INT,
    intercepciones      INT,
    despejes            INT,
    duelos_ganados      INT,
    duelos_totales      INT,
    tarjetas_amarillas  INT DEFAULT 0,
    tarjetas_rojas      INT DEFAULT 0,
    faltas_cometidas    INT,
    faltas_recibidas    INT,
    fueras_de_juego     INT,
    valoracion          FLOAT
);

SELECT create_hypertable('estadisticas_jugador_partido', 'tiempo');