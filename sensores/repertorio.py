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
    
}
