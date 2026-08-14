from ofxparse import OfxParser as OfxParserLib

from .categorizador import categorizar_transacao


class OfxExtratoParser:
    """Lê um arquivo .OFX e devolve as transações em um formato normalizado."""

    @staticmethod
    def parse(arquivo):
        ofx = OfxParserLib.parse(arquivo)
        conta = ofx.account
        statement = conta.statement

        transacoes = []
        for t in statement.transactions:
            # OFX usa valores negativos para saídas e positivos para entradas
            transacoes.append({
                'descricao': (t.memo or t.payee or 'Importado via OFX')[:100],
                'valor': abs(float(t.amount)),
                'tipo': 'RECEITA' if t.amount > 0 else 'DESPESA',
                'categoria': categorizar_transacao(t.memo or t.payee or ''),
                'data': t.date.date(),
                'transacao_id_externo': t.id,
            })

        return transacoes
