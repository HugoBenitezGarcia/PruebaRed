import ipaddress
import socket
import random
import time

# Definimos ID y puerto
ID = random.randint(0, 9999)
puerto = 4000
emparejado = False

# Definimos funciones dummy para que el código no falle al final
def host(addr):
    print(f"\n>>> INICIANDO COMO HOST (Oponente: {addr}) <<<\n")

def cliente(addr):
    print(f"\n>>> INICIANDO COMO CLIENTE (Conectando a: {addr}) <<<\n")

def obtener_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        mi_ip = s.getsockname()[0]
    finally:
        s.close()
    return mi_ip

def calcular_broadcast():
    # Nota: A veces '255.255.255.255' da menos problemas en Windows que la específica
    return str(ipaddress.IPv4Network(obtener_ip() + "/24", strict=False).broadcast_address)

def BuscarPartida():
    global emparejado
    dir_broadcast = calcular_broadcast()
    
    print(f"Mi IP: {obtener_ip()} | ID: {ID} | Broadcast a: {dir_broadcast}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # CORRECCIÓN 1: Permitir reutilizar puerto para pruebas en local
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    sock.bind(("", puerto))
    
    # CORRECCIÓN 2: Timeout más corto para enviar pings más frecuentes
    sock.settimeout(1.0) 

    mensaje = f"BUSCANDO;{ID}".encode()
    print("Buscando oponente...")

    while not emparejado:
        # CORRECCIÓN 3: Enviamos el ping DENTRO del bucle siempre.
        # Esto asegura que si el otro PC acaba de llegar, me escuche ahora.
        sock.sendto(mensaje, (dir_broadcast, puerto))

        try:
            # Escuchamos respuesta
            data, addr = sock.recvfrom(1024)
            texto = data.decode()
            
            # Validación básica del mensaje
            if ";" not in texto: continue
            
            msg_header, id_oponente_str = texto.split(";")
            
            if msg_header != "BUSCANDO": continue
            
            id_oponente = int(id_oponente_str)

            # Si soy yo mismo, ignoro
            if id_oponente == ID:
                continue

            print(f"¡Paquete recibido de {addr[0]} con ID {id_oponente}!")
            
            # Lógica de Host/Cliente
            emparejado = True
            sock.close() # Cerramos antes de cambiar de lógica
            
            if ID > id_oponente:
                host(addr[0])
            elif ID < id_oponente:
                cliente(addr[0])
            else:
                # Caso rarísimo: IDs iguales. Reiniciamos búsqueda.
                print("Conflicto de IDs iguales. Reintentando...")
                ID = random.randint(0, 9999) # Cambiamos ID
                emparejado = False
                BuscarPartida() # Recursividad simple o volver al loop

        except socket.timeout:
            # Simplemente el bucle vuelve a empezar y vuelve a mandar el broadcast
            pass
        except ValueError:
            pass # Por si llega basura que no es un numero

if __name__ == "__main__":
    BuscarPartida()