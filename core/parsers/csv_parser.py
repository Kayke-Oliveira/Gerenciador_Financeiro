import csv
import io
import re
from datetime import date
from core.parsers.categorizador import categorizar_transacao


class PicPayParser:
    """Parser específico para extratos do PicPay."""
    
    @staticmethod
    def parse_linha(linha, cabecalho):
        idx_data = next((i for i, c in enumerate(cabecalho) if 'data' in c), None)
        idx_valor = next((i for i, c in enumerate(cabecalho) if 'valor' in c), None)
        idx_tipo = next((i for i, c in enumerate(cabecalho) if 'tipo' in c), None)
        idx_origem = next((i for i, c in enumerate(cabecalho) if any(k in c for k in ['origem', 'destino', 'descri', 'lançamento', 'histórico'])), None)

        val_raw = linha[idx_valor].strip() if idx_valor is not None and idx_valor < len(linha) else ""
        if not val_raw:
            return None

        tipo_raw = linha[idx_tipo].strip() if idx_tipo is not None and idx_tipo < len(linha) else ""
        origem_raw = linha[idx_origem].strip() if idx_origem is not None and idx_origem < len(linha) else ""
        data_raw = linha[idx_data].strip() if idx_data is not None and idx_data < len(linha) else ""

        descricao = f"{tipo_raw} - {origem_raw}" if (tipo_raw and origem_raw) else (origem_raw or tipo_raw or "Importado PicPay")

        val_limpo = val_raw.replace('–', '-').replace('—', '-').replace('\u2212', '-').replace('R$', '').replace('\xa0', '').strip()
        val_limpo = re.sub(r'\s+', '', val_limpo)

        # Regra do PicPay
        tipo_lower = tipo_raw.lower()
        if '-' in val_limpo or 'pix enviado' in tipo_lower:
            tipo_final = 'DESPESA'
        else:
            tipo_final = 'RECEITA'

        return data_raw, val_limpo, descricao, tipo_final


class NubankParser:
    """Parser específico para extratos do Nubank."""
    
    @staticmethod
    def parse_linha(linha, cabecalho):
        # O Nubank costuma ter colunas: Data, Valor, Identificador, Descrição
        idx_data = next((i for i, c in enumerate(cabecalho) if 'data' in c), 0)
        idx_valor = next((i for i, c in enumerate(cabecalho) if 'valor' in c), 1)
        idx_desc = next((i for i, c in enumerate(cabecalho) if 'descri' in c or 'title' in c), 2)

        val_raw = linha[idx_valor].strip() if idx_valor < len(linha) else ""
        if not val_raw:
            return None

        data_raw = linha[idx_data].strip() if idx_data < len(linha) else ""
        descricao = linha[idx_desc].strip() if idx_desc < len(linha) else "Importado Nubank"

        val_limpo = val_raw.replace('R$', '').replace('\xa0', '').strip()
        val_limpo = re.sub(r'\s+', '', val_limpo)

        # No Nubank, valores com sinal negativo (-) são despesas
        tipo_final = 'DESPESA' if '-' in val_limpo else 'RECEITA'

        return data_raw, val_limpo, descricao, tipo_final

class BradescoParser:
    """Parser específico para extratos do Bradesco."""
    
    @staticmethod
    def parse_linha(linha, cabecalho):
        # Colunas típicas Bradesco: Data, Histórico, Docto., Crédito (R$), Débito (R$) OU Data, Histórico, Valor
        idx_data = next((i for i, c in enumerate(cabecalho) if 'data' in c), 0)
        idx_desc = next((i for i, c in enumerate(cabecalho) if any(k in c for k in ['histór', 'descri', 'lançamento'])), 1)
        
        data_raw = linha[idx_data].strip() if idx_data < len(linha) else ""
        descricao = linha[idx_desc].strip() if idx_desc < len(linha) else "Importado Bradesco"

        # Tenta identificar por colunas separadas de Débito/Crédito
        idx_credito = next((i for i, c in enumerate(cabecalho) if 'crédit' in c or 'credito' in c), None)
        idx_debito = next((i for i, c in enumerate(cabecalho) if 'débit' in c or 'debito' in c), None)

        if idx_credito is not None and idx_debito is not None:
            val_cred = linha[idx_credito].strip() if idx_credito < len(linha) else ""
            val_deb = linha[idx_debito].strip() if idx_debito < len(linha) else ""

            if val_deb and val_deb != '0' and val_deb != '0,00':
                return data_raw, val_deb, descricao, 'DESPESA'
            elif val_cred and val_cred != '0' and val_cred != '0,00':
                return data_raw, val_cred, descricao, 'RECEITA'

        # Fallback para coluna de Valor única com sinal de (-)
        idx_valor = next((i for i, c in enumerate(cabecalho) if 'valor' in c), 2)
        val_raw = linha[idx_valor].strip() if idx_valor < len(linha) else ""
        if not val_raw:
            return None

        val_limpo = val_raw.replace('R$', '').replace('\xa0', '').strip()
        val_limpo = re.sub(r'\s+', '', val_limpo)

        tipo_final = 'DESPESA' if '-' in val_limpo else 'RECEITA'
        return data_raw, val_limpo, descricao, tipo_final


class ItauParser:
    """Parser específico para extratos do Itaú."""
    
    @staticmethod
    def parse_linha(linha, cabecalho):
        # O Itaú costuma usar a coluna Data, Lançamento/Descrição e Valor (com sinal -)
        idx_data = next((i for i, c in enumerate(cabecalho) if 'data' in c), 0)
        idx_desc = next((i for i, c in enumerate(cabecalho) if any(k in c for k in ['lançamento', 'lancamento', 'historico', 'descri'])), 1)
        idx_valor = next((i for i, c in enumerate(cabecalho) if 'valor' in c), 2)

        val_raw = linha[idx_valor].strip() if idx_valor < len(linha) else ""
        if not val_raw:
            return None

        data_raw = linha[idx_data].strip() if idx_data < len(linha) else ""
        descricao = linha[idx_desc].strip() if idx_desc < len(linha) else "Importado Itaú"

        val_limpo = val_raw.replace('R$', '').replace('\xa0', '').strip()
        val_limpo = re.sub(r'\s+', '', val_limpo)

        # Trata formato do Itaú onde saídas podem ter (-) ou o sufixo " D" (ex: 50,00D)
        desc_lower = descricao.lower()
        if '-' in val_limpo or val_limpo.endswith('d') or 'tarifa' in desc_lower or 'pagto' in desc_lower:
            tipo_final = 'DESPESA'
        else:
            tipo_final = 'RECEITA'

        val_limpo = val_limpo.rstrip('d').rstrip('D').rstrip('c').rstrip('C')
        return data_raw, val_limpo, descricao, tipo_final


class SantanderParser:
    """Parser específico para extratos do Santander."""
    
    @staticmethod
    def parse_linha(linha, cabecalho):
        # Santander costuma trazer: Data, Descrição/Histórico, Valor (com sinal)
        idx_data = next((i for i, c in enumerate(cabecalho) if 'data' in c), 0)
        idx_desc = next((i for i, c in enumerate(cabecalho) if any(k in c for k in ['descri', 'historico', 'histór', 'detalhe'])), 1)
        idx_valor = next((i for i, c in enumerate(cabecalho) if 'valor' in c), 2)

        val_raw = linha[idx_valor].strip() if idx_valor < len(linha) else ""
        if not val_raw:
            return None

        data_raw = linha[idx_data].strip() if idx_data < len(linha) else ""
        descricao = linha[idx_desc].strip() if idx_desc < len(linha) else "Importado Santander"

        val_limpo = val_raw.replace('R$', '').replace('\xa0', '').strip()
        val_limpo = re.sub(r'\s+', '', val_limpo)

        tipo_final = 'DESPESA' if '-' in val_limpo else 'RECEITA'

        return data_raw, val_limpo, descricao, tipo_final

class CsvExtratoParser:
    """Orquestrador que direciona o arquivo para o parser do banco correto."""

    # Mapeamento dos parsers por chave do banco
    PARSERS = {
        'picpay': PicPayParser,
        'nubank': NubankParser,
        'bradesco': BradescoParser,
        'itau': ItauParser,
        'santander': SantanderParser,
    }

    @staticmethod
    def parse(arquivo, banco='picpay'):
        try:
            conteudo = arquivo.read().decode('utf-8')
        except UnicodeDecodeError:
            arquivo.seek(0)
            conteudo = arquivo.read().decode('latin-1')

        delimitador = ';' if ';' in conteudo else ','
        stream = io.StringIO(conteudo)
        leitor = list(csv.reader(stream, delimiter=delimitador))

        if not leitor:
            return []

        cabecalho = [col.strip().lower() for col in leitor[0]]
        
        # Seleciona a classe do banco ou usa o PicPay como fallback genérico
        parser_classe = CsvExtratoParser.PARSERS.get(str(banco).lower(), PicPayParser)

        transacoes = []

        for linha in leitor[1:]:
            if not linha or len(linha) < 2:
                continue

            # Processa a linha com base na regra específica do banco
            dados = parser_classe.parse_linha(linha, cabecalho)
            if not dados:
                continue

            data_raw, val_limpo, descricao, tipo_final = dados

            # Conversão genérica de número (PT-BR)
            val_num_str = val_limpo.replace('\u2212', '-').replace('-', '').replace('(', '').replace(')', '')
            if ',' in val_num_str:
                val_num_str = val_num_str.replace('.', '').replace(',', '.')

            try:
                valor_float = abs(float(val_num_str))
            except ValueError:
                continue

            if valor_float == 0:
                continue

            # Tratamento da Data
            data_str = date.today().strftime('%Y-%m-%d')
            if data_raw and '/' in data_raw:
                partes = data_raw.split('/')
                if len(partes) == 3:
                    data_str = f"{partes[2]}-{partes[1].zfill(2)}-{partes[0].zfill(2)}"
            elif data_raw and '-' in data_raw:
                data_str = data_raw  # Já está em YYYY-MM-DD

            transacoes.append({
                'descricao': descricao[:100],
                'valor': valor_float,
                'tipo': tipo_final,
                'categoria': categorizar_transacao(descricao),
                'data': data_str,
            })

        return transacoes