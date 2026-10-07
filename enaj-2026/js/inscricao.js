// Página de inscrição: monta as opções, valida, envia e dá acesso ao card pelo e-mail.

import {
    EMAIL_RE,
    MSG_SEM_CONEXAO,
    acessarPorEmail,
    buscarOpcoes,
    criarInscricao,
    urlDoCard,
} from './api.js';

const CARGO_OUTRO = 'Outro';
const HORARIO_RE = /^([01]\d|2[0-3]):[0-5]\d$/;

// Textos de cada trecho do bloco "Chegada e saída de Goiânia"
const TRECHOS = {
    chegada: {
        titulo: 'Chegada a Goiânia',
        icone: 'flight_land',
        rotuloVoo: 'Voo de chegada',
        rotuloHorario: { aereo: 'Horário do voo', terrestre: 'Horário previsto de chegada' },
    },
    saida: {
        titulo: 'Saída de Goiânia',
        icone: 'flight_takeoff',
        rotuloVoo: 'Voo de volta',
        rotuloHorario: { aereo: 'Horário do voo', terrestre: 'Horário previsto de saída' },
    },
};
const CAMPOS_TRECHO = ['data', 'transporte', 'voo', 'operadora', 'horario'];

const form = document.getElementById('form-inscricao');
const botaoEnviar = document.getElementById('form-enviar');
const erroGeral = document.getElementById('form-erro-geral');

// ===== Montagem do formulário (opções vindas de /api/opcoes) =====

function criarOpcao(idTemplate, valor, campos, nome) {
    const opcao = document.getElementById(idTemplate).content.cloneNode(true);
    const input = opcao.querySelector('input');
    input.value = valor;
    if (nome) input.name = nome;
    Object.entries(campos).forEach(([campo, texto]) => {
        opcao.querySelector(`[data-campo="${campo}"]`).textContent = texto;
    });
    return opcao;
}

function mostrar(elemento, visivel, display = 'block') {
    elemento.classList.toggle('hidden', !visivel);
    elemento.classList.toggle(display, visivel);
}

function montarCargos(cargos) {
    const container = document.getElementById('opcoes-cargos');
    [...cargos, CARGO_OUTRO].forEach((cargo) => container.append(criarOpcao('tpl-cargo', cargo, { rotulo: cargo })));

    const blocoOutro = document.getElementById('bloco-cargo-outro');
    container.addEventListener('change', (evento) => {
        mostrar(blocoOutro, evento.target.value === CARGO_OUTRO);
    });
}

function montarTrecho(prefixo, transportes) {
    const textos = TRECHOS[prefixo];
    const bloco = document.getElementById('tpl-trecho').content.cloneNode(true);

    bloco.querySelector('[data-campo="titulo"]').textContent = textos.titulo;
    bloco.querySelector('[data-campo="icone"]').textContent = textos.icone;
    bloco.querySelector('[data-campo="rotulo-voo"]').textContent = textos.rotuloVoo;

    // data-nome="voo" vira name/id "chegada_voo" no input, for no label e data-erro na mensagem
    bloco.querySelectorAll('[data-nome]').forEach((elemento) => {
        const nome = `${prefixo}_${elemento.dataset.nome}`;
        if (elemento.matches('input')) {
            elemento.name = nome;
            elemento.id = nome;
        } else if (elemento.matches('label')) {
            elemento.htmlFor = nome;
        } else if (elemento.matches('.campo-erro')) {
            elemento.dataset.erro = nome;
        }
    });

    const opcoesTransporte = bloco.querySelector('.opcoes-transporte');
    transportes.forEach((t) => {
        opcoesTransporte.append(
            criarOpcao('tpl-transporte', t.valor, { rotulo: t.rotulo, icone: t.icone }, `${prefixo}_transporte`)
        );
    });

    const trecho = bloco.querySelector('.trecho');
    opcoesTransporte.addEventListener('change', (evento) => {
        const transporte = evento.target.value;
        mostrar(trecho.querySelector('.dados-aereo'), transporte === 'aereo', 'grid');
        mostrar(trecho.querySelector('.bloco-horario'), true);
        trecho.querySelector('.rotulo-horario').textContent = textos.rotuloHorario[transporte];
    });

    document.getElementById(`trecho-${prefixo}`).append(bloco);
}

async function montarFormulario() {
    const { ok, dados } = await buscarOpcoes().catch(() => ({ ok: false }));
    if (!ok) {
        mostrarErroGeral('Não foi possível carregar o formulário. Recarregue a página.');
        botaoEnviar.disabled = true;
        return;
    }
    document.getElementById('opcoes-juntas').append(
        ...dados.juntas.map((j) => criarOpcao('tpl-junta', j.valor, { sigla: j.sigla, estado: j.estado }))
    );
    montarCargos(dados.cargos);
    Object.keys(TRECHOS).forEach((prefixo) => montarTrecho(prefixo, dados.transportes));
    document.getElementById('opcoes-visita').append(
        ...dados.visita_pirenopolis.map((v) => criarOpcao('tpl-visita', v.valor, { rotulo: v.rotulo, icone: v.icone }))
    );
}

// ===== Leitura e validação =====

function lerFormulario() {
    const fd = new FormData(form);
    const ler = (campo) => (fd.get(campo) || '').trim();
    const campos = ['nome', 'email', 'junta', 'cargo', 'cargo_outro', 'visita_pirenopolis', 'site'];
    Object.keys(TRECHOS).forEach((prefixo) => {
        CAMPOS_TRECHO.forEach((campo) => campos.push(`${prefixo}_${campo}`));
    });
    return Object.fromEntries(campos.map((campo) => [campo, ler(campo)]));
}

function validarTrecho(dados, prefixo, erros) {
    const campo = (nome) => `${prefixo}_${nome}`;
    if (!dados[campo('data')]) erros[campo('data')] = 'Informe a data.';
    if (!dados[campo('transporte')]) {
        erros[campo('transporte')] = 'Selecione o meio de transporte.';
        return;
    }
    if (dados[campo('transporte')] === 'aereo') {
        if (!dados[campo('voo')]) erros[campo('voo')] = 'Informe o número do voo.';
        if (!dados[campo('operadora')]) erros[campo('operadora')] = 'Informe a companhia aérea.';
    }
    if (!HORARIO_RE.test(dados[campo('horario')])) erros[campo('horario')] = 'Informe o horário.';
}

function validar(dados) {
    const erros = {};
    if (!dados.nome) erros.nome = 'Informe seu nome.';
    if (!EMAIL_RE.test(dados.email)) erros.email = 'Informe um e-mail válido.';
    if (!dados.junta) erros.junta = 'Selecione a Junta Comercial que representa.';
    if (!dados.cargo) erros.cargo = 'Selecione o seu cargo.';
    if (dados.cargo === CARGO_OUTRO && !dados.cargo_outro) erros.cargo_outro = 'Informe qual é o seu cargo.';
    Object.keys(TRECHOS).forEach((prefixo) => validarTrecho(dados, prefixo, erros));
    if (dados.chegada_data && dados.saida_data && dados.saida_data < dados.chegada_data) {
        erros.saida_data = 'A saída não pode ser antes da chegada.';
    }
    if (!dados.visita_pirenopolis) erros.visita_pirenopolis = 'Selecione uma opção.';
    return erros;
}

function mostrarErrosDosCampos(erros) {
    document.querySelectorAll('.campo-erro').forEach((elemento) => {
        const mensagem = erros[elemento.dataset.erro] || '';
        elemento.textContent = mensagem;
        elemento.classList.toggle('hidden', !mensagem);
    });
    const primeiro = document.querySelector('.campo-erro:not(.hidden)');
    primeiro?.closest('.trecho, .etapa').scrollIntoView({ behavior: 'smooth', block: 'center' });
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

form.addEventListener('submit', enviar);
formAcesso.addEventListener('submit', acessar);

document.querySelectorAll('[data-abrir-acesso]').forEach((botao) => botao.addEventListener('click', () => abrirAcesso()));
document.querySelector('[data-fechar-acesso]').addEventListener('click', () => dialogo.close());
dialogo.addEventListener('click', (evento) => {
    if (evento.target === dialogo) dialogo.close();
});

montarFormulario();
if (location.hash === '#acesso') abrirAcesso();
