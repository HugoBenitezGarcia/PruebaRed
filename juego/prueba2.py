import ipaddress
import socket
import time
import uuid
from hundirFlota import Tablero, Barco

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


def validar_formato_coord(coord):
    if len(coord) < 2:
        return False
    letra = coord[0].lower()
    if letra not in "abcdefgh":
        return False
    try:
        fila = int(coord[1:])
        if fila < 0 or fila > 7:
            return False
    except ValueError:
        return False
    return True


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

        mi_tablero = Tablero(8)
        flota = [
            Barco(5, "Portaaviones"), Barco(4, "Acorazado"),
            Barco(3, "Crucero"), Barco(3, "Submarino"), Barco(2, "Destructor")
        ]
        for b in flota:
            mi_tablero.agregar_barco(b)

        tablero_rival_vista = Tablero(8)
        
        disparos_realizados = []
        partida_activa = True

        while partida_activa:
            if es_mi_turno:
                print(f"\n--- TU TURNO DE ATACAR A {nombre_rival} ---")
                print("TU TABLERO:")
                mi_tablero.imprimir(ocultar_barcos=False)
                print("TABLERO RIVAL (Tus disparos):")
                tablero_rival_vista.imprimir(ocultar_barcos=True)
                
                coordenada_valida = False
                disparo = ""

                while not coordenada_valida:
                    disparo = input("Introduce coordenada (ej: A5): ").strip().upper()
                    
                    if not validar_formato_coord(disparo):
                        print("Formato incorrecto. Usa LetraNumero (A-H, 0-7).")
                    elif disparo in disparos_realizados:
                        print(f"Ya disparaste a {disparo} antes.")
                    else:
                        coordenada_valida = True
                        disparos_realizados.append(disparo)

                try:
                    canal_juego.sendall(disparo.encode())
                    print(f"[RED] Enviando disparo: {disparo}")

                    respuesta = recibir_mensaje(canal_juego)
                    
                    if respuesta is None:
                        print("El rival se ha desconectado.")
                        partida_activa = False
                        break

                    print(f"[RED] Resultado: {respuesta}")

                    letra = disparo[0].lower()
                    fila = int(disparo[1:])
                    idx_col = ord(letra) - 97
                    
                    marca = "o"
                    if "TOCADO" in respuesta or "HUNDIDO" in respuesta or "VICTORIA" in respuesta:
                        marca = "X"
                    
                    tablero_rival_vista.cuadricula[fila][idx_col] = marca

                    if "VICTORIA" in respuesta:
                        print("\nVICTORIA. HAS HUNDIDO TODA LA FLOTA.")
                        partida_activa = False
                    
                    es_mi_turno = False

                except Exception as e:
                    print(f"Error de conexión: {e}")
                    partida_activa = False

            else:
                print(f"\n--- TURNO DE {nombre_rival} ---")
                print("Esperando disparo...")
                
                try:
                    disparo_recibido = recibir_mensaje(canal_juego)
                    
                    if disparo_recibido is None:
                        print("El rival se ha desconectado.")
                        partida_activa = False
                        break

                    print(f"[RED] Rival dispara a: {disparo_recibido}")

                    letra_r = disparo_recibido[0].lower()
                    fila_r = int(disparo_recibido[1:])
                    
                    resultado_impacto = mi_tablero.recibir_ataque(letra_r, fila_r)
                    
                    if not mi_tablero.quedan_barcos_vivos():
                        resultado_impacto = "VICTORIA"
                        print("\nDERROTA. HAN HUNDIDO TU FLOTA.")
                        partida_activa = False
                    
                    canal_juego.sendall(resultado_impacto.encode())
                    es_mi_turno = True

                except Exception as e:
                    print(f"Error de conexión: {e}")
                    partida_activa = False

        print("Cerrando conexión...")
        canal_juego.close()
