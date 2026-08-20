# Documentacao Oficial do Projeto

**Gerenciador Financeiro** — Sistema web para gerenciamento de financas pessoais.

**Autor:** Kayke-Oliveira  
**GitHub:** [https://github.com/Kayke-Oliveira/Gerenciador_Financeiro](https://github.com/Kayke-Oliveira/Gerenciador_Financeiro)  
**URL Producao:** [https://gerenciador-financeiro-13lx.onrender.com](https://gerenciador-financeiro-13lx.onrender.com)

---

## 1. Sumario

1. [Visao Geral](#2-visao-geral)
2. [Arquitetura do Sistema](#3-arquitetura-do-sistema)
3. [Stack Tecnologica](#4-stack-tecnologica)
4. [Estrutura de Diretorios](#5-estrutura-de-diretorios)
5. [Models](#6-models)
6. [Funcionalidades](#7-funcionalidades)
7. [Endpoints da API REST](#8-endpoints-da-api-rest)
8. [Templates e Frontend](#9-templates-e-frontend)
9. [Deploy (Render + Supabase)](#10-deploy-render--supabase)
10. [Variaveis de Ambiente](#11-variaveis-de-ambiente)
11. [Seguranca](#12-seguranca)
12. [Servicos e Parsers](#13-servicos-e-parsers)
13. [Historico de Commits](#14-historico-de-commits)

---

## 2. Visao Geral

Aplicacao web Django para gerenciamento financeiro pessoal. Permite cadastrar transacoes manualmente, importar extratos bancarios (OFX e CSV), gerenciar orcamentos mensais, definir metas financeiras com diagnostico preditivo, e controlar contas a pagar e a receber. Interface responsiva com sidebar lateral, layout SaaS, graficos interativos e exportacao de relatorios em PDF.

---

## 3. Arquitetura do Sistema

```
Requisicao HTTP
     |
     v
    URLs  ─────────────────────────────────────────────────────────────────
     |  (core/urls.py)                                                       |
     |                                                                       |
     v                                                                       v
   Views (core/views.py)                                                 Router REST
     |                                                                       |
     |--- View Web (HTML) --- Template (index.html) <-- Contexto              |
     |                                                                       |
     |--- API REST (ViewSets) --- Serializer --- Model --- Banco (Supabase)  |
     |                                                                       |
     |--- Servicos --- Parsers                                               |
         (dashboard_service)   (ofx_parser, csv_parser)                       |
         (extrato_service)                                                      |
         (planejamento_service)                                                  |
     |                                                                       |
     v                                                                       v
   Template (index.html) <--- Dados via JS (app.js) <--- Fetch API <--- API REST
```

---

## 4. Stack Tecnologica

### Backend

| Componente | Versao / Detalhes |
|------------|-------------------|
| **Python** | 3.12+ |
| **Django** | 6.0.7 |
| **Django REST Framework** | 3.18.0 |
| **dj-database-url** | 3.1.2 |
| **psycopg2-binary** | 2.9.9 |
| **pandas** | 2.2.3 |
| **ofxparse** | 0.2.1 |
| **gunicorn** | 23.0.0 |

### Frontend

| Componente | Detalhes |
|------------|----------|
| **Tailwind CSS** | CDN (via `cdn.tailwindcss.com`) |
| **Lucide Icons** | CDN (via `unpkg.com/lucide`) |
| **Chart.js** | CDN (via `cdn.jsdelivr.net`) |
| **JavaScript vanilla** | Arquivo estatico `core/static/core/js/app.js` (sem framework, sem inline JS) |

### Infraestrutura

| Componente | Detalhes |
|------------|----------|
| **Hospedagem** | Render.com (plano free) |
| **Banco de dados** | Supabase PostgreSQL (pooler IPv4) |
| **Arquivos estaticos** | Whitenoise 6.8.2 (CompressedManifestStaticFilesStorage) |
| **Servidor WSGI** | Gunicorn 23.0.0 |

---

## 5. Estrutura de Diretorios

```
gerenciador_financeiro/
|
|-- setup/                            # Configuracoes do projeto Django
|   |-- settings.py                   # Configuracoes centrais
|   |-- urls.py                       # URLs raiz (admin + core)
|   |-- asgi.py
|   |-- wsgi.py
|
|-- core/                             # App principal
|   |-- models.py                     # Modelos de dados
|   |-- views.py                      # Views (Web + API REST)
|   |-- serializers.py                # Serializers REST
|   |-- urls.py                       # URLs do app (rotas + API)
|   |-- admin.py                      # Registro no Django Admin
|   |-- apps.py
|   |
|   |-- templates/core/
|   |   |-- index.html                # Template principal (SPA com sidebar)
|   |   |-- login.html                # Pagina de login
|   |   |-- register.html             # Pagina de registro
|   |
|   |-- static/core/
|   |   |-- css/
|   |   |   |-- style.css             # CSS customizado
|   |   |-- js/
|   |       |-- app.js                # JavaScript extraido (~730 linhas)
|   |
|   |-- parsers/
|   |   |-- base_parser.py
|   |   |-- ofx_parser.py
|   |   |-- csv_parser.py
|   |
|   |-- services/
|       |-- dashboard_service.py
|       |-- extrato_service.py
|       |-- planejamento_service.py
|
|-- staticfiles/                      # Arquivos estaticos copiados (collectstatic)
|-- manage.py
|-- requirements.txt                  # Dependencias (todas versionadas)
|-- render.yaml                       # Configuracao de deploy no Render
|-- .gitignore
|-- CREDENCIAIS_DEPLOY.md             # Credenciais (em .gitignore, nunca commitado)
|-- DOCUMENTACAO.md                   # Este arquivo
|-- MANUAL_ERROS_CORRECOES.md         # Historico de bugs e correcoes
|-- README.md                         # Leitura do repositorio
|-- design.md                         # Documentacao de design/UX
|-- novafeat.md                       # Especificacao: Contas a Pagar
|-- refatorar.md                      # Plano de refatoracao
|-- correcaoProblema.md               # Descricao do bug de importacao PicPay
|-- Exigencias.md                     # Requisitos de UX (toast, transicoes)
```

---

## 6. Models

Todos os models tem `ForeignKey` para `User` com `on_delete=models.CASCADE`, garantindo exclusao em cascata.

### Transacao

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `usuario` | FK -> User | Dono da transacao |
| `id` | UUID (PK) | Identificador unico |
| `descricao` | CharField(255) | Descricao da transacao |
| `valor` | DecimalField(10,2) | Valor (ate 99.999.999,99) |
| `tipo` | CharField(10) | `RECEITA` ou `DESPESA` |
| `data` | DateField | Data da transacao |
| `categoria` | CharField(50) | 10 categorias fixas |
| `criado_em` | DateTimeField | Auto preenchido |
| `transacao_id_externo` | CharField(255) | ID externo OFX (unique, previne duplicatas) |

### OrcamentoMensal

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `usuario` | FK -> User | Dono do orcamento |
| `renda_mensal` | DecimalField(10,2) | Renda mensal declarada |
| `criado_em` | DateTimeField | Auto preenchido |

### ArquivoImportado

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `usuario` | FK -> User | Dono do arquivo |
| `hash_arquivo` | CharField(64) | Hash SHA-256 do conteudo |
| `nome_arquivo` | CharField(255) | Nome sanitizado |
| `criado_em` | DateTimeField | Auto preenchido |
| `unique_together` | (usuario, hash_arquivo) | Previne upload duplicado |

### MetaFinanceira

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `usuario` | FK -> User | Dono da meta |
| `titulo` | CharField(100) | Nome da meta |
| `valor_objetivo` | DecimalField(10,2) | Valor alvo |
| `valor_atual` | DecimalField(10,2) | Valor acumulado |
| `aporte_mensal_desejado` | DecimalField(10,2) | Aporte mensal necessario |
| `prazo_meses` | IntegerField | Prazo em meses |
| `progresso_percentual` | @property | Calcula percentual atingido |

### ContaPagar

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `usuario` | FK -> User | Dono da conta |
| `descricao` | CharField(255) | Descricao |
| `valor` | DecimalField(15,2) | Valor |
| `data_vencimento` | DateField | Data de vencimento |
| `categoria` | CharField(50) | Mesmas 10 categorias de Transacao |
| `paga` | BooleanField | Status de pagamento |
| `recorrente` | BooleanField | Se repete mensalmente |
| `transacao_gerada` | OneToOne -> Transacao | Transacao criada ao dar baixa |

### ContaReceber

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `usuario` | FK -> User | Dono da conta |
| `descricao` | CharField(255) | Descricao |
| `valor` | DecimalField(15,2) | Valor |
| `data_recebimento` | DateField | Data de recebimento |
| `categoria` | CharField(50) | Mesmas 10 categorias de Transacao |
| `recebida` | BooleanField | Status de recebimento |
| `recorrente` | BooleanField | Se repete mensalmente |
| `transacao_gerada` | OneToOne -> Transacao | Transacao criada ao dar baixa |

---

## 7. Funcionalidades

- **Dashboard**: resumo mensal, saldo, receitas, despesas, saldo planejado
- **Graficos interativos**: rosca (despesas por categoria) e barras (receita vs despesa) via Chart.js
- **CRUD de Transacoes**: criar, editar, excluir, filtrar por mes/ano/categoria
- **CRUD de Orcamentos**: definir renda mensal para planejamento
- **CRUD de Metas Financeiras**: definir objetivos com diagnostico preditivo (Neutro, Critico, Excelente, Proximo, Longe)
- **Importacao de Extratos**: upload de OFX e CSV com parsers dedicados por banco (PicPay, Itau, Bradesco, Banco do Brasil, Santander, Nubank, Inter, C6, PagBank, Mercado Pago, Genérico)
- **Contas a Pagar**: gerenciar compromissos futuros com baixa manual (cria Transacao automaticamente)
- **Contas a Receber**: gerenciar recebimentos futuros com baixa manual (cria Transacao automaticamente)
- **Exportacao PDF**: gerar relatorio consolidado
- **Deletar Conta**: exclusao permanente da conta com confirmacao de senha
- **Layout responsivo**: sidebar colapsavel em mobile com hamburger menu
- **Toast notifications**: sistema de notificacoes nao intrusivo
- **Transicoes entre abas**: fade-in animado com preservacao de estado via URL

---

## 8. Endpoints da API REST

### Rotas do Router DRF

| Metodo | URL | Descricao |
|--------|-----|-----------|
| GET/POST | `/api/transacoes/` | Listar / Criar transacoes |
| GET/PUT/PATCH/DELETE | `/api/transacoes/{id}/` | Detalhes / Editar / Excluir transacao |
| DELETE | `/api/transacoes/limpar_todas/` | Excluir todas as transacoes do usuario |
| GET/POST | `/api/orcamento/` | Listar / Criar orcamentos |
| GET/POST | `/api/metas/` | Listar / Criar metas financeiras |
| GET/PUT/PATCH/DELETE | `/api/metas/{id}/` | Detalhes / Editar / Excluir meta |
| GET/POST | `/api/contas-pagar/` | Listar / Criar contas a pagar |
| GET/PUT/PATCH/DELETE | `/api/contas-pagar/{id}/` | Detalhes / Editar / Excluir conta |
| POST | `/api/contas-pagar/{id}/dar_baixa/` | Marcar como paga e criar transacao |
| GET/POST | `/api/contas-receber/` | Listar / Criar contas a receber |
| GET/PUT/PATCH/DELETE | `/api/contas-receber/{id}/` | Detalhes / Editar / Excluir conta |
| POST | `/api/contas-receber/{id}/dar_baixa/` | Marcar como recebida e criar transacao |

### Outros Endpoints

| Metodo | URL | Descricao |
|--------|-----|-----------|
| GET | `/api/graficos-dados/` | Dados para graficos Chart.js (?mes=X&ano=Y) |
| POST | `/api/importar-extrato/` | Upload de extrato OFX/CSV |
| POST | `/api/deletar-conta/` | Excluir conta do usuario (requer senha) |

### Paginas Web

| Metodo | URL | Descricao |
|--------|-----|-----------|
| GET | `/` | Dashboard principal |
| GET | `/login/` | Pagina de login |
| POST | `/login/` | Autenticar usuario |
| GET | `/register/` | Pagina de registro |
| POST | `/register/` | Criar novo usuario |
| POST | `/logout/` | Encerrar sessao (requer POST) |

---

## 9. Templates e Frontend

### Arquitetura SPA com Sidebar

O `index.html` funciona como uma Single Page Application com navegacao por abas:
- **Sidebar lateral** (`<aside>`) com menu de navegacao
- **Conteudo principal** (`<main>`) com abas ocultas/exibidas via JavaScript
- **JS extraido** para `core/static/core/js/app.js` (~730 linhas, sem inline JS)
- **Lucide Icons** para iconografia (sem emojis Unicode)
- **Tailwind CSS** via CDN para estilizacao
- **Chart.js** para graficos de rosca e barras

### Templates

| Template | Descricao |
|----------|-----------|
| `index.html` | Dashboard principal, todas as abas (Dashboard, Transacoes, Planejamento, Metas, Contas a Pagar, Contas a Receber) |
| `login.html` | Formulario de login |
| `register.html` | Formulario de registro |

---

## 10. Deploy (Render + Supabase)

### Configuracao do Render (`render.yaml`)

```yaml
services:
  - type: web
    name: gerenciador-financeiro
    runtime: python
    buildCommand: pip install -r requirements.txt && python manage.py collectstatic --noinput
    startCommand: gunicorn setup.wsgi:application
    plan: free
```

### Supabase PostgreSQL

- **Host**: `aws-0-us-west-2.pooler.supabase.com` (pooler, IPv4)
- **Porta**: `6543`
- **SSL**: `ssl_require=True` (obrigatorio)
- **Conn Max Age**: 600 segundos
- **Conn Health Checks**: Ativado

### Credenciais

Todas as credenciais estao em `CREDENCIAIS_DEPLOY.md` (em `.gitignore`, nunca commitado).

---

## 11. Variaveis de Ambiente

| Variavel | Obrigatorio | Descricao |
|----------|-------------|-----------|
| `DJANGO_SECRET_KEY` | **Sim** | Chave secreta do Django (raise ValueError se ausente) |
| `DATABASE_URL` | **Sim** | URL de conexao com Supabase PostgreSQL |
| `DJANGO_ALLOWED_HOSTS` | Sim | Hosts permitidos (default: `localhost,127.0.0.1`) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Sim | Origens confiaveis CSRF (default: `http://localhost,http://127.0.0.1`) |
| `DJANGO_DEBUG` | Nao | Modo debug (default: `False`) |

> **Nota:** `DEBUG = True` so e permitido em ambiente local. Em producao (Render), `DEBUG=False` e obrigatorio.

---

## 12. Seguranca

### Headers HTTP (Django 6.0 built-in)

| Header | Valor |
|--------|-------|
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Cross-Origin-Opener-Policy` | `same-origin` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` |

### Content Security Policy (CSP)

Configurado via `django.middleware.csp.ContentSecurityPolicyMiddleware` (Django 6.0):

| Diretiva | Dominios Permitidos |
|----------|---------------------|
| `default-src` | `'self'` |
| `script-src` | `'self'`, `cdn.tailwindcss.com`, `cdn.jsdelivr.net`, `unpkg.com` |
| `style-src` | `'self'`, `cdn.tailwindcss.com`, `cdn.jsdelivr.net`, `unpkg.com`, `'unsafe-inline'` |
| `img-src` | `'self'`, `data:` |
| `font-src` | `'self'`, `fonts.gstatic.com`, `cdn.jsdelivr.net` |
| `connect-src` | `'self'` |
| `frame-src` | `'none'` |
| `object-src` | `'none'` |

> **Nota:** `'unsafe-inline'` em `style-src` e necessario para o Tailwind CDN (`<style>` blocks). O `script-src` NAO usa `'unsafe-inline'` — todo JS esta no arquivo estatico `app.js`.

### HTTPS / HSTS

- `SECURE_SSL_REDIRECT`: ativo em producao
- `SECURE_HSTS_SECONDS`: 31536000 (1 ano)
- `SECURE_HSTS_INCLUDE_SUBDOMAINS`: True
- `SECURE_HSTS_PRELOAD`: True

### Cookies

| Cookie | Configuracao |
|--------|--------------|
| `SESSION_COOKIE_SECURE` | True (producao) |
| `SESSION_COOKIE_HTTPONLY` | True |
| `CSRF_COOKIE_SECURE` | True (producao) |
| `CSRF_COOKIE_HTTPONLY` | True |

### Rate Limiting (DRF Throttling)

| Classe | Limite |
|--------|--------|
| `AnonRateThrottle` | 30 requisicoes/hora |
| `UserRateThrottle` | 200 requisicoes/hora |

### Protecao de Views

- **Logout**: requer `POST` (`@require_POST`) — previne CSRF logout via GET
- **Importar Extrato**: requer `POST`, valida extensao (.ofx/.csv), valida tamanho (5MB), sanitiza nome do arquivo com `os.path.basename()`, calcula hash SHA-256 para detectar duplicatas
- **Deletar Conta**: requer `POST`, valida senha antes de excluir, registra log com `logging.warning()`

### XSS Prevention

- Todas as saidas dinamicas usam funcao `escapeHtml()` antes de injetar no DOM via `innerHTML`
- Toasts sanitizados com `escapeHtml()`
- Mensagens de erro sanitizadas no backend

### Upload

- Limite de tamanho: 5 MB (`DATA_UPLOAD_MAX_MEMORY_SIZE` e `FILE_UPLOAD_MAX_MEMORY_SIZE`)
- Extensao validada no backend: apenas `.ofx` e `.csv`
- Nome sanitizado com `os.path.basename()`

### Logging

Configurado em `settings.py` com handler `console` (StreamHandler) para os loggers `django` e `core` (nivel INFO).

---

## 13. Servicos e Parsers

### Servicos

| Servico | Descricao |
|---------|-----------|
| `DashboardService` | Resumo mensal, planejamento financeiro, dados para graficos |
| `ExtratoService` | Orquestrador de importacao (detecta formato e delega ao parser correto) |
| `PlanejamentoService` | Diagnostico preditivo de metas financeiras |

### Parsers

| Parser | Formato | Bancos Suportados |
|--------|---------|-------------------|
| `OfxParser` | OFX | Generico |
| `CsvExtratoParser` | CSV | Generico, detecta delimitador automaticamente |
| `PicPayParser` | CSV | PicPay |
| `ItauParser` | CSV | Itau |
| `BradescoParser` | CSV | Bradesco |
| `BancoDoBrasilParser` | CSV | Banco do Brasil |
| `SantanderParser` | CSV | Santander |
| `NubankParser` | CSV | Nubank |
| `InterParser` | CSV | Inter |
| `C6Parser` | CSV | C6 Bank |
| `PagBankParser` | CSV | PagBank |
| `MercadoPagoParser` | CSV | Mercado Pago |

---

## 14. Historico de Commits

Commits ordenados do mais recente ao mais antigo:

| Hash | Descricao |
|------|-----------|
| `90830a7` | Extract JS to static file, add CSP middleware and STATICFILES_DIRS |
| `9033596` | Harden security: pinned deps, SSRF/XSS fixes, logout POST, upload validation, security headers, throttling |
| `53400d7` | Feat: funcionalidade de deletar conta do usuario com confirmacao de senha |
| `873ebd3` | Fix: conexao IPv4 pooler Supabase e layout responsivo mobile |
| `f742860` | Chore: adiciona CREDENCIAIS_DEPLOY.md ao .gitignore |
| `9a7a08f` | Feat: configuracao de deploy para Render + Supabase (PostgreSQL) |
| `92e4f40` | Feat: contas a receber, redesign sidebar, Lucide Icons e docs atualizadas |
| `e0e0997` | Feat: contas a pagar, correcao de graficos/diagnostico de metas e atualizacao de docs |
| `ab20c0c` | Feat: metas financeiras, diagnostico preditivo, importacao CSV por banco e melhoria de UX |
| `2c3989e` | Feat: novas funcionalidades, correcoes e refatoracao da importacao de extratos |
