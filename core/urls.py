from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import TransacaoViewSet, OrcamentoViewSet ,pagina_inicial

# O Router gera as URLs RESTful do CRUD automaticamente
router = DefaultRouter()
router.register(r'transacoes', TransacaoViewSet, basename='transacao')
router.register(r'orcamento', OrcamentoViewSet, basename='orcamento')

urlpatterns = [
    path('', pagina_inicial, name='pagina_inicial'),
    path('api/', include(router.urls)),
]
