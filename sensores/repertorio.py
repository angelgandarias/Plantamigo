"""
Formato de cada canción:
- "negra": duración de una negra en segundos (el tempo de la canción).
- "notas": lista de pares (nota, duración):
    * nota: nombre + octava, ej. "Mi4", "Sol#3", "Sib4".
      (# = sostenido, b = bemol)
    * duración en negras: 1 = negra, 0.5 = corchea, 1.5 = negra con
      puntillo, 2 = blanca, 4 = redonda.
"""

REPERTORIO = {
    "himno_alegria": {
        "negra": 0.4,
        "notas": [
            ("Mi5", 1), ("Mi5", 1), ("Fa5", 1), ("Sol5", 1),
            ("Sol5", 1), ("Fa5", 1), ("Mi5", 1), ("Re5", 1),
            ("Do5", 1), ("Do5", 1), ("Re5", 1), ("Mi5", 1),
            ("Mi5", 1.5), ("Re5", 0.5), ("Re5", 2),
           ("Mi5", 1), ("Mi5", 1), ("Fa5", 1), ("Sol5", 1),
            ("Sol5", 1), ("Fa5", 1), ("Mi5", 1), ("Re5", 1),
            ("Do5", 1), ("Do5", 1), ("Re5", 1), ("Mi5", 1),
            ("Re5", 1.5), ("Do5", 0.5), ("Do5", 2),
        ],
    },
    "mario_bros": {
        "negra": 0.3,
        "notas": [
            # Intro
            ("Mi6", 0.5), ("Mi6", 0.5), ("REST", 0.5), ("Mi6", 0.5), ("REST", 0.5), ("Do6", 0.5), ("Mi6", 0.5),
            ("Sol6", 1), ("REST", 1), ("Sol5", 0.5), ("REST", 1),

            # Tema principal (vuelta 1)
            ("Do6", 1.5), ("Sol5", 0.5), ("REST", 1), ("Mi5", 1.5),
            ("La5", 1), ("Si5", 1), ("La#5", 0.5), ("La5", 1),
            ("Sol5", 0.75), ("Mi6", 0.75), ("Sol6", 0.75), ("La6", 1), ("Fa6", 0.5), ("Sol6", 0.5),
            ("REST", 0.5), ("Mi6", 1), ("Do6", 0.5), ("Re6", 0.5), ("Si5", 1.5),

            # Tema principal (vuelta 2)
            ("Do6", 1.5), ("Sol5", 0.5), ("REST", 1), ("Mi5", 1.5),
            ("La5", 1), ("Si5", 1), ("La#5", 0.5), ("La5", 1),
            ("Sol5", 0.75), ("Mi6", 0.75), ("Sol6", 0.75), ("La6", 1), ("Fa6", 0.5), ("Sol6", 0.5),
            ("REST", 0.5), ("Mi6", 1), ("Do6", 0.5), ("Re6", 0.5), ("Si5", 1.5),

            # Cierre
            ("REST", 1), ("Sol6", 0.5), ("Fa#6", 0.5), ("Fa6", 0.5), ("Re#6", 1), ("Mi6", 0.5),
            ("REST", 0.5), ("Sol#5", 0.5), ("La5", 0.5), ("Do5", 0.5), ("REST", 0.5), ("La5", 0.5), ("Do6", 0.5), ("Re6", 0.5),
            ("REST", 1), ("Re#6", 1), ("REST", 0.5), ("Re6", 1.5),
            ("Do6", 2),
        ],
    },

}
