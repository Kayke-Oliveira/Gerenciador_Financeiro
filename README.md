# Gerenciador Financeiro

Sistema web para gerenciamento de financas pessoais, construido com Django e deployado no Render.com com Supabase PostgreSQL.

**Autor:** Kayke-Oliveira  
**Producao:** [https://gerenciador-financeiro-13lx.onrender.com](https://gerenciador-financeiro-13lx.onrender.com)  
**Repositorio:** [https://github.com/Kayke-Oliveira/Gerenciador_Financeiro](https://github.com/Kayke-Oliveira/Gerenciador_Financeiro)

---

## Funcionalidades

- Dashboard com resumo financeiro mensal e graficos interativos (Chart.js)
- CRUD de transacoes com filtros por mes/ano e categorias
- Importacao de extratos bancarios (OFX e CSV) com suporte a multiplos bancos
- Gerenciamento de orcamentos mensais
- Metas financeiras com diagnostico preditivo (Neutro, Critico, Excelente, Proximo, Longe)
- Contas a pagar e a receber com baixa manual e criacao automatica de transacoes
- Exportacao de relatorios em PDF
- Deletar conta com confirmacao de senha
- Layout responsivo com sidebar colapsavel em mobile
- Toast notifications para feedback nao intrusivo

## Stack

| Componente | Versao |
|------------|--------|
| Python | 3.12+ |
| Django | 6.0.7 |
| Django REST Framework | 3.18.0 |
| pandas | 2.2.3 |
| ofxparse | 0.2.1 |
| psycopg2-binary | 2.9.9 |
| dj-database-url | 3.1.2 |
| whitenoise | 6.8.2 |
| gunicorn | 23.0.0 |
| Tailwind CSS | CDN |
| Lucide Icons | CDN |
| Chart.js | CDN |

## Infraestrutura

- **Hospedagem:** Render.com (plano free)
- **Banco de dados:** Supabase PostgreSQL (pooler IPv4, SSL)
- **Arquivos estaticos:** Whitenoise (CompressedManifestStaticFilesStorage)
- **CI/CD:** Deploy automatico via GitHub (push na branch `main`)

## Seguranca

- Content Security Policy (CSP) via Django 6.0 built-in middleware
- HSTS (1 ano), SSL redirect, cookies seguros (Secure + HttpOnly)
- Headers de seguranca: X-Frame-Options DENY, X-Content-Type-Options nosniff, XSS filter
- Rate limiting: 30 req/h (anonimo), 200 req/h (autenticado)
- Logout requer POST (previne CSRF logout via GET)
- Upload de extratos: validacao de extensao (.ofx/.csv), tamanho maximo (5MB), nome sanitizado
- Protecao XSS: escape em todo innerHTML dinamico (funcao `escapeHtml()`)
- JavaScript extraido para arquivo estatico (`core/static/core/js/app.js`), sem inline JS
- SECRET_KEY via variavel de ambiente (raise ValueError se ausente)
- Credenciais de deploy nunca commitadas (em `.gitignore`)

## Como Rodar Localmente

```bash
# 1. Clonar o repositorio
git clone https://github.com/Kayke-Oliveira/Gerenciador_Financeiro.git
cd Gerenciador_Financeiro

# 2. Criar e ativar ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variaveis de ambiente (criar arquivo .env)
# DJANGO_SECRET_KEY=sua_chave_secreta_aqui
# DATABASE_URL=postgres://...
# DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
# DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1
# DJANGO_DEBUG=True

# 5. Rodar migracoes
python manage.py migrate

# 6. Criar superusuario
python manage.py createsuperuser

# 7. Iniciar servidor
python manage.py runserver
```

## Estrutura do Projeto

```
gerenciador_financeiro/
|-- setup/                  # Configuracoes Django (settings, urls, wsgi)
|-- core/                   # App principal
|   |-- models.py           # Modelos de dados
|   |-- views.py            # Views (Web + API REST)
|   |-- serializers.py      # Serializers DRF
|   |-- urls.py             # Rotas do app
|   |-- templates/core/     # Templates HTML
|   |-- static/core/        # CSS e JavaScript
|   |-- parsers/            # Parsers de extratos (OFX, CSV)
|   |-- services/           # Logica de negocios
|-- requirements.txt        # Dependencias versionadas
|-- render.yaml             # Configuracao de deploy
```

## Documentacao

- [DOCUMENTACAO.md](DOCUMENTACAO.md) — Documentacao completa do projeto
- [MANUAL_ERROS_CORRECOES.md](MANUAL_ERROS_CORRECOES.md) — Historico de bugs e correcoes
