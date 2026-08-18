from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    TransacaoViewSet, 
    OrcamentoViewSet,
    MetaViewSet, 
    pagina_inicial, 
    register_view, 
    login_view, 
    logout_view,
    GraficosDataAPIView,
    importar_extrato,
    tela_planejamento
)

# O Router gera as URLs da API RESTful (Apenas para ViewSets)
router = DefaultRouter()
router.register(r'transacoes', TransacaoViewSet, basename='transacao')
router.register(r'orcamento', OrcamentoViewSet, basename='orcamento')
router.register(r'metas', MetaViewSet, basename='meta')

urlpatterns = [
    # Páginas Web (HTML)
    path('', pagina_inicial, name='index'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),

    # Endpoints da API REST
    path('api/', include(router.urls)),
    path('api/graficos-dados/', GraficosDataAPIView.as_view(), name='graficos-dados'),
    path('api/importar-extrato/', importar_extrato, name='importar_extrato'),
    path('api/tela-planejamento/', tela_planejamento, name='tela_planejamento'),
]