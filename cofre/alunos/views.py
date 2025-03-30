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

UPLOAD_SENHA = '123456'  # senha de upload do servidor

# Login do aluno
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        print(request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            return Response(AlunoSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

# Lista de arquivos disponíveis
class ArquivoListView(ListAPIView):
    serializer_class = ArquivoSerializer
    permission_classes = [permissions.AllowAny]  # Pode mudar para IsAuthenticated

    def get_queryset(self):
        return Arquivo.objects.all().order_by('-data_envio')

class UploadArquivoView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [permissions.AllowAny]  # ou IsAuthenticated se quiser login obrigatório

    def post(self, request):
        senha = request.data.get('senha')
        nome = request.data.get('nome')
        arquivo = request.data.get('arquivo')
        usuario_id = request.data.get('usuario_id')

        if senha != UPLOAD_SENHA:
            return Response({'erro': 'Senha inválida.'}, status=403)

        try:
            aluno = Aluno.objects.get(id=usuario_id)
        except Aluno.DoesNotExist:
            return Response({'erro': 'Aluno não encontrado.'}, status=404)

        novo_arquivo = Arquivo.objects.create(
            nome=nome,
            arquivo=arquivo,
            dono=aluno
        )

        return Response({'mensagem': 'Arquivo enviado com sucesso!', 'id': novo_arquivo.id})



@api_view(['POST'])
def iniciar_download_udp(request):
    nome_arquivo = request.data.get('nome')
    aluno_id = request.data.get('aluno_id')

    output_path = os.path.join(settings.MEDIA_ROOT, 'baixados', f"baixado_{nome_arquivo}")

    sucesso, erro = baixar_arquivo_udp(
        nome_arquivo=nome_arquivo,
        output_path=output_path,
        servidor_udp='127.0.0.1',  # ou IP do seu servidor UDP em produção
        porta_udp=2005
    )

    if not sucesso:
        return Response({'erro': erro}, status=500)

    arquivo = open(output_path, 'rb')
    response = FileResponse(arquivo, as_attachment=True, filename=f"{nome_arquivo}")
    return response

class UploadViaUDP(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        print("📥 [UPLOAD] Requisição recebida.")

        arquivo = request.data.get('arquivo')
        senha = request.data.get('senha')
        arquivo = request.data.get('arquivo')
        usuario_id = request.data.get('usuario_id')

        try:
            aluno = Aluno.objects.get(id=usuario_id)
        except Aluno.DoesNotExist:
            return Response({'erro': 'Aluno não encontrado.'}, status=404)
        
        if not aluno.check_password(senha):
            return Response({'erro': 'Senha incorreta.'}, status=403)

        if not arquivo:
            print("⚠️ [UPLOAD] Nenhum arquivo foi enviado no campo 'arquivo'.")
            return Response({'erro': 'Nenhum arquivo enviado.'}, status=400)

        nome = arquivo.name
        temp_path = os.path.join(settings.MEDIA_ROOT, 'temp', nome)
        print(f"📁 [UPLOAD] Salvando temporariamente em: {temp_path}")

        try:
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)

            with open(temp_path, 'wb+') as dest:
                for chunk in arquivo.chunks():
                    dest.write(chunk)

            print("✅ [UPLOAD] Arquivo salvo com sucesso. Enviando via UDP...")

            sucesso, erro = enviar_arquivo_udp(
                path=temp_path,
                nome_arquivo=nome,
                servidor_udp='127.0.0.1',  # substitua por IP real em produção
                porta_udp=2005
            )

            os.remove(temp_path)
            print("🧹 [UPLOAD] Arquivo temporário removido.")

            if not sucesso:
                print(f"❌ [UPLOAD] Erro ao enviar via UDP: {erro}")
                return Response({'erro': erro}, status=500)

            novo_arquivo = Arquivo.objects.create(
            nome=nome,
            arquivo=arquivo,
            dono=aluno
        )
            print("✅ [UPLOAD] Upload concluído com sucesso via UDP.")
            return Response({'mensagem': 'Arquivo enviado com sucesso!', 'id': novo_arquivo.id})

        except Exception as e:
            print(f"🔥 [UPLOAD] EXCEÇÃO GERAL: {e}")
            return Response({'erro': str(e)}, status=500)