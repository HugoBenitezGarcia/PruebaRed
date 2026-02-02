import ipaddress
import socket
import random

ID = random.randint(0, 9999)
print(f"🎲 Mi ID: {ID}")
emparejado = False

def obtener_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        mi_ip = s.getsockname()[0]
    finally:
        s.close()
    return mi_ip

def calcular_broadcast():
    return str(ipaddress.IPv4Network(obtener_ip() + "/24", strict=False).broadcast_address)

def BuscarPartida():
    puerto = 4000
    dir_broadcast = calcular_broadcast()
    mi_ip = obtener_ip()
    nombre = "hola"
    global emparejado
    
    print(f"📍 Mi IP: {mi_ip}")
    print(f"📡 Broadcast: {dir_broadcast}")
    print("-" * 50)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", puerto))
    sock.settimeout(1)
    
    mensaje = f"DESCUBRIR;{ID};{nombre}".encode()
    sock.sendto(mensaje, (dir_broadcast, puerto))
    print("📤 Buscando oponente...")
    
    while not emparejado:
        try:
            data, addr = sock.recvfrom(1024)
            print(f"📨 ¡RECIBIDO de {addr[0]}!: {data.decode()}")
            
            texto = data.decode()
            partes = texto.split(";")
            if len(partes) != 3:
                continue
            
            tipo, id_oponente, nombre_oponente = partes
            
            if tipo != "DESCUBRIR":
                continue
            
            id_oponente = int(id_oponente)
            
            if ID == id_oponente:
                print(f"🔁 Es mi propio mensaje, ignorando")
                continue
            
            print(f"🎉 ¡CONECTADO con {nombre_oponente}!")
            emparejado = True
            sock.close()
            
        except socket.timeout:
            print('⏳ No hay respuesta, reintentando...')
            sock.sendto(mensaje, (dir_broadcast, puerto))

BuscarPartida()