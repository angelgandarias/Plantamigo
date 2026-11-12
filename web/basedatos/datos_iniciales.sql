-- Catálogo inicial de canciones. Se puede ejecutar varias veces.

INSERT INTO canciones (nombre_cancion, precio_puntos) VALUES
    ('Himno de la Alegría', 0)
ON CONFLICT (nombre_cancion) DO NOTHING;
