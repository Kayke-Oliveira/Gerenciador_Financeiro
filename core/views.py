import hashlib

from django.shortcuts import render, redirect
from django.utils import timezone

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.http import JsonResponse

from django.views.decorators.http import require_POST

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Transacao, OrcamentoMensal, ArquivoImportado, MetaFinanceira, ContaPagar, ContaReceber
from .serializers import TransacaoSerializer, OrcamentoSerializer, MetaSerializer, ContaPagarSerializer, ContaReceberSerializer
from .services.dashboard_service import DashboardService
from .services.extrato_service import ExtratoService, FormatoNaoSuportadoError
from .services.planejamento_service import PlanejamentoService


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

    # DELETE /api/transacoes/limpar_todas/
    @action(detail=False, methods=['delete'])
    def limpar_todas(self, request):
        qtd, _ = Transacao.objects.filter(usuario=request.user).delete()
        return Response({
            'sucesso': True,
            'mensagem': f'{qtd} transação(ões) excluída(s).'
        })


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
        hoje = timezone.localdate()
        mes = int(request.GET.get('mes', hoje.month))
        ano = int(request.GET.get('ano', hoje.year))

        dados = DashboardService.dados_graficos(request.user, mes, ano)
        return Response(dados)


class MetaViewSet(viewsets.ModelViewSet):
    serializer_class = MetaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MetaFinanceira.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class ContaPagarViewSet(viewsets.ModelViewSet):
    serializer_class = ContaPagarSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ContaPagar.objects.filter(usuario=self.request.user)
        mes = self.request.query_params.get('mes')
        ano = self.request.query_params.get('ano')
        if mes and ano:
            qs = qs.filter(data_vencimento__month=mes, data_vencimento__year=ano)
        return qs

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def destroy(self, request, *args, **kwargs):
        conta = self.get_object()
        if conta.transacao_gerada:
            conta.transacao_gerada.delete()
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def dar_baixa(self, request, pk=None):
        conta = self.get_object()
        if conta.paga:
            return Response({'erro': 'Conta ja foi paga.'}, status=400)

        transacao = Transacao.objects.create(
            usuario=request.user,
            descricao=conta.descricao,
            valor=conta.valor,
            tipo='DESPESA',
            data=conta.data_vencimento,
            categoria=conta.categoria,
        )

        conta.paga = True
        conta.transacao_gerada = transacao
        conta.save()

        return Response({'sucesso': True, 'mensagem': 'Conta liquidada e lancada no saldo.'})


class ContaReceberViewSet(viewsets.ModelViewSet):
    serializer_class = ContaReceberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ContaReceber.objects.filter(usuario=self.request.user)
        mes = self.request.query_params.get('mes')
        ano = self.request.query_params.get('ano')
        if mes and ano:
            qs = qs.filter(data_recebimento__month=mes, data_recebimento__year=ano)
        return qs

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def destroy(self, request, *args, **kwargs):
        conta = self.get_object()
        if conta.transacao_gerada:
            conta.transacao_gerada.delete()
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def dar_baixa(self, request, pk=None):
        conta = self.get_object()
        if conta.recebida:
            return Response({'erro': 'Conta ja foi recebida.'}, status=400)

        transacao = Transacao.objects.create(
            usuario=request.user,
            descricao=conta.descricao,
            valor=conta.valor,
            tipo='RECEITA',
            data=conta.data_recebimento,
            categoria=conta.categoria,
        )

        conta.recebida = True
        conta.transacao_gerada = transacao
        conta.save()

        return Response({'sucesso': True, 'mensagem': 'Conta recebida e lancada no saldo.'})


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
    hoje = timezone.localdate()
    mes_selecionado = int(request.GET.get('mes', hoje.month))
    ano_selecionado = int(request.GET.get('ano', hoje.year))

    # Aplica o filtro exato por usuário, mês e ano
    transacoes = Transacao.objects.filter(
        usuario=request.user,
        data__month=mes_selecionado,
        data__year=ano_selecionado
    ).order_by('-data', '-id')

    totais = DashboardService.resumo_mensal(transacoes)
    orcamento = OrcamentoMensal.objects.filter(usuario=request.user).last()
    planejamento = DashboardService.planejamento_financeiro(orcamento)
    metas = MetaFinanceira.objects.filter(usuario=request.user)

    metas_com_diagnostico = []
    for meta in metas:
        try:
            diag = PlanejamentoService.calcular_diagnostico_meta(
                meta.id, request.user
            )
        except Exception:
            diag = {'status_label': 'Sem dados', 'mensagem': 'Sem dados suficientes para diagnostico.'}
        metas_com_diagnostico.append({'meta': meta, 'diagnostico': diag})

    contexto = {
        'transacoes': transacoes,
        'planejamento': planejamento,
        'totais': totais,
        'metas_com_diagnostico': metas_com_diagnostico,
        'mes_selecionado': mes_selecionado,
        'ano_selecionado': ano_selecionado,

        'meses': [
            (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
            (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
            (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
        ],
        'anos': range(hoje.year - 6, hoje.year + 3),  # Gera de 2020 a 2028
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


# View de Extrato
@login_required
@require_POST
def importar_extrato(request):
    if 'extrato' not in request.FILES:
        return JsonResponse({'erro': 'Nenhum arquivo enviado.'}, status=400)

    arquivo = request.FILES['extrato']

    # Calcula o hash do conteúdo para detectar uploads repetidos
    hash_arquivo = hashlib.sha256(arquivo.read()).hexdigest()
    arquivo.seek(0)

    ja_importado = ArquivoImportado.objects.filter(
        usuario=request.user, hash_arquivo=hash_arquivo).exists()

    # Se o arquivo já foi importado, pede confirmação antes de prosseguir
    if ja_importado and request.POST.get('confirmar') != 'true':
        return JsonResponse({
            'ja_importado': True,
            'erro': 'Você já fez o upload desse arquivo anteriormente.'
        }, status=409)

    try:
        banco_selecionado = request.POST.get('banco', 'picpay')
        resultado = ExtratoService.importar(
            arquivo, request.user, banco_selecionado=banco_selecionado)
    except FormatoNaoSuportadoError:
        return JsonResponse({'erro': 'Formato não suportado. Envie um arquivo .OFX ou .CSV.'}, status=400)
    except Exception as e:
        return JsonResponse({'erro': f'Erro ao processar arquivo: {str(e)}'}, status=500)

    # Registra o hash do arquivo apenas se a importação teve sucesso
    ArquivoImportado.objects.get_or_create(
        usuario=request.user,
        hash_arquivo=hash_arquivo,
        defaults={'nome_arquivo': arquivo.name},
    )

    return JsonResponse({
        'sucesso': True,
        'mensagem': f'{resultado.criadas} transações importadas com sucesso! ({resultado.ignoradas} duplicadas ignoradas)'
    })

@login_required
def tela_planejamento(request):
    return redirect('index')


@login_required
@require_POST
def deletar_conta(request):
    senha = request.POST.get('senha', '')
    if not senha:
        return JsonResponse({'erro': 'Senha obrigatoria.'}, status=400)

    if not request.user.check_password(senha):
        return JsonResponse({'erro': 'Senha incorreta.'}, status=400)

    username = request.user.username
    request.user.delete()
    logout(request)
    return JsonResponse({'sucesso': True, 'mensagem': f'Conta "{username}" excluida com sucesso.'})