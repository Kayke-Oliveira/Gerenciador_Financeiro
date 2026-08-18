# Documentacao Oficial — Gerenciador de Financas Pessoais

> Documento tecnico completo do projeto. Descreve o objetivo, a stack, a estrutura de arquivos, o funcionamento de cada modulo e de cada funcionalidade.

---

## 1. Objetivo do Projeto

O **Gerenciador de Financas Pessoais** e uma aplicacao web para controle financeiro pessoal. O usuario pode:

- Cadastrar, editar e excluir movimentacoes financeiras (receitas e despesas);
- Visualizar resumos mensais (entradas, saidas e saldo);
- Acompanhar graficos de **entradas vs. saidas** e de **despesas por categoria**;
- Configurar a renda mensal e obter um **planejamento financeiro automatico** (metas de renda passiva, reserva de emergencia e divisao do orcamento);
- **Criar, editar e excluir metas financeiras** com acompanhamento de progresso;
- **Importar extratos bancarios** nos formatos **OFX** e **CSV** (com suporte a PicPay, Nubank, Itau, Bradesco e Santander), que sao convertidos automaticamente em transacoes no sistema.

Todas as informacoes sao **isoladas por usuario** (autenticacao obrigatoria).

---

## 2. Stack Tecnologica

| Camada | Tecnologia | Versao |
|---|---|---|
| Linguagem | Python | 3.14 |
| Framework Web | Django | 6.0.7 |
| API REST | Django REST Framework (DRF) | 3.17.1 |
| Processamento de dados | Pandas | 3.0.5 |
| Leitura de arquivos OFX | ofxparse | 0.21 |
| Banco de dados | SQLite (`db.sqlite3`) | — |
| Frontend | HTML5 + JavaScript (Fetch API) | — |
| Estilizacao | Tailwind CSS (via CDN) | — |
| Graficos | Chart.js (via CDN) | — |

> Obs.: nao ha `requirements.txt` no projeto. As dependencias minimas sao `django`, `djangorestframework`, `pandas` e `ofxparse`.

---

## 3. Estrutura de Arquivos

```
gerenciador_financeiro/
├── manage.py                  # Ponto de entrada dos comandos Django
├── db.sqlite3                 # Banco de dados SQLite
├── .gitignore
├── README.md                  # README original do projeto
├── DOCUMENTACAO.md            # (este arquivo)
├── MANUAL_ERROS_CORRECOES.md  # Manual de erros e correcoes
│
├── setup/                     # Pacote de configuracao do projeto
│   ├── settings.py            # Configuracoes do Django
│   ├── urls.py                # Rotas raiz (admin + core)
│   ├── asgi.py                # Servidor ASGI
│   ├── wsgi.py                # Servidor WSGI
│   └── __init__.py
│
└── core/                      # Aplicacao principal
    ├── models.py              # Modelos do banco (Transacao, OrcamentoMensal, ArquivoImportado, MetaFinanceira)
    ├── views.py               # Views Web + ViewSets/APIViews da API REST
    ├── serializers.py         # Serializadores REST (Transacao, Orcamento, Meta)
    ├── urls.py                # Rotas da aplicacao core
    ├── admin.py               # Registro no admin (vazio)
    ├── apps.py                # Config do app
    ├── tests.py               # Testes
    ├── migrations/            # Migracoes do banco (0001 a 0007)
    │
    ├── services/              # Camada de servicos (logica de negocio)
    │   ├── extrato_service.py     # Orquestra importacao OFX/CSV
    │   ├── dashboard_service.py   # Agregacao do dashboard (cards e graficos)
    │   └── planejamento_service.py# Calculo do planejamento financeiro + diagnostico de metas
    │
    ├── parsers/               # Camada de parsers (leitura de arquivos)
    │   ├── csv_parser.py      # Parsers de CSV por banco + orquestrador
    │   ├── ofx_parser.py      # Parser de arquivos OFX
    │   └── categorizador.py   # Categorizacao automatica por palavras-chave
    │
    └── templates/core/        # Templates HTML
        ├── index.html         # Dashboard principal (tudo em uma pagina)
        ├── login.html         # Tela de login
        └── register.html      # Tela de cadastro
```

---

## 4. Como Cada Arquivo Funciona

### 4.1 `manage.py`
Ponto de entrada padrao do Django. Carrega as configuracoes de `setup.settings` e executa comandos (`runserver`, `migrate`, `check`, etc.).

### 4.2 `setup/settings.py`
Configuracoes globais do projeto:
- `INSTALLED_APPS`: apps do Django + `rest_framework` + `core`.
- `REST_FRAMEWORK`: exige autenticacao em todas as views da API (`IsAuthenticated`) e desativa o HTML navegavel do DRF (retorna apenas JSON).
- `DATABASES`: SQLite (`db.sqlite3`).
- `DEBUG = True` e `SECRET_KEY` de desenvolvimento (nao usar em producao).

### 4.3 `setup/urls.py`
Rotas raiz: `admin/` e delegacao das demais rotas para `core.urls`.

### 4.4 `core/models.py`
Define as entidades do banco:

- **`Transacao`** — uma movimentacao financeira:
  - `usuario` (FK para `User`) — dono da transacao;
  - `id` (UUID, PK automatica);
  - `descricao` (`CharField(255)`);
  - `valor` (`DecimalField(10, 2)`);
  - `tipo` (`CharField` com choices `RECEITA` / `DESPESA`);
  - `data` (`DateField`);
  - `categoria` (`CharField` com choices: Alimentacao, Moradia, Transporte, Lazer, Saude, Educacao, Compras, Salario, Investimentos, Outros);
  - `criado_em` (`DateTimeField`, automatico);
  - `transacao_id_externo` (`CharField` **unica**, usado para evitar duplicatas de OFX via FITID).

- **`OrcamentoMensal`** — a renda mensal informada:
  - `usuario` (FK);
  - `renda_mensal` (`DecimalField(10, 2)`, default `0.00`);
  - `criado_em` (automatico).

- **`ArquivoImportado`** — controle de duplicatas de upload:
  - `usuario` (FK);
  - `hash_arquivo` (`CharField(64)`, SHA-256 do conteudo);
  - `nome_arquivo` (`CharField(255)`);
  - `criado_em` (automatico);
  - `unique_together = ('usuario', 'hash_arquivo')`.

- **`MetaFinanceira`** — meta financeira do usuario:
  - `usuario` (FK);
  - `titulo` (`CharField(100)`);
  - `valor_objetivo` (`DecimalField(10, 2)`);
  - `valor_atual` (`DecimalField(10, 2)`, default `0`);
  - `aporte_mensal_desejado` (`DecimalField(10, 2)`);
  - `prazo_meses` (`IntegerField`);
  - `data_criacao` (`DateTimeField`, automatico);
  - `@property progresso_percentual` — calcula `(valor_atual / valor_objetivo) * 100`.

### 4.5 `core/views.py`
Arquitetura **Thin Views**: recebe o request HTTP e delega a logica para as camadas de servico.

- **ViewSets da API REST:**
  - `TransacaoViewSet` — CRUD completo de transacoes; filtra por `usuario` logado e atribui o usuario automaticamente no `create`. Inclui action `limpar_todas` (DELETE) para excluir todas as transacoes do usuario.
  - `OrcamentoViewSet` — CRUD de orcamento; mesmo isolamento por usuario.
  - `MetaViewSet` — CRUD de metas financeiras; filtra por `usuario` logado e atribui o usuario automaticamente no `create`.
- **APIView:**
  - `GraficosDataAPIView` — retorna dados estruturados para o Chart.js (mes/ano via query string) delegando a `DashboardService.dados_graficos`.
- **Views Web (HTML):**
  - `pagina_inicial` — dashboard; filtra transacoes por usuario + mes + ano; monta cards (via `DashboardService.resumo_mensal`), planejamento (via `DashboardService.planejamento_financeiro`), lista de metas com diagnostico preditivo (`PlanejamentoService.calcular_diagnostico_meta` para cada meta) e passa tudo no contexto.
  - `register_view` / `login_view` / `logout_view` — autenticacao com `UserCreationForm` / `AuthenticationForm`.
  - `importar_extrato` (`POST`) — le `request.POST.get('banco', 'picpay')` e chama `ExtratoService.importar(arquivo, usuario, banco_selecionado=...)`, retornando JSON de sucesso/erro. Verifica duplicatas via `ArquivoImportado` (hash SHA-256).
  - `tela_planejamento` — redireciona para a pagina principal (`index`).

### 4.6 `core/serializers.py`
- `TransacaoSerializer`, `OrcamentoSerializer` e `MetaSerializer` — expoe todos os campos (`__all__`) com `usuario` como `read_only_field` (o usuario e atribuido pela view).

### 4.7 `core/urls.py`
- **Paginas:** `/`, `/login/`, `/register/`, `/logout/`.
- **API (via `DefaultRouter`):** `api/transacoes/`, `api/orcamento/`, `api/metas/`.
- **Endpoints customizados:** `api/graficos-dados/`, `api/importar-extrato/`, `api/tela-planejamento/`.

### 4.8 `core/services/` (camada de servicos)

#### `extrato_service.py`
Orquestra a leitura de extratos:

- `ExtratoService.importar(arquivo, usuario, banco_selecionado='geral')` — identifica a extensao do arquivo:
  - `.ofx` → delega a `_importar_ofx`;
  - `.csv` → delega a `_importar_csv(arquivo, usuario, banco_selecionado)`;
  - outro → lanca `FormatoNaoSuportadoError`.
- `_importar_ofx(arquivo, usuario)` — chama `OfxExtratoParser.parse`; ignora transacoes cujo `transacao_id_externo` ja exista para o usuario (anti-duplicata).
- `_importar_csv(arquivo, usuario, banco_selecionado)` — chama `CsvExtratoParser.parse(arquivo, banco=banco_selecionado)` e cria as transacoes.
- Retorna `ImportResult(criadas, ignoradas)`.

#### `dashboard_service.py`
- `resumo_mensal(transacoes)` — soma agregada de RECEITAS e DESPESAS e calcula saldo.
- `planejamento_financeiro(orcamento)` — chama o calculo de planejamento se houver renda > 0.
- `dados_graficos(usuario, mes, ano)` — usa Pandas para agrupar por tipo (rosca) e por categoria de despesa (barras).

#### `planejamento_service.py`
- `calcular_planejamento_financeiro(salario)` — retorna:
  - `meta_renda_passiva` = salario x 200;
  - `reserva_emergencia` = salario x 6;
  - `investimento_mensal` = 10%, `contas_fixas` = 60%, `lazer` = 30%.
- `PlanejamentoService.calcular_diagnostico_meta(meta_id, usuario, mes, ano)` — para uma meta especifica (chamado na view `pagina_inicial` para cada meta do usuario):
  - Calcula valor restante e aporte necessario mensal;
  - Compara sobra mensal (receitas - despesas) com o aporte necessario;
  - Retorna diagnostico preditivo com status: Neutro (sem transacoes), Critico, Excelente, Proximo ou Longe.

### 4.9 `core/parsers/` (camada de parsers)

#### `csv_parser.py`
Parsers especificos por banco + orquestrador:

| Classe | Banco | Observacoes |
|---|---|---|
| `PicPayParser` | PicPay | Usa colunas `data`, `hora`, `tipo`, `origem / destino`, `valor`, `forma de pagamento`. DESPESA se houver `-` no valor ou `pix enviado` no tipo. |
| `NubankParser` | Nubank | DESPESA se o valor tiver sinal `-`. |
| `BradescoParser` | Bradesco | Detecta colunas Debito/Credito ou valor com sinal. |
| `ItauParser` | Itau | Trata sufixo `D` (debito) e palavras como "tarifa"/"pagto". |
| `SantanderParser` | Santander | DESPESA se o valor tiver sinal `-`. |
| `CsvExtratoParser` | Orquestrador | Detecta delimitador (`;` ou `,`), encoding (utf-8 → latin-1), seleciona o parser via `PARSERS[banco]` (fallback: `PicPayParser`), normaliza valores pt-BR, datas e cria os dicionarios de transacao. |

Detalhe do orquestrador:
- Leitura com fallback de encoding (`utf-8`, em caso de erro `latin-1`);
- Delimitador detectado pelo conteudo (`;` ou `,`);
- Normalizacao do **sinal de menos Unicode (U+2212)** para hifen ASCII antes do `float()` — essencial para o CSV do PicPay;
- Conversao do numero pt-BR: `"1.250,50"` → `1250.50`;
- Datas: aceita `DD/MM/AAAA` (converte para `AAAA-MM-DD`) ou `AAAA-MM-DD` (ja pronta), senao usa a data atual;
- Pula linhas sem valor, com valor `0` ou com valor nao numerico.

#### `ofx_parser.py`
- `OfxExtratoParser.parse(arquivo)` — usa a lib `ofxparse`; `amount > 0` → RECEITA, senao DESPESA; guarda `t.id` (FITID) como `transacao_id_externo`.

#### `categorizador.py`
- `categorizar_transacao(descricao)` — mapeia palavras-chave para categorias: Transporte (uber, 99, posto...), Alimentacao (ifood, restaurante, mercado...), Moradia (aluguel, condominio, luz...), Salario (salario, rendimento, provento) e `Outros`.

### 4.10 `core/templates/core/`

#### `index.html` (pagina principal)
Pagina unica com abas (Dashboard, Lancamentos & Historico, Planejamento) e modais. JavaScript integra com a API via `fetch`:

- **Salario:** `POST /api/orcamento/` (`{renda_mensal}`);
- **Criar transacao:** `POST /api/transacoes/`;
- **Editar transacao:** `PATCH /api/transacoes/{id}/`;
- **Excluir transacao:** `DELETE /api/transacoes/{id}/`;
- **Excluir todas:** `DELETE /api/transacoes/limpar_todas/`;
- **Criar meta:** `POST /api/metas/`;
- **Editar meta:** `PATCH /api/metas/{id}/`;
- **Excluir meta:** `DELETE /api/metas/{id}/`;
- **Graficos:** `GET /api/graficos-dados/?mes=&ano=` → Chart.js (doughnut e bar);
- **Importacao:** `POST /api/importar-extrato/` com `FormData` (`extrato` + `banco`).

Recursos de UX:
- **Transicoes entre abas:** animacao CSS `fadeInUp` (0.6s) ao trocar de aba;
- **Toast notifications:** `mostrarToast(mensagem, tipo)` — substitui todos os `alert()` nativos por notificacoes visuais (sucesso em teal, erro em rose) com auto-dismiss de 4s;
- **Confirmacao customizada:** `confirmarAcao(mensagem)` — substitui todos os `confirm()` nativos por modal customizado com Promise;
- **Preservacao de aba:** a aba ativa e gravada na URL via parametro `?aba=` e restaurada no carregamento da pagina;
- **Diagnostico de metas:** cada card de meta exibe badge colorido (Neutro=azul, Critico=rose, Excelente=emerald, Proximo=amber, Longe=cinza) com tooltip nativo contendo a mensagem completa do diagnostico.

CSRF obtido via cookie `csrftoken` (fallback para o input `{% csrf_token %}`).

#### `login.html` e `register.html`
Telas simples com formularios do Django (`AuthenticationForm` / `UserCreationForm`) estilizados com Tailwind.

---

## 5. Funcionalidades e Como Funcionam

### 5.1 Autenticacao
- **Cadastro** (`/register/`): `UserCreationForm`; apos salvar, o usuario e logado automaticamente e redirecionado ao dashboard.
- **Login** (`/login/`): `AuthenticationForm`; valida credenciais e redireciona.
- **Logout** (`/logout/`): encerra a sessao.
- **Protecao:** as views web usam `@login_required` e a API usa `IsAuthenticated`.

### 5.2 Dashboard e Graficos
1. `pagina_inicial` filtra as transacoes do usuario pelo mes/ano selecionado.
2. `DashboardService.resumo_mensal` calcula Entradas, Saidas e Saldo → cards.
3. `GraficosDataAPIView` retorna dados agregados (Pandas) para:
   - **Grafico de rosca** (entradas vs. saidas);
   - **Grafico de barras horizontais** (despesas por categoria).
4. O frontend renderiza com Chart.js e recarrega ao trocar a aba/mes/ano.

### 5.3 Lancamentos e Historico
- Formulario inline para adicionar receita/despesa com categoria, descricao, valor, tipo e data atual.
- Tabela com todas as transacoes do periodo, com botoes de **editar** (modal → `PATCH`) e **excluir** (confirmacao customizada → `DELETE`).
- Botao "Excluir Todas" para limpar todas as transacoes do usuario.
- Filtro de periodo (mes/ano) via GET no formulario `formFiltroData`.

### 5.4 Planejamento Financeiro e Metas
- Modal de onboarding pergunta o salario; ao salvar (`POST /api/orcamento/`), `planejamento_service` calcula as metas.
- Aba "Planejamento Financeiro" exibe: meta de renda passiva (200x), reserva de emergencia (6x), investimento (10%), contas fixas (60%) e lazer (30%).
- **Metas Financeiras:** o usuario pode criar, editar e excluir metas com titulo, valor alvo, valor acumulado e prazo.
  - O aporte mensal e calculado automaticamente: `(valor_objetivo - valor_atual) / prazo_meses`.
  - Cada card de meta exibe barra de progresso com percentual e **badge de diagnostico preditivo** (Neutro/Critico/Excelente/Proximo/Longe) com tooltip descritivo.
  - Edicao via modal (`PATCH /api/metas/{id}/`) e exclusao via modal de confirmacao customizado (`DELETE /api/metas/{id}/`).
  - O diagnostico e calculado pela view `pagina_inicial` para cada meta, comparando a sobra mensal do usuario com o aporte necessario.

### 5.5 Importacao de Extratos (OFX/CSV)
1. Modal de importacao: seleciona arquivo `.ofx`/`.csv` e o **banco** (Padrao/Outros, PicPay, Nubank, Itau, Bradesco, Santander).
2. O JavaScript envia via `FormData`: `extrato` (arquivo) e `banco` (valor do select).
3. `importar_extrato` (view) repassa o `banco` para `ExtratoService.importar`.
4. O servico roteia para o parser correto; as transacoes normalizadas sao salvas.
5. OFX usa `transacao_id_externo` (FITID) para **evitar duplicatas**. CSV nao possui ID externo.
6. A view verifica duplicatas de upload via hash SHA-256 do conteudo (`ArquivoImportado`). Se o arquivo ja foi importado, retorna 409 com flag `ja_importado`.

> **Importante:** no CSV, o "Padrao / Outros Bancos" (`generico`/`geral`) cai no **PicPayParser como fallback** do `CsvExtratoParser`.

### 5.6 Notificacoes e Confirmacoes
- **Toast notifications:** funcao global `mostrarToast(mensagem, tipo)` renderiza cards no canto superior direito com animacao de entrada/saida. Suporta tipos `sucesso` (teal) e `erro` (rose). Auto-remove apos 4 segundos ou pelo botao de fechar.
- **Confirmacao customizada:** funcao `confirmarAcao(mensagem)` retorna uma Promise. Exibe modal com botoes "Sim" (rose) e "Nao" (cinza). Usada para exclusao de transacoes, metas e limpeza total.

---

## 6. Como Executar

```bash
# 1. Criar e ativar o ambiente virtual (Windows)
python -m venv venv
.\venv\Scripts\activate

# 2. Instalar dependencias
pip install django djangorestframework pandas ofxparse

# 3. Aplicar migracoes
python manage.py migrate

# 4. Subir o servidor
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/`.

---

## 7. Endpoints da API

| Metodo | Rota | Descricao |
|---|---|---|
| GET/POST | `/api/transacoes/` | Listar / criar transacoes |
| GET/PATCH/DELETE | `/api/transacoes/{uuid}/` | Detalhe / editar / excluir transacao |
| DELETE | `/api/transacoes/limpar_todas/` | Excluir todas as transacoes do usuario |
| GET/POST | `/api/orcamento/` | Listar / criar orcamento |
| GET/PATCH/DELETE | `/api/orcamento/{id}/` | Detalhe / editar / excluir orcamento |
| GET/POST | `/api/metas/` | Listar / criar metas financeiras |
| GET/PATCH/DELETE | `/api/metas/{id}/` | Detalhe / editar / excluir meta |
| GET | `/api/graficos-dados/?mes=&ano=` | Dados dos graficos |
| POST | `/api/importar-extrato/` | Importar arquivo (multipart: `extrato`, `banco`) |
