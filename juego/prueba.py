import ipaddress
import socket
import time
import uuid
from hundirFlota import *

PUERTO = 4000
ID = str(uuid.uuid4())
NOMBRE = "Jugador_Python"


def obtener_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def calcular_broadcast():
    return str(ipaddress.IPv4Network(obtener_ip() + "/21", strict=False).broadcast_address)


def buscar_partida():
    dir_broadcast = calcular_broadcast()
    mi_ip = obtener_ip()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", PUERTO))
    sock.settimeout(1.0)

    estado = "ESPERANDO"
    soy_host = False
    oponente = None

    print(f"[INFO] Mi IP: {mi_ip}")
    print("[BUSCANDO] Buscando partida...")

    while estado == "ESPERANDO":
        mensaje = f"DESCUBRIR;{ID};{NOMBRE}"
        sock.sendto(mensaje.encode(), (dir_broadcast, PUERTO))

        try:
            data, addr = sock.recvfrom(1024)
            ip_oponente, _ = addr
            modo, id_oponente, nombre_oponente = data.decode().split(";")

            if modo == "DESCUBRIR":
                if id_oponente != ID and ID < id_oponente:
                    print(f"[ACEPTADO] Aceptando a {nombre_oponente} ({ip_oponente})")

                    sock.sendto(
                        f"ACEPTADO;{ID};{NOMBRE}".encode(),
                        addr
                    )

                    oponente = (ip_oponente, nombre_oponente)
                    soy_host = True
                    estado = "JUGANDO"
                else:
                    print("[INFO] Esperando respuesta...")

            elif modo == "ACEPTADO":
                print(f"[ACEPTADO] {nombre_oponente} me ha aceptado")

                oponente = (ip_oponente, nombre_oponente)
                soy_host = False
                estado = "JUGANDO"

        except socket.timeout:
            pass

        if estado == "ESPERANDO":
            time.sleep(1)

    sock.close()
    return oponente[0], soy_host, oponente[1]


def abrir_servidor():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((obtener_ip(), PUERTO))
    s.listen(1)
    print("[HOST] Esperando conexión TCP...")
    conn, addr = s.accept()
    print("[HOST] Conectado con", addr)
    return conn


def conectar_cliente(ip_rival):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip_rival, PUERTO))
    print("[CLIENTE] Conectado al host")
    return s


def recibir_mensajes(sock):
    while True:
        try:
            mensaje = sock.recv(1024).decode()
            if mensaje:
                print(f"[RIVAL]: {mensaje}")
        except:
            break

if __name__ == "__main__":
    resultado = buscar_partida()

    if resultado:
        ip_rival, soy_host, nombre_rival = resultado
        print(f"\nPARTIDA ENCONTRADA contra {nombre_rival}")

        # --- Preparar el tablero propio (igual para host y cliente) ---
        mi_tablero = Tablero(dimension=8)
        flota = [
            Barco(5, "Portaaviones"),
            Barco(4, "Acorazado"),
            Barco(3, "Crucero"),
            Barco(3, "Submarino"),
            Barco(2, "Destructor")
        ]
        for barco in flota:
            mi_tablero.agregar_barco(barco)

        print("\n[TABLERO] Este es tu tablero:")
        mi_tablero.imprimir()

        if soy_host:
            print("[ROL] HOST")
            conn = abrir_servidor()

            # El host empieza disparando (mi_turno = True)
            mi_turno = True

            # aqui iria un while del bucle de la partida
            while True:
                if mi_turno:
                    # con esto: te envias mensajes y seguido
                    coords = input("Tu disparo (fila,columna): ")
                    fila, columna = map(int, coords.split(","))
                    disparo = f"{fila},{columna}"

                    conn.sendall(disparo.encode())

                    # Empieza a jugar el host
                    respuesta = conn.recv(1024).decode().strip()
                    print(f"[RESULTADO] {respuesta}")

                    if respuesta == "Hundido":
                        # Comprobamos si todos los barcos del rival están hundidos
                        conn.sendall("COMPROBANDO".encode())
                        estado_rival = conn.recv(1024).decode().strip()
                        if estado_rival == "FIN":
                            print("[FIN] ¡Has ganado! Todos los barcos rivales hundidos.")
                            break

                else:
                    # parte de cuando te atacan
                    disparo_recibido = conn.recv(1024).decode().strip()

                    if disparo_recibido == "COMPROBANDO":
                        # El rival quiere saber si hemos perdido
                        barcos_vivos = [b for b in mi_tablero.barcos if b.vidas > 0]
                        if len(barcos_vivos) == 0:
                            conn.sendall("FIN".encode())
                            print("[FIN] Has perdido. Todos tus barcos han sido hundidos.")
                            break
                        else:
                            conn.sendall("SIGUE".encode())
                    else:
                        fila, columna = map(int, disparo_recibido.split(","))
                        resultado_ataque = mi_tablero.recibir_ataque(fila, columna)
                        conn.sendall(resultado_ataque.encode())
                        print(f"[RECIBIDO] Disparo en ({fila},{columna}) → {resultado_ataque}")
                        mi_tablero.imprimir()

                mi_turno = not mi_turno

        else:
            print("[ROL] CLIENTE")
            time.sleep(1)
            s = conectar_cliente(ip_rival)

            # El cliente espera primero (mi_turno = False)
            mi_turno = False

            while True:
                if mi_turno:
                    coords = input("Tu disparo (fila,columna): ")
                    fila, columna = map(int, coords.split(","))
                    disparo = f"{fila},{columna}"

                    s.sendall(disparo.encode())

                    respuesta = s.recv(1024).decode().strip()
                    print(f"[RESULTADO] {respuesta}")

                    if respuesta == "Hundido":
                        s.sendall("COMPROBANDO".encode())
                        estado_rival = s.recv(1024).decode().strip()
                        if estado_rival == "FIN":
                            print("[FIN] ¡Has ganado! Todos los barcos rivales hundidos.")
                            break

                else:
                    disparo_recibido = s.recv(1024).decode().strip()

                    if disparo_recibido == "COMPROBANDO":
                        barcos_vivos = [b for b in mi_tablero.barcos if b.vidas > 0]
                        if len(barcos_vivos) == 0:
                            s.sendall("FIN".encode())
                            print("[FIN] Has perdido. Todos tus barcos han sido hundidos.")
                            break
                        else:
                            s.sendall("SIGUE".encode())
                    else:
                        fila, columna = map(int, disparo_recibido.split(","))
                        resultado_ataque = mi_tablero.recibir_ataque(fila, columna)
                        s.sendall(resultado_ataque.encode())
                        print(f"[RECIBIDO] Disparo en ({fila},{columna}) → {resultado_ataque}")
                        mi_tablero.imprimir()

                mi_turno = not mi_turno