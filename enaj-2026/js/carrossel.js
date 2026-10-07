// Carrossel do topo da página inicial (mesmo comportamento do ENAJ 2025).

const INTERVALO_MS = 5000;

const container = document.getElementById('carousel-container');
const slides = container.querySelectorAll('.carousel-slide');
const dots = document.querySelectorAll('.carousel-dot');

let atual = 0;
let timerRolagem;
let timerAutomatico;

function irPara(indice) {
    // Rola só o carrossel (scrollIntoView rolaria a página inteira)
    if (slides[indice]) container.scrollTo({ left: slides[indice].offsetLeft, behavior: 'smooth' });
}

function marcarDot(indice) {
    dots.forEach((dot, i) => {
        dot.classList.toggle('bg-accent', i === indice);
        dot.classList.toggle('bg-gray-300', i !== indice);
    });
}

function slideMaisProximo() {
    const centro = container.scrollLeft + container.clientWidth / 2;
    let maisProximo = 0;
    let menorDistancia = Infinity;
    slides.forEach((slide, i) => {
        const distancia = Math.abs(centro - (slide.offsetLeft + slide.offsetWidth / 2));
        if (distancia < menorDistancia) {
            menorDistancia = distancia;
            maisProximo = i;
        }
    });
    return maisProximo;
}

function iniciarAutomatico() {
    pararAutomatico();
    timerAutomatico = setInterval(() => irPara((atual + 1) % slides.length), INTERVALO_MS);
}

function pararAutomatico() {
    clearInterval(timerAutomatico);
}

function navegar(indice) {
    irPara(indice);
    iniciarAutomatico();
}

document.getElementById('carousel-prev').addEventListener('click', () => navegar(Math.max(0, atual - 1)));
document.getElementById('carousel-next').addEventListener('click', () => navegar(Math.min(slides.length - 1, atual + 1)));
dots.forEach((dot) => dot.addEventListener('click', () => navegar(Number(dot.dataset.slideIndex))));

container.addEventListener('scroll', () => {
    clearTimeout(timerRolagem);
    timerRolagem = setTimeout(() => {
        atual = slideMaisProximo();
        marcarDot(atual);
    }, 100);
});

// Pausa enquanto a pessoa interage com o carrossel
container.addEventListener('mouseenter', pararAutomatico);
container.addEventListener('mouseleave', iniciarAutomatico);
container.addEventListener('touchstart', pararAutomatico, { passive: true });

marcarDot(0);
iniciarAutomatico();
