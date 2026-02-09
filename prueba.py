import ipaddress
import socket
import random
import time
import threading

PUERTO = 4000
ID = random.randint(0, 9999)
NOMBRE = f"Jugador_{ID}"
TAMAÑO_TABLERO = 10
BARCOS = [5, 4, 3, 3, 2]

class Tablero:
    def __init__(self):
        self.grid = [['~' for _ in range(TAMAÑO_TABLERO)] for _ in range(TAMAÑO_TABLERO)]
        self.barcos = []
        self.disparos_recibidos = set()
        self.impactos = 0
        self.total_casillas_barco = sum(BARCOS)
    
    def colocar_barcos(self):
        for tamaño in BARCOS:
            colocado = False
            while not colocado:
                horizontal = random.choice([True, False])
                if horizontal:
                    fila = random.randint(0, TAMAÑO_TABLERO - 1)
                    col = random.randint(0, TAMAÑO_TABLERO - tamaño)
                    posiciones = [(fila, col + i) for i in range(tamaño)]
                else:
                    fila = random.randint(0, TAMAÑO_TABLERO - tamaño)
                    col = random.randint(0, TAMAÑO_TABLERO - 1)
                    posiciones = [(fila + i, col) for i in range(tamaño)]
                
                if self.puede_colocar(posiciones):
                    self.barcos.append(posiciones)
                    for f, c in posiciones:
                        self.grid[f][c] = 'B'
                    colocado = True
    
    def puede_colocar(self, posiciones):
        for f, c in posiciones:
            if self.grid[f][c] != '~':
                return False
            for df in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nf, nc = f + df, c + dc
                    if 0 <= nf < TAMAÑO_TABLERO and 0 <= nc < TAMAÑO_TABLERO:
                        if self.grid[nf][nc] == 'B':
                            return False
        return True
    
    def recibir_disparo(self, fila, col):
        if (fila, col) in self.disparos_recibidos:
            return "REPETIDO"
        
        self.disparos_recibidos.add((fila, col))
        
        if self.grid[fila][col] == 'B':
            self.grid[fila][col] = 'X'
            self.impactos += 1
            if self.impactos == self.total_casillas_barco:
                return "HUNDIDO_TOTAL"
            return "IMPACTO"
        else:
            self.grid[fila][col] = 'O'
            return "AGUA"
    
    def mostrar(self):
        print("   " + " ".join(str(i) for i in range(TAMAÑO_TABLERO)))
        for i, fila in enumerate(self.grid):
            print(f"{i:2} " + " ".join(fila))

class JugadorIA:
    def __init__(self):
        self.disparos_realizados = set()
        self.impactos = []
        self.modo_caza = False
    
    def obtener_disparo(self):
        if self.modo_caza and self.impactos:
            disparo = self.disparo_inteligente()
            if disparo:
                self.disparos_realizados.add(disparo)
                return disparo
        
        while True:
            fila = random.randint(0, TAMAÑO_TABLERO - 1)
            col = random.randint(0, TAMAÑO_TABLERO - 1)
            if (fila, col) not in self.disparos_realizados:
                self.disparos_realizados.add((fila, col))
                return fila, col
    
    def disparo_inteligente(self):
        ultimo_impacto = self.impactos[-1]
        fila, col = ultimo_impacto
        
        direcciones = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        random.shuffle(direcciones)
        
        for df, dc in direcciones:
            nf, nc = fila + df, col + dc
            if (0 <= nf < TAMAÑO_TABLERO and 0 <= nc < TAMAÑO_TABLERO and
                (nf, nc) not in self.disparos_realizados):
                return nf, nc
        
        if len(self.impactos) > 1:
            self.impactos.pop()
            return self.disparo_inteligente()
        
        return None
    
    def procesar_resultado(self, fila, col, resultado):
        if resultado == "IMPACTO":
            self.impactos.append((fila, col))
            self.modo_caza = True
        elif resultado == "HUNDIDO_TOTAL":
            self.impactos = []
            self.modo_caza = False

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

    print(f"[INFO] Mi IP: {mi_ip} | ID: {ID}")
    print("[INFO] Buscando oponente...")

    ultimo_envio = 0
    oponente_ip = None
    oponente_id = None
    oponente_nombre = None
    confirmaciones = {"enviada": False, "recibida": False}
    tiempo_salida = None

    try:
        while True:
            ahora = time.time()
            
            # Si ya tenemos ambas confirmaciones, esperamos un poco y salimos
            if confirmaciones["enviada"] and confirmaciones["recibida"]:
                if tiempo_salida is None:
                    tiempo_salida = ahora + 1
                elif ahora > tiempo_salida:
                    break
            
            # Enviar descubrimiento periódicamente hasta encontrar oponente
            if ahora - ultimo_envio > 1.5:
                mensaje = f"DESCUBRIR;{ID};{NOMBRE}"
                sock.sendto(mensaje.encode(), (dir_broadcast, PUERTO))
                ultimo_envio = ahora

            try:
                data, addr = sock.recvfrom(1024)
                if addr[0] == mi_ip:
                    continue

                partes = data.decode().split(";")
                
                # Recibir DESCUBRIR
                if len(partes) == 3 and partes[0] == "DESCUBRIR":
                    id_remoto = int(partes[1])
                    nombre_remoto = partes[2]
                    
                    # Si no tenemos oponente, aceptar este
                    if oponente_id is None:
                        oponente_id = id_remoto
                        oponente_ip = addr[0]
                        oponente_nombre = nombre_remoto
                        soy_host = ID > id_remoto
                        rol = "HOST" if soy_host else "CLIENTE"
                        
                        print(f"\n[MATCH] ¡Oponente encontrado!")
                        print(f" -> Nombre: {nombre_remoto} ({addr[0]})")
                        print(f" -> Mi ID: {ID} vs ID oponente: {id_remoto}")
                        print(f" -> Rol asignado: {rol}")
                    
                    # Solo responder al oponente que hemos aceptado
                    if id_remoto == oponente_id:
                        mensaje_confirm = f"CONFIRMACION;{ID};{NOMBRE}"
                        sock.sendto(mensaje_confirm.encode(), (addr[0], PUERTO))
                        confirmaciones["enviada"] = True
                
                # Recibir CONFIRMACION
                elif len(partes) == 3 and partes[0] == "CONFIRMACION":
                    id_confirm = int(partes[1])
                    nombre_confirm = partes[2]
                    
                    # Solo aceptar confirmación del oponente esperado
                    if oponente_id is not None and id_confirm == oponente_id:
                        if not confirmaciones["recibida"]:
                            print(f"[CONFIRMADO] {nombre_confirm} confirmó la conexión")
                            confirmaciones["recibida"] = True

            except socket.timeout:
                continue
                    
    finally:
        sock.close()
    
    if oponente_id is not None:
        soy_host = ID > oponente_id
        return (oponente_ip, soy_host, oponente_nombre)
    
    return None

def jugar_como_host(ip_rival, nombre_rival):
    print(f"\n{'='*50}")
    print(f"INICIANDO PARTIDA COMO HOST")
    print(f"Oponente: {nombre_rival}")
    print(f"{'='*50}\n")
    
    mi_tablero = Tablero()
    mi_tablero.colocar_barcos()
    ia = JugadorIA()
    
    print("Mi tablero inicial:")
    mi_tablero.mostrar()
    print()
    
    # Crear servidor TCP INMEDIATAMENTE
    print(f"[HOST] Iniciando servidor en puerto {PUERTO}...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("", PUERTO))
    server.listen(1)
    server.settimeout(30)  # Aumentar timeout a 30 segundos
    
    print(f"[HOST] Esperando conexión del cliente...")
    
    try:
        conn, addr = server.accept()
        print(f"[HOST] ¡Cliente conectado desde {addr}!\n")
    except socket.timeout:
        print("[ERROR] Timeout esperando conexión del cliente")
        server.close()
        return
    
    # Handshake
    try:
        conn.send(b"LISTO_HOST")
        msg = conn.recv(1024)
        if msg != b"LISTO_CLIENTE":
            print("[ERROR] Handshake fallido")
            conn.close()
            server.close()
            return
    except:
        print("[ERROR] Error en handshake")
        conn.close()
        server.close()
        return
    
    print("¡PARTIDA INICIADA!")
    print("="*50)
    time.sleep(1)
    
    turno = 0
    juego_activo = True
    
    while juego_activo:
        try:
            # Turno par: HOST dispara
            if turno % 2 == 0:
                print(f"\n{'='*40}")
                print(f"TURNO {turno // 2 + 1} - MI ATAQUE")
                print(f"{'='*40}")
                
                fila, col = ia.obtener_disparo()
                print(f"→ Disparando a posición ({fila}, {col})...")
                
                mensaje = f"DISPARO;{fila};{col}"
                conn.send(mensaje.encode())
                
                respuesta = conn.recv(1024).decode()
                if not respuesta:
                    print("[ERROR] Conexión perdida")
                    break
                
                partes = respuesta.split(";")
                resultado = partes[1]
                
                if resultado == "IMPACTO":
                    print(f"✓ ¡IMPACTO!")
                elif resultado == "AGUA":
                    print(f"✗ Agua...")
                elif resultado == "HUNDIDO_TOTAL":
                    print(f"★ ¡HUNDIDO TOTAL!")
                
                ia.procesar_resultado(fila, col, resultado)
                
                if resultado == "HUNDIDO_TOTAL":
                    print(f"\n{'★'*50}")
                    print("¡VICTORIA! ¡Has hundido toda la flota enemiga!")
                    print(f"{'★'*50}\n")
                    juego_activo = False
                
                time.sleep(1)
            
            # Turno impar: CLIENTE dispara
            else:
                print(f"\n{'='*40}")
                print(f"TURNO {turno // 2 + 1} - DEFENSA")
                print(f"{'='*40}")
                
                data = conn.recv(1024).decode()
                if not data:
                    print("[ERROR] Conexión perdida")
                    break
                
                partes = data.split(";")
                
                if partes[0] == "DISPARO":
                    fila = int(partes[1])
                    col = int(partes[2])
                    print(f"← El enemigo dispara a ({fila}, {col})...")
                    
                    resultado = mi_tablero.recibir_disparo(fila, col)
                    
                    if resultado == "IMPACTO":
                        print(f"✗ Nos dieron...")
                    elif resultado == "AGUA":
                        print(f"✓ ¡Falló!")
                    elif resultado == "HUNDIDO_TOTAL":
                        print(f"☠ Nos hundieron...")
                    
                    respuesta = f"RESULTADO;{resultado}"
                    conn.send(respuesta.encode())
                    
                    if resultado == "HUNDIDO_TOTAL":
                        print(f"\n{'☠'*50}")
                        print("DERROTA. El enemigo hundió toda tu flota.")
                        print(f"{'☠'*50}\n")
                        juego_activo = False
                    else:
                        print("\nMi tablero:")
                        mi_tablero.mostrar()
                
                time.sleep(1)
            
            turno += 1
            
        except Exception as e:
            print(f"[ERROR] {e}")
            break
    
    conn.close()
    server.close()

def jugar_como_cliente(ip_host, nombre_rival):
    print(f"\n{'='*50}")
    print(f"INICIANDO PARTIDA COMO CLIENTE")
    print(f"Oponente: {nombre_rival}")
    print(f"{'='*50}\n")
    
    mi_tablero = Tablero()
    mi_tablero.colocar_barcos()
    ia = JugadorIA()
    
    print("Mi tablero inicial:")
    mi_tablero.mostrar()
    print()
    
    # Esperar un poco para que el host inicie el servidor
    print(f"[CLIENTE] Esperando 2 segundos para que el host inicie...")
    time.sleep(2)
    
    print(f"[CLIENTE] Conectando a {ip_host}:{PUERTO}...")
    
    sock = None
    conectado = False
    
    for intento in range(1, 21):  # Aumentar a 20 intentos
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((ip_host, PUERTO))
            conectado = True
            print(f"[CLIENTE] ¡Conectado al host!\n")
            break
        except:
            print(f"[CLIENTE] Intento {intento}/20...")
            time.sleep(1)
            if sock:
                sock.close()
    
    if not conectado:
        print("[ERROR] No se pudo conectar al host")
        return
    
    # Handshake
    try:
        msg = sock.recv(1024)
        if msg != b"LISTO_HOST":
            print("[ERROR] Handshake fallido")
            sock.close()
            return
        sock.send(b"LISTO_CLIENTE")
    except:
        print("[ERROR] Error en handshake")
        sock.close()
        return
    
    print("¡PARTIDA INICIADA!")
    print("="*50)
    time.sleep(1)
    
    turno = 0
    juego_activo = True
    
    while juego_activo:
        try:
            # Turno par: HOST dispara (nosotros defendemos)
            if turno % 2 == 0:
                print(f"\n{'='*40}")
                print(f"TURNO {turno // 2 + 1} - DEFENSA")
                print(f"{'='*40}")
                
                data = sock.recv(1024).decode()
                if not data:
                    print("[ERROR] Conexión perdida")
                    break
                
                partes = data.split(";")
                
                if partes[0] == "DISPARO":
                    fila = int(partes[1])
                    col = int(partes[2])
                    print(f"← El enemigo dispara a ({fila}, {col})...")
                    
                    resultado = mi_tablero.recibir_disparo(fila, col)
                    
                    if resultado == "IMPACTO":
                        print(f"✗ Nos dieron...")
                    elif resultado == "AGUA":
                        print(f"✓ ¡Falló!")
                    elif resultado == "HUNDIDO_TOTAL":
                        print(f"☠ Nos hundieron...")
                    
                    respuesta = f"RESULTADO;{resultado}"
                    sock.send(respuesta.encode())
                    
                    if resultado == "HUNDIDO_TOTAL":
                        print(f"\n{'☠'*50}")
                        print("DERROTA. El enemigo hundió toda tu flota.")
                        print(f"{'☠'*50}\n")
                        juego_activo = False
                    else:
                        print("\nMi tablero:")
                        mi_tablero.mostrar()
                
                time.sleep(1)
            
            # Turno impar: CLIENTE dispara (nosotros atacamos)
            else:
                print(f"\n{'='*40}")
                print(f"TURNO {turno // 2 + 1} - MI ATAQUE")
                print(f"{'='*40}")
                
                fila, col = ia.obtener_disparo()
                print(f"→ Disparando a posición ({fila}, {col})...")
                
                mensaje = f"DISPARO;{fila};{col}"
                sock.send(mensaje.encode())
                
                respuesta = sock.recv(1024).decode()
                if not respuesta:
                    print("[ERROR] Conexión perdida")
                    break
                
                partes = respuesta.split(";")
                resultado = partes[1]
                
                if resultado == "IMPACTO":
                    print(f"✓ ¡IMPACTO!")
                elif resultado == "AGUA":
                    print(f"✗ Agua...")
                elif resultado == "HUNDIDO_TOTAL":
                    print(f"★ ¡HUNDIDO TOTAL!")
                
                ia.procesar_resultado(fila, col, resultado)
                
                if resultado == "HUNDIDO_TOTAL":
                    print(f"\n{'★'*50}")
                    print("¡VICTORIA! ¡Has hundido toda la flota enemiga!")
                    print(f"{'★'*50}\n")
                    juego_activo = False
                
                time.sleep(1)
            
            turno += 1
            
        except Exception as e:
            print(f"[ERROR] {e}")
            break
    
    sock.close()

if __name__ == "__main__":
    print(f"\n{'='*50}")
    print("HUNDIR LA FLOTA - MODO AUTOMÁTICO")
    print(f"{'='*50}\n")
    
    resultado = buscar_partida()
    
    if resultado:
        ip_rival, es_host, nombre_rival = resultado
        
        # NO hay delay aquí, cada función maneja sus propios tiempos
        if es_host:
            jugar_como_host(ip_rival, nombre_rival)
        else:
            jugar_como_cliente(ip_rival, nombre_rival)
        
        print("\n¡Partida finalizada!")
    else:
        print("[ERROR] No se pudo encontrar oponente")