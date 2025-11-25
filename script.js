
function filterEvents() {
    const year = document.getElementById('year').value;
    const status = document.getElementById('status').value;
    const category = document.getElementById('category').value;
    const search = document.getElementById('search').value.toLowerCase();

    const cards = document.querySelectorAll('.event-card');
    const noResultsMsg = document.getElementById('no-results');
    const eventsGrid = document.getElementById('eventsGrid');

    let visibleCount = 0; // Contador de cards visíveis

    cards.forEach(card => {
        const cardYear = card.dataset.year;
        const cardStatus = card.dataset.status;
        const cardCategory = card.dataset.category;
        // Verifica título e também a descrição para busca ficar mais esperta
        const cardContent = card.innerText.toLowerCase();

        let show = true;

        if (year !== 'all' && cardYear !== year) show = false;
        if (status !== 'all' && cardStatus !== status) show = false;
        if (category !== 'all' && cardCategory !== category) show = false;
        // Busca no conteúdo todo do card (título, local, etc)
        if (search && !cardContent.includes(search)) show = false;

        if (show) {
            card.style.display = 'block'; // ou 'flex' dependendo do seu layout original do card
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });

    // Lógica para mostrar/esconder a mensagem de erro
    if (visibleCount === 0) {
        noResultsMsg.style.display = 'block';
        eventsGrid.style.display = 'none'; // Esconde o grid para não ficar espaço vazio
    } else {
        noResultsMsg.style.display = 'none';
        eventsGrid.style.display = 'grid'; // Traz o grid de volta
    }
}

// Adiciona o evento de 'input' para a busca (digitação)
document.getElementById('search').addEventListener('input', filterEvents);

// Adiciona o evento de 'change' para os selects (menus suspensos)
// Assim que mudar a opção, ele filtra automaticamente
document.getElementById('year').addEventListener('change', filterEvents);
document.getElementById('status').addEventListener('change', filterEvents);
document.getElementById('category').addEventListener('change', filterEvents);

