from decimal import Decimal

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
