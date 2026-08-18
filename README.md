# Gerenciador de Financas Pessoais

Uma aplicacao web completa para controle financeiro pessoal, desenvolvida com **Django** e **Django REST Framework** no backend, integrada a uma interface minimalista e responsiva estilizada com **Tailwind CSS**.

O sistema permite que o usuario registre sua renda mensal para obter um planejamento automatico de distribuicao do orcamento (investimentos, reserva de emergencia, contas fixas e lazer), alem de registrar e acompanhar suas entradas e saidas em tempo real.

---

## Funcionalidades

- **Onboarding:** Modal inicial para definicao do salario mensal.
- **Planejamento Recomendado:** Calculo automatico de metas baseado no salario:
  - Meta de Renda Passiva (200x o salario)
  - Reserva de Emergencia (6x o salario)
  - Divisao ideal: 10% Investimento, 60% Contas Fixas e 30% Lazer.
- **Resumo Financeiro em Tempo Real:** Cards com totalizadores de Entradas, Saidas e Saldo Atual.
- **Graficos Interativos:** Grafico de rosca (entradas vs. saidas) e grafico de barras horizontais (despesas por categoria) via Chart.js.
- **Lancamento de Movimentacoes:** Cadastro rapido de receitas e despesas com categorias.
- **Historico de Transacoes:** Listagem de registros com edicao, exclusao e filtro por mes/ano.
- **Metas Financeiras:** Criacao, edicao e exclusao de metas com acompanhamento de progresso e diagnostico preditivo (badge colorido por status).
- **Importacao de Extratos:** Suporte a OFX e CSV (PicPay, Nubank, Itau, Bradesco, Santander) com deduplicacao automatica.
- **Autenticacao:** Sistema completo de cadastro, login e logout com isolamento de dados por perfil.
- **Toast Notifications:** Notificacoes visuais para feedback do usuario.
- **Confirmacao Customizada:** Modal de confirmacao para acoes destrutivas.

---

## Stack Tecnologica

- **Backend:** Python, Django, Django REST Framework (DRF)
- **Frontend:** HTML5, JavaScript (Fetch API), Tailwind CSS (CDN)
- **Graficos:** Chart.js (CDN)
- **Banco de Dados:** SQLite (Desenvolvimento)
- **Processamento de Dados:** Pandas (agregacao para graficos)
- **Leitura de Extratos:** ofxparse (OFX), parsers customizados (CSV)

---

## Como Executar o Projeto Localmente

### Pre-requisitos
- Python 3.10+ instalado
- Git instalado

### Passo a Passo

1. **Clone o repositorio:**
   ```bash
   git clone https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git
   cd SEU-REPOSITORIO
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Instale as dependencias:**
   ```bash
   pip install django djangorestframework pandas ofxparse
   ```

4. **Execute as migracoes do banco de dados:**
   ```bash
   python manage.py migrate
   ```

5. **Inicie o servidor de desenvolvimento:**
   ```bash
   python manage.py runserver
   ```

6. Acesse a aplicacao em `http://127.0.0.1:8000/` no seu navegador.

---

## Estrutura do Projeto

```
gerenciador_financeiro/
├── manage.py
├── setup/                     # Configuracao do Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py / asgi.py
│
└── core/                      # Aplicacao principal
    ├── models.py              # Modelos (Transacao, OrcamentoMensal, MetaFinanceira, ArquivoImportado)
    ├── views.py               # Views Web + API Views
    ├── serializers.py         # Serializadores REST
    ├── urls.py                # Rotas da aplicacao
    ├── services/              # Camada de servicos
    │   ├── dashboard_service.py
    │   ├── planejamento_service.py
    │   └── extrato_service.py
    ├── parsers/               # Parsers de importacao
    │   ├── csv_parser.py
    │   ├── ofx_parser.py
    │   └── categorizador.py
    └── templates/core/
        ├── index.html         # Dashboard principal (SPA)
        ├── login.html
        └── register.html
```

---

## Licenca

Este projeto esta sob a licenca MIT. Veja o arquivo `LICENSE` para mais detalhes.
