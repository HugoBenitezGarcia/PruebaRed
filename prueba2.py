import socket
import random
import time

PUERTO = 4000
MULTICAST_GROUP = '224.0.0.251'  # Dirección multicast
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

def buscar_partida():
    mi_ip = obtener_ip()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Configuración multicast
    sock.bind(('', PUERTO))
    
    # Unirse al grupo multicast
    import struct
    mreq = struct.pack('4sL', socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    
    # TTL para multicast (1 = misma red local)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    
    sock.settimeout(0.5)

    print(f"[INFO] Mi IP: {mi_ip} | ID: {ID} | Multicast: {MULTICAST_GROUP}")
    print("[INFO] Buscando oponente...")

    ultimo_envio = 0
    oponente_encontrado = None
    confirmacion_enviada = False

    try:
        while True:
            ahora = time.time()
            
            if ahora - ultimo_envio > 2 and not oponente_encontrado:
                mensaje = f"DESCUBRIR;{ID};{NOMBRE}"
                sock.sendto(mensaje.encode(), (MULTICAST_GROUP, PUERTO))
                ultimo_envio = ahora

            try:
                data, addr = sock.recvfrom(1024)
                if addr[0] == mi_ip:
                    continue

                partes = data.decode().split(";")
                
                if len(partes) == 3 and partes[0] == "DESCUBRIR":
                    id_oponente = int(partes[1])
                    nombre_oponente = partes[2]

                    soy_host = ID > id_oponente
                    rol = "HOST" if soy_host else "CLIENTE"
                    
                    print(f"\n[MATCH] ¡Oponente encontrado!")
                    print(f" -> Nombre: {nombre_oponente} ({addr[0]})")
                    print(f" -> Rol: {rol}")
                    
                    oponente_encontrado = (addr[0], soy_host, nombre_oponente)
                    
                    if not confirmacion_enviada:
                        mensaje_confirm = f"CONFIRMACION;{ID};{NOMBRE};{rol}"
                        sock.sendto(mensaje_confirm.encode(), (addr[0], PUERTO))
                        confirmacion_enviada = True
                        print(f"[INFO] Confirmación enviada a {nombre_oponente}")
                
                elif len(partes) == 4 and partes[0] == "CONFIRMACION":
                    nombre_confirm = partes[2]
                    rol_confirm = partes[3]
                    
                    print(f"\n[CONFIRMADO] {nombre_confirm} confirmó la conexión como {rol_confirm}")
                    
                    if oponente_encontrado:
                        break

            except socket.timeout:
                if oponente_encontrado and confirmacion_enviada:
                    continue
                    
    finally:
        sock.close()
    
    return oponente_encontrado

resultado = buscar_partida()

if resultado:
    ip_rival, es_host, nombre_rival = resultado
    if es_host:
        print(f"\n[LISTO] Iniciando servidor TCP en {PUERTO}...")
    else:
        print(f"\n[LISTO] Conectando como cliente a {ip_rival}:{PUERTO}...")