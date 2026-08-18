from django.db import models
import uuid
from django.contrib.auth.models import User


class Transacao(models.Model):
    # Opções fixas de categoria de gasto
    CATEGORIA_CHOICES = [
        ('Alimentação', 'Alimentação'),
        ('Moradia', 'Moradia'),
        ('Transporte', 'Transporte'),
        ('Lazer', 'Lazer'),
        ('Saúde', 'Saúde'),
        ('Educação', 'Educação'),
        ('Compras', 'Compras'),
        ('Salário', 'Salário'),
        ('Investimentos', 'Investimentos'),
        ('Outros', 'Outros'),
    ]
    # Opções fixas de movimentação
    TIPO_CHOICES = [
        ('RECEITA', 'Receita (Entrada)'),
        ('DESPESA', 'Despesa (Saída)'),
    ]

    # Campos da tabela do banco de dados
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transacoes')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    descricao = models.CharField(max_length=255)
    # Aceita até 99.999.999,99
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    data = models.DateField()
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, default='Outros')
    # Salva a data/hora do cadastro automaticamente
    criado_em = models.DateTimeField(auto_now_add=True)

    #Esse campo evita duplicatas de OFX
    transacao_id_externo = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        unique=True,
        help_text="ID único da transação importada via OFX (FITID)"
    )

    def __str__(self):
        return f'{self.tipo} - {self.descricao} - R$ {self.valor}'


class OrcamentoMensal(models.Model):
    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='orcamento')

    renda_mensal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Renda Cadastrada: R${self.renda_mensal}'


class ArquivoImportado(models.Model):
    """Registra o hash do conteúdo de cada extrato importado para detectar
    tentativas de upload repetido do mesmo arquivo."""
    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='arquivos_importados')

    hash_arquivo = models.CharField(max_length=64)
    nome_arquivo = models.CharField(max_length=255)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'hash_arquivo')

    def __str__(self):
        return f'{self.nome_arquivo} - {self.criado_em:%d/%m/%Y %H:%M}'

class MetaFinanceira(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='metas')
    titulo = models.CharField(max_length=100)
    valor_objetivo = models.DecimalField(max_digits=10, decimal_places=2)
    valor_atual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    aporte_mensal_desejado = models.DecimalField(max_digits=10, decimal_places=2)
    prazo_meses = models.IntegerField()
    data_criacao = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f'{self.titulo} - {self.usuario.username}'

    @property
    def progresso_percentual(self):
        if self.valor_objetivo > 0:
            return round((self.valor_atual / self.valor_objetivo) * 100, 1)
        return 0


class ContaPagar(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contas_pagar')
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    data_vencimento = models.DateField()
    categoria = models.CharField(max_length=50, choices=Transacao.CATEGORIA_CHOICES, default='Outros')
    paga = models.BooleanField(default=False)
    recorrente = models.BooleanField(default=False)
    transacao_gerada = models.OneToOneField(
        'Transacao',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='conta_origem'
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data_vencimento']

    def __str__(self):
        status = 'Paga' if self.paga else 'Pendente'
        return f'{self.descricao} - R$ {self.valor} ({status})'
