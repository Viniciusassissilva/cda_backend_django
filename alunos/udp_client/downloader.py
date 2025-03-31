from cofre.settings import UDP_PORT, UDP_IP
import socket
import hashlib
from .protocol import ler_pacote

def baixar_arquivo_udp(nome_arquivo, output_path, servidor_udp=UDP_PORT, porta_udp=UDP_IP):
    SEQ_ESPERADO = 0
    BUFFER = 1024
    hash_recebido = None
    recebeu_hash = False

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)

    try:
        sock.sendto(nome_arquivo.encode(), (servidor_udp, porta_udp))
        with open(output_path, 'wb') as f:
            while True:
                pacote, _ = sock.recvfrom(BUFFER)
                seq, tipo, dados = ler_pacote(pacote)
                
                if tipo == 'F':
                    print(f'[DEBUG - INFO]: FIM DA TRANSFERENCIA, AGUARDANDO HASH')
                    break

                if seq == SEQ_ESPERADO:
                    f.write(dados)
                    ack = f"ACK{SEQ_ESPERADO}".encode()
                    sock.sendto(ack, (servidor_udp, porta_udp))
                    SEQ_ESPERADO = 1 - SEQ_ESPERADO
                else:
                    ack = f"ACK{1 - SEQ_ESPERADO}".encode()
                    sock.sendto(ack, (servidor_udp, porta_udp))

        while True:
            pacote, _ = sock.recvfrom(BUFFER)
            seq, tipo, dados = ler_pacote(pacote)

            print({seq, tipo, dados})
            recebeu_hash = False
            if tipo == 'H':
                hash_recebido = dados
                recebeu_hash = True
                print("[HASH] Pacote de hash recebido.")
                # vamos comparar o hash depois do arquivo estar completo
            # arquivo completo, agora compara o hash
            print(recebeu_hash)
            if recebeu_hash:
                sha256 = hashlib.sha256()
                with open(output_path, 'rb') as f_check:
                    while chunk := f_check.read(8192):
                        sha256.update(chunk)
                hash_local = sha256.digest()
                print(f"[DEBUG - INFO]: HASH LOCAL: {hash_local} - HASH RECEBIDO: {hash_recebido}") 
                hash_valido = hash_local == hash_recebido

                print(f"[HASH] Comparação: {'válido' if hash_valido else 'inválido'}")

                if hash_valido:
                    sock.sendto(b"ACK_HASH", (servidor_udp, porta_udp))
                    print("[HASH] ACK_HASH enviado ao servidor")
                    break
                else:
                    print("[HASH] Hash inválido — ACK_HASH não enviado")
                    return False, None
            else:
                print("[HASH] Nenhum hash foi recebido do servidor.")
                return False, None

        return True, None

    except Exception as e:
        return False, str(e)

    finally:
        sock.close()
