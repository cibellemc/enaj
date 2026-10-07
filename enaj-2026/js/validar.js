// Validação de entrada: página aberta pelo QR code do card.

import { buscarInscricao, codigoDaUrl, formatarNumero, montarEquipe, mostrarSomente } from './api.js';

const ESTADOS = ['v-carregando', 'v-valida', 'v-invalida'];

async function iniciar() {
    const { ok, dados } = await buscarInscricao(codigoDaUrl()).catch(() => ({ ok: false }));
    if (!ok) {
        mostrarSomente(ESTADOS, 'v-invalida');
        return;
    }

    const inscricao = dados.inscricao;
    document.getElementById('v-numero').textContent = formatarNumero(inscricao.numero);
    document.getElementById('v-nome').textContent = inscricao.nome_presidente;
    document.getElementById('v-junta').textContent = inscricao.junta;
    document.getElementById('v-equipe').textContent = montarEquipe(inscricao);
    mostrarSomente(ESTADOS, 'v-valida');
}

iniciar();
