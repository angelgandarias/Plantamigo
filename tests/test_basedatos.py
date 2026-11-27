"""Para pruebas.

Se necesita una base de datos PostgreSQL vacía:
    TEST_DATABASE_URL=postgresql://... pytest tests
"""

import os

import psycopg
import pytest

URL_PRUEBAS = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL_PRUEBAS, reason="Falta TEST_DATABASE_URL")


@pytest.fixture
def bd(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", URL_PRUEBAS)
    from web import basedatos

    basedatos.crear_esquema()
    with basedatos.conectar() as conexion:
        conexion.execute(
            "TRUNCATE usuarios, plantas, datos_planta, usuarios_canciones RESTART IDENTITY CASCADE"
        )
    return basedatos


def test_crear_esquema_es_idempotente(bd):
    bd.crear_esquema()


def test_usuario_y_credenciales(bd):
    id_usuario = bd.crear_usuario("ana", "Ana@example.com", "secreta")

    usuario = bd.comprobar_credenciales("ana", "secreta")
    assert usuario["id_usuario"] == id_usuario
    assert usuario["puntos"] == 0
    assert "contrasena_hash" not in usuario
    assert bd.comprobar_credenciales("ana", "mala") is None


def test_email_unico_sin_distinguir_mayusculas(bd):
    bd.crear_usuario("ana", "ana@example.com", "x")
    with pytest.raises(psycopg.errors.UniqueViolation):
        bd.crear_usuario("otra", "ANA@example.com", "x")


def test_usuario_google(bd):
    #Primera vez: se crea con el nombre sacado del email y sin contraseña
    nuevo = bd.usuario_google("sub-1", "luis@gmail.com")
    assert nuevo["nombre_usuario"] == "luis"
    assert "contrasena_hash" not in nuevo
    assert bd.comprobar_credenciales("luis", "") is None  #no puede entrar con contraseña

    #Segunda vez: es el mismo usuario, no se duplica
    assert bd.usuario_google("sub-1", "luis@gmail.com")["id_usuario"] == nuevo["id_usuario"]

    #Cuenta existente con ese email: se vincula a Google
    id_ana = bd.crear_usuario("ana", "Ana@example.com", "secreta")
    assert bd.usuario_google("sub-2", "ana@example.com")["id_usuario"] == id_ana
    assert bd.comprobar_credenciales("ana", "secreta") is not None  #su contraseña sigue valiendo

    #Nombre de usuario ya cogido: se le añade un número
    assert bd.usuario_google("sub-3", "luis@otro.com")["nombre_usuario"] == "luis2"


def test_lecturas_de_planta(bd):
    id_usuario = bd.crear_usuario("ana", "ana@example.com", "x")
    id_planta = bd.crear_planta(id_usuario, "Girasol", "Sunny")

    bd.guardar_lectura(id_planta, temperatura=21.4, humedad=55)
    bd.guardar_lectura(id_planta, luz=300.5)

    lecturas = bd.ultimas_lecturas(id_planta)
    assert len(lecturas) == 2
    assert lecturas[0]["luz"] == pytest.approx(300.5)
    assert float(lecturas[1]["temperatura"]) == 21.4
    assert [p["nombre_planta"] for p in bd.plantas_de_usuario(id_usuario)] == ["Sunny"]


def test_obtener_planta(bd):
    id_planta = bd.crear_planta(bd.crear_usuario("ana", "a@e.com", "x"), "Girasol", "Sunny", "En el balcón")
    planta = bd.obtener_planta(id_planta)
    assert (planta["nombre_planta"], planta["tipo_planta"]) == ("Sunny", "Girasol")
    assert planta["descripcion_planta"] == "En el balcón"
    assert bd.obtener_planta(id_planta + 1) is None


def test_media_y_limpieza(bd):
    id_planta = bd.crear_planta(bd.crear_usuario("ana", "a@e.com", "x"), "Girasol", "Sunny")
    assert bd.media_y_limpieza(id_planta) is None  #sin lecturas

    #10 lecturas, una por minuto, con humedad 10, 20, ..., 100
    with bd.conectar() as conexion:
        for i in range(1, 11):
            conexion.execute(
                """INSERT INTO datos_planta (id_planta, fecha, humedad)
                   VALUES (%s, now() - make_interval(mins => %s), %s)""",
                (id_planta, 10 - i, i * 10),
            )

    resumen = bd.media_y_limpieza(id_planta)
    assert resumen["lecturas"] == 7
    assert resumen["humedad"] == 70.0  #media de 40..100
    assert resumen["temperatura"] is None  #ese sensor no tiene datos
    assert resumen["borradas"] == 3
    assert len(bd.ultimas_lecturas(id_planta)) == 7


def test_humedad_fuera_de_rango(bd):
    id_planta = bd.crear_planta(bd.crear_usuario("ana", "a@e.com", "x"), "Cactus", "Pinchos")
    with pytest.raises(psycopg.errors.CheckViolation):
        bd.guardar_lectura(id_planta, humedad=120)


def test_comprar_cancion(bd):
    id_usuario = bd.crear_usuario("ana", "ana@example.com", "x")
    with bd.conectar() as conexion:
        id_cancion = conexion.execute(
            "INSERT INTO canciones (nombre_cancion, precio_puntos) VALUES ('Prueba', 10)"
            " ON CONFLICT (nombre_cancion) DO UPDATE SET precio_puntos = 10 RETURNING id_cancion"
        ).fetchone()["id_cancion"]

    with pytest.raises(bd.PuntosInsuficientes):
        bd.comprar_cancion(id_usuario, id_cancion)
    assert bd.canciones_de_usuario(id_usuario) == []  #rollback

    bd.sumar_puntos(id_usuario, 15)
    bd.comprar_cancion(id_usuario, id_cancion)
    bd.comprar_cancion(id_usuario, id_cancion)  #repetir no cobra dos veces
    assert [c["nombre_cancion"] for c in bd.canciones_de_usuario(id_usuario)] == ["Prueba"]
    assert bd.sumar_puntos(id_usuario, 0) == 5
