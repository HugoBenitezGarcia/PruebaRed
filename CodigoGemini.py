import ipaddress
import socket
import random
import time

PUERTO = 4000
ID = random.randint(0, 9999)
NOMBRE = "hola"

emparejado = False
soy_host = False


def obtener_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def calcular_broadcast():
    return str(ipaddress.IPv4Network(obtener_ip() + "/24", strict=False).broadcast_address)


def BuscarPartida():
    global emparejado, soy_host

    dir_broadcast = calcular_broadcast()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", PUERTO))
    sock.settimeout(1)

    mensaje = f"DESCUBRIR;{ID};{NOMBRE}".encode()

    print(f"[INFO] Mi ID: {ID}")
    print("[INFO] Buscando oponente...")

    ultimo_envio = 0

    while not emparejado:
        # Broadcast cada 2 segundos
        if time.time() - ultimo_envio > 2:
            sock.sendto(mensaje, (dir_broadcast, PUERTO))
            ultimo_envio = time.time()

        try:
            data, addr = sock.recvfrom(1024)
            texto = data.decode()
            partes = texto.split(";")

            if len(partes) != 3:
                continue

            tipo, id_oponente, nombre_oponente = partes

            if tipo == "DESCUBRIR":
                id_oponente = int(id_oponente)

            if id_oponente == ID:
                continue

    # RESPONDER siempre
            sock.sendto(mensaje, addr)

            soy_host = ID > id_oponente
            rol = "HOST" if soy_host else "CLIENTE"

            print(f"[MATCH] Encontrado {nombre_oponente} ({addr[0]})")
            print(f"[ROL] Soy {rol}")

            emparejado = True


        except socket.timeout:
            pass

    sock.close()
    print("[INFO] Emparejamiento completado")


BuscarPartida()
