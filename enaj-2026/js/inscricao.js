// Página de inscrição: monta as opções, valida, envia e dá acesso ao card pelo e-mail.

import {
    EMAIL_RE,
    MSG_SEM_CONEXAO,
    acessarPorEmail,
    buscarOpcoes,
    criarInscricao,
    urlDoCard,
} from './api.js';

const INTEGRANTE_OUTRO = 'Outro';

const form = document.getElementById('form-inscricao');
const botaoEnviar = document.getElementById('form-enviar');
const erroGeral = document.getElementById('form-erro-geral');
const outroCheck = document.getElementById('integrantes-outro-check');
const outroTexto = document.getElementById('integrantes-outro');

// ===== Opções do formulário (vindas de /api/opcoes) =====

function criarOpcao(idTemplate, valor, campos) {
    const opcao = document.getElementById(idTemplate).content.cloneNode(true);
    opcao.querySelector('input').value = valor;
    Object.entries(campos).forEach(([campo, texto]) => {
        opcao.querySelector(`[data-campo="${campo}"]`).textContent = texto;
    });
    return opcao;
}

async function montarOpcoes() {
    const { ok, dados } = await buscarOpcoes().catch(() => ({ ok: false }));
    if (!ok) {
        mostrarErroGeral('Não foi possível carregar o formulário. Recarregue a página.');
        botaoEnviar.disabled = true;
        return;
    }
    document.getElementById('opcoes-juntas').append(
        ...dados.juntas.map((j) => criarOpcao('tpl-junta', j.valor, { sigla: j.sigla, estado: j.estado }))
    );
    document.getElementById('opcoes-integrantes').append(
        ...dados.integrantes.map((i) => criarOpcao('tpl-integrante', i, { rotulo: i }))
    );
    document.getElementById('opcoes-visita').append(
        ...dados.visita_pirenopolis.map((v) => criarOpcao('tpl-visita', v.valor, { rotulo: v.rotulo, icone: v.icone }))
    );
}

// ===== Validação e erros =====

function lerFormulario() {
    const fd = new FormData(form);
    return {
        nome_presidente: (fd.get('nome_presidente') || '').trim(),
        email: (fd.get('email') || '').trim(),
        junta: fd.get('junta') || '',
        integrantes: fd.getAll('integrantes'),
        integrantes_outro: (fd.get('integrantes_outro') || '').trim(),
        visita_pirenopolis: fd.get('visita_pirenopolis') || '',
        site: fd.get('site') || '',
    };
}

function validar(dados) {
    const erros = {};
    if (!dados.nome_presidente) erros.nome_presidente = 'Informe o nome do presidente da Junta Comercial.';
    if (!EMAIL_RE.test(dados.email)) erros.email = 'Informe um e-mail válido.';
    if (!dados.junta) erros.junta = 'Selecione a Junta Comercial que representa.';
    if (dados.integrantes.length === 0) erros.integrantes = 'Selecione pelo menos um integrante da equipe.';
    if (!dados.visita_pirenopolis) erros.visita_pirenopolis = 'Selecione uma opção.';
    return erros;
}

function mostrarErrosDosCampos(erros) {
    document.querySelectorAll('.campo-erro').forEach((elemento) => {
        const mensagem = erros[elemento.dataset.erro] || '';
        elemento.textContent = mensagem;
        elemento.classList.toggle('hidden', !mensagem);
        elemento.classList.toggle('flex', Boolean(mensagem));
    });
    const primeiro = Object.keys(erros)[0];
    if (primeiro) {
        document.querySelector(`[data-erro="${primeiro}"]`)
            .closest('.etapa')
            .scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function mostrarErroGeral(mensagem, acao) {
    erroGeral.replaceChildren(mensagem);
    if (acao) {
        const botao = document.createElement('button');
        botao.type = 'button';
        botao.className = 'ml-1 font-bold underline';
        botao.textContent = acao.rotulo;
        botao.addEventListener('click', acao.aoClicar);
        erroGeral.append(botao);
    }
    erroGeral.classList.remove('hidden');
}

// ===== Envio =====

async function enviar(evento) {
    evento.preventDefault();
    erroGeral.classList.add('hidden');

    const dados = lerFormulario();
    const erros = validar(dados);
    mostrarErrosDosCampos(erros);
    if (Object.keys(erros).length) return;

    botaoEnviar.disabled = true;
    try {
        const { ok, dados: resposta } = await criarInscricao(dados);
        if (ok) {
            if (resposta.codigo) location.href = urlDoCard(resposta.codigo);
            return;
        }
        if (resposta.erros) {
            mostrarErrosDosCampos(resposta.erros);
        } else if (resposta.ja_inscrito) {
            mostrarErroGeral(resposta.erro, {
                rotulo: 'Acessar minha inscrição',
                aoClicar: () => abrirAcesso(dados.email),
            });
        } else {
            mostrarErroGeral(resposta.erro || 'Não foi possível enviar. Tente novamente.');
        }
    } catch {
        mostrarErroGeral(MSG_SEM_CONEXAO);
    } finally {
        botaoEnviar.disabled = false;
    }
}

// ===== Acesso à inscrição pelo e-mail =====

const dialogo = document.getElementById('dlg-acesso');
const formAcesso = document.getElementById('form-acesso');
const acessoEmail = document.getElementById('acesso-email');
const acessoErro = document.getElementById('acesso-erro');
const acessoBotao = document.getElementById('acesso-enviar');

function abrirAcesso(email = '') {
    acessoErro.classList.add('hidden');
    if (email) acessoEmail.value = email;
    dialogo.showModal();
    acessoEmail.focus();
}

function mostrarErroAcesso(mensagem) {
    acessoErro.textContent = mensagem;
    acessoErro.classList.remove('hidden');
}

async function acessar(evento) {
    evento.preventDefault();
    const email = acessoEmail.value.trim();
    acessoErro.classList.add('hidden');
    if (!EMAIL_RE.test(email)) {
        mostrarErroAcesso('Informe um e-mail válido.');
        return;
    }

    acessoBotao.disabled = true;
    try {
        const { ok, dados } = await acessarPorEmail(email);
        if (ok) {
            location.href = urlDoCard(dados.codigo);
            return;
        }
        mostrarErroAcesso(dados.erro || 'Não foi possível buscar agora. Tente novamente.');
    } catch {
        mostrarErroAcesso(MSG_SEM_CONEXAO);
    }
    acessoBotao.disabled = false;
}

// ===== Eventos =====

// Preencher "Outros integrantes" marca a opção "Outro" (campo escondido)
outroTexto.addEventListener('input', () => {
    outroCheck.checked = outroTexto.value.trim() !== '';
});
outroCheck.value = INTEGRANTE_OUTRO;

form.addEventListener('submit', enviar);
formAcesso.addEventListener('submit', acessar);

document.querySelectorAll('[data-abrir-acesso]').forEach((botao) => botao.addEventListener('click', () => abrirAcesso()));
document.querySelector('[data-fechar-acesso]').addEventListener('click', () => dialogo.close());
dialogo.addEventListener('click', (evento) => {
    if (evento.target === dialogo) dialogo.close();
});

montarOpcoes();
if (location.hash === '#acesso') abrirAcesso();
