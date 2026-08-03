from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated  # Importação corrigida!

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


# ==========================================
# VIEWS WEB (HTML)
# ==========================================

@login_required(login_url='login')  # Proteção adicionada para evitar erro com AnonymousUser
def pagina_inicial(request):
    """
    Renderiza o Dashboard principal com o resumo financeiro, 
    o planejamento matemático e a lista de transações.
    """
    transacoes = Transacao.objects.filter(usuario=request.user).order_by('-data')

    # 1. Cálculo dos cards de totais
    entradas = Transacao.objects.filter(usuario=request.user, tipo='RECEITA').aggregate(Sum('valor'))['valor__sum'] or 0
    saidas = Transacao.objects.filter(usuario=request.user, tipo='DESPESA').aggregate(Sum('valor'))['valor__sum'] or 0
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
            login(request, user)  # Loga o usuário automaticamente após cadastrar
            messages.success(request, "Usuário cadastrado com sucesso!")
            return redirect('index')
        else:
            messages.error(request, "Erro ao efetuar cadastro. Verifique os dados fornecidos.")
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