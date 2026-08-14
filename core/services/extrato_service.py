from ..models import Transacao
from ..parsers.csv_parser import CsvExtratoParser
from ..parsers.ofx_parser import OfxExtratoParser


class FormatoNaoSuportadoError(Exception):
    """Erro lançado quando o arquivo enviado não é .OFX nem .CSV."""


class ImportResult:
    def __init__(self, criadas=0, ignoradas=0):
        self.criadas = criadas
        self.ignoradas = ignoradas


class ExtratoService:
    """Orquestra a leitura de extratos (OFX/CSV) e a criação das transações."""

    @staticmethod
    def importar(arquivo, usuario, banco_selecionado='geral'):
        nome_arquivo = arquivo.name.lower()

        if nome_arquivo.endswith('.ofx'):
            return ExtratoService._importar_ofx(arquivo, usuario)

        if nome_arquivo.endswith('.csv'):
            # Passa o banco_selecionado para o método interno de CSV
            return ExtratoService._importar_csv(arquivo, usuario, banco_selecionado)

        raise FormatoNaoSuportadoError(
            'Formato não suportado. Envie um arquivo .OFX ou .CSV.'
        )

    @staticmethod
    def _importar_ofx(arquivo, usuario):
        criadas = 0
        ignoradas = 0

        for t in OfxExtratoParser.parse(arquivo):
            if t['transacao_id_externo'] and Transacao.objects.filter(
                    transacao_id_externo=t['transacao_id_externo'], usuario=usuario).exists():
                ignoradas += 1
                continue

            Transacao.objects.create(usuario=usuario, **t)
            criadas += 1

        return ImportResult(criadas, ignoradas)

    @staticmethod
    def _importar_csv(arquivo, usuario, banco_selecionado='geral'):
        criadas = 0

        # Passa o banco_selecionado para o parser se ele aceitar o argumento
        for t in CsvExtratoParser.parse(arquivo, banco=banco_selecionado):
            Transacao.objects.create(usuario=usuario, **t)
            criadas += 1

        return ImportResult(criadas, 0)