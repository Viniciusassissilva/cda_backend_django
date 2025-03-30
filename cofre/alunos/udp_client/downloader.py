import socket, os
from .protocol import ler_pacote, criar_pacote

def baixar_arquivo_udp(nome_arquivo, output_path, servidor_udp='127.0.0.1', porta_udp=2005):
    SEQ_ESPERADO = 0
    BUFFER = 1024

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)

    try:
        sock.sendto(nome_arquivo.encode(), (servidor_udp, porta_udp))
        with open(output_path, 'wb') as f:
            while True:
                pacote, _ = sock.recvfrom(BUFFER)
                seq, tipo, dados = ler_pacote(pacote)

                if tipo == 'F':
                    break

                if seq == SEQ_ESPERADO:
                    f.write(dados)
                    ack = f"ACK{SEQ_ESPERADO}".encode()
                    sock.sendto(ack, (servidor_udp, porta_udp))
                    SEQ_ESPERADO = 1 - SEQ_ESPERADO
                else:
                    ack = f"ACK{1 - SEQ_ESPERADO}".encode()
                    sock.sendto(ack, (servidor_udp, porta_udp))

        return True, None

    except Exception as e:
        return False, str(e)

    finally:
        sock.close()