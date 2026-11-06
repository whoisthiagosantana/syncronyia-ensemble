import { move, spawn, getStatus } from './game.mjs';

const cells = Array.from(document.querySelectorAll('[data-testid="board"] [data-testid="cell"]'));
const scoreElement = document.querySelector('[data-testid="score"]');
const statusElement = document.querySelector('[data-testid="status"]');
const restartButton = document.querySelector('[data-testid="restart"]');
const directions = {
  ArrowLeft: 'left',
  ArrowRight: 'right',
  ArrowUp: 'up',
  ArrowDown: 'down'
};

let board;
let score;

function render() {
  board.flat().forEach((value, index) => {
    cells[index].textContent = value === 0 ? '' : String(value);
    cells[index].dataset.value = String(value);
    cells[index].setAttribute('aria-label', value === 0 ? 'Empty' : String(value));
  });
  scoreElement.textContent = String(score);
  const { won, lost } = getStatus(board);
  statusElement.textContent = won && lost
    ? 'You win! You reached 2048. Game over!'
    : won
      ? 'You win! You reached 2048.'
      : lost
        ? 'Game over! No moves left.'
        : 'Use arrow keys or the buttons to play.';
}

function newGame() {
  board = Array.from({ length: 4 }, () => [0, 0, 0, 0]);
  board = spawn(spawn(board));
  score = 0;
  render();
}

function play(direction) {
  const result = move(board, direction);
  if (!result.moved) return;
  board = spawn(result.board);
  score += result.score;
  render();
}

window.addEventListener('keydown', event => {
  if (event.altKey || event.ctrlKey || event.metaKey) return;
  const direction = directions[event.key];
  if (!direction) return;
  event.preventDefault();
  play(direction);
});

for (const button of document.querySelectorAll('button[data-direction]')) {
  button.addEventListener('click', () => play(button.dataset.direction));
}
restartButton.addEventListener('click', newGame);
newGame();
