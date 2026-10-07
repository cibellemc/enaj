// Chamadas à API de inscrições (/api) e utilidades compartilhadas entre as páginas.

export const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
export const MSG_SEM_CONEXAO = 'Não foi possível conectar. Verifique sua conexão e tente novamente.';

async function requisitar(caminho, opcoes = {}) {
    const resposta = await fetch('/api' + caminho, {
        headers: { 'Content-Type': 'application/json' },
        ...opcoes,
    });
    const dados = await resposta.json().catch(() => ({}));
    return { ok: resposta.ok && dados.ok === true, status: resposta.status, dados };
}

export const buscarOpcoes = () => requisitar('/opcoes');

export const criarInscricao = (inscricao) =>
    requisitar('/inscricoes', { method: 'POST', body: JSON.stringify(inscricao) });

export const buscarInscricao = (codigo) => requisitar('/inscricoes/' + encodeURIComponent(codigo));

export const acessarPorEmail = (email) =>
    requisitar('/inscricoes/acesso', { method: 'POST', body: JSON.stringify({ email }) });

export const codigoDaUrl = () => new URLSearchParams(location.search).get('c') || '';

export const urlDoCard = (codigo) => 'confirmacao.html?c=' + encodeURIComponent(codigo);

export const urlDeValidacao = (codigo) =>
    new URL('validar.html?c=' + encodeURIComponent(codigo), location.href).href;

export const formatarNumero = (numero) => 'Nº ' + String(numero).padStart(4, '0');

export const montarEquipe = (inscricao) =>
    [...inscricao.integrantes, ...(inscricao.integrantes_outro ? [inscricao.integrantes_outro] : [])].join(', ');

/** Mostra só o bloco `ativo` entre os ids informados (carregando, erro, conteúdo...). */
export function mostrarSomente(ids, ativo) {
    ids.forEach((id) => {
        const elemento = document.getElementById(id);
        elemento.classList.toggle('hidden', id !== ativo);
        elemento.classList.toggle('flex', id === ativo);
    });
}
