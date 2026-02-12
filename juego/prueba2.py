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


def recibir_mensaje(sock):
    try:
        datos = sock.recv(1024)
        if not datos:
            return None
        return datos.decode().strip()
    except:
        return None


if __name__ == "__main__":
    resultado = buscar_partida()

    if resultado:
        ip_rival, soy_host, nombre_rival = resultado
        print(f"\nPARTIDA ENCONTRADA contra {nombre_rival}")

        canal_juego = None
        es_mi_turno = False

        if soy_host:
            print("[ROL] HOST")
            canal_juego = abrir_servidor()
            es_mi_turno = True
        else:
            print("[ROL] CLIENTE")
            time.sleep(1)
            canal_juego = conectar_cliente(ip_rival)
            es_mi_turno = False

        mi_tablero = inicializar_tablero()
        colocar_barcos(mi_tablero)
        tablero_tracking = inicializar_tablero_vacio()
        
        disparos_realizados = []
        partida_activa = True

        while partida_activa:
            if es_mi_turno:
                print(f"TU TURNO DE ATACAR A {nombre_rival}")
                
                coordenada_valida = False
                disparo = ""

                while not coordenada_valida:
                    disparo = input("Introduce coordenada de disparo: ").upper()
                    
                    if not validar_coordenada(disparo):
                        print("Formato incorrecto.")
                    elif disparo in disparos_realizados:
                        print(f"Ya disparaste a {disparo} antes.")
                    else:
                        coordenada_valida = True
                        disparos_realizados.append(disparo)

                try:
                    canal_juego.sendall(disparo.encode())
                    print(f"[RED] Enviando disparo: {disparo}")

                    respuesta = canal_juego.recv(1024).decode().strip()
                    print(f"[RED] Resultado recibido: {respuesta}")

                    actualizar_tablero_tracking(tablero_tracking, disparo, respuesta)

                    if "VICTORIA" in respuesta:
                        print("HAS HUNDIDO TODA LA FLOTA. HAS GANADO.")
                        partida_activa = False
                    
                    es_mi_turno = False

                except Exception as e:
                    print(f"Error de conexión: {e}")
                    partida_activa = False

            else:
                print(f"TURNO DE {nombre_rival}")
                print("Esperando disparo del rival...")
                
                try:
                    disparo_recibido = canal_juego.recv(1024).decode().strip()
                    
                    if not disparo_recibido:
                        print("El rival se ha desconectado.")
                        partida_activa = False
                        break

                    print(f"[RED] Rival dispara a: {disparo_recibido}")

                    resultado_impacto = comprobar_impacto(mi_tablero, disparo_recibido)
                    
                    if quedan_barcos_vivos(mi_tablero) == False:
                        resultado_impacto = "VICTORIA"
                        print("HAN HUNDIDO TU FLOTA. HAS PERDIDO.")
                        partida_activa = False
                    
                    canal_juego.sendall(resultado_impacto.encode())
                    es_mi_turno = True

                except Exception as e:
                    print(f"Error de conexión: {e}")
                    partida_activa = False

        print("Cerrando conexión...")
        canal_juego.close()