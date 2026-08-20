# Manual de Erros e Correcoes

> Registro de todos os problemas enfrentados durante o desenvolvimento, suas causas e as correcoes aplicadas.
> Ultima atualizacao: 19/08/2026 (seguranca reforcada)

---

## Indice de Problemas

1. [Pix enviado cadastrado como RECEITA (importacao de CSV PicPay)](#1-pix-enviado-cadastrado-como-receita)
2. [Transacoes de saida nao eram importadas (sinal de menos Unicode U+2212)](#2-transacoes-de-saida-nao-eram-importadas-sinal-u2212)
3. [Duplicacao de transacoes em importacoes repetidas](#3-duplicacao-de-transacoes-em-importacoes-repetidas)
4. [CSV quebrava quando o valor tinha virgula sem aspas](#4-csv-quebrava-com-virgula-sem-aspas)
5. [Erro de encoding (utf-8 vs latin-1) ao ler CSVs](#5-erro-de-encoding-utf-8-vs-latin-1)
6. [Valor "0" e linhas vazias criando transacoes invalidas](#6-valor-0-e-linhas-vazias-criando-transacoes-invalidas)
7. [Data em formato brasileiro quebrando o banco de dados](#7-data-em-formato-brasileiro-quebrando-o-banco)
8. [Lixo no banco: descricao incorreta e registros orfaos](#8-lixo-no-banco-descricao-incorreta-e-registros-orfaos)
9. [KeyError no aggregate de receitas (alias sr vs s)](#9-keyerror-no-aggregate-de-receitas-alias-sr-vs-s)
10. [Erro 400 ao criar meta: campos obrigatorios ausentes no serializer](#10-erro-400-ao-criar-meta-campos-obrigatorios-ausentes-no-serializer)
11. [MetaViewSet sem isolamento por usuario](#11-metaviewset-sem-isolamento-por-usuario)
12. [JS enviava nomes errados para criar/editar meta](#12-js-enviava-nomes-errados-para-criar-editar-meta)
13. [Template planejamento.html inexistente causava erro 500](#13-template-planejamentohtml-inexistente-causava-erro-500)
14. [Template index.html usava nomes errados dos campos da MetaFinanceira](#14-template-indexhtml-usava-nomes-errados-dos-campos-da-metafinanceira)
15. [Aba retornava ao dashboard apos qualquer operacao](#15-aba-retornava-ao-dashboard-apos-qualquer-operacao)
16. [Campo pago e PlanejamentoService mortos no codigo](#16-campo-pago-e-planejamentoservice-mortos-no-codigo)
17. [Diagnostico de metas sempre mostrava Critico](#17-diagnostico-de-metas-sempre-mostrava-critico)
18. [Graficos nao carregavam ao abrir o site (parametros vazios na URL)](#18-graficos-nao-carregavam-ao-abrir-o-site-parametros-vazios-na-url)
19. [Status da meta nao era exibido visualmente (3 bugs encadeados)](#19-status-da-meta-nao-era-exibido-visualmente-3-bugs-encadeados)
20. [ContaReceber: related_name duplicado causava conflito de reverse accessor](#20-contareceber-related-name-duplicado-causava-conflito-de-reverse-accessor)
21. [ContaReceber: campo `paga` em vez de `recebida`](#21-contareceber-campo-paga-em-vez-de-recebida)
22. [ContaReceber: ordering apontava para campo inexistente](#22-contareceber-ordering-apontava-para-campo-inexistente)
23. [ContaReceberViewSet definido dentro de ContaPagarViewSet (classe aninhada)](#23-contareceberViewSet-definido-dentro-de-contapagarviewset-classe-aninhada)
24. [ContaReceberViewSet nao registrado no router](#24-contareceberViewSet-nao-registrado-no-router)
25. [Valor das categorias no HTML nao correspondia aos choices do model](#25-valor-das-categorias-no-html-nao-correspondia-aos-choices-do-model)
26. [Emojis na interface substituidos por Lucide Icons](#26-emojis-na-interface-substituidos-por-lucide-icons)
27. [Layout de abas horizontais substituido por Sidebar Lateral](#27-layout-de-abas-horizontais-substituido-por-sidebar-lateral)
28. [XSS via innerHTML — mensagens de erro injetadas sem sanitizacao](#28-xss-via-innerhtml--mensagens-de-erro-e-dados-do-usuario-injetados-sem-sanitizacao)
29. [Logout via GET permite CSRF logout](#29-logout-via-get-permite-csrf-logout)
30. [JavaScript inline no template — viola CSP e dificulta manutencao](#30-javascript-inline-no-template--viola-csp-e-dificulta-manutencao)
31. [Content Security Policy (CSP) nao configurada](#31-content-security-policy-csp-nao-configurada)
32. [Upload de extratos sem validacao de extensao, tamanho ou sanitizacao](#32-upload-de-extratos-sem-validacao-de-extensao-tamanho-ou-sanitizacao)
33. [Exclusao de conta sem registro em log](#33-exclusao-de-conta-sem-registro-em-log)
34. [DRF sem rate limiting (throttling)](#34-drf-sem-rate-limiting-throttling)
35. [SECRET_KEY com fallback inseguro](#35-secret_key-com-fallback-inseguro)
36. [Dependentencias nao versionadas no requirements.txt](#36-dependentencias-nao-versionadas-no-requirementstxt)
37. [Credenciais de deploy expostas no repositorio](#37-credenciais-de-deploy-expostas-no-repositorio)

---

## 1. Pix enviado cadastrado como RECEITA

**Sintoma:** Ao importar o CSV do PicPay, transacoes "Pix enviado" (saidas) eram cadastradas com `tipo = RECEITA`, inflando as entradas do dashboard.

### Causa
O parser do PicPay decidia o tipo pela presenca de um sinal de menos (`-`) no valor. O **banco do extrato nao chegava ao parser**: a view `importar_extrato` nao lia o valor do `<select>`, o `select` nao tinha `name`, e o JavaScript nao enviava o campo `banco` no `FormData`. Com isso, o parser usava configuracao generica e o valor negativo — que vinha com o **sinal de menos Unicode (U+2212)** — nao era reconhecido como saida.

### Correcao aplicada
1. **`core/views.py`** — `importar_extrato` passou a ler o banco:
   ```python
   banco_selecionado = request.POST.get('banco', 'picpay')
   resultado = ExtratoService.importar(arquivo, usuario, banco_selecionado=banco_selecionado)
   ```
2. **`core/templates/core/index.html`** — adicionado `name="banco"` no `<select id="selectBanco">`:
   ```html
   <select id="selectBanco" name="banco" ...>
   ```
3. **`core/templates/core/index.html` (JS)** — campo adicionado ao corpo do fetch:
   ```js
   formData.append('banco', document.getElementById('selectBanco').value);
   ```
4. **`core/parsers/csv_parser.py` (PicPayParser)** — regra explicita de tipo: se `"pix enviado"` no tipo → DESPESA (além do sinal no valor).

**Aprendizado:** ao mapear parametros do frontend → servico, verifique toda a cadeia: `HTML (name)` → `JS (formData)` → `view (request.POST)` → `servico → parser`.

---

## 2. Transacoes de saida nao eram importadas (sinal U+2212)

**Sintoma:** apos o fix anterior, as transacoes "Pix enviado" simplesmente **nao apareciam** no banco — todas as 90 transacoes existentes eram RECEITA.

### Causa raiz
O PicPay exporta valores negativos com o **sinal de menos Unicode U+2212** (`-`, "minus sign") em vez do hifen comum ASCII `-`:

```
Pix recebido, "+R$ 0,10",
Pix enviado, "-R$ 0,77",   <- U+2212
```

Ao tentar `float('-0.77')`, o Python lancava `ValueError`. O orquestrador tratava isso com `except ValueError: continue`, **descartando a linha em silencio** — por isso nenhuma saida era registrada e nao havia erro aparente.

### Correcao aplicada
1. **`core/parsers/csv_parser.py` (PicPayParser, ~linha 28)** — normalizacao antes do parse:
   ```python
   val_limpo = val_raw.replace('\u2013', '-').replace('\u2014', '-')
                          .replace('\u2212', '-')  # menos unicode → hifen
                          .replace('R$', '').replace('\xa0', '').strip()
   ```
2. **`core/parsers/csv_parser.py` (CsvExtratoParser, ~linha 205)** — normalizacao generica em qualquer banco:
   ```python
   val_num_str = val_limpo.replace('\u2212', '-')
                          .replace('-', '').replace('(', '').replace(')', '')
   ```

**Resultado (validado com dados reais):**
- `Pix recebido` → `tipo=RECEITA`
- `Pix enviado` → `tipo=DESPESA`
- `manage.py check` sem erros.

**Aprendizado:** falhas silenciosas em parsers (linhas descartadas por `except`) escondem bugs. Prefira contabilizar erros no `ImportResult` em vez de ignorar.

---

## 3. Duplicacao de transacoes em importacoes repetidas

**Sintoma:** importar o mesmo extrato mais de uma vez criava registros repetidos (foram encontradas 5x duplicatas de varias transacoes).

### Causa
O CSV nao possui um identificador unico por linha. Para OFX o sistema usa `transacao_id_externo` (FITID) como campo `unique` e ignora duplicatas, mas **CSV nao tinha mecanismo anti-duplicata**.

### Correcao aplicada
1. **Migracao `0004`** — campo `transacao_id_externo` (unique) para transacoes OFX.
2. **`extrato_service._importar_ofx`** — verifica se `transacao_id_externo` ja existe antes de criar.
3. Para CSV, a mitigacao atual e **limpeza manual** do banco (ver [problema 8](#8-lixo-no-banco-descricao-incorreta-e-registros-orfaos)).

**Recomendacao futura:** gerar uma chave de deduplicacao para CSV (ex.: hash de `usuario + data + descricao + valor + tipo`) e verifica-la antes de inserir.

---

## 4. CSV quebrava com virgula sem aspas

**Sintoma:** linhas cujo valor/campo continha virgula decimal (`1,50`) sem estar entre aspas eram divididas em colunas erradas, distorcendo `tipo` e `valor`.

### Causa
O `csv` do Python usa apenas `,` como delimitador por padrao. Arquivos com `;` eram lidos como um campo so, e arquivos com `,` decimal sem aspas eram fatiados no lugar errado.

### Correcao aplicada
- **`CsvExtratoParser`** passou a **detectar o delimitador** automaticamente com base no conteudo do arquivo (`;` ou `,`) antes de usar `csv.reader`.

**Aprendizado:** nunca assuma o delimitador; detecte a partir das primeiras linhas do arquivo.

---

## 5. Erro de encoding (utf-8 vs latin-1)

**Sintoma:** `UnicodeDecodeError` (ou texto com acentos corrompidos, ex.: `Sal?rio`) ao ler CSVs gerados em sistemas Windows (Excel/Bancos).

### Causa
Arquivos brasileiros frequentemente sao salvos em **latin-1 (cp1252)**, enquanto o Python tenta ler em **utf-8** por padrao.

### Correcao aplicada
- **`CsvExtratoParser`** le o arquivo em `utf-8` e, em caso de `UnicodeDecodeError`, refaz a leitura em `latin-1` (fallback).

**Obs.:** registros antigos gravados com encoding errado (ex.: `Sal?rio`) precisaram ser **deletados** — ver [problema 8](#8-lixo-no-banco-descricao-incorreta-e-registros-orfaos).

---

## 6. Valor "0" e linhas vazias criando transacoes invalidas

**Sintoma:** linhas sem valor ou com `0` geravam transacoes descartaveis (ou excecoes).

### Causa
O orquestrador convertia o valor antes de validar; linhas malformadas ou zeradas passavam.

### Correcao aplicada
- No `CsvExtratoParser`, linhas sem valor, com valor `0` ou com valor nao numerico sao **puladas** (apos a normalizacao do sinal U+2212 e de virgulas).

---

## 7. Data em formato brasileiro quebrando o banco

**Sintoma:** datas `DD/MM/AAAA` gravadas como texto invalido no `DateField`, ou `"janela de ontem"` sendo usada para transacoes do extrato.

### Causa
O CSV usa `DD/MM/AAAA`; o Django espera `AAAA-MM-DD`.

### Correcao aplicada
- **`CsvExtratoParser`**: normalizacao de data —
  - `DD/MM/AAAA` → converte para `AAAA-MM-DD`;
  - `AAAA-MM-DD` → usa como esta;
  - invalido → `date.today()` como fallback.

---

## 8. Lixo no banco: descricao incorreta e registros orfaos

**Sintoma:** o banco continha registros antigos/incorretos:
- descricoes com a **hora no lugar da descricao** (formato errado de versoes antigas do parser);
- **categorias corrompidas** por encoding (`Sal?rio`);
- **90 transacoes** que eram, na sua maioria, duplicatas de importacoes repetidas (5x) e todas RECEITA (nunca havia saidas).

### Causa
Acumulo de dados gerados por parsers antigos (antes das correcoes dos problemas 1, 2 e 5) + importacoes repetidas sem deduplicacao para CSV.

### Correcao aplicada
- **Limpeza do banco a pedido do usuario:** as 90 transacoes de `core_transacao` foram **excluidas** via script Django temporario (removido apos o uso). Usuarios e orcamentos foram preservados.
- Apos a limpeza e os fixes de parsing, a importacao foi **validada com dados reais** e passou a funcionar corretamente.

---

## 9. KeyError no aggregate de receitas (alias sr vs s)

**Sintoma:** erro `KeyError: 's'` ao acessar a aba Planejamento Financeiro ou ao calcular diagnosticos de meta.

### Causa
Em `planejamento_service.py`, a linha de aggregacao de receitas usava o alias `sr` mas o acesso ao dicionario usava `['s']`:

```python
# Linha 60 - ERRO: alias 'sr', mas acessa ['s']
total_receitas = transacoes_mes.filter(tipo='RECEITA').aggregate(sr=Sum('valor'))['s']
# Linha 61 - CORRETO: alias 's' e acessa ['s']
total_despesas = transacoes_mes.filter(tipo='DESPESA').aggregate(s=Sum('valor'))['s']
```

### Correcao aplicada
- **`core/services/planejamento_service.py:60`** — alias `sr` alterado para `s` para coincidir com o acesso `['s']`:
  ```python
  total_receitas = transacoes_mes.filter(tipo='RECEITA').aggregate(s=Sum('valor'))['s']
  ```

---

## 10. Erro 400 ao criar meta: campos obrigatorios ausentes no serializer

**Sintoma:** ao tentar cadastrar uma meta financeira via `POST /api/metas/`, o servidor retornava erro 400 com campos obrigatorios faltando.

### Causa
O `MetaSerializer` nao tinha `read_only_fields = ['usuario']`, o que exigia que o campo `usuario` fosse enviado no POST. O JavaScript nao enviava esse campo (o `perform_create` da view deveria atribui-lo automaticamente).

### Correcao aplicada
1. **`core/serializers.py`** — adicionado `read_only_fields = ['usuario']` ao `MetaSerializer`:
   ```python
   class MetaSerializer(serializers.ModelSerializer):
       class Meta:
           model = MetaFinanceira
           fields = '__all__'
           read_only_fields = ['usuario']
   ```
2. **`core/views.py`** — adicionado `perform_create` ao `MetaViewSet`:
   ```python
   def perform_create(self, serializer):
       serializer.save(usuario=self.request.user)
   ```

---

## 11. MetaViewSet sem isolamento por usuario

**Sintoma:** qualquer usuario autenticado podia visualizar e modificar metas de outros usuarios.

### Causa
O `MetaViewSet` usava `queryset = MetaFinanceira.objects.all()` sem filtrar por `request.user`, e nao tinha `get_queryset()`.

### Correcao aplicada
- **`core/views.py`** — `MetaViewSet` atualizado com isolamento:
  ```python
  class MetaViewSet(viewsets.ModelViewSet):
      serializer_class = MetaSerializer
      permission_classes = [IsAuthenticated]

      def get_queryset(self):
          return MetaFinanceira.objects.filter(usuario=self.request.user)

      def perform_create(self, serializer):
          serializer.save(usuario=self.request.user)
  ```

---

## 12. JS enviava nomes errados para criar/editar meta

**Sintoma:** erro 400 ao criar meta; o campo `valor_objetivo` nao era reconhecido.

### Causa
O JavaScript enviava `valor_alvo` no payload, mas o campo do model e `valor_objetivo`. Tambem nao enviava `aporte_mensal_desejado` (campo obrigatorio sem default).

### Correcao aplicada
- **`core/templates/core/index.html` (JS)** — payload corrigido:
  ```javascript
  const payload = {
      titulo: document.getElementById('metaTitulo').value,
      valor_objetivo: parseFloat(document.getElementById('metaValorAlvo').value),
      valor_atual: parseFloat(document.getElementById('metaValorAtual').value) || 0,
      aporte_mensal_desejado: valorRestante / prazoMeses,
      prazo_meses: parseInt(document.getElementById('metaPrazoMeses').value)
  };
  ```

---

## 13. Template planejamento.html inexistente causava erro 500

**Sintoma:** ao acessar `/api/tela-planejamento/`, o servidor retornava erro 500 com `TemplateDoesNotExist`.

### Causa
A view `tela_planejamento` fazia `render(request, 'planejamento.html', ...)` mas o template nao existia. Todos os templates estavam em `core/templates/core/`.

### Correcao aplicada
- **`core/views.py`** — `tela_planejamento` alterada para redirecionar para a pagina principal:
  ```python
  @login_required
  def tela_planejamento(request):
      return redirect('index')
  ```

---

## 14. Template index.html usava nomes errados dos campos da MetaFinanceira

**Sintoma:** campos da meta nao apareciam no dashboard (valores zerados ou ausentes).

### Causa
O template usava nomes de campos inexistentes no model:
- `meta.valor_alvo` → deveria ser `meta.valor_objetivo`
- `meta.aporte_mensal` → deveria ser `meta.aporte_mensal_desejado`
- `meta.progresso_percentual` → nao existia no model

### Correcao aplicada
1. **`core/templates/core/index.html`** — nomes corrigidos no template:
   - `meta.valor_alvo` → `meta.valor_objetivo`
   - `meta.aporte_mensal` → `meta.aporte_mensal_desejado`
2. **`core/models.py`** — adicionado `@property progresso_percentual` ao `MetaFinanceira`:
   ```python
   @property
   def progresso_percentual(self):
       if self.valor_objetivo > 0:
           return round((self.valor_atual / self.valor_objetivo) * 100, 1)
       return 0
   ```
3. **`core/views.py`** — adicionado `metas` ao contexto de `pagina_inicial`:
   ```python
   metas = MetaFinanceira.objects.filter(usuario=request.user)
   # Adicionado 'metas': metas no dict contexto
   ```

---

## 15. Aba retornava ao dashboard apos qualquer operacao

**Sintoma:** ao editar, excluir ou criar uma transacao/meta, a pagina recarregava e voltava para a aba Dashboard, perdendo a posicao do usuario.

### Causa
O `window.location.reload()` recarregava a pagina, mas o estado da aba ativa so era mantido no DOM (classe `hidden`). Ao recarregar, todas as abas voltavam ao estado padrao (dashboard visivel).

### Correcao aplicada
1. **`alternarAba()`** — grava a aba ativa na URL via `?aba=nomeAba`:
   ```javascript
   const url = new URL(window.location);
   url.searchParams.set('aba', nomeAba);
   window.history.replaceState({}, '', url);
   ```
2. **`DOMContentLoaded`** — restaura a aba ativa a partir da URL:
   ```javascript
   const aba = urlParams.get('aba');
   if (aba && aba !== 'dashboard') {
       alternarAba(aba);
   } else {
       carregarGraficos();
   }
   ```
3. **`aplicarFiltroData()`** — preserva o parametro `aba` ao filtrar por mes/ano.

---

## 16. Campo pago e PlanejamentoService mortos no codigo

**Sintoma:** dois itens de codigo existiam mas nao eram utilizados em lugar nenhum:
1. Campo `pago` (`BooleanField`) no model `Transacao` — nunca era exibido no template, nunca era filtrado, o JS sempre enviava `pago: true` sem utilidade.
2. `PlanejamentoService.calcular_diagnostico_meta()` — metodo completo com diagnostico preditivo (Critico/Excelente/Proximo/Longe) mas nunca chamado por nenhuma view, URL ou JS.

### Causa
- O campo `pago` foi adicionado em fase inicial do projeto (possivelmente para controle "pago/nao pago") mas nunca foi integrado a interface.
- O `PlanejamentoService` foi implementado com a logica de diagnostico mas a view `pagina_inicial` so passava as metas como queryset simples, sem calcular o diagnostico.

### Correcao aplicada
1. **Campo `pago` removido:**
   - `core/models.py` — removida a linha `pago = models.BooleanField(default=False)`;
   - `core/templates/core/index.html` — removido `pago: true` do payload JS de criacao de transacao;
   - Migration `0007_remove_pago_field` gerada.

2. **PlanejamentoService tornado funcional:**
   - `core/views.py` — `pagina_inicial` agora itera sobre cada meta e chama `PlanejamentoService.calcular_diagnostico_meta(meta.id, request.user, mes, ano)`, passando os diagnosticos no contexto como `metas_com_diagnostico`;
   - `core/templates/core/index.html` — cada card de meta exibe badge colorido com o status do diagnostico e tooltip nativo com a mensagem completa;
   - Cores: Critico=rose, Excelente=emerald, Proximo=amber, Longe=cinza.

**Aprendizado:** codigo morto deve ser detectado cedo — nao adianta implementar funcionalidade se nao ha caminho de chamada (view → template → JS).

---

## 17. Diagnostico de metas sempre mostrava Critico

**Sintoma:** o badge de diagnostico de todas as metas sempre exibia "Critico" (rose), independentemente dos valores definidos na meta ou das transacoes do usuario.

### Causa
A logica de diagnostico em `planejamento_service.py` verificava `if sobra_mes <= 0` como primeira condicao. Quando o usuario nao tinha transacoes no mes selecionado, `sobra_mes = 0`, e `0 <= 0` e True — resultando sempre em "Critico".

Alem disso, o template usava nomes de status em maiusculo (`PRÓXIMO`, `LONGE`) que nao combinavam com os valores retornados pelo service (`Próximo`, `Longe`).

### Correcao aplicada
1. **`core/services/planejamento_service.py`** — reestruturada a ordem de verificacao:
   - Primeiro: `if not transacoes_mes.exists()` → retorna `Neutro` (sem transacoes no periodo);
   - Depois: `elif sobra_mes < 0` → `Critico` (despesas > receitas);
   - Depois: `elif aporte_necessario_mensal <= 0` → `Excelente` (meta ja atingida);
   - Depois: `elif percentual_capacidade >= 100` → `Excelente` (sobra cobre aporte);
   - Depois: `elif percentual_capacidade >= 70` → `Próximo`;
   - Senao: `Longe`.

2. **`core/templates/core/index.html`** — badges atualizados:
   - Corrigidos nomes: `PRÓXIMO` → `Próximo`, `LONGE` → `Longe`;
   - Adicionado badge `Neutro` (azul) para metas sem transacoes no periodo.

**Aprendizado:** `<= 0` inclui zero — quando o intuito e detectar "negativo", usar `< 0`. E importante tratar o caso "sem dados" separadamente do caso "dados negativos".

---

## 18. Graficos nao carregavam ao abrir o site (parametros vazios na URL)

**Sintoma:** ao acessar a pagina principal (`/`), os graficos de rosca e barras permaneciam em branco. Nenhum erro visivel era exibido ao usuario.

### Causa
Em `index.html`, a funcao `carregarGraficos()` montava a URL da API com parametros vazios:

```javascript
const mes = urlParams.get('mes') || '';
const ano = urlParams.get('ano') || '';
const response = await fetch(`/api/graficos-dados/?mes=${mes}&ano=${ano}`);
```

Ao acessar `/` sem query params, `mes` e `ano` eram strings vazias (`''`). A URL resultante era `/api/graficos-dados/?mes=&ano=`. No backend (`GraficosDataAPIView`), `request.GET.get('mes', hoje.month)` retornava `''` (a chave existia, so o valor estava vazio), e `int('')')` lancava `ValueError`. O `try/except` em `carregarGraficos()` engolia o erro silenciosamente.

### Correcao aplicada
- **`core/templates/core/index.html`** — parametros so sao incluidos na URL se tiverem valor:
  ```javascript
  const params = new URLSearchParams();
  const mes = urlParams.get('mes');
  const ano = urlParams.get('ano');
  if (mes) params.set('mes', mes);
  if (ano) params.set('ano', ano);
  const qs = params.toString();
  const response = await fetch(`/api/graficos-dados/${qs ? '?' + qs : ''}`);
  ```

**Aprendizado:** `dict.get(key, default)` so usa o default quando a chave **nao existe**. Se a chave existe com valor vazio, retorna o valor vazio. Nunca envie parametros vazios em query strings.

---

## 19. Status da meta nao era exibido visualmente (3 bugs encadeados)

**Sintoma:** o badge de status das metas financeiras nunca aparecia no dashboard, independentemente dos valores da meta.

### Causa (3 bugs encadeados)

**Bug A — Argumentos extras na chamada do service:**
Em `views.py`, a view `pagina_inicial` chamava `calcular_diagnostico_meta` com 4 argumentos, mas o metodo so aceitava 2:

```python
# views.py (ERRADO)
diag = PlanejamentoService.calcular_diagnostico_meta(
    meta.id, request.user, mes_selecionado, ano_selecionado
)

# planejamento_service.py (aceita apenas 2)
def calcular_diagnostico_meta(meta_id, usuario):
```

Isso lancava `TypeError` a cada chamada, que era capturado pelo `except Exception`.

**Bug B — Chave errada no fallback:**
O bloco `except` criava um dict com a chave `'status'`, mas o template lia `diag.status_label`:

```python
# ERRADO: chave 'status' em vez de 'status_label'
diag = {'status': 'Sem dados', 'mensagem': '...'}
```

**Bug C — Strings nao coincidiam entre service e template:**
Mesmo se os bugs A e B fossem corrigidos, as strings do service tinham maiusculas e genero diferentes do template:

| Service produzia       | Template esperava       | Match? |
|------------------------|-------------------------|--------|
| `Inicio da Meta`       | `Inicio da meta`        | NAO    |
| `Em Andamento`         | `Em andamento`          | NAO    |
| `Perto do Objetivo`    | `Perto do objetivo`     | NAO    |
| `Concluida`            | `Concluido`             | NAO    |

### Correcao aplicada
1. **`core/views.py:123`** — removidos os argumentos extras:
   ```python
   diag = PlanejamentoService.calcular_diagnostico_meta(meta.id, request.user)
   ```
2. **`core/views.py:126`** — chave do fallback corrigida:
   ```python
   diag = {'status_label': 'Sem dados', 'mensagem': '...'}
   ```
3. **`core/templates/core/index.html:403-410`** — strings do template atualizadas para coincidir com o service (capitalizacao e genero corretos).

**Aprendizado:** quando 3 camadas se comunicam (service → view → template), erros de nomenclatura em qualquer uma delas causam falhas silenciosas. Validar os nomes das chaves e strings em toda a cadeia e essencial.

---

## 20. ContaReceber: related_name duplicado causava conflito de reverse accessor

**Sintoma:** `django.core.exceptions.EreludeError: Reverse accessor 'transacao.conta_origem' for 'core.Transacao.conta_origem' clashes with field name 'core.Transacao.conta_origem_receber'`.

### Causa
O model `ContaReceber` definia `related_name='conta_origem'` no `OneToOneField` para `Transacao`, mas o model `ContaPagar` ja usava o mesmo `related_name='conta_origem'`. Dois campos ManyToOne/OneToOne no mesmo model nao podem compartilhar o mesmo `related_name`.

### Correcao aplicada
- **`core/models.py`** — `related_name` do `OneToOneField` em `ContaReceber` alterado para `'conta_origem_receber'`:
  ```python
  transacao_gerada = models.OneToOneField(
      'Transacao', null=True, blank=True,
      on_delete=models.SET_NULL,
      related_name='conta_origem_receber'
  )
  ```

---

## 21. ContaReceber: campo `paga` em vez de `recebida`

**Sintoma:** ao executar `makemigrations` para `ContaReceber`, o campo booleano era gerado como `paga` em vez do nome correto `recebida`.

### Causa
O model foi criado inicialmente copiando a estrutura de `ContaPagar` sem ajustar o nome do campo booleano. O campo `paga` nao tem sentido semantico em uma conta a receber.

### Correcao aplicada
- **`core/models.py`** — campo renomeado de `paga` para `recebida`:
  ```python
  recebida = models.BooleanField(default=False)
  ```

---

## 22. ContaReceber: ordering apontava para campo inexistente

**Sintoma:** `django.core.exceptions.FieldError: Cannot resolve keyword 'data_vencimento' in ordering`.

### Causa
O `Meta.ordering` de `ContaReceber` foi copiado de `ContaPagar` com `ordering=['data_vencimento']`, mas o campo de data do model e `data_recebimento`.

### Correcao aplicada
- **`core/models.py`** — `ordering` corrigido para `['data_recebimento']`.

---

## 23. ContaReceberViewSet definido dentro de ContaPagarViewSet (classe aninhada)

**Sintoma:** a rota `/api/contas-receber/` retornava erro 404; o `ViewSet` nao existia como classe separada.

### Causa
`ContaReceberViewSet` foi escrita com indentacao dentro da classe `ContaPagarViewSet`, tornando-se um atributo/metodo interno em vez de uma classe independente. Tambem faltava `perform_create` com ` usuario=self.request.user` e a action `dar_baixa` nao estava implementada.

### Correcao aplicada
- **`core/views.py`** — `ContaReceberViewSet` extraida como classe independente com `get_queryset`, `perform_create`, `destroy` (remove transacao vinculada) e `dar_baixa` (cria `Transacao` de `TIPO=RECEITA`).

---

## 24. ContaReceberViewSet nao registrado no router

**Sintoma:** `NoReverseMatch` ao tentar gerar URLs da API para `conta-receber`; a rota simplesmente nao existia.

### Causa
O `router.register` para `ContaReceberViewSet` nao foi adicionado em `core/urls.py`, e a importacao de `ContaReceberViewSet` e `ContaReceberSerializer` estava faltando.

### Correcao aplicada
1. **`core/urls.py`** — adicionado registro:
   ```python
   router.register(r'contas-receber', ContaReceberViewSet, basename='conta-receber')
   ```
2. **`core/urls.py`** — importacoes adicionadas:
   ```python
   from .views import ContaReceberViewSet
   ```

---

## 25. Valor das categorias no HTML nao correspondia aos choices do model

**Sintoma:** ao cadastrar conta a pagar/receber, o campo `categoria` era enviado com valor sem acento (ex: `Alimentacao`) mas o `CATEGORIA_CHOICES` do model usava acentos (ex: `Alimentacao`). O Django retornava erro de validacao.

### Causa
Os `<option value="">` nos modais de ContaPagar e ContaReceber foram escritos com valores sem acentos, mas os choices do model `Transacao.CATEGORIA_CHOICES` usam strings com acento (`Alimentação`, `Saúde`, etc.).

### Correcao aplicada
- **`core/templates/core/index.html`** — todos os `value` das opcoes de categoria nos modais de ContaPagar e ContaReceber foram ajustados para incluir acentos corretos:
  ```html
  <option value="Alimentação">Alimentação</option>
  <option value="Moradia">Moradia</option>
  <option value="Saúde">Saúde</option>
  ...
  ```

---

## 26. Emojis na interface substituidos por Lucide Icons

**Sintoma:** a interface continha dezenas de emojis Unicode (ex: `💰`, `📊`, `💸`, `✅`) que funcionavam de forma inconsistente entre navegadores e sistemas operacionais, e nao seguiam o padrao visual do design SaaS.

### Causa
A aplicacao foi construida originalmente usando emojis como solucao rapida de icones, sem uma biblioteca de icones dedicada.

### Correcao aplicada
1. **`index.html`** — adicionado CDN do Lucide Icons:
   ```html
   <script src="https://unpkg.com/lucide@latest"></script>
   ```
2. **`index.html`** — todas as tags de emoji estaticas substituidas por tags `<i data-lucide="nome-do-icone">` e `lucide.createIcons()` chamado no `DOMContentLoaded` e apos cada renderizacao dinamica de tabelas (funcoes `renderizarTabelaTransacoes`, `renderizarTabelaMetas`, `renderizarTabelaContasPagar`, `renderizarTabelaContasReceber`).

---

## 27. Layout de abas horizontais substituido por Sidebar Lateral

**Sintoma:** o design original usava abas horizontais no topo da pagina, nao correspondendo ao layout SaaS com sidebar lateral fixa especificado no `design.md`.

### Causa
O template original foi construido com navegacao por abas horizontais (`alternarAba()` com classList hidden/visible), sem suporte a um layout sidebar.

### Correcao aplicada
- **`index.html`** — reescrito com layout sidebar:
  - `<aside class="w-64 ...">` com menu de navegacao vertical;
  - `<main class="flex-1 ...">` com area de conteudo;
  - `alternarAba()` reescrita para mapear IDs `nav-*` → `conteudo-aba-*` e atualizar titulo via `#titulo-pagina-ativa`;
  - Preservacao de todas as funcionalidades JS existentes (CRUDs, modais, graficos, filtros).

---

## 28. XSS via innerHTML — mensagens de erro e dados do usuario injetados sem sanitizacao

**Sintoma:** potencial vulnerabilidade de XSS (Cross-Site Scripting). Dados vindos do backend (descricoes, nomes de categorias, valores, mensagens de erro) eram injetados diretamente no DOM via `innerHTML` sem sanitizacao.

### Causa
Todo o template `index.html` usava `element.innerHTML = ...` com interpolacao de strings sem escape. Se um atacante cadastrasse uma transacao com descricao contendo `<script>alert(1)</script>`, o codigo seria executado no navegador de qualquer usuario que visse a lista.

### Correcao aplicada
1. **`core/templates/core/index.html`** — adicionada funcao `escapeHtml()` que converte `<`, `>`, `&`, `"`, `'` em suas entidades HTML:
   ```javascript
   function escapeHtml(str) {
       if (!str) return '';
       return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
                         .replace(/"/g,'&quot;').replace(/'/g,'&#039;');
   }
   ```
2. Todas as saidas dinamicas (`innerHTML`) passaram a usar `escapeHtml()`:
   - Tabelas de transacoes, metas, contas a pagar, contas a receber
   - Toast notifications
   - Mensagens de erro do backend

**Commit:** `9033596`

---

## 29. Logout via GET permite CSRF logout

**Sintoma:** a view de logout aceitava requisicoes GET. Um atacante podia criar um link `<img src="/logout/">` e, ao ser clicado, encerrar a sessao do usuario (CSRF logout).

### Causa
A view `logout_view` nao tinha restricao de metodo HTTP. Qualquer requisicao (GET, POST, etc.) executava o `logout()`.

### Correcao aplicada
1. **`core/views.py`** — adicionado decorator `@require_POST`:
   ```python
   @login_required
   @require_POST
   def logout_view(request):
       logout(request)
       return redirect('login')
   ```
2. **`core/templates/core/index.html`** — botao de logout alterado de link GET para form POST:
   ```html
   <form method="post" action="{% url 'logout' %}">
       {% csrf_token %}
       <button type="submit">Sair</button>
   </form>
   ```

**Commit:** `9033596`

---

## 30. JavaScript inline no template — viola CSP e dificulta manutencao

**Sintoma:** todo o JavaScript da aplicacao (~730 linhas) estava em blocos `<script>` inline dentro de `index.html`. Isso viola politicas CSP estritas e dificulta manutencao e debug.

### Causa
O projeto foi construido com todo o JS no template HTML, padrao comum em projetos Django monoliticos.

### Correcao aplicada
1. **`core/static/core/js/app.js`** — criado com todo o JavaScript extraido de `index.html`
2. **`core/templates/core/index.html`** — blocos `<script>` inline removidos, substituidos por:
   ```html
   {% load static %}
   <script src="{% static 'core/js/app.js' %}"></script>
   ```
3. **`setup/settings.py`** — adicionado `STATICFILES_DIRS`:
   ```python
   STATICFILES_DIRS = [BASE_DIR / 'core' / 'static']
   ```
4. Funcao `lucide.createIcons()` movida para dentro do callback `DOMContentLoaded` no `app.js`.

**Commit:** `90830a7`

---

## 31. Content Security Policy (CSP) nao configurada

**Sintoma:** nenhum header CSP era enviado. O navegador aceitava scripts, estilos e frames de qualquer origem.

### Causa
O Django nao tinha middleware de CSP configurado. Versoes anteriores ao Django 6.0 exigiam pacotes externos (ex: `django-csp`), mas o Django 6.0 traz middleware nativo.

### Correcao aplicada
1. **`setup/settings.py`** — middleware adicionado:
   ```python
   'django.middleware.csp.ContentSecurityPolicyMiddleware',
   ```
2. **`setup/settings.py`** — politica configurada via `SECURE_CSP`:
   ```python
   from django.utils.csp import CSP
   SECURE_CSP = {
       'default-src': [CSP.SELF],
       'script-src': [CSP.SELF, 'cdn.tailwindcss.com', 'cdn.jsdelivr.net', 'unpkg.com'],
       'style-src': [CSP.SELF, 'cdn.tailwindcss.com', 'cdn.jsdelivr.net', 'unpkg.com', "'unsafe-inline'"],
       'img-src': [CSP.SELF, 'data:'],
       'font-src': [CSP.SELF, 'fonts.gstatic.com', 'cdn.jsdelivr.net'],
       'connect-src': [CSP.SELF],
       'frame-src': ['none'],
       'object-src': ['none'],
   }
   ```

**Commit:** `90830a7`

---

## 32. Upload de extratos sem validacao de extensao, tamanho ou sanitizacao

**Sintoma:** a view de importacao aceitava qualquer tipo de arquivo e tamanho. Nome do arquivo era usado sem sanitizacao.

### Causa
A view `importar_extrato` apenas verificava se `request.FILES` continha um arquivo, sem validar extensao, tamanho ou nome.

### Correcao aplicada
1. **`core/views.py`** — validacao de extensao:
   ```python
   nome_ext = os.path.splitext(arquivo.name)[1].lower()
   if nome_ext not in ('.ofx', '.csv'):
       return JsonResponse({'erro': 'Formato nao suportado.'}, status=400)
   ```
2. Validacao de tamanho (5 MB):
   ```python
   if arquivo.size > 5 * 1024 * 1024:
       return JsonResponse({'erro': 'Arquivo muito grande. Limite: 5 MB.'}, status=400)
   ```
3. Sanitizacao do nome do arquivo:
   ```python
   nome_seguro = os.path.basename(arquivo.name)[:255]
   ```
4. Limits de upload adicionados em `settings.py`:
   ```python
   DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
   FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
   ```

**Commit:** `9033596`

---

## 33. Exclusao de conta sem registro em log

**Sintoma:** a operacao de deletar conta nao gerava nenhum registro em log, dificultando auditoria e rastreabilidade.

### Causa
A view `deletar_conta` executava `request.user.delete()` sem registrar a operacao.

### Correcao aplicada
- **`core/views.py`** — adicionado `logging.warning()` antes da exclusao:
  ```python
  logging.warning('Conta deletada: usuario=%s (id=%s)', username, user_id)
  ```

**Commit:** `9033596`

---

## 34. DRF sem rate limiting (throttling)

**Sintoma:** a API REST nao tinha limitacao de requisicoes. Um atacante podia fazer brute force no login ou sobrecarregar o servidor com muitas requisicoes.

### Causa
O `REST_FRAMEWORK` em `settings.py` nao configurava `DEFAULT_THROTTLE_CLASSES` nem `DEFAULT_THROTTLE_RATES`.

### Correcao aplicada
- **`setup/settings.py`** — throttling adicionado:
  ```python
  REST_FRAMEWORK = {
      'DEFAULT_THROTTLE_CLASSES': [
          'rest_framework.throttling.AnonRateThrottle',
          'rest_framework.throttling.UserRateThrottle',
      ],
      'DEFAULT_THROTTLE_RATES': {
          'anon': '30/hour',
          'user': '200/hour',
      }
  }
  ```

**Commit:** `9033596`

---

## 35. SECRET_KEY com fallback inseguro

**Sintoma:** se a variavel `DJANGO_SECRET_KEY` nao estivesse configurada, o Django usaria um valor padrao pre-definido — comprometendo assinaturas de sessoes e tokens CSRF em producao.

### Causa
A configuracao original tinha `SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'fallback-inseguro')`, permitindo que o sistema rodasse com uma chave conhecida.

### Correcao aplicada
- **`setup/settings.py`** — ValueError se a variavel nao existir:
  ```python
  SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
  if not SECRET_KEY:
      raise ValueError("A variavel de ambiente DJANGO_SECRET_KEY nao esta configurada.")
  ```

**Commit:** `9033596`

---

## 36. Dependentencias nao versionadas no requirements.txt

**Sintoma:** `requirements.txt` nao tinha versoes fixas. Cada `pip install` podia instalar versoes diferentes, causando incompatibilidades em producao.

### Causa
O `requirements.txt` original continha apenas nomes dos pacotes sem versoes:
```
Django
djangorestframework
pandas
...
```

### Correcao aplicada
- **`requirements.txt`** — todas as 8 dependencias versionadas:
  ```
  Django==6.0.7
  djangorestframework==3.18.0
  pandas==2.2.3
  ofxparse==0.2.1
  dj-database-url==3.1.2
  whitenoise==6.8.2
  gunicorn==23.0.0
  psycopg2-binary==2.9.9
  ```

**Commit:** `9033596`

---

## 37. Credenciais de deploy expostas no repositorio

**Sintoma:** o arquivo `CREDENCIAIS_DEPLOY.md` com senhas e URLs de producao estava visivel no repositorio GitHub.

### Causa
O arquivo foi criado no inicio do projeto e commitado antes de ser adicionado ao `.gitignore`.

### Correcao aplicada
1. Arquivo adicionado ao `.gitignore` (regra `*.md` + excecoes para docs publicos)
2. Arquivo removido do historico de commits do Git
3. Verificado com `git log -p -- "CREDENCIAIS_DEPLOY.md"` — nenhum conteudo sensivel encontrado

**Commit:** `f742860`

---

## Como Prevenir (checklist): `HTML name` → `JS FormData` → `view request.POST` → `servico` → `parser`.
- [ ] Normalizar sinais e caracteres especiais antes do `float()` (U+2212, `R$`, `\xa0`, espacos).
- [ ] Nunca descartar linhas em silencio — registrar em `ImportResult(criadas, ignoradas, erros)`.
- [ ] Detectar delimitador do CSV em vez de assumir.
- [ ] Tentar leitura em `utf-8` com fallback para `latin-1`.
- [ ] Normalizar datas pt-BR antes de gravar.
- [ ] Usar identificador externo (FITID) para OFX e planejar deduplicacao para CSV.
- [ ] Verificar nomes de campos entre serializer, model, template e JavaScript.
- [ ] Adicionar `read_only_fields = ['usuario']` em todos os serializers com FK para User.
- [ ] Adicionar `get_queryset()` filtrando por `request.user` em todos os ViewSets.
- [ ] Preservar estado da UI (abas, filtros) apos recarregamentos.
- [ ] Validar assinaturas de metodos (qtd de argumentos) entre view e service.
- [ ] Validar chaves de dicts entre service, view e template (ex: `status` vs `status_label`).
- [ ] Validar strings de comparacao entre service e template (case-sensitive, genero).
- [ ] Nao enviar parametros vazios em query strings — omitir a chave quando nao houver valor.
- [ ] Nao duplicar `related_name` entre OneToOneField no mesmo model (conflito de reverse accessor).
- [ ] Usar nomes semanticos corretos para campos booleanos (ex: `recebida` em vez de `paga` para contas a receber).
- [ ] Verificar que `ordering` do Meta aponta para campos existentes no model.
- [ ] Manter ViewSets como classes independentes — nunca indentar dentro de outra ViewSet.
- [ ] Registrar todos os ViewSets no router (`router.register`) e verificar importacoes em `urls.py`.
- [ ] Garantir que `value` dos `<option>` HTML coincida exatamente com os choices do model (acentos importam).
- [ ] Sanitizar todo innerHTML dinamico com `escapeHtml()` antes de injetar no DOM.
- [ ] Logout deve requerer POST (`@require_POST`) para prevenir CSRF logout.
- [ ] JavaScript nao deve ficar inline no template — extrair para arquivo estatico.
- [ ] Configurar CSP via middleware nativo do Django 6.0 (`ContentSecurityPolicyMiddleware`).
- [ ] Validar extensao e tamanho de uploads no backend, nao apenas no frontend.
- [ ] Sanitizar nome de arquivos com `os.path.basename()` antes de usar.
- [ ] SECRET_KEY deve obrigar variavel de ambiente (raise ValueError se ausente).
- [ ] Versionar todas as dependencias no `requirements.txt` (nunca usar nomes sem versao).
- [ ] Credenciais nunca devem ser commitadas — usar `.gitignore` e variaveis de ambiente.
- [ ] Configurar rate limiting (throttling) no DRF para APIs publicas.
- [ ] Registrar operacoes criticas em log (exclusao de conta, erros de importacao).
