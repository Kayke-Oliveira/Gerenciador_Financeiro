from django.db import models
import uuid
from django.contrib.auth.models import User

class Transacao(models.Model):
    #Opções fixas de movimentação
    TIPO_CHOICES=[
        ('RECEITA', 'Receita (Entrada)'),
        ('DESPESA', 'Despesa (Saída)'),
    ]

    #Campos da tabela do banco de dados
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transacoes')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=10, decimal_places=2) #Aceita até 99.999.999,99
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    pago = models.BooleanField(default=False)
    data = models.DateField()
    categoria = models.CharField(max_length=100, default='Geral')
    criado_em = models.DateTimeField(auto_now_add=True) #Salva a data/hora do cadastro automaticamente

    def __str__(self):
        return f'{self.tipo} - {self.descricao} - R$ {self.valor}'
    
class OrcamentoMensal(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orcamento')
    
    renda_mensal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Renda Cadastrada: R${self.renda_mensal}'
