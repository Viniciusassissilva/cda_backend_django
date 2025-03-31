from rest_framework import serializers
from .models import Aluno, Arquivo
from django.contrib.auth import authenticate

class AlunoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno
        fields = ['id', 'username', 'email', 'matricula', 'is_superuser']

class ArquivoSerializer(serializers.ModelSerializer):
    dono = AlunoSerializer(read_only=True)

    class Meta:
        model = Arquivo
        fields = ['id', 'nome', 'arquivo', 'data_envio', 'dono']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Usuário ou senha inválidos.")
