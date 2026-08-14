from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import Transacao, ArquivoImportado


class TesteNovasFuncionalidades(TestCase):
    def setUp(self):
        self.client = Client()
        self.usuario = self._criar_usuario()

    def _criar_usuario(self):
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='teste', password='senha123')
        self.client.login(username='teste', password='senha123')
        return user

    def _csv(self):
        conteudo = (
            'data,hora,tipo,"origem / destino",valor,"forma de pagamento"\n'
            '2026-08-11,20:54,"Pix recebido","EMPRESA TESTE LTDA.","+R$ 10,00",\n'
            '2026-08-07,20:18,"Pix enviado","UBER DO BRASIL TECNOLOGIA LTDA.","\u2212R$ 5,00","Com saldo"\n'
        ).encode('utf-8')
        return SimpleUploadedFile('extrato.csv', conteudo, content_type='text/csv')

    def test_fluxo_completo(self):
        # 1. Primeiro upload -> sucesso
        resp1 = self.client.post('/api/importar-extrato/', {
            'extrato': self._csv(), 'banco': 'picpay'
        })
        self.assertEqual(resp1.status_code, 200, resp1.content)
        self.assertEqual(Transacao.objects.filter(usuario=self.usuario).count(), 2)
        self.assertTrue(ArquivoImportado.objects.filter(usuario=self.usuario).exists())

        # 2. Mesmo arquivo de novo -> 409 com flag ja_importado
        resp2 = self.client.post('/api/importar-extrato/', {
            'extrato': self._csv(), 'banco': 'picpay'
        })
        self.assertEqual(resp2.status_code, 409)
        self.assertTrue(resp2.json()['ja_importado'])

        # 3. Confirmando (confirmar=true) -> prossegue e salva
        resp3 = self.client.post('/api/importar-extrato/', {
            'extrato': self._csv(), 'banco': 'picpay', 'confirmar': 'true'
        })
        self.assertEqual(resp3.status_code, 200, resp3.content)
        self.assertEqual(Transacao.objects.filter(usuario=self.usuario).count(), 4)

        # 4. Sem arquivo -> 400
        resp4 = self.client.post('/api/importar-extrato/', {'banco': 'picpay'})
        self.assertEqual(resp4.status_code, 400)

        # 5. Deletar todas -> limpa transações do usuário
        resp5 = self.client.delete('/api/transacoes/limpar_todas/')
        self.assertEqual(resp5.status_code, 200, resp5.content)
        self.assertEqual(Transacao.objects.filter(usuario=self.usuario).count(), 0)

    def test_limpar_todas_nao_afeta_outros_usuarios(self):
        from django.contrib.auth.models import User
        outro = User.objects.create_user(username='outro', password='senha123')
        Transacao.objects.create(
            usuario=outro, descricao='x', valor=1, tipo='RECEITA',
            data='2026-08-01', categoria='Outros'
        )
        self.client.delete('/api/transacoes/limpar_todas/')
        self.assertEqual(Transacao.objects.filter(usuario=outro).count(), 1)
