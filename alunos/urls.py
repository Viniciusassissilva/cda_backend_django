from django.urls import path
from .views import (
    LoginView,
    ArquivoListView,
    iniciar_download_udp,
    UploadViaUDP,
    ListaArquivosView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('arquivos/', ArquivoListView.as_view(), name='lista-arquivos'),
    path('upload-via-udp/', UploadViaUDP.as_view(), name='upload-via-udp'),  # ✅ esta rota aqui
    path('download/', iniciar_download_udp, name='download-udp'),
    path("all-files/", ListaArquivosView.as_view(), name="todos_arquivos"),
]