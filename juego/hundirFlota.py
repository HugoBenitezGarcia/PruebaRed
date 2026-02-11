import random


class Barco:
    def __init__(self, tamanio, nombre="Barco"):
        self.tamanio = tamanio
        self.nombre = nombre
        self.posiciones = []
        self.vidas = tamanio

    def __str__(self):
        return f"Barco: {self.nombre} - Tamaño: {self.tamanio} - Posiciones: {self.posiciones}"

    def __repr__(self):
        # Esto le dice a Python: "Cuando estés en una lista, usa lo mismo que en __str__"
        return self.__str__()


class Tablero:
    def __init__(self, dimension=8):
        self.dimension = dimension
        self.cuadricula = [["~"] * dimension for _ in range(dimension)]
        self.barcos = []
        self.ataques = []

    def agregar_barco(self, barco):
        barco_puesto = False

        while not barco_puesto:
            orientaciones = ["V", "H"]
            orientacion = random.choice(orientaciones)

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
                if orientacion == "H":
                    f, c = fila, columna + i
                else:
                    f, c = fila + i, columna

                coordenadas_posibles.append((f, c))

                # Si la casilla NO es agua, ya no es válido
                for i_f in range(f - 1, f + 2):
                    for i_c in range(c - 1, c + 2):

                        # A. Comprobamos si la casilla vecina está DENTRO del tablero
                        if 0 <= i_f < len(self.cuadricula) and 0 <= i_c < len(self.cuadricula):

                            # B. Si está dentro, miramos si NO es agua
                            if self.cuadricula[i_f][i_c] != "~":
                                es_valido = False

            if es_valido:
                for f, c in coordenadas_posibles:
                    self.cuadricula[f][c] = barco.nombre[0]

                barco.posiciones = coordenadas_posibles

                self.barcos.append(barco)

                barco_puesto = True

    def recibir_ataque(self, fila, columna):
        """
        Verifica un ataque recibido en (fila, columna).
        Actualiza el tablero y la vida de los barcos.
        Devuelve: 'Agua', 'Tocado', 'Hundido' o 'Repetido'.
        """

        # Leemos qué hay en la casilla antes de tocar nada
        contenido = self.cuadricula[fila][columna]
        estado_ataque = ""

        # --- CASO 1: YA SE HABÍA DISPARADO AHÍ ---
        if contenido == "X" or contenido == "o":
            estado_ataque = "Repetido"

        # --- CASO 2: ES AGUA ---
        elif contenido == "~":
            self.cuadricula[fila][columna] = "o"  # Marcamos fallo
            estado_ataque = "Agua"

        # --- CASO 3: ES UN BARCO ---
        else:
            # 1. Marcamos el golpe en el mapa visual
            self.cuadricula[fila][columna] = "X"

            # 2. Buscamos a qué barco le ha dolido (SIN usar break)
            barco_encontrado = False
            indice = 0

            # Recorremos la lista de barcos hasta encontrar al dueño o terminar la lista
            while indice < len(self.barcos) and not barco_encontrado:
                barco = self.barcos[indice]

                # Comprobamos si la coordenada está en este barco
                if (fila, columna) in barco.posiciones:
                    barco.vidas -= 1  # Restamos vida
                    barco_encontrado = True  # Esto detiene el while limpiamente

                    # Decidimos si es tocado o hundido
                    if barco.vidas == 0:
                        estado_ataque = "Hundido"
                    else:
                        estado_ataque = "Tocado"

                indice += 1  # Avanzamos al siguiente barco si no lo hemos encontrado

        return estado_ataque

    def imprimir(self):
        print()
        for fila in self.cuadricula:
            print(fila)
        print()

def main():
    tablero_juego = Tablero(dimension=8)

    flota = [
        Barco(5, "Portaaviones"),
        Barco(4, "Acorazado"),
        Barco(3, "Crucero"),
        Barco(3, "Submarino"),
        Barco(2, "Destructor")
    ]

    for barco in flota:
        tablero_juego.agregar_barco(barco)

    tablero_juego.imprimir()



    print(tablero_juego.recibir_ataque(2,2))




if __name__ == '__main__':
    main()