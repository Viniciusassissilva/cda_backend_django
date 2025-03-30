from django.db import models
from django.contrib.auth.models import AbstractUser

# Aluno herda de User e pode ser usado para login
class Aluno(AbstractUser):
    matricula = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return f"{self.username} ({self.matricula})"

# Arquivo PDF que será enviado/baixado
class Arquivo(models.Model):
    nome = models.CharField(max_length=255)
    arquivo = models.FileField(upload_to='uploads/')
    dono = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='arquivos')
    data_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} ({self.dono.username})"
