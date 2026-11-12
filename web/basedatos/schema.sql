-- Esquema de la base de datos de Plantamigo (PostgreSQL 13+).
-- Se puede ejecutar varias veces sin borrar datos.

BEGIN;

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario      INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_usuario  VARCHAR(50)  NOT NULL UNIQUE,
    email           VARCHAR(254) NOT NULL,
    contrasena_hash VARCHAR(255) NOT NULL,  -- nunca la contraseña en claro
    puntos          INTEGER      NOT NULL DEFAULT 0 CHECK (puntos >= 0),
    fecha_registro  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

--El email es único sin distinguir mayúsculas
CREATE UNIQUE INDEX IF NOT EXISTS uq_usuarios_email ON usuarios (lower(email));


CREATE TABLE IF NOT EXISTS plantas (
    id_planta          INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario         INTEGER      NOT NULL REFERENCES usuarios (id_usuario) ON DELETE CASCADE,
    tipo_planta        VARCHAR(100) NOT NULL,
    nombre_planta      VARCHAR(100) NOT NULL,
    descripcion_planta TEXT,
    fecha_alta         TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_plantas_usuario ON plantas (id_usuario);


--Melodías del buzzer que se desbloquean con puntos en la tienda
CREATE TABLE IF NOT EXISTS canciones (
    id_cancion     INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_cancion VARCHAR(100) NOT NULL UNIQUE,
    precio_puntos  INTEGER      NOT NULL DEFAULT 0 CHECK (precio_puntos >= 0)
);

--Canciones que tiene desbloqueadas cada usuario (relación N:M)
CREATE TABLE IF NOT EXISTS usuarios_canciones (
    id_usuario      INTEGER     NOT NULL REFERENCES usuarios (id_usuario) ON DELETE CASCADE,
    id_cancion      INTEGER     NOT NULL REFERENCES canciones (id_cancion) ON DELETE CASCADE,
    fecha_obtencion TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id_usuario, id_cancion)
);


--Lecturas periódicas de los sensores. Cada columna admite NULL porque
--un sensor puede fallar o no estar conectado en esa lectura.
CREATE TABLE IF NOT EXISTS datos_planta (
    id_planta    INTEGER      NOT NULL REFERENCES plantas (id_planta) ON DELETE CASCADE,
    fecha        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    temperatura  NUMERIC(4,1),                                          -- °C (DHT11)
    humedad      NUMERIC(4,1) CHECK (humedad BETWEEN 0 AND 100),        -- % HR (DHT11)
    luz          REAL         CHECK (luz >= 0),                         -- lux (BH1750)
    calidad_aire REAL         CHECK (calidad_aire >= 0),                -- ppm aprox. (MQ135)
    --La PK también sirve de índice para consultar el histórico de una planta por fechas
    PRIMARY KEY (id_planta, fecha)
);

COMMIT;
