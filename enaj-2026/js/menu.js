// Abre e fecha o menu no celular (usado em todas as páginas).

const botao = document.getElementById('menu-toggle');
const menu = document.getElementById('mobile-menu');

botao?.addEventListener('click', () => menu.classList.toggle('hidden'));
