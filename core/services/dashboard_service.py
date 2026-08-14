import pandas as pd

from django.db.models import Sum

from ..models import Transacao
from .planejamento_service import calcular_planejamento_financeiro


class DashboardService:
    """Responsável por agregar os dados do dashboard (cards e gráficos)."""

    @staticmethod
    def resumo_mensal(transacoes):
        entradas = transacoes.filter(tipo='RECEITA').aggregate(Sum('valor'))['valor__sum'] or 0
        saidas = transacoes.filter(tipo='DESPESA').aggregate(Sum('valor'))['valor__sum'] or 0

        return {
            'entradas': entradas,
            'saidas': saidas,
            'saldo': entradas - saidas
        }

    @staticmethod
    def planejamento_financeiro(orcamento):
        if orcamento and orcamento.renda_mensal > 0:
            return calcular_planejamento_financeiro(orcamento.renda_mensal)
        return None

    @staticmethod
    def dados_graficos(usuario, mes, ano):
        """
        Retorna os dados estruturados para o Chart.js (gráfico de rosca por tipo
        e gráfico de barras por categoria de despesa).
        """
        transacoes = Transacao.objects.filter(
            usuario=usuario,
            data__month=mes,
            data__year=ano
        )

        qs = transacoes.values('descricao', 'valor', 'tipo', 'categoria', 'data')

        if not qs.exists():
            return {
                'resumo_tipo': {'labels': [], 'valores': []},
                'categorias': {'labels': [], 'valores': []}
            }

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

        return {
            'resumo_tipo': chart_tipos,
            'categorias': chart_categorias
        }
