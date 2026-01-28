# BUSCANDO, Puerto 4000, id aleatorio 0-9999 (el id mas alto es el host)
import ipaddress
import socket
import random
import time 


ID = random.randint(0, 9999)
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

    global emparejado
    # Creacion del socket y permisos para hacer broadcast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("", puerto))
    #si no responde nadie en 5 segundos se vuelve a alanzar la peticion desde el except 
    sock.settimeout(5)

    mensaje = f"BUSCANDO;{ID}".encode()

    #Mandar broadcast
    sock.sendto(mensaje, (dir_broadcast, puerto))
    print("Buscando oponente")

    #Bucle para encontrar la otra maquina
    while not emparejado:
        try:
            data, addr = sock.recvfrom(1024) #Aqui se recibe los datos de la otra maquina
            texto = data.decode() #Pasar de bytes a string
            tipo, id_oponente = texto.split(";")
            id_oponente = int(id_oponente)
            
            if id_oponente == ID:
                continue

            print("Partida encontrada")
            emparejado = True #se cierra el emparejamiento

            #Aqui se decide quien es host y cliente 
            if ID > id_oponente:  #si sale un nuemro mayor eres host 
                host(addr[0])
            else:  #si sale menor eres cliente
                cliente(addr[0])

            sock.close() #Cierro socket para que no busque mas maquinas 

        #si se acaba el tiempo de 5 segundos vuelve a buscar oponente
        except socket.timeout:
            print('No se encuentran jugadores')
            sock.sendto(mensaje, (dir_broadcast, puerto))
BuscarPartida()

# HACER PING AL SERVIDOR DE GOOGLE Y QUE ME DEVUELVA MI IP, CALCULAR EL BROADCAST DE LA  SUBRED CON EL /24 

