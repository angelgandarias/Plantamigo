-- Datos de ejemplo para probar el esquema a mano.
-- Ejecutar después de schema.sql y datos_iniciales.sql. NO usar en producción.

BEGIN;

INSERT INTO usuarios (nombre_usuario, email, contrasena_hash, puntos) VALUES
    ('ana',   'ana@example.com',   'hash_de_prueba', 50),
    ('mikel', 'mikel@example.com', 'hash_de_prueba', 5);

INSERT INTO plantas (id_usuario, tipo_planta, nombre_planta, descripcion_planta)
SELECT id_usuario, 'Girasol', 'Sunny', 'En el balcón' FROM usuarios WHERE nombre_usuario = 'ana'
UNION ALL
SELECT id_usuario, 'Cactus', 'Pinchos', NULL FROM usuarios WHERE nombre_usuario = 'mikel';

INSERT INTO canciones (nombre_cancion, precio_puntos) VALUES
    ('Cumpleaños feliz', 20),
    ('Estrellita', 10)
ON CONFLICT (nombre_cancion) DO NOTHING;

INSERT INTO usuarios_canciones (id_usuario, id_cancion)
SELECT u.id_usuario, c.id_cancion
FROM usuarios u CROSS JOIN canciones c
WHERE u.nombre_usuario = 'ana' AND c.nombre_cancion IN ('Himno de la Alegría', 'Estrellita');

--Una lectura cada hora durante las últimas 24 h para cada planta
INSERT INTO datos_planta (id_planta, fecha, temperatura, humedad, luz, calidad_aire)
SELECT p.id_planta,
       date_trunc('hour', now()) - make_interval(hours => h),
       round((18 + random() * 8)::numeric, 1),
       round((40 + random() * 30)::numeric, 1),
       round((random() * 1000)::numeric, 1),
       round((400 + random() * 200)::numeric, 1)
FROM plantas p CROSS JOIN generate_series(0, 23) AS h;

COMMIT;


--===== Consultas de comprobación =====

--Plantas con su dueño
SELECT u.nombre_usuario, p.nombre_planta, p.tipo_planta
FROM plantas p JOIN usuarios u USING (id_usuario);

--Canciones desbloqueadas por usuario
SELECT u.nombre_usuario, c.nombre_cancion, c.precio_puntos
FROM usuarios_canciones uc
JOIN usuarios u USING (id_usuario)
JOIN canciones c USING (id_cancion)
ORDER BY u.nombre_usuario, c.nombre_cancion;

--Media de las últimas 24 h por planta
SELECT p.nombre_planta,
       round(avg(d.temperatura), 1) AS temperatura_media,
       round(avg(d.humedad), 1)     AS humedad_media,
       count(*)                     AS lecturas
FROM datos_planta d JOIN plantas p USING (id_planta)
WHERE d.fecha >= now() - interval '24 hours'
GROUP BY p.nombre_planta;
