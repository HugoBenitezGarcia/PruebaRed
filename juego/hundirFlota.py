import random


class Barco:
    def __init__(self, tamanio, nombre="Barco"):
        self.tamanio = tamanio
        self.nombre = nombre
        self.posiciones = []
        self.vidas = tamanio


class Tablero:
    def __init__(self, dimension=8):
        self.dimension = dimension
        self.cuadricula = [["~"] * dimension for _ in range(dimension)]
        self.barcos = []
        self.ataques_realizados = []

        # Atributos para la IA
        self.cola_objetivos = []
        self.ultimo_ataque_exitoso = None
        self.casillas_descartadas = set()
        self.impactos_barco_actual = []

    def agregar_barco(self, barco):
        barco_puesto = False
        while not barco_puesto:
            orientacion = random.choice(["V", "H"])
            limite = self.dimension - barco.tamanio
            if orientacion == "H":
                fila = random.randint(0, self.dimension - 1)
                columna = random.randint(0, limite)
            else:
                fila = random.randint(0, limite)
                columna = random.randint(0, self.dimension - 1)

            es_valido = True
            coordenadas_posibles = []
            for i in range(barco.tamanio):
                f, c = (fila, columna + i) if orientacion == "H" else (fila + i, columna)
                coordenadas_posibles.append((f, c))
                for i_f in range(f - 1, f + 2):
                    for i_c in range(c - 1, c + 2):
                        if 0 <= i_f < self.dimension and 0 <= i_c < self.dimension:
                            if self.cuadricula[i_f][i_c] != "~":
                                es_valido = False
            if es_valido:
                for f, c in coordenadas_posibles:
                    self.cuadricula[f][c] = barco.nombre[0]
                barco.posiciones = coordenadas_posibles
                self.barcos.append(barco)
                barco_puesto = True

    def recibir_ataque(self, columna_letra, fila):
        """Recibe ataque con formato (letra, número)."""
        diccionario_letras = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
        columna_num = diccionario_letras[columna_letra]
        contenido = self.cuadricula[fila][columna_num]

        if contenido == "X" or contenido == "o":
            return "YA DISPARADO"
        elif contenido == "~":
            self.cuadricula[fila][columna_num] = "o"
            return "AGUA"
        else:
            self.cuadricula[fila][columna_num] = "X"
            for barco in self.barcos:
                if (fila, columna_num) in barco.posiciones:
                    barco.vidas -= 1
                    return "HUNDIDO" if barco.vidas == 0 else "TOCADO"
        return "ERROR"

    def _casilla_valida_para_atacar(self, fila, col_num):
        """Verifica si una casilla es válida para atacar."""
        if not (0 <= fila < self.dimension and 0 <= col_num < self.dimension):
            return False
        letra_c = chr(97 + col_num)
        if [letra_c, fila] in self.ataques_realizados:
            return False
        if (fila, col_num) in self.casillas_descartadas:
            return False
        return True

    def _descartar_adyacentes(self, fila, col_num):
        """Marca las casillas adyacentes (incluidas diagonales) como descartadas."""
        for df in range(-1, 2):
            for dc in range(-1, 2):
                vf, vc = fila + df, col_num + dc
                if 0 <= vf < self.dimension and 0 <= vc < self.dimension:
                    self.casillas_descartadas.add((vf, vc))

    def atacar(self):
        """Estrategia inteligente con patrón de ajedrez. Devuelve [letra, número]."""
        diccionario_num_a_let = {i: chr(97 + i) for i in range(8)}

        fila, col_num = None, None

        # MODO DESTRUCCIÓN: Atacar objetivos prioritarios
        while self.cola_objetivos and fila is None:
            candidato = self.cola_objetivos.pop(0)
            if self._casilla_valida_para_atacar(candidato[0], candidato[1]):
                fila, col_num = candidato

        # MODO CAZA: Patrón de ajedrez
        if fila is None:
            casillas_ajedrez = [
                (f, c) for f in range(self.dimension)
                for c in range(self.dimension)
                if (f + c) % 2 == 0 and self._casilla_valida_para_atacar(f, c)
            ]

            if casillas_ajedrez:
                fila, col_num = random.choice(casillas_ajedrez)
            else:
                # Fallback: cualquier casilla válida restante
                casillas_restantes = [
                    (f, c) for f in range(self.dimension)
                    for c in range(self.dimension)
                    if self._casilla_valida_para_atacar(f, c)
                ]
                if casillas_restantes:
                    fila, col_num = random.choice(casillas_restantes)

        if fila is not None:
            columna_letra = diccionario_num_a_let[col_num]
            intento = [columna_letra, fila]  # (letra, número)
            self.ataques_realizados.append(intento)
            self.ultimo_ataque_exitoso = (fila, col_num)
            return intento

    def registrar_resultado(self, resultado):
        """Actualiza la estrategia según el resultado del último ataque."""
        f, c = self.ultimo_ataque_exitoso

        if resultado == "TOCADO":
            self.impactos_barco_actual.append((f, c))
            diagonales = [(f - 1, c - 1), (f - 1, c + 1), (f + 1, c - 1), (f + 1, c + 1)]
            for vf, vc in diagonales:
                if 0 <= vf < self.dimension and 0 <= vc < self.dimension:
                    self.casillas_descartadas.add((vf, vc))

            vecinos = [(f - 1, c), (f + 1, c), (f, c - 1), (f, c + 1)]
            for vf, vc in vecinos:
                if self._casilla_valida_para_atacar(vf, vc) and (vf, vc) not in self.cola_objetivos:
                    self.cola_objetivos.append((vf, vc))

        elif resultado == "HUNDIDO":
            self.impactos_barco_actual.append((f, c))
            for impacto_f, impacto_c in self.impactos_barco_actual:
                self._descartar_adyacentes(impacto_f, impacto_c)
            self.impactos_barco_actual = []
            self.cola_objetivos = []

        elif resultado == "AGUA":
            self.casillas_descartadas.add((f, c))

    def quedan_barcos_vivos(self):
        return any(barco.vidas > 0 for barco in self.barcos)

    def imprimir(self, ocultar_barcos=False):
        """Imprime el tablero. Si ocultar_barcos=True, no muestra los barcos."""
        print("\n    ", end="")
        for letra in "ABCDEFGH"[:self.dimension]:
            print(letra, end=" ")
        print()

        for idx, fila in enumerate(self.cuadricula):
            print(f"  {idx} ", end="")
            for celda in fila:
                if ocultar_barcos and celda not in ["~", "X", "o"]:
                    print("~", end=" ")
                else:
                    print(celda, end=" ")
            print()
        print()


def main():
    tablero_jugador = Tablero(dimension=8)
    tablero_oponente = Tablero(dimension=8)

    flota_jugador = [
        Barco(5, "Portaaviones"), Barco(4, "Acorazado"),
        Barco(3, "Crucero"), Barco(3, "Submarino"), Barco(2, "Destructor")
    ]
    flota_oponente = [
        Barco(5, "Portaaviones"), Barco(4, "Acorazado"),
        Barco(3, "Crucero"), Barco(3, "Submarino"), Barco(2, "Destructor")
    ]

    for barco in flota_jugador:
        tablero_jugador.agregar_barco(barco)
    for barco in flota_oponente:
        tablero_oponente.agregar_barco(barco)

    print("=" * 50)
    print("         BATALLA NAVAL - IA vs IA")
    print("=" * 50)

    print("\nTU TABLERO (tus barcos):")
    tablero_jugador.imprimir(ocultar_barcos=False)

    print("\nTABLERO ENEMIGO (tus ataques):")
    tablero_oponente.imprimir(ocultar_barcos=True)

    jugar = True
    turno = 1

    while jugar:
        print(f"\n{'='*50}")
        print(f"TURNO {turno}")
        print(f"{'='*50}")

        # TURNO JUGADOR (IA)
        print("\n--- Tu Turno ---")
        columna, fila = tablero_jugador.atacar()
        estado = tablero_oponente.recibir_ataque(columna, fila)
        print(f"➤ Atacas en ({columna.upper()}, {fila}): {estado}")
        tablero_jugador.registrar_resultado(estado)

        if not tablero_oponente.quedan_barcos_vivos():
            print("\n" + "=" * 50)
            print("¡VICTORIA!")
            print("Has hundido toda la flota enemiga")
            print("=" * 50)
            print("\nTABLERO ENEMIGO FINAL:")
            tablero_oponente.imprimir(ocultar_barcos=False)
            jugar = False
            continue

        # TURNO OPONENTE
        print("\n--- Turno del Oponente ---")
        columna, fila = tablero_oponente.atacar()  # (letra, número)
        estado = tablero_jugador.recibir_ataque(columna, fila)
        print(f"➤ Enemigo ataca en ({columna.upper()}, {fila}): {estado}")
        tablero_oponente.registrar_resultado(estado)

        print("\n TU TABLERO:")
        tablero_jugador.imprimir(ocultar_barcos=False)

        print("\nTABLERO ENEMIGO:")
        tablero_oponente.imprimir(ocultar_barcos=True)

        if not tablero_jugador.quedan_barcos_vivos():
            print("\n" + "=" * 50)
            print("DERROTA")
            print("El enemigo hundió tu flota")
            print("=" * 50)
            jugar = False

        turno += 1


if __name__ == '__main__':
    main()