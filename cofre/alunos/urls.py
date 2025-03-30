from django.urls import path
from .views import (
    LoginView,
    ArquivoListView,
    UploadArquivoView,
    iniciar_download_udp,
    UploadViaUDP
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('arquivos/', ArquivoListView.as_view(), name='lista-arquivos'),
    path('upload/', UploadArquivoView.as_view(), name='upload-arquivo'),
    path('upload-via-udp/', UploadViaUDP.as_view(), name='upload-via-udp'),  # ✅ esta rota aqui
    path('download/', iniciar_download_udp, name='download-udp'),
]