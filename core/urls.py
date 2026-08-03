from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    TransacaoViewSet, 
    OrcamentoViewSet, 
    pagina_inicial, 
    register_view, 
    login_view, 
    logout_view
)

# O Router gera as URLs da API RESTful (Apenas para ViewSets)
router = DefaultRouter()
router.register(r'transacoes', TransacaoViewSet, basename='transacao')
router.register(r'orcamento', OrcamentoViewSet, basename='orcamento')

urlpatterns = [
    # Páginas Web (HTML)
    path('', pagina_inicial, name='index'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),

    # Endpoints da API REST
    path('api/', include(router.urls)),
]