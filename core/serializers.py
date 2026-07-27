from rest_framework import serializers #serializers é o componente que traduz o json para a linguagem do django
from .models import Transacao, OrcamentoMensal

class TransacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transacao
        #Aqui é definido quais campos do Model ficam vísiveis na API
        fields = '__all__'

class OrcamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrcamentoMensal
        fields = '__all__'