import struct
import hashlib

def criar_pacote(seq, tipo, dados):
    """
    Cria um pacote com cabeçalho (2 bytes) + dados.
    Cabeçalho:
      - seq: número de sequência (0 ou 1)
      - tipo: caractere ('D' = dado, 'F' = fim, 'H' = hash)
    """
    header = struct.pack('!BB', seq, ord(tipo))
    return header + dados

def ler_pacote(pacote):
    """
    Lê um pacote e retorna: (seq, tipo, dados)
    """
    seq, tipo = struct.unpack('!BB', pacote[:2])
    dados = pacote[2:]
    return seq, chr(tipo), dados

def calcular_hash_arquivo(path):
    """
    Gera um hash SHA-256 do arquivo dado
    """
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.digest()
