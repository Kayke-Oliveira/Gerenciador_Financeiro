from django.shortcuts import render
from rest_framework import viewsets
from django.db.models import Sum
from .models import Transacao, OrcamentoMensal
from .services import calcular_planejamento_financeiro
from .serializers import TransacaoSerializer, OrcamentoSerializer

from rest_framework.permissions import AllowAny


class TransacaoViewSet(viewsets.ModelViewSet):
    """
    ViewSets agregam toda a lógica do CRUD automático em uma única classe.

    Ao Herdar de 'ModelViewSet', o Django REST Framework cuida dos 6 verbos HTTP:
    - GET /api/transacoes/         -> Lista todos os registros
    - POST /api/transacoes/        -> Cria um novo registro
    - GET /api/transacoes/<id>/    -> Busca os detalhes de um registro
    - PUT /api/transacoes/<id>/    -> Atualização completa do registro
    - PATCH /api/transacoes/<id>/  -> Atualização parcial (ex: mudar 'pago' para True)
    - DELETE /api/transacoes/<id>/ -> Deleta o registro do SQLite
    """
    # 1 - Consultar no banco via ORM (tradutor de python para sql), ordenando as mais recentes para as mais antigas
    queryset = Transacao.objects.all().order_by('-data')

    # 2 - Especifica qual tradutor (serializer) será usado para converter em JSON
    serializer_class = TransacaoSerializer

    # 3 - Permite que qualquer usuário envie os dados para a API
    permission_classes = [AllowAny]

class OrcamentoViewSet(viewsets.ModelViewSet):
    """
    API REST para Registro do Orçamento / Salário Mensal.
    - GET /api/orcamento/
    - POST /api/orcamento/
    """
    queryset = OrcamentoMensal.objects.all()
    serializer_class = OrcamentoSerializer
    permission_classes = [AllowAny]

# View do site em html
def pagina_inicial(request):
    """
    Renderiza o Dashboard principal com o resumo financeiro, 
    o planejamento matemático e a lista de transações.
    """
    transacoes = Transacao.objects.all().order_by('-data')

    # 1. Cálculo dos cards de totais (Entradas, Saídas e Saldo)
    entradas = Transacao.objects.filter(tipo='RECEITA').aggregate(Sum('valor'))['valor__sum'] or 0
    saidas = Transacao.objects.filter(tipo='DESPESA').aggregate(Sum('valor'))['valor__sum'] or 0
    saldo = entradas - saidas

    totais = {
        'entradas': entradas,
        'saidas': saidas,
        'saldo': saldo
    }

    # 2. Busca o último orçamento cadastrado
    orcamento = OrcamentoMensal.objects.last()
    
    # 3. Executa as regras de planejamento apenas se houver salário cadastrado
    planejamento = None
    if orcamento and orcamento.renda_mensal > 0:
        planejamento = calcular_planejamento_financeiro(orcamento.renda_mensal)

    contexto = {
        'transacoes': transacoes,
        'planejamento': planejamento,
        'totais': totais,
    }

    return render(request, 'core/index.html', contexto)