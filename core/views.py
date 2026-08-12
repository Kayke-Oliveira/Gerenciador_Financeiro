import pandas as pd
from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated  # Importação corrigida!
from rest_framework.response import Response

from .models import Transacao, OrcamentoMensal
from .services import calcular_planejamento_financeiro
from .serializers import TransacaoSerializer, OrcamentoSerializer


# ==========================================
# API REST (ViewSets)
# ==========================================

class TransacaoViewSet(viewsets.ModelViewSet):
    serializer_class = TransacaoSerializer
    permission_classes = [IsAuthenticated]

    # Garante que cada usuário veja APENAS as suas transações
    def get_queryset(self):
        return Transacao.objects.filter(usuario=self.request.user).order_by('-data')

    # Atribui automaticamente o usuário logado ao criar via POST
    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class OrcamentoViewSet(viewsets.ModelViewSet):
    serializer_class = OrcamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OrcamentoMensal.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class GraficosDataAPIView(APIView):
    """
    Endpoint da API REST para fornecer dados estruturados para o Chart.js.
    Acessível apenas para usuários autenticados.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):

        hoje = datetime.now()
        mes = request.GET.get('mes')
        ano = request.GET.get('ano')

        # Se não vier na requisição, assume o mês/ano atual
        mes = int(mes) if mes else hoje.month
        ano = int(ano) if ano else hoje.year

        # 📍 Filtra as transações do gráfico por mês e ano
        transacoes = Transacao.objects.filter(
            usuario=request.user,
            data__month=mes,
            data__year=ano
        )

        # 🔧 CORREÇÃO: Utilizando a queryset 'transacoes' (que já possui os filtros de mês e ano)
        # em vez de refazer a busca sem filtro no banco de dados.
        qs = transacoes.values('descricao', 'valor', 'tipo', 'categoria', 'data')

        if not qs.exists():
            return Response({
                'resumo_tipo': {'labels': [], 'valores': []},
                'categorias': {'labels': [], 'valores': []} # Ajustado a chave para 'categorias'
            })

        df = pd.DataFrame(list(qs))
        df['valor'] = df['valor'].astype(float)

        # 1 - Gráfico de Rosca
        tipo_grouped = df.groupby('tipo')['valor'].sum().reset_index()
        chart_tipos = {
            'labels': tipo_grouped['tipo'].tolist(),
            'valores': tipo_grouped['valor'].tolist()
        }

        # 2 - Gráfico de Barras Horizontais
        df_despesas = df[df['tipo'] == 'DESPESA']

        if not df_despesas.empty:
            df_despesas['categoria'] = df_despesas['categoria'].fillna(
                'Outros').replace('', 'Outros')

            # Agrupa, soma e ordena do maior para o menor gasto
            catch_grouped = df_despesas.groupby(
                'categoria')['valor'].sum().reset_index()
            catch_grouped = catch_grouped.sort_values(
                by='valor', ascending=False)

            chart_categorias = {
                'labels': catch_grouped['categoria'].tolist(),
                'valores': catch_grouped['valor'].tolist()
            }
        else:
            chart_categorias = {'labels': [], 'valores': []}

        return Response({
            'resumo_tipo': chart_tipos,
            'categorias': chart_categorias
        })

# ==========================================
# VIEWS WEB (HTML)
# ==========================================


# Proteção adicionada para evitar erro com AnonymousUser
@login_required(login_url='login')
def pagina_inicial(request):
    """
    Renderiza o Dashboard principal com o resumo financeiro, 
    o planejamento matemático e a lista de transações.
    """
    # Para obter mês e ano e transformar em um filtro
    hoje = datetime.now()
    # Obtém mês e ano dos parâmetros GET da URL ou usa o mês/ano atual
    mes_selecionado = int(request.GET.get('mes', hoje.month))
    ano_selecionado = int(request.GET.get('ano', hoje.year))

    # 🔧 MODIFICAÇÃO: Removida a primeira chamada duplicada a Transacao.objects.filter()
    # Aplica o filtro exato por usuário, mês e ano
    transacoes = Transacao.objects.filter(
        usuario=request.user,
        data__month=mes_selecionado,
        data__year=ano_selecionado
    ).order_by('-data', '-id')

    # 1. Cálculo dos cards de totais
    # 🔧 CORREÇÃO: Aplica a soma agregada diretamente sobre a QuerySet 'transacoes' (que já está filtrada por mês/ano)
    entradas = transacoes.filter(tipo='RECEITA').aggregate(Sum('valor'))['valor__sum'] or 0
    saidas = transacoes.filter(tipo='DESPESA').aggregate(Sum('valor'))['valor__sum'] or 0
    saldo = entradas - saidas

    totais = {
        'entradas': entradas,
        'saidas': saidas,
        'saldo': saldo
    }

    # 2. Busca o último orçamento do usuário
    orcamento = OrcamentoMensal.objects.filter(usuario=request.user).last()

    # 3. Executa as regras de planejamento apenas se houver salário cadastrado
    planejamento = None
    if orcamento and orcamento.renda_mensal > 0:
        planejamento = calcular_planejamento_financeiro(orcamento.renda_mensal)

    contexto = {
        'transacoes': transacoes,
        'planejamento': planejamento,
        'totais': totais,
        'mes_selecionado': mes_selecionado,
        'ano_selecionado': ano_selecionado,

        'meses': [
            (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
            (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
            (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
        ],
        'anos': range(hoje.year - 2, hoje.year + 3),  # Gera de 2024 a 2028
    }

    return render(request, 'core/index.html', contexto)


# View de Registro
def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Loga o usuário automaticamente após cadastrar
            login(request, user)
            messages.success(request, "Usuário cadastrado com sucesso!")
            return redirect('index')
        else:
            messages.error(
                request, "Erro ao efetuar cadastro. Verifique os dados fornecidos.")
    else:
        form = UserCreationForm()

    return render(request, 'core/register.html', {'form': form})


# View de Login
def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, "Usuário ou senha inválidos.")
    else:
        form = AuthenticationForm()

    return render(request, 'core/login.html', {'form': form})


# View de Logout
def logout_view(request):
    logout(request)
    return redirect('login')