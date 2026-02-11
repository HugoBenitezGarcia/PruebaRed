import ipaddress
import random
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

        if soy_host:
            print("[ROL] HOST")
            conn = abrir_servidor()

            tablero_jugador1 = Tablero()
            flota1 = [Barco(5, "Portaaviones"), Barco(4, "Acorazado"), Barco(3, "Crucero"), Barco(3, "Submarino"), Barco(2, "Destructor")]
            for barco in flota1:
                tablero_jugador1.agregar_barco(barco)

            turno = "MI_TURNO"
            jugando = True

            while jugando:
                if turno == "MI_TURNO":
                    fila = random.choice()
                    columna = random.choice()
                    disparo = f"{fila},{columna}"
                    conn.sendall(disparo.encode())

                    respuesta = conn.recv(1024).decode().strip()
                    print(f"[RESULTADO]: {respuesta}")

                    if respuesta == "Derrota":
                        print("[FIN] ¡Has ganado!")
                        jugando = False
                    else:
                        turno = "TURNO_RIVAL"

                else:
                    disparo_recibido = conn.recv(1024).decode().strip()
                    f_r, c_r = map(int, disparo_recibido.split(","))
                    resultado = tablero_jugador1.recibir_ataque(f_r, c_r)

                    barcos_vivos = sum(1 for b in tablero_jugador1.barcos if b.vidas > 0)
                    if barcos_vivos == 0:
                        conn.sendall("Derrota".encode())
                        print("[FIN] Has perdido.")
                        jugando = False
                    else:
                        conn.sendall(resultado.encode())
                        turno = "MI_TURNO"

        else:
            print("[ROL] CLIENTE")
            time.sleep(1)
            s = conectar_cliente(ip_rival)

            tablero_jugador2 = Tablero()
            flota2 = [Barco(5, "Portaaviones"), Barco(4, "Acorazado"), Barco(3, "Crucero"), Barco(3, "Submarino"), Barco(2, "Destructor")]
            for barco in flota2:
                tablero_jugador2.agregar_barco(barco)

            turno = "TURNO_RIVAL"
            jugando = True

            while jugando:
                if turno == "TURNO_RIVAL":
                    disparo_recibido = s.recv(1024).decode().strip()
                    f_r, c_r = map(int, disparo_recibido.split(","))
                    resultado = tablero_jugador2.recibir_ataque(f_r, c_r)

                    barcos_vivos = sum(1 for b in tablero_jugador2.barcos if b.vidas > 0)
                    if barcos_vivos == 0:
                        s.sendall("Derrota".encode())
                        print("[FIN] Has perdido.")
                        jugando = False
                    else:
                        s.sendall(resultado.encode())
                        turno = "MI_TURNO"

                else:
                    fila = random.choice()
                    columna = random.choice()
                    disparo = f"{fila},{columna}"
                    s.sendall(disparo.encode())

                    respuesta = s.recv(1024).decode().strip()
                    print(f"[RESULTADO]: {respuesta}")

                    if respuesta == "Derrota":
                        print("[FIN] ¡Has ganado!")
                        jugando = False
                    else:
                        turno = "TURNO_RIVAL"
