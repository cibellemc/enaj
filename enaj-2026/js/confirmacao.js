// Card de confirmação: mostra a inscrição, gera o QR code e permite baixar o card em PNG.
// As bibliotecas de js/vendor são carregadas sob demanda (o html2canvas só ao baixar).

import {
    buscarInscricao,
    codigoDaUrl,
    formatarNumero,
    montarEquipe,
    mostrarSomente,
    urlDeValidacao,
} from './api.js';

const ESTADOS = ['estado-carregando', 'estado-erro', 'estado-card'];

function carregarScript(src) {
    return new Promise((resolver, rejeitar) => {
        const script = document.createElement('script');
        script.src = src;
        script.onload = resolver;
        script.onerror = rejeitar;
        document.head.append(script);
    });
}

function preencher(id, texto) {
    document.getElementById(id).textContent = texto;
}

async function gerarQrCode(texto) {
    await carregarScript('js/vendor/qrcode.min.js');
    const qr = qrcode(0, 'M');
    qr.addData(texto);
    qr.make();
    return qr.createDataURL(8, 0);
}

async function baixarCard(inscricao, botao) {
    botao.disabled = true;
    try {
        if (!window.html2canvas) await carregarScript('js/vendor/html2canvas.min.js');
        const canvas = await html2canvas(document.getElementById('card'), { scale: 3, backgroundColor: null });
        const link = document.createElement('a');
        link.download = `inscricao-enaj-2026-${String(inscricao.numero).padStart(4, '0')}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
    } finally {
        botao.disabled = false;
    }
}

async function iniciar() {
    const { ok, dados } = await buscarInscricao(codigoDaUrl()).catch(() => ({ ok: false }));
    if (!ok) {
        mostrarSomente(ESTADOS, 'estado-erro');
        return;
    }

    const inscricao = dados.inscricao;
    preencher('c-nome', inscricao.nome_presidente);
    preencher('c-junta', inscricao.junta);
    preencher('c-equipe', montarEquipe(inscricao));
    preencher('c-numero', formatarNumero(inscricao.numero));
    preencher('c-email', inscricao.email);
    preencher('c-visita', inscricao.visita_pirenopolis);
    preencher('c-data', new Date(inscricao.criado_em).toLocaleString('pt-BR', {
        dateStyle: 'short',
        timeStyle: 'short',
        timeZone: 'America/Sao_Paulo',
    }));

    // O QR code abre a página de validação de entrada
    document.getElementById('c-qr').src = await gerarQrCode(urlDeValidacao(inscricao.codigo));

    const botaoBaixar = document.getElementById('btn-baixar');
    botaoBaixar.addEventListener('click', () => baixarCard(inscricao, botaoBaixar));

    mostrarSomente(ESTADOS, 'estado-card');
}

iniciar();
