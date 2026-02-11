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
    return str(ipaddress.IPv4Network(obtener_ip() + "/24", strict=False).broadcast_address)
#/24 si vamos a jugar por cable, /21 si vamos a jugar por red ( creo que es imposible jugar por red)


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


            #aqui iria un while del bucle de la partida
            #  con esto: te envias mensajes y seguido
            #
            # conn.sendall(disparo.encode()) 
            #
            # respuesta = conn.recv(1024).decode().strip()
            # Empieza a jugar el host
            #
            #parte de cuando te atacan
            # disparo_recibido = conn.recv(1024).decode().strip()

            #resultado = recibir_disparo(tablero_jugador1, disparo_recibido)
            #conn.sendall(resultado.encode())


   
        else:
            print("[ROL] CLIENTE")
            time.sleep(1)
            s = conectar_cliente(ip_rival)