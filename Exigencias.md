Preciso de duas melhorias visuais e de UX no meu arquivo HTML/JS (Django template) sem usar frameworks como React. Siga as orientações abaixo:

1. Aumentar o Tempo de Transição entre Telas (Abas):
- Ajuste a alternância de abas (`alternarAba`) para que a transição entre os conteúdos não seja instantânea.
- Adicione uma animação de transição suave em CSS (fade-in com opacidade e suave deslocamento vertical) ao alternar entre as abas (#aba-dashboard, #aba-transacoes, #aba-planejamento).
- O tempo da animação deve ser perceptível, durando cerca de 0.5 a 0.8 segundos.

2. Sistema de Notificações em Toast (Substituir os alert() nativos):
- Crie um container fixo para Toasts no canto superior direito da tela (`top-5 right-5 z-50`).
- Crie uma função JavaScript global `mostrarToast(mensagem, tipo = 'sucesso')` que renderiza dinamicamente um card de aviso moderno (estilo React Toastify).
- O Toast deve suportar dois estilos:
  * Sucesso (fundo ou borda verde/teal)
  * Erro (fundo ou borda vermelha/rose)
- O Toast deve ter uma animação suave de entrada (slide/fade) e desaparecer automaticamente após 4 segundos, ou ao clicar no botão de fechar (x).
- Substitua TODOS os `alert()` do projeto por chamadas para essa nova função `mostrarToast()`.

Exemplo de estrutura esperada para a função de Toast:
function mostrarToast(mensagem, tipo = 'sucesso') {
  // Cria elemento div do toast dinamicamente
  // Aplica classes do Tailwind CSS (sombra, animação, cores)
  // Adiciona ao container e define temporizador para remover
}

Por favor, forneça o código ajustado e indique onde inserir o CSS e a estrutura das notificações.