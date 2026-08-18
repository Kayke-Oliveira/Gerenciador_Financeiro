from decimal import Decimal
from django.db.models import Sum
from datetime import datetime
from core.models import MetaFinanceira, Transacao

def calcular_planejamento_financeiro(salario_mensal):
    #Aqui será realizado o cálculo de metas e também será distribuido com base em valores pré setados o orçamento mensal com base no salário informado
    salario = Decimal(str(salario_mensal))

    if salario <= 0:
        return None

    #Metas de longo prazo
    meta_renda_passiva = round(salario * Decimal('200'))
    reserva_emergencia = round(salario * Decimal('6'))

    #Distribuição do Orçamento Mensal
    investimento_mensal = round(salario * Decimal('0.10')) #10%
    contas_fixas = round(salario * Decimal('0.60')) #60%
    lazer = round(salario * Decimal('0.30')) #30%

    return{
        'salario': salario,
        #Metas globais
        'meta_renda_passiva': meta_renda_passiva,
        'reserva_emergencia': reserva_emergencia,
        #Orçamento Mensal
        'investimento_mensal': investimento_mensal,
        'contas_fixas': contas_fixas,
        'lazer': lazer,
    }

class PlanejamentoService:

    @staticmethod
    def calcular_diagnostico_meta(meta_id, usuario, mes=None, ano=None):
        meta = MetaFinanceira.objects.get(id=meta_id, usuario=usuario)

        #Filtra mês/ano atual se não informado
        hoje = datetime.now()
        mes = mes or hoje.month
        ano = ano or hoje.year

        #Quanto o usuario precisa poupar no total e por mês (com base no prazo)
        valor_restante = max(Decimal('0.00'), meta.valor_objetivo - meta.valor_atual)

        if meta.prazo_meses > 0:
            aporte_necessario_mensal = valor_restante / Decimal(meta.prazo_meses)

        else:
            aporte_necessario_mensal = valor_restante

        #Busca receitas e despesas do mês selecionado
        transacoes_mes = Transacao.objects.filter(
            usuario=usuario,
            data__year=ano,
            data__month=mes
        )

        total_receitas = transacoes_mes.filter(tipo='RECEITA').aggregate(s=Sum('valor'))['s'] or Decimal('0.00')
        total_despesas = transacoes_mes.filter(tipo='DESPESA').aggregate(s=Sum('valor'))['s'] or Decimal('0.00')

        # Capacidade Real de Poupança no Mês (Sobra de caixa)
        sobra_mes = total_receitas - total_despesas

        # Percentual de capacidade (quanto da necessidade mensal a sobra cobre)
        if aporte_necessario_mensal > 0 and sobra_mes > 0:
            percentual_capacidade = (sobra_mes / aporte_necessario_mensal) * 100
        else:
            percentual_capacidade = Decimal('0.00')

        # Diagnóstico: só avalia se houver transações no período
        if not transacoes_mes.exists():
            status = 'Neutro'
            mensagem = 'Registre suas receitas e despesas deste período para obter um diagnóstico.'
        elif sobra_mes < 0:
            status = 'Crítico'
            mensagem = 'Suas despesas superaram suas receitas neste mês. Você não tem sobra para aportar.'
        elif aporte_necessario_mensal <= 0:
            status = 'Excelente'
            mensagem = 'Parabéns! Sua meta já foi atingida.'
        elif percentual_capacidade >= 100:
            status = 'Excelente'
            mensagem = f'Você está superando a meta! Sua sobra de R${sobra_mes:.2f} cobre o aporte necessário de R${aporte_necessario_mensal:.2f} este mês.'
        elif percentual_capacidade >= 70:
            status = 'Próximo'
            mensagem = f'Você está perto! Conseguirá cobrir {percentual_capacidade:.1f}% do aporte necessário este mês.'
        else:
            status = 'Longe'
            diferenca = aporte_necessario_mensal - sobra_mes
            mensagem = f'Você está longe do objetivo. Faltam R$ {diferenca:.2f} de sobra no mês para atingir o aporte ideal.'

        #Progresso geral do objetivo acumulado
        progresso_total_pct = (meta.valor_atual / meta.valor_objetivo * 100) if meta.valor_objetivo > 0 else 0

        return {
                    'meta': meta,
                    'valor_restante': valor_restante,
                    'aporte_necessario_mensal': round(aporte_necessario_mensal, 2),
                    'aporte_desejado_usuario': meta.aporte_mensal_desejado,
                    'sobra_atual_mes': round(sobra_mes, 2),
                    'percentual_alcancado_mes': round(percentual_capacidade, 1),
                    'progresso_total_pct': round(progresso_total_pct, 1),
                    'status': status,
                    'mensagem': mensagem
                }