# 💰 Gerenciador de Finanças Pessoais

Uma aplicação web completa para controle financeiro pessoal, desenvolvida com **Django** e **Django REST Framework** no backend, integrada a uma interface minimalista e responsiva estilizada com **Tailwind CSS**.

O sistema permite que o usuário registre sua renda mensal para obter um planejamento automático de distribuição do orçamento (investimentos, reserva de emergência, contas fixas e lazer), além de registrar e acompanhar suas entradas e saídas em tempo real.

---

## ✨ Funcionalidades Atuais

- 🎯 **Etapa de Onboarding:** Modal inicial para definição do salário mensal.
- 📊 **Planejamento Recomendado:** Cálculo automático de metas baseado no salário:
  - Meta de Viver de Renda Passiva ($200\times$ o salário)
  - Reserva de Emergência ($6\times$ o salário)
  - Divisão ideal do salário: **10%** Investimento, **60%** Contas Fixas e **30%** Lazer.
- 💵 **Resumo Financeiro em Tempo Real:** Cards com totalizadores de Entradas, Saídas e Saldo Atual.
- ➕ **Lançamento de Movimentações:** Cadastro rápido de receitas e despesas.
- 📋 **Histórico de Transações:** Listagem de registros atualizada via API REST.
- ⚡ **API RESTful:** Endpoints estruturados para integração com o front-end.

---

## 🚀 Tecnologias Utilizadas

- **Backend:** Python, Django, Django REST Framework (DRF)
- **Frontend:** HTML5, JavaScript (Fetch API), Tailwind CSS
- **Banco de Dados:** SQLite (Desenvolvimento)
- **Outros:** UUID para identificação única de transações

---

## 🛠️ Como Executar o Projeto Localmente

### Pré-requisitos
- Python 3.10+ instalado
- Git instalado

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git](https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git)
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

3. **Instale as dependências:**
   ```bash
   pip install django djangorestframework
   ```

4. **Execute as migrações do banco de dados:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Inicie o servidor de desenvolvimento:**
   ```bash
   python manage.py runserver
   ```

6. Acesse a aplicação em `http://127.0.0.1:8000/` no seu navegador.

---

## 📌 Roadmap / Próximos Passos

- [ ] **Autenticação de Usuários:** Sistema completo de cadastro, login e logout com isolamento de dados por perfil.
- [ ] **Gestão Avançada de Transações:** Funcionalidades de edição (UPDATE) e exclusão (DELETE) de lançamentos.
- [ ] **Dashboard Interativo:** Gráficos visuais (Chart.js) de receitas vs. despesas com filtros por mês e ano.
- [ ] **Categorização de Gastos:** Filtros e tags personalizadas (Alimentação, Transporte, Moradia, etc.).

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.