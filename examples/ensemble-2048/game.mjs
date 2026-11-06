function copyBoard(board) {
  return board.map(row => row.slice());
}

function slide(line) {
  const tiles = line.filter(value => value !== 0);
  const result = [];
  let score = 0;

  for (let i = 0; i < tiles.length; i += 1) {
    if (i + 1 < tiles.length && tiles[i] === tiles[i + 1]) {
      const merged = tiles[i] * 2;
      result.push(merged);
      score += merged;
      i += 1;
    } else {
      result.push(tiles[i]);
    }
  }

  while (result.length < 4) result.push(0);
  return { line: result, score };
}

export function move(board, direction) {
  const next = copyBoard(board);
  if (!['left', 'right', 'up', 'down'].includes(direction)) {
    return { board: next, score: 0, moved: false };
  }

  let score = 0;
  for (let fixed = 0; fixed < 4; fixed += 1) {
    const positions = [];
    for (let offset = 0; offset < 4; offset += 1) {
      if (direction === 'left') positions.push([fixed, offset]);
      else if (direction === 'right') positions.push([fixed, 3 - offset]);
      else if (direction === 'up') positions.push([offset, fixed]);
      else positions.push([3 - offset, fixed]);
    }

    const { line, score: lineScore } = slide(positions.map(([row, col]) => board[row][col]));
    score += lineScore;
    positions.forEach(([row, col], index) => { next[row][col] = line[index]; });
  }

  const moved = next.some((row, rowIndex) => row.some((value, colIndex) => value !== board[rowIndex][colIndex]));
  return { board: next, score, moved };
}

export function spawn(board, rng = Math.random) {
  const next = copyBoard(board);
  const empty = [];
  for (let row = 0; row < 4; row += 1) {
    for (let col = 0; col < 4; col += 1) {
      if (next[row][col] === 0) empty.push([row, col]);
    }
  }
  if (empty.length === 0) return next;

  const randomCell = rng();
  const index = Math.min(empty.length - 1, Math.max(0, Math.floor(randomCell * empty.length)));
  const [row, col] = empty[index];
  next[row][col] = rng() < 0.9 ? 2 : 4;
  return next;
}

export function getStatus(board) {
  let won = false;
  let lost = true;
  for (let row = 0; row < 4; row += 1) {
    for (let col = 0; col < 4; col += 1) {
      const value = board[row][col];
      if (value >= 2048) won = true;
      if (value === 0 || (col < 3 && value === board[row][col + 1]) || (row < 3 && value === board[row + 1][col])) lost = false;
    }
  }
  return { won, lost };
}
