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
