# Manual de Erros e Correcoes

> Registro de todos os problemas enfrentados durante o desenvolvimento, suas causas e as correcoes aplicadas.
> Ultima atualizacao: 17/08/2026

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
