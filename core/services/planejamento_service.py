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
    def calcular_diagnostico_meta(meta_id, usuario):
        meta = MetaFinanceira.objects.get(id=meta_id, usuario=usuario)

        valor_objetivo = meta.valor_objetivo or Decimal('0.00')
        valor_atual = meta.valor_atual or Decimal('0.00')

        # Evita divisão por zero
        if valor_objetivo > 0:
            progresso_pct = (valor_atual / valor_objetivo) * 100
        else:
            progresso_pct = Decimal('0.00')

        # Define o status com base puramente no valor já acumulado
        if progresso_pct >= 100:
            status_label = 'Concluída 🎉'
            mensagem = 'Parabéns! Você alcançou o valor total definido para esta meta.'
        elif progresso_pct >= 70:
            status_label = 'Perto do Objetivo 🎯'
            mensagem = f'Você já acumulou {progresso_pct:.1f}% da sua meta. Falta bem pouco!'
        elif progresso_pct >= 30:
            status_label = 'Em Andamento ⏳'
            mensagem = f'Você já conquistou {progresso_pct:.1f}% do objetivo. Mantenha o foco!'
        else:
            status_label = 'Início da Meta 🚀'
            mensagem = f'Você possui {progresso_pct:.1f}% acumulado. Continue guardando para avançar!'

        return {
            'meta': meta,
            'progresso_pct': round(float(progresso_pct), 1),
            'status_label': status_label,
            'mensagem': mensagem
        }