from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Arquivo
from .serializers import LoginSerializer, ArquivoSerializer, AlunoSerializer
from rest_framework.generics import ListAPIView
from rest_framework.parsers import MultiPartParser
from alunos.models import Aluno
from rest_framework.decorators import api_view
from alunos.udp_client.downloader import baixar_arquivo_udp
from django.conf import settings
import os
from django.http import FileResponse
from rest_framework.parsers import MultiPartParser
from alunos.udp_client.uploader import enviar_arquivo_udp
import threading
from datetime import datetime
from cofre.settings import UDP_IP, UDP_PORT
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from waffle import flag_is_active
from alunos.udp_client.listar_arquivos import solicitar_lista_de_arquivos_udp

# Login do aluno
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        print(request.data)
        if serializer.is_valid():
            user = serializer.validated_data

            # ✅ Gera tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            # ✅ Monta resposta com usuário + token
            return Response({
                "user": AlunoSerializer(user).data,
                "access": access_token
            })

        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

# Lista de arquivos disponíveis
class ArquivoListView(ListAPIView):
    serializer_class = ArquivoSerializer
    permission_classes = [permissions.AllowAny]  # Pode mudar para IsAuthenticated

    def get_queryset(self):
        return Arquivo.objects.all().order_by('-data_envio')



@api_view(['POST'])
def iniciar_download_udp(request):
    print("[INFO] Requisiçao recebida para iniciar download via UDP.")
    
    nome_arquivo = request.data.get('nome')
    aluno_id = request.data.get('aluno_id')
    print(f"[DEBUG] Nome do arquivo: {nome_arquivo}")
    print(f"[DEBUG] ID do aluno: {aluno_id}")

    output_path = os.path.join(settings.MEDIA_ROOT, 'baixados', f"baixado_{nome_arquivo}")
    print(f"[DEBUG] Caminho do arquivo de saída: {output_path}")

    mensagem = f"DOWNLOAD:{nome_arquivo}"
    if flag_is_active(request, "simular_perda"):
        mensagem += ":SIMULAR_PERDA"

    print(f'[DEBUG]: FEATURE FLAG ATIVA: {flag_is_active(request, "simular_perda")}')

    try:
 
        sucesso, erro = baixar_arquivo_udp(
            nome_arquivo=mensagem,
            output_path=output_path,
            servidor_udp=UDP_IP,  # ou IP do seu servidor UDP em produçao
            porta_udp=UDP_PORT
        )
    except Exception as e:
        print(f"[ERRO] Falha ao chamar baixar_arquivo_udp: {e}")
        return Response({'erro': str(e)}, status=500)

    if not sucesso:
        print(f"[ERRO] Erro ao baixar arquivo via UDP: {erro}")
        return Response({'erro': erro}, status=500)

    print("[INFO] Arquivo baixado com sucesso. Preparando para envio...")

    try:
        arquivo = open(output_path, 'rb')
    except Exception as e:
        print(f"[ERRO] Nao foi possível abrir o arquivo baixado: {e}")
        return Response({'erro': 'Erro ao abrir o arquivo baixado'}, status=500)

    def remove_file():
        try:
            os.remove(output_path)
            print(f"[INFO] Arquivo removido após envio: {output_path}")
        except Exception as e:
            print(f"[ERRO] Erro ao remover o arquivo: {e}")

    print(f"[INFO] FILE RESPONSE: {arquivo}, {nome_arquivo}")
    response = FileResponse(arquivo, as_attachment=True, filename=f"{nome_arquivo}")

    # Remove o arquivo depois de um pequeno delay
    threading.Timer(3.0, remove_file).start()

    print("[INFO] Resposta com o arquivo sendo retornada ao cliente.")
    return response


class UploadViaUDP(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        print("[UPLOAD] Requisiçao recebida.")

        senha = request.data.get('senha')
        arquivo = request.data.get('arquivo')
        usuario_id = request.data.get('usuario_id')

        try:
            aluno = Aluno.objects.get(id=usuario_id)
        except Aluno.DoesNotExist:
            return Response({'erro': 'Aluno nao encontrado.'}, status=404)
        
        if not aluno.check_password(senha):
            return Response({'erro': 'Senha incorreta.'}, status=403)

        if not arquivo:
            print("[UPLOAD] Nenhum arquivo foi enviado no campo 'arquivo'.")
            return Response({'erro': 'Nenhum arquivo enviado.'}, status=400)

        nome = arquivo.name
        temp_path = os.path.join(settings.MEDIA_ROOT, 'temp', nome)
        print(f"[UPLOAD] Salvando temporariamente em: {temp_path}")

        try:
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)

            with open(temp_path, 'wb+') as dest:
                for chunk in arquivo.chunks():
                    dest.write(chunk)

            print("[UPLOAD] Arquivo salvo com sucesso. Enviando via UDP...")
            sucesso, erro = enviar_arquivo_udp(
                path=temp_path,
                nome_arquivo=nome,
                servidor_udp=UDP_IP,
                porta_udp=UDP_PORT
            )


            os.remove(temp_path)
            print("[UPLOAD] Arquivo temporário removido.")

            if not sucesso:
                print(f"[UPLOAD] Erro ao enviar via UDP: {erro}")
                return Response({'erro': erro}, status=500)

            novo_arquivo = Arquivo.objects.create(
            nome=nome,
            arquivo=arquivo,
            dono=aluno
        )
            print("[UPLOAD] Upload concluído com sucesso via UDP.")
            return Response({'mensagem': 'Arquivo enviado com sucesso!', 'id': novo_arquivo.id})

        except Exception as e:
            print(f"[UPLOAD] EXCEÇaO GERAL: {e}")
            return Response({'erro': str(e)}, status=500)
        
class ListaArquivosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_superuser:
            return Response({"detail": "Acesso negado."}, status=status.HTTP_403_FORBIDDEN)
        
        mensagem = "LISTAR_ARQUIVOS"
        if flag_is_active(request, "simular_perda"):
            mensagem += ":SIMULAR_PERDA"

        nomes_arquivos = solicitar_lista_de_arquivos_udp(mensagem)
        arquivos_no_banco = Arquivo.objects.all()

        resultado = []
        for nome in nomes_arquivos:
            arquivo = arquivos_no_banco.filter(nome=nome).first()
            resultado.append({
                "filename": nome,
                "has_owner": arquivo and arquivo.dono is not None,
                "owner": arquivo.dono.username if arquivo and arquivo.dono else None
            })

        return Response(resultado)