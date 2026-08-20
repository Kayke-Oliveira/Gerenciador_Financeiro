    let chartTiposInstance = null;
    let chartCategoriasInstance = null;

    // --- TOAST ---
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function mostrarToast(mensagem, tipo = 'sucesso') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        const cores = tipo === 'sucesso'
            ? 'bg-emerald-600 border-emerald-700 text-white'
            : 'bg-rose-600 border-rose-700 text-white';
        const icone = tipo === 'sucesso' ? '&#10003;' : '&#10007;';
        toast.className = `pointer-events-auto flex items-center gap-3 px-5 py-3 rounded-2xl shadow-lg border ${cores} toast-enter text-sm font-medium max-w-sm`;
        toast.innerHTML = `
            <span class="text-base font-bold">${icone}</span>
            <span class="flex-1">${escapeHtml(mensagem)}</span>
            <button onclick="this.parentElement.remove()" class="ml-2 text-white/70 hover:text-white text-lg font-bold leading-none">&times;</button>
        `;
        container.appendChild(toast);
        setTimeout(() => {
            toast.classList.remove('toast-enter');
            toast.classList.add('toast-exit');
            toast.addEventListener('animationend', () => toast.remove());
        }, 4000);
    }

    // --- CONFIRMAÇÃO GENÉRICA ---
    function confirmarAcao(mensagem) {
        return new Promise(resolve => {
            document.getElementById('mensagemConfirmarGenerico').textContent = mensagem;
            document.getElementById('modalConfirmarGenerico').classList.remove('hidden');
            const btnSim = document.getElementById('btnConfirmarGenericoSim');
            const btnNao = document.getElementById('btnConfirmarGenericoNao');
            function limpar() {
                document.getElementById('modalConfirmarGenerico').classList.add('hidden');
                btnSim.removeEventListener('click', onSim);
                btnNao.removeEventListener('click', onNao);
            }
            function onSim() { limpar(); resolve(true); }
            function onNao() { limpar(); resolve(false); }
            btnSim.addEventListener('click', onSim);
            btnNao.addEventListener('click', onNao);
        });
    }

    // --- CSRF ---
    function getCsrfToken() {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, 10) === ('csrftoken=')) {
                    cookieValue = decodeURIComponent(cookie.substring(10));
                    break;
                }
            }
        }
        if (!cookieValue) {
            const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfInput) cookieValue = csrfInput.value;
        }
        return cookieValue;
    }

    function getCsrfTokenContas() {
        const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
        if (cookie) return cookie.split('=')[1];
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        return input ? input.value : '';
    }

    // --- FILTRO DE DATA ---
    function aplicarFiltroData() {
        const urlParams = new URLSearchParams(window.location.search);
        const aba = urlParams.get('aba');
        if (aba) {
            let inputAba = document.querySelector('#formFiltroData input[name="aba"]');
            if (!inputAba) {
                inputAba = document.createElement('input');
                inputAba.type = 'hidden';
                inputAba.name = 'aba';
                document.getElementById('formFiltroData').appendChild(inputAba);
            }
            inputAba.value = aba;
        }
        document.getElementById('formFiltroData').submit();
    }

    // --- SIDEBAR MOBILE ---
    function abrirSidebarMobile() {
        document.getElementById('sidebar-overlay').classList.remove('hidden');
        document.getElementById('sidebar-mobile').classList.remove('-translate-x-full');
    }
    function fecharSidebarMobile() {
        document.getElementById('sidebar-overlay').classList.add('hidden');
        document.getElementById('sidebar-mobile').classList.add('-translate-x-full');
    }

    // --- NAVEGAÇÃO POR ABAS (SIDEBAR) ---
    function alternarAba(nomeAba) {
        document.querySelectorAll('.conteudo-aba').forEach(el => {
            el.classList.add('hidden');
            el.classList.remove('aba-animate');
        });

        document.querySelectorAll('nav button').forEach(btn => {
            btn.classList.remove('bg-white', 'text-[#064e3b]', 'shadow-md', 'font-semibold');
            btn.classList.add('text-emerald-100', 'hover:bg-emerald-800/50', 'font-medium');
        });

        const abaAlvo = document.getElementById(`aba-${nomeAba}`);
        if (abaAlvo) {
            abaAlvo.classList.remove('hidden');
            abaAlvo.style.opacity = '0';
            requestAnimationFrame(() => { abaAlvo.classList.add('aba-animate'); });
        }

        const btnAtivo = document.getElementById(`nav-${nomeAba}`);
        if (btnAtivo) {
            btnAtivo.classList.add('bg-white', 'text-[#064e3b]', 'shadow-md', 'font-semibold');
            btnAtivo.classList.remove('text-emerald-100', 'hover:bg-emerald-800/50', 'font-medium');
        }
        const btnMobAtivo = document.getElementById(`nav-mob-${nomeAba}`);
        if (btnMobAtivo) {
            btnMobAtivo.classList.add('bg-white', 'text-[#064e3b]', 'shadow-md', 'font-semibold');
            btnMobAtivo.classList.remove('text-emerald-100', 'hover:bg-emerald-800/50', 'font-medium');
        }

        const titulos = {
            'dashboard': 'Dashboard & Gráficos',
            'lancamentos': 'Lançamentos & Histórico',
            'planejamento': 'Planejamento Financeiro',
            'contas-pagar': 'Contas a Pagar',
            'contas-receber': 'Contas a Receber'
        };
        document.getElementById('titulo-pagina-ativa').innerText = titulos[nomeAba] || 'Painel';

        const url = new URL(window.location);
        url.searchParams.set('aba', nomeAba);
        window.history.replaceState({}, '', url);

        if (nomeAba === 'dashboard') carregarGraficos();
        if (nomeAba === 'contas-pagar') carregarContasPagar();
        if (nomeAba === 'contas-receber') carregarContasReceber();
    }

    // --- GRÁFICOS ---
    async function carregarGraficos() {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const params = new URLSearchParams();
            const mes = urlParams.get('mes');
            const ano = urlParams.get('ano');
            if (mes) params.set('mes', mes);
            if (ano) params.set('ano', ano);

            const qs = params.toString();
            const response = await fetch(`/api/graficos-dados/${qs ? '?' + qs : ''}`);
            if (!response.ok) return;

            const data = await response.json();

            const ctxTipos = document.getElementById('chartTipos').getContext('2d');
            const coreTipos = data.resumo_tipo.labels.map(label =>
                label === 'RECEITA' ? '#059669' : '#E11D48'
            );

            if (chartTiposInstance) chartTiposInstance.destroy();
            chartTiposInstance = new Chart(ctxTipos, {
                type: 'doughnut',
                data: {
                    labels: data.resumo_tipo.labels,
                    datasets: [{ data: data.resumo_tipo.valores, backgroundColor: coreTipos, borderWidth: 2, borderColor: '#ffffff' }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom' }, tooltip: { callbacks: { label: ctx => `${ctx.label}: R$ ${(ctx.raw || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}` } } },
                    cutout: '70%'
                }
            });

            const ctxCategorias = document.getElementById('chartCategorias').getContext('2d');
            if (chartCategoriasInstance) chartCategoriasInstance.destroy();
            chartCategoriasInstance = new Chart(ctxCategorias, {
                type: 'bar',
                data: {
                    labels: data.categorias.labels,
                    datasets: [{ label: 'Gasto Total (R$)', data: data.categorias.valores, backgroundColor: '#E11D48', borderRadius: 4 }]
                },
                options: {
                    indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `Total: R$ ${(ctx.raw || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}` } } },
                    scales: { x: { grid: { color: '#f3f4f6' }, ticks: { callback: v => 'R$ ' + v } }, y: { grid: { display: false } } }
                }
            });
        } catch (error) { console.error('Erro ao renderizar gráficos:', error); }
    }

    // --- MODAIS: ABERTURA / FECHAMENTO ---
    function fecharModalSalario() { document.getElementById('modalSalario').classList.add('hidden'); }
    function abrirModalSalario()  { document.getElementById('modalSalario').classList.remove('hidden'); }
    function abrirModalMeta()     { document.getElementById('modalMeta').classList.remove('hidden'); }
    function fecharModalMeta()    { document.getElementById('modalMeta').classList.add('hidden'); document.getElementById('formMeta').reset(); }

    function abrirModalEdicao(id, descricao, valor, tipo) {
        document.getElementById('editId').value = id;
        document.getElementById('editDescricao').value = descricao;
        document.getElementById('editValor').value = parseFloat(String(valor).replace(',', '.'));
        if (tipo === 'RECEITA') document.getElementById('editTipoReceita').checked = true;
        else document.getElementById('editTipoDespesa').checked = true;
        document.getElementById('modalEditar').classList.remove('hidden');
    }
    function fecharModalEdicao() { document.getElementById('modalEditar').classList.add('hidden'); }

    function abrirModalEditarMeta(id, titulo, valorObjetivo, valorAtual, prazoMeses) {
        document.getElementById('editMetaId').value = id;
        document.getElementById('editMetaTitulo').value = titulo;
        document.getElementById('editMetaValorObjetivo').value = parseFloat(String(valorObjetivo).replace(',', '.'));
        document.getElementById('editMetaValorAtual').value = parseFloat(String(valorAtual).replace(',', '.')) || 0;
        document.getElementById('editMetaPrazoMeses').value = parseInt(prazoMeses);
        document.getElementById('modalEditarMeta').classList.remove('hidden');
    }
    function fecharModalEditarMeta() { document.getElementById('modalEditarMeta').classList.add('hidden'); }

    // --- MODAL DELETAR CONTA ---
    function abrirModalDeletarConta() {
        document.getElementById('senhaDeletarConta').value = '';
        document.getElementById('modalDeletarConta').classList.remove('hidden');
    }
    function fecharModalDeletarConta() {
        document.getElementById('modalDeletarConta').classList.add('hidden');
        document.getElementById('senhaDeletarConta').value = '';
    }

    document.getElementById('formDeletarConta').addEventListener('submit', async function (e) {
        e.preventDefault();
        const senha = document.getElementById('senhaDeletarConta').value;
        if (!senha) { mostrarToast('Digite sua senha para confirmar.', 'erro'); return; }
        try {
            const formData = new FormData();
            formData.append('senha', senha);
            const response = await fetch('/api/deletar-conta/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
                body: formData
            });
            const data = await response.json();
            if (response.ok) {
                mostrarToast(data.mensagem, 'sucesso');
                setTimeout(() => { window.location.href = '/login/'; }, 1500);
            } else {
                mostrarToast(data.erro || 'Erro ao deletar conta.', 'erro');
            }
        } catch { mostrarToast('Erro de conexao.', 'erro'); }
    });

    // --- FORMULÁRIOS: SUBMISSÃO API ---

    // Salvar Salário
    document.getElementById('formSalario').addEventListener('submit', async function (e) {
        e.preventDefault();
        const salarioVal = parseFloat(document.getElementById('inputSalario').value);
        if (isNaN(salarioVal) || salarioVal <= 0) { mostrarToast('Insira um valor válido.', 'erro'); return; }
        try {
            const response = await fetch('/api/orcamento/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify({ renda_mensal: salarioVal })
            });
            if (response.ok) window.location.reload();
            else { const d = await response.json(); mostrarToast(`Erro: ${JSON.stringify(d)}`, 'erro'); }
        } catch { mostrarToast('Erro ao conectar com o servidor.', 'erro'); }
    });

    // Salvar Meta
    document.getElementById('formMeta').addEventListener('submit', async function (e) {
        e.preventDefault();
        const valorObjetivo = parseFloat(document.getElementById('metaValorAlvo').value) || 0;
        const valorAtual = parseFloat(document.getElementById('metaValorAtual').value) || 0;
        const prazoMeses = parseInt(document.getElementById('metaPrazoMeses').value) || 1;
        const payload = {
            titulo: document.getElementById('metaTitulo').value,
            valor_objetivo: valorObjetivo, valor_atual: valorAtual,
            aporte_mensal_desejado: parseFloat(((valorObjetivo - valorAtual) / prazoMeses).toFixed(2)),
            prazo_meses: prazoMeses
        };
        try {
            const response = await fetch('/api/metas/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify(payload)
            });
            if (response.ok) window.location.reload();
            else { const d = await response.json(); mostrarToast(`Erro: ${JSON.stringify(d)}`, 'erro'); }
        } catch { mostrarToast('Erro de conexão.', 'erro'); }
    });

    // Editar Meta
    document.getElementById('formEditarMeta').addEventListener('submit', async function (e) {
        e.preventDefault();
        const id = document.getElementById('editMetaId').value;
        const valorObjetivo = parseFloat(document.getElementById('editMetaValorObjetivo').value);
        const valorAtual = parseFloat(document.getElementById('editMetaValorAtual').value) || 0;
        const prazoMeses = parseInt(document.getElementById('editMetaPrazoMeses').value);
        const payload = {
            titulo: document.getElementById('editMetaTitulo').value,
            valor_objetivo: valorObjetivo, valor_atual: valorAtual,
            aporte_mensal_desejado: parseFloat(((valorObjetivo - valorAtual) / prazoMeses).toFixed(2)),
            prazo_meses: prazoMeses
        };
        try {
            const response = await fetch(`/api/metas/${id}/`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify(payload)
            });
            if (response.ok) window.location.reload();
            else { const d = await response.json(); mostrarToast(`Erro: ${JSON.stringify(d)}`, 'erro'); }
        } catch { mostrarToast('Erro de conexão.', 'erro'); }
    });

    // Adicionar Transação
    document.getElementById('formTransacao').addEventListener('submit', async function (e) {
        e.preventDefault();
        const payload = {
            descricao: document.getElementById('descricao').value,
            valor: parseFloat(document.getElementById('valor').value),
            tipo: document.querySelector('input[name="tipo_radio"]:checked').value,
            data: new Date().toLocaleDateString('sv-SE'),
            categoria: document.getElementById('categoria').value,
        };
        try {
            const response = await fetch('/api/transacoes/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify(payload)
            });
            if (response.ok) window.location.reload();
            else { const d = await response.json(); mostrarToast(`Erro: ${JSON.stringify(d)}`, 'erro'); }
        } catch { mostrarToast('Erro de conexão.', 'erro'); }
    });

    // Editar Transação
    document.getElementById('formEditarTransacao').addEventListener('submit', async function (e) {
        e.preventDefault();
        const id = document.getElementById('editId').value;
        const payload = {
            descricao: document.getElementById('editDescricao').value,
            valor: parseFloat(document.getElementById('editValor').value),
            tipo: document.querySelector('input[name="editTipo"]:checked').value,
        };
        try {
            const response = await fetch(`/api/transacoes/${id}/`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify(payload)
            });
            if (response.ok) window.location.reload();
            else { const d = await response.json(); mostrarToast(`Erro: ${JSON.stringify(d)}`, 'erro'); }
        } catch { mostrarToast('Erro de conexão.', 'erro'); }
    });

    // Deletar Transação
    async function deletarTransacao(id) {
        if (!await confirmarAcao('Tem certeza que deseja excluir esta transação?')) return;
        try {
            const response = await fetch(`/api/transacoes/${id}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (response.ok) window.location.reload();
            else mostrarToast('Erro ao excluir.', 'erro');
        } catch { mostrarToast('Erro de conexão.', 'erro'); }
    }

    // Deletar Meta
    async function deletarMeta(id) {
        if (!await confirmarAcao('Tem certeza que deseja excluir esta meta?')) return;
        try {
            const response = await fetch(`/api/metas/${id}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (response.ok) window.location.reload();
            else mostrarToast('Erro ao excluir.', 'erro');
        } catch { mostrarToast('Erro de conexão.', 'erro'); }
    }

    // Deletar Todas Transações
    async function deletarTodasTransacoes() {
        if (!await confirmarAcao('Tem certeza que deseja excluir TODAS as suas transações?')) return;
        try {
            const response = await fetch('/api/transacoes/limpar_todas/', {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (response.ok) { const d = await response.json(); mostrarToast(d.mensagem, 'sucesso'); window.location.reload(); }
            else mostrarToast('Erro ao excluir.', 'erro');
        } catch { mostrarToast('Erro de conexão.', 'erro'); }
    }

    // ==========================================
    // CONTAS A PAGAR
    // ==========================================

    async function carregarContasPagar() {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const params = new URLSearchParams();
            const mes = urlParams.get('mes');
            const ano = urlParams.get('ano');
            if (mes) params.set('mes', mes);
            if (ano) params.set('ano', ano);
            const qs = params.toString();
            const response = await fetch(`/api/contas-pagar/${qs ? '?' + qs : ''}`);
            if (!response.ok) return;

            const contas = await response.json();
            const tabela = document.getElementById('tabelaContasPagar');
            const hoje = new Date(); hoje.setHours(0, 0, 0, 0);
            let totalPendente = 0, qtdVencidas = 0;

            if (contas.length === 0) {
                tabela.innerHTML = '<tr><td colspan="7" class="px-4 py-8 text-center text-slate-400">Nenhuma conta encontrada.</td></tr>';
            } else {
                tabela.innerHTML = contas.map(conta => {
                    const venc = new Date(conta.data_vencimento + 'T00:00:00');
                    let badge = '';
                    if (conta.paga) badge = '<span class="text-xs font-bold px-3 py-1 rounded-full bg-emerald-100 text-emerald-700">Paga</span>';
                    else if (venc < hoje) { badge = '<span class="text-xs font-bold px-3 py-1 rounded-full bg-rose-100 text-rose-700">Vencida</span>'; totalPendente += parseFloat(conta.valor); qtdVencidas++; }
                    else if (venc.getTime() === hoje.getTime()) { badge = '<span class="text-xs font-bold px-3 py-1 rounded-full bg-amber-100 text-amber-700">Vence Hoje</span>'; totalPendente += parseFloat(conta.valor); qtdVencidas++; }
                    else { badge = '<span class="text-xs font-bold px-3 py-1 rounded-full bg-sky-100 text-sky-700">A Vencer</span>'; totalPendente += parseFloat(conta.valor); }

                    const valorStr = parseFloat(conta.valor).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
                    const desc = escapeHtml(conta.descricao);
                    const cat = escapeHtml(conta.categoria);
                    const descAttr = conta.descricao.replace(/'/g, "\\'").replace(/"/g, '&quot;');
                    let acoes = '';
                    if (!conta.paga) acoes += `<button onclick="darBaixaConta('${conta.id}')" class="text-emerald-600 hover:text-emerald-800 text-xs font-medium" title="Dar Baixa"><i data-lucide="check-circle-2" class="w-3 h-3 inline"></i> Pagar</button> `;
                    acoes += `<button onclick="abrirModalEditarContaPagar('${conta.id}', '${descAttr}', '${conta.valor}', '${conta.data_vencimento}', '${escapeHtml(conta.categoria)}', ${conta.recorrente})" class="text-slate-400 hover:text-emerald-600 transition text-xs" title="Editar"><i data-lucide="pencil" class="w-3 h-3 inline"></i> Editar</button> `;
                    acoes += `<button onclick="deletarContaPagar('${conta.id}')" class="text-slate-400 hover:text-rose-600 transition text-xs" title="Excluir"><i data-lucide="trash-2" class="w-3 h-3 inline"></i> Excluir</button>`;

                    return `<tr class="hover:bg-slate-50/50 transition">
                        <td class="px-4 py-3">${badge}</td>
                        <td class="px-4 py-3 font-medium text-slate-800">${desc}</td>
                        <td class="px-4 py-3 text-slate-600">${cat}</td>
                        <td class="px-4 py-3 text-slate-600">${venc.toLocaleDateString('pt-BR')}</td>
                        <td class="px-4 py-3 text-right font-medium text-slate-800">${valorStr}</td>
                        <td class="px-4 py-3 text-center text-slate-600">${conta.recorrente ? 'Sim' : '—'}</td>
                        <td class="px-4 py-3 text-center space-x-2">${acoes}</td>
                    </tr>`;
                }).join('');
            }
            document.getElementById('totalPendenteContas').textContent = totalPendente.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
            document.getElementById('qtdVencidasContas').textContent = qtdVencidas;
            lucide.createIcons();
        } catch (error) { console.error('Erro ao carregar contas a pagar:', error); }
    }

    function abrirModalContaPagar() {
        document.getElementById('contaPagarId').value = '';
        document.getElementById('contaPagarDescricao').value = '';
        document.getElementById('contaPagarValor').value = '';
        document.getElementById('contaPagarVencimento').value = '';
        document.getElementById('contaPagarCategoria').value = 'Outros';
        document.getElementById('contaPagarRecorrente').checked = false;
        document.getElementById('tituloModalContaPagar').textContent = 'Nova Conta a Pagar';
        document.getElementById('modalContaPagar').classList.remove('hidden');
    }
    function fecharModalContaPagar() { document.getElementById('modalContaPagar').classList.add('hidden'); }

    function abrirModalEditarContaPagar(id, descricao, valor, vencimento, categoria, recorrente) {
        document.getElementById('contaPagarId').value = id;
        document.getElementById('contaPagarDescricao').value = descricao;
        document.getElementById('contaPagarValor').value = valor;
        document.getElementById('contaPagarVencimento').value = vencimento;
        document.getElementById('contaPagarCategoria').value = categoria;
        document.getElementById('contaPagarRecorrente').checked = recorrente;
        document.getElementById('tituloModalContaPagar').textContent = 'Editar Conta a Pagar';
        document.getElementById('modalContaPagar').classList.remove('hidden');
    }

    async function salvarContaPagar(event) {
        event.preventDefault();
        const id = document.getElementById('contaPagarId').value;
        const payload = {
            descricao: document.getElementById('contaPagarDescricao').value,
            valor: parseFloat(document.getElementById('contaPagarValor').value),
            data_vencimento: document.getElementById('contaPagarVencimento').value,
            categoria: document.getElementById('contaPagarCategoria').value,
            recorrente: document.getElementById('contaPagarRecorrente').checked,
        };
        const isEdicao = id !== '';
        try {
            const response = await fetch(isEdicao ? `/api/contas-pagar/${id}/` : '/api/contas-pagar/', {
                method: isEdicao ? 'PATCH' : 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfTokenContas(), 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify(payload)
            });
            if (response.ok) { fecharModalContaPagar(); mostrarToast(isEdicao ? 'Conta atualizada!' : 'Conta criada!', 'sucesso'); carregarContasPagar(); }
            else { const e = await response.json(); mostrarToast('Erro: ' + JSON.stringify(e), 'erro'); }
        } catch { mostrarToast('Erro de conexão.', 'erro'); }
    }

    async function darBaixaConta(id) {
        try {
            const response = await fetch(`/api/contas-pagar/${id}/dar_baixa/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrfTokenContas(), 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (response.ok) { mostrarToast('Conta liquidada!', 'sucesso'); carregarContasPagar(); }
            else { const e = await response.json(); mostrarToast(e.erro || 'Erro ao dar baixa.', 'erro'); }
        } catch { mostrarToast('Erro de conexão.', 'erro'); }
    }

    async function deletarContaPagar(id) {
        if (!await confirmarAcao('Excluir esta conta a pagar?')) return;
        try {
            const response = await fetch(`/api/contas-pagar/${id}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCsrfTokenContas(), 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (response.ok) { mostrarToast('Conta excluída!', 'sucesso'); carregarContasPagar(); }
            else mostrarToast('Erro ao excluir.', 'erro');
        } catch { mostrarToast('Erro de conexão.', 'erro'); }
    }

    // ==========================================
    // CONTAS A RECEBER
    // ==========================================

    async function carregarContasReceber() {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const params = new URLSearchParams();
            const mes = urlParams.get('mes');
            const ano = urlParams.get('ano');
            if (mes) params.set('mes', mes);
            if (ano) params.set('ano', ano);
            const qs = params.toString();
            const response = await fetch(`/api/contas-receber/${qs ? '?' + qs : ''}`);
            if (!response.ok) return;

            const contas = await response.json();
            const tabela = document.getElementById('tabelaContasReceber');
            const hoje = new Date(); hoje.setHours(0, 0, 0, 0);
            let totalPendente = 0, qtdAtrasadas = 0;

            if (contas.length === 0) {
                tabela.innerHTML = '<tr><td colspan="7" class="px-4 py-8 text-center text-slate-400">Nenhuma conta encontrada.</td></tr>';
            } else {
                tabela.innerHTML = contas.map(conta => {
                    const receb = new Date(conta.data_recebimento + 'T00:00:00');
                    let badge = '';
                    if (conta.recebida) badge = '<span class="text-xs font-bold px-3 py-1 rounded-full bg-emerald-100 text-emerald-700">Recebida</span>';
                    else if (receb < hoje) { badge = '<span class="text-xs font-bold px-3 py-1 rounded-full bg-rose-100 text-rose-700">Atrasada</span>'; totalPendente += parseFloat(conta.valor); qtdAtrasadas++; }
                    else if (receb.getTime() === hoje.getTime()) { badge = '<span class="text-xs font-bold px-3 py-1 rounded-full bg-amber-100 text-amber-700">Vence Hoje</span>'; totalPendente += parseFloat(conta.valor); qtdAtrasadas++; }
                    else { badge = '<span class="text-xs font-bold px-3 py-1 rounded-full bg-sky-100 text-sky-700">A Receber</span>'; totalPendente += parseFloat(conta.valor); }

                    const valorStr = parseFloat(conta.valor).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
                    const desc = escapeHtml(conta.descricao);
                    const cat = escapeHtml(conta.categoria);
                    const descAttr = conta.descricao.replace(/'/g, "\\'").replace(/"/g, '&quot;');
                    let acoes = '';
                    if (!conta.recebida) acoes += `<button onclick="darBaixaReceber('${conta.id}')" class="text-emerald-600 hover:text-emerald-800 text-xs font-medium" title="Receber"><i data-lucide="check-circle-2" class="w-3 h-3 inline"></i> Receber</button> `;
                    acoes += `<button onclick="abrirModalEditarContaReceber('${conta.id}', '${descAttr}', '${conta.valor}', '${conta.data_recebimento}', '${escapeHtml(conta.categoria)}', ${conta.recorrente})" class="text-slate-400 hover:text-emerald-600 transition text-xs" title="Editar"><i data-lucide="pencil" class="w-3 h-3 inline"></i> Editar</button> `;
                    acoes += `<button onclick="deletarContaReceber('${conta.id}')" class="text-slate-400 hover:text-rose-600 transition text-xs" title="Excluir"><i data-lucide="trash-2" class="w-3 h-3 inline"></i> Excluir</button>`;

                    return `<tr class="hover:bg-slate-50/50 transition">
                        <td class="px-4 py-3">${badge}</td>
                        <td class="px-4 py-3 font-medium text-slate-800">${desc}</td>
                        <td class="px-4 py-3 text-slate-600">${cat}</td>
                        <td class="px-4 py-3 text-slate-600">${receb.toLocaleDateString('pt-BR')}</td>
                        <td class="px-4 py-3 text-right font-medium text-slate-800">${valorStr}</td>
                        <td class="px-4 py-3 text-center text-slate-600">${conta.recorrente ? 'Sim' : '—'}</td>
                        <td class="px-4 py-3 text-center space-x-2">${acoes}</td>
                    </tr>`;
                }).join('');
            }
            document.getElementById('totalPendenteReceber').textContent = totalPendente.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
            document.getElementById('qtdAtrasadasReceber').textContent = qtdAtrasadas;
            lucide.createIcons();
        } catch (error) { console.error('Erro ao carregar contas a receber:', error); }
    }

    function abrirModalContaReceber() {
        document.getElementById('contaReceberId').value = '';
        document.getElementById('contaReceberDescricao').value = '';
        document.getElementById('contaReceberValor').value = '';
        document.getElementById('contaReceberRecebimento').value = '';
        document.getElementById('contaReceberCategoria').value = 'Outros';
        document.getElementById('contaReceberRecorrente').checked = false;
        document.getElementById('tituloModalContaReceber').textContent = 'Nova Conta a Receber';
        document.getElementById('modalContaReceber').classList.remove('hidden');
    }
    function fecharModalContaReceber() { document.getElementById('modalContaReceber').classList.add('hidden'); }

    function abrirModalEditarContaReceber(id, descricao, valor, recebimento, categoria, recorrente) {
        document.getElementById('contaReceberId').value = id;
        document.getElementById('contaReceberDescricao').value = descricao;
        document.getElementById('contaReceberValor').value = valor;
        document.getElementById('contaReceberRecebimento').value = recebimento;
        document.getElementById('contaReceberCategoria').value = categoria;
        document.getElementById('contaReceberRecorrente').checked = recorrente;
        document.getElementById('tituloModalContaReceber').textContent = 'Editar Conta a Receber';
        document.getElementById('modalContaReceber').classList.remove('hidden');
    }

    async function salvarContaReceber(event) {
        event.preventDefault();
        const id = document.getElementById('contaReceberId').value;
        const payload = {
            descricao: document.getElementById('contaReceberDescricao').value,
            valor: parseFloat(document.getElementById('contaReceberValor').value),
            data_recebimento: document.getElementById('contaReceberRecebimento').value,
            categoria: document.getElementById('contaReceberCategoria').value,
            recorrente: document.getElementById('contaReceberRecorrente').checked,
        };
        const isEdicao = id !== '';
        try {
            const response = await fetch(isEdicao ? `/api/contas-receber/${id}/` : '/api/contas-receber/', {
                method: isEdicao ? 'PATCH' : 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfTokenContas(), 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify(payload)
            });
            if (response.ok) { fecharModalContaReceber(); mostrarToast(isEdicao ? 'Conta atualizada!' : 'Conta criada!', 'sucesso'); carregarContasReceber(); }
            else { const e = await response.json(); mostrarToast('Erro: ' + JSON.stringify(e), 'erro'); }
        } catch { mostrarToast('Erro de conexão.', 'erro'); }
    }

    async function darBaixaReceber(id) {
        try {
            const response = await fetch(`/api/contas-receber/${id}/dar_baixa/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrfTokenContas(), 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (response.ok) { mostrarToast('Conta recebida!', 'sucesso'); carregarContasReceber(); }
            else { const e = await response.json(); mostrarToast(e.erro || 'Erro ao receber.', 'erro'); }
        } catch { mostrarToast('Erro de conexão.', 'erro'); }
    }

    async function deletarContaReceber(id) {
        if (!await confirmarAcao('Excluir esta conta a receber?')) return;
        try {
            const response = await fetch(`/api/contas-receber/${id}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCsrfTokenContas(), 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (response.ok) { mostrarToast('Conta excluída!', 'sucesso'); carregarContasReceber(); }
            else mostrarToast('Erro ao excluir.', 'erro');
        } catch { mostrarToast('Erro de conexão.', 'erro'); }
    }

    // ==========================================
    // IMPORTAÇÃO DE EXTRATO
    // ==========================================

    function abrirModalImportacao() { document.getElementById('modalImportacao').classList.remove('hidden'); }
    function fecharModalImportacao() {
        document.getElementById('modalImportacao').classList.add('hidden');
        document.getElementById('formImportarExtrato').reset();
        document.getElementById('nomeArquivoSelecionado').innerText = 'Clique para selecionar o arquivo';
        arquivoImportacaoSelecionado = null;
    }
    function atualizarNomeArquivo(input) {
        if (input.files && input.files[0]) document.getElementById('nomeArquivoSelecionado').innerText = input.files[0].name;
    }

    let arquivoImportacaoSelecionado = null;

    async function enviarArquivoExtrato(confirmar) {
        const btnEnviar = document.getElementById('btnEnviarImportacao');
        btnEnviar.innerText = 'Processando...'; btnEnviar.disabled = true;
        const formData = new FormData();
        formData.append('extrato', arquivoImportacaoSelecionado);
        formData.append('banco', document.getElementById('selectBanco').value);
        if (confirmar) formData.append('confirmar', 'true');
        try {
            const response = await fetch('/api/importar-extrato/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
                body: formData
            });
            const data = await response.json();
            if (response.status === 409 && data.ja_importado) { document.getElementById('modalConfirmarImportacao').classList.remove('hidden'); return; }
            if (response.ok) { mostrarToast(data.mensagem, 'sucesso'); window.location.reload(); }
            else mostrarToast(`Erro: ${data.erro}`, 'erro');
        } catch { mostrarToast('Erro de conexão.', 'erro'); }
        finally { btnEnviar.innerText = 'Processar e Salvar'; btnEnviar.disabled = false; }
    }

    document.getElementById('formImportarExtrato').addEventListener('submit', async function (e) {
        e.preventDefault();
        const inputArquivo = document.getElementById('inputArquivoExtrato');
        if (!inputArquivo.files.length) { mostrarToast('Selecione um arquivo.', 'erro'); return; }
        arquivoImportacaoSelecionado = inputArquivo.files[0];
        await enviarArquivoExtrato(false);
    });

    document.getElementById('btnConfirmarImportacaoSim').addEventListener('click', async function () {
        document.getElementById('modalConfirmarImportacao').classList.add('hidden');
        await enviarArquivoExtrato(true);
    });
    document.getElementById('btnConfirmarImportacaoNao').addEventListener('click', function () {
        document.getElementById('modalConfirmarImportacao').classList.add('hidden');
    });

    // ==========================================
    // INICIALIZAÇÃO
    // ==========================================

    document.addEventListener('DOMContentLoaded', () => {
        const urlParams = new URLSearchParams(window.location.search);
        const aba = urlParams.get('aba');
        if (aba && aba !== 'dashboard') {
            alternarAba(aba);
        } else {
            carregarGraficos();
        }
        if (aba === 'contas-pagar' || !aba) carregarContasPagar();
        if (aba === 'contas-receber' || !aba) carregarContasReceber();
        lucide.createIcons();
    });
