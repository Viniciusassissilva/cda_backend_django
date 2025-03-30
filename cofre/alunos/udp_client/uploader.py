import socket
import os
from .protocol import criar_pacote

def enviar_arquivo_udp(path, nome_arquivo, servidor_udp, porta_udp):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)

    try:
        # Enviar comando inicial
        sock.sendto(f"UPLOAD:{nome_arquivo}".encode(), (servidor_udp, porta_udp))

        SEQ = 0
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(1022)
                if not chunk:
                    break
                enviado = False
                while not enviado:
                    pacote = criar_pacote(SEQ, 'D', chunk)
                    sock.sendto(pacote, (servidor_udp, porta_udp))

                    try:
                        ack, _ = sock.recvfrom(1024)
                        if ack.startswith(f"ACK{SEQ}".encode()):
                            SEQ = 1 - SEQ
                            enviado = True
                    except socket.timeout:
                        print("Timeout, reenviando")

        fim = criar_pacote(9, 'F', b'')
        sock.sendto(fim, (servidor_udp, porta_udp))
        print("Arquivo enviado com sucesso.")
        return True, None

    except Exception as e:
        return False, str(e)

    finally:
        sock.close()
