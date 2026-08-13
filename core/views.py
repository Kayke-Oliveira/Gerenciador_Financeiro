import pandas as pd
from datetime import datetime

from django.shortcuts import render, redirect

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.db.models import Sum

from django.http import JsonResponse

from django.views.decorators.http import require_POST

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Transacao, OrcamentoMensal
from .services import calcular_planejamento_financeiro
from .serializers import TransacaoSerializer, OrcamentoSerializer

import csv
import io
from ofxparse import OfxParser




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

# View de Extrato
# Função auxiliar simples para inferir categoria básica
def categorizar_transacao(descricao):
    desc = descricao.lower()
    if any(k in desc for k in ['uber', '99', 'posto', 'shell', 'combustivel']):
        return 'Transporte'
    elif any(k in desc for k in ['ifood', 'restaurante', 'mcdonalds', 'supermercado', 'mercado']):
        return 'Alimentação'
    elif any(k in desc for k in ['aluguel', 'condominio', 'luz', 'agua', 'internet', 'claro', 'vivo']):
        return 'Moradia'
    elif any(k in desc for k in ['salario', 'rendimento', 'provento']):
        return 'Salário'
    return 'Outros'

@login_required
@require_POST
def importar_extrato(request):
    if 'extrato' not in request.FILES:
        return JsonResponse({'erro': 'Nenhum arquivo enviado.'}, status=400)

    arquivo = request.FILES['extrato']
    nome_arquivo = arquivo.name.lower()

    transacoes_criadas = 0
    transacoes_ignoradas = 0

    try:
        # ----------------------------------------------------
        # 1. PROCESSAMENTO DE ARQUIVOS OFX
        # ----------------------------------------------------
        if nome_arquivo.endswith('.ofx'):
            ofx = OfxParser.parse(arquivo)
            conta = ofx.account
            statement = conta.statement

            for t in statement.transactions:
                # Evita importar transações repetidas se o ID já existir
                if t.id and Transacao.objects.filter(transacao_id_externo=t.id, usuario=request.user).exists():
                    transacoes_ignoradas += 1
                    continue

                # OFX usa valores negativos para saídas e positivos para entradas
                tipo = 'RECEITA' if t.amount > 0 else 'DESPESA'
                valor = abs(float(t.amount))
                categoria = categorizar_transacao(t.memo or t.payee or '')

                Transacao.objects.create(
                    usuario=request.user,
                    descricao=(t.memo or t.payee or 'Importado via OFX')[:100],
                    valor=valor,
                    tipo=tipo,
                    categoria=categoria,
                    data=t.date.date(),
                    transacao_id_externo=t.id
                )
                transacoes_criadas += 1

        # ----------------------------------------------------
        # 2. PROCESSAMENTO DE ARQUIVOS CSV
        # ----------------------------------------------------
        elif nome_arquivo.endswith('.csv'):
            # Lê o conteúdo lidando com possíveis encodings (utf-8 ou latin-1)
            try:
                conteudo = arquivo.read().decode('utf-8')
            except UnicodeDecodeError:
                arquivo.seek(0)
                conteudo = arquivo.read().decode('latin-1')

            # Detecta o delimitador (; ou ,)
            delimitador = ';' if ';' in conteudo else ','
            stream = io.StringIO(conteudo)
            leitor = csv.reader(stream, delimiter=delimitador)

            for linha in leitor:
                # Pula linhas vazias ou muito curtas
                if not linha or len(linha) < 2:
                    continue

                # Normaliza todos os campos da linha
                colunas = [c.strip() for c in linha if c.strip()]

                valor_float = None
                data_str = None
                descricao_partes = []

                for item in colunas:
                    # 1. Tenta identificar a DATA
                    if not data_str and ('/' in item or '-' in item) and len(item) <= 10:
                        # Checa se parece uma data (ex: 12/08/2026 ou 2026-08-12)
                        data_str = item
                        continue

                    # 2. Tenta identificar o VALOR NUMÉRICO
                    if valor_float is None:
                        # Limpa formatação brasileira: "R$ 1.250,50" -> "1250.50"
                        item_num = item.replace('R$', '').replace(' ', '')
                        
                        # Trata formato pt-BR: remove ponto de milhar e substitui vírgula por ponto
                        if ',' in item_num:
                            item_num = item_num.replace('.', '').replace(',', '.')
                        
                        try:
                            # Testa se é um número válido
                            val_test = float(item_num)
                            # Se for o ano da data (ex: 2026), ignora como valor
                            if not (data_str and item in data_str):
                                valor_float = val_test
                                continue
                        except ValueError:
                            pass

                    # 3. O que sobrou vira parte da DESCRIÇÃO
                    descricao_partes.append(item)

                # Se encontrou pelo menos um valor válido na linha, salva a transação
                if valor_float is not None and valor_float != 0:
                    descricao = " ".join(descricao_partes) if descricao_partes else "Importado via CSV"

                    # Formata a data para YYYY-MM-DD
                    if data_str and '/' in data_str:
                        partes = data_str.split('/')
                        if len(partes) == 3:
                            # Trata DD/MM/YYYY
                            data_str = f"{partes[2]}-{partes[1].zfill(2)}-{partes[0].zfill(2)}"
                    elif not data_str:
                        from datetime import date
                        data_str = date.today().strftime('%Y-%m-%d')

                    tipo = 'RECEITA' if valor_float > 0 else 'DESPESA'
                    valor = abs(valor_float)

                    Transacao.objects.create(
                        usuario=request.user,
                        descricao=descricao[:100],
                        valor=valor,
                        tipo=tipo,
                        categoria=categorizar_transacao(descricao),
                        data=data_str
                    )
                    transacoes_criadas += 1

        else:
            return JsonResponse({'erro': 'Formato não suportado. Envie um arquivo .OFX ou .CSV.'}, status=400)

        return JsonResponse({
            'sucesso': True,
            'mensagem': f'{transacoes_criadas} transações importadas com sucesso! ({transacoes_ignoradas} duplicadas ignoradas)'
        })

    except Exception as e:
        return JsonResponse({'erro': f'Erro ao processar arquivo: {str(e)}'}, status=500)