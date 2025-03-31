import socket
import json
from cofre.settings import UDP_IP,UDP_PORT
def solicitar_lista_de_arquivos_udp(mensagem):    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(3.0)
            sock.sendto(mensagem.encode(), (UDP_IP, UDP_PORT))
            data, _ = sock.recvfrom(8192)
            lista = json.loads(data.decode())
            return lista  # Espera: ["arquivo1.txt", "sem_dono.pdf", ...]
    except Exception as e:
        print("Erro UDP:", e)
        return []
