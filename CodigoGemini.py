import ipaddress
import socket
import random
import time

PUERTO = 4000
ID = random.randint(0, 9999)
NOMBRE = "Jugador_Python"

def obtener_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

def calcular_broadcast():
    ip = obtener_ip()
    red = ipaddress.IPv4Interface(f"{ip}/255.255.255.0")
    return str(red.network.broadcast_address)

def buscar_partida():
    dir_broadcast = calcular_broadcast()
    mi_ip = obtener_ip()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    sock.bind(("", PUERTO))
    sock.settimeout(0.5)

    print(f"[INFO] Mi IP: {mi_ip} | ID: {ID} | Broadcast: {dir_broadcast}")
    print("[INFO] Buscando oponente...")

    ultimo_envio = 0
    oponente_encontrado = None
    confirmacion_enviada = False

    try:
        while True:
            ahora = time.time()
            
            # Enviar mensaje de descubrimiento
            if ahora - ultimo_envio > 2 and not oponente_encontrado:
                mensaje = f"DESCUBRIR;{ID};{NOMBRE}"
                sock.sendto(mensaje.encode(), (dir_broadcast, PUERTO))
                ultimo_envio = ahora

            try:
                data, addr = sock.recvfrom(1024)
                if addr[0] == mi_ip:
                    continue

                partes = data.decode().split(";")
                
                # Recibir descubrimiento
                if len(partes) == 3 and partes[0] == "DESCUBRIR":
                    id_oponente = int(partes[1])
                    nombre_oponente = partes[2]

                    soy_host = ID > id_oponente
                    rol = "HOST" if soy_host else "CLIENTE"
                    
                    print(f"\n[MATCH] ¡Oponente encontrado!")
                    print(f" -> Nombre: {nombre_oponente} ({addr[0]})")
                    print(f" -> Rol: {rol}")
                    
                    oponente_encontrado = (addr[0], soy_host, nombre_oponente)
                    
                    # Enviar confirmación al oponente
                    if not confirmacion_enviada:
                        mensaje_confirm = f"CONFIRMACION;{ID};{NOMBRE};{rol}"
                        sock.sendto(mensaje_confirm.encode(), (addr[0], PUERTO))
                        confirmacion_enviada = True
                        print(f"[INFO] Confirmación enviada a {nombre_oponente}")
                
                # Recibir confirmación
                elif len(partes) == 4 and partes[0] == "CONFIRMACION":
                    id_confirm = int(partes[1])
                    nombre_confirm = partes[2]
                    rol_confirm = partes[3]
                    
                    print(f"\n[CONFIRMADO] {nombre_confirm} confirmó la conexión como {rol_confirm}")
                    
                    # Si ya teníamos un oponente y recibimos su confirmación, salimos
                    if oponente_encontrado:
                        break

            except socket.timeout:
                # Si ya encontramos oponente y enviamos confirmación, esperamos un poco más
                if oponente_encontrado and confirmacion_enviada:
                    # Dar tiempo para recibir la confirmación del otro
                    continue
                    
    finally:
        sock.close()
    
    return oponente_encontrado

resultado = buscar_partida()

if resultado:
    ip_rival, es_host, nombre_rival = resultado
    if es_host:
        print(f"\n[LISTO] Iniciando servidor TCP en {PUERTO}...")
        print(f"Esperando conexión de {nombre_rival}...")
    else:
        print(f"\n[LISTO] Conectando como cliente a {ip_rival}:{PUERTO}...")
        print(f"Conectando con {nombre_rival}...")