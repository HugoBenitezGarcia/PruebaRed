import ipaddress
import socket
import time
import uuid
from hundirFlota import *

PUERTO = 4000
ID = str(uuid.uuid4())
NOMBRE = "Empanada de queso"

# --- FUNCIONES DE RED BÁSICAS ---

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
                    sock.sendto(f"ACEPTADO;{ID};{NOMBRE}".encode(), addr)
                    oponente = (ip_oponente, nombre_oponente)
                    soy_host = True
                    estado = "JUGANDO"
                else:
                    print("[INFO] Esperando respuesta...", end="\r")

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
    while True:
        try:
            s.connect((ip_rival, PUERTO))
            print("[CLIENTE] Conectado al host")
            return s
        except ConnectionRefusedError:
            print("Intentando conectar...", end="\r")
            time.sleep(1)


def recibir_mensaje(sock):
    try:
        datos = sock.recv(1024)
        if not datos:
            return None
        return datos.decode().strip()
    except:
        return None

# --- BLOQUE PRINCIPAL DEL JUEGO ---

if __name__ == "__main__":
    resultado = buscar_partida()

    if resultado:
        ip_rival, soy_host, nombre_rival = resultado
        print(f"\nPARTIDA ENCONTRADA contra {nombre_rival}")

        canal_juego = None
        es_mi_turno = False

        # Conexión TCP
        if soy_host:
            print("[ROL] HOST (Empiezas atacando)")
            canal_juego = abrir_servidor()
            es_mi_turno = True
        else:
            print("[ROL] CLIENTE (Esperas ataque)")
            time.sleep(1) # Esperamos un poco a que el host levante el server
            canal_juego = conectar_cliente(ip_rival)
            es_mi_turno = False

        # Inicializar lógica del juego
        mi_tablero = Tablero(8)
        flota = [
            Barco(5, "Portaaviones"), Barco(4, "Acorazado"),
            Barco(3, "Crucero"), Barco(3, "Submarino"), Barco(2, "Destructor")
        ]
        for b in flota:
            mi_tablero.agregar_barco(b)
        
        partida_activa = True

        print("\n--- INICIO DE LA BATALLA ---")

        while partida_activa:
            # Pausa dramática para ver qué pasa
            time.sleep(1.5)

            if es_mi_turno:
                print(f"\n>>> ATACANDO A {nombre_rival} >>>")
                
                # 1. IA decide dónde disparar
                coord_ia = mi_tablero.atacar() # Devuelve ['c', 4]
                letra = coord_ia[0].upper()
                fila = coord_ia[1]
                disparo = f"{letra}{fila}" # "C4"

                try:
                    # 2. Enviar disparo
                    canal_juego.sendall(disparo.encode())
                    print(f"   [YO] Disparo a: {disparo}")

                    # 3. Recibir resultado
                    respuesta = recibir_mensaje(canal_juego)
                    
                    if respuesta is None:
                        print("!! El rival se desconectó inesperadamente.")
                        partida_activa = False
                        break

                    print(f"   [RIVAL] Dice: {respuesta}")

                    # 4. Informar a mi tablero (Feedback)
                    mi_tablero.registrar_resultado(respuesta)

                    # 5. Analizar resultado
                    if "VICTORIA" in respuesta:
                        print("\n" + "#"*40)
                        print("   ¡¡VICTORIA!! HAS HUNDIDO TODA LA FLOTA")
                        print("#"*40)
                        partida_activa = False
                    
                    elif "HUNDIDO" in respuesta:
                        print("   ¡¡BARCO HUNDIDO!! ¡FUEGO A DISCRECIÓN!")
                        es_mi_turno = True # Repetir turno
                        
                    elif "TOCADO" in respuesta:
                        print("   ¡IMPACTO! Repites turno.")
                        es_mi_turno = True # Repetir turno
                        
                    else: # AGUA
                        print("   Agua. Fin del turno.")
                        es_mi_turno = False # Cambio de turno

                except Exception as e:
                    print(f"Error crítico atacando: {e}")
                    partida_activa = False

            else:
                print(f"\n<<< DEFENDIENDO DE {nombre_rival} <<<")
                print("   Esperando impacto...", end="\r")
                
                try:
                    # 1. Recibir disparo
                    disparo_recibido = recibir_mensaje(canal_juego)
                    
                    if disparo_recibido is None:
                        print("!! El rival se desconectó.")
                        partida_activa = False
                        break

                    print(f"   [RIVAL] Dispara a: {disparo_recibido}")

                    # 2. Calcular daño en mi tablero
                    letra_r = disparo_recibido[0].lower()
                    fila_r = int(disparo_recibido[1:])
                    
                    resultado_impacto = mi_tablero.recibir_ataque(letra_r, fila_r)
                    
                    # 3. Verificar derrota
                    if not mi_tablero.quedan_barcos_vivos():
                        resultado_impacto = "VICTORIA"
                        print("\n" + "!"*40)
                        print("   DERROTA... HAN HUNDIDO TU FLOTA")
                        print("!"*40)
                        partida_activa = False
                    else:
                        print(f"   [YO] Resultado: {resultado_impacto}")

                    # 4. Enviar resultado al rival
                    canal_juego.sendall(resultado_impacto.encode())

                    # 5. Decidir de quién es el turno ahora
                    if "TOCADO" in resultado_impacto or "HUNDIDO" in resultado_impacto or "VICTORIA" in resultado_impacto:
                        es_mi_turno = False # Rival repite (o ganó)
                    else:
                        es_mi_turno = True # Rival falló, me toca

                except Exception as e:
                    print(f"Error crítico defendiendo: {e}")
                    partida_activa = False

        # --- CIERRE SEGURO ---
        print("\nCerrando partida...")
        # ¡IMPORTANTE! Pausa para asegurar que el último mensaje "VICTORIA" sale
        time.sleep(2) 
        try:
            canal_juego.close()
        except:
            pass
        print("Conexión cerrada.")
