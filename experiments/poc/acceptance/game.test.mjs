import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';

// Candidate code is never imported into the assertion/reporting process.
function call(name,args,randomValue=null) {
  const child=spawnSync('/node',['--experimental-vm-modules','/acceptance/logic_runner.mjs'],{
    input:JSON.stringify({name,args,randomValue}),encoding:'utf8',timeout:3000,maxBuffer:65536,env:{}});
  assert.equal(child.status,0,'Candidate runner failed: '+(child.stderr||'').slice(-1500));
  const value=JSON.parse(child.stdout);
  assert.deepEqual(value.after,args,'Input mutation'); return value.result;
}
const move=(...args)=>call('move',args);
const getStatus=(...args)=>call('getStatus',args);
function spawn(board,rng) {
  return call('spawn',[board],rng());
}

const board = row => [row, [0,0,0,0], [0,0,0,0], [0,0,0,0]];
let count = 0;
for (const [input, expected, score] of [
  [[2,2,2,2], [4,4,0,0], 8],
  [[2,2,4,0], [4,4,0,0], 4],
  [[0,2,0,2], [4,0,0,0], 4],
  [[4,4,8,8], [8,16,0,0], 24],
  [[2,4,8,16], [2,4,8,16], 0],
  [[0,0,0,0], [0,0,0,0], 0],
  [[2,2,4,4], [4,8,0,0], 12],
]) {
  const original = board(input); const frozen = JSON.stringify(original);
  const result = move(original, 'left');
  assert.deepEqual(result.board, board(expected));
  assert.equal(result.score, score);
  assert.equal(result.moved, JSON.stringify(original) !== JSON.stringify(result.board));
  assert.equal(JSON.stringify(original), frozen); count++;
}
assert.deepEqual(move(board([2,2,2,2]), 'right').board[0], [0,0,4,4]); count++;
const vertical = [[2,0,0,0],[2,0,0,0],[2,0,0,0],[2,0,0,0]];
assert.deepEqual(move(vertical,'up').board.map(r=>r[0]), [4,4,0,0]); count++;
assert.deepEqual(move(vertical,'down').board.map(r=>r[0]), [0,0,4,4]); count++;
assert.deepEqual(getStatus(board([2048,0,0,0])), {won:true,lost:false}); count++;
const full = [[2,4,2,4],[4,2,4,2],[2,4,2,4],[4,2,4,2]];
assert.deepEqual(getStatus(full), {won:false,lost:true}); count++;
const open = structuredClone(full); open[3][3]=0;
assert.equal(getStatus(open).lost, false); count++;
const mergeable = structuredClone(full); mergeable[0][1]=2;
assert.equal(getStatus(mergeable).lost, false); count++;
for (const direction of ['left','right','up','down']) {
  const result = move(full, direction);
  assert.equal(result.moved, false); assert.equal(result.score, 0);
  assert.deepEqual(result.board,full); count++;
}
const empty = board([0,0,0,0]);
const spawned = spawn(empty,()=>0);
assert.equal(spawned.flat().filter(Boolean).length,1); assert.equal(spawned[0][0],2);
assert.equal(empty.flat().filter(Boolean).length,0); count++;
assert.equal(spawn(empty,()=>.99)[3][3],4); count++;
assert.deepEqual(spawn(full,()=>0),full); count++;
// Conservation of tile values for every direction over deterministic pseudo-random boards.
for (let seed=1; seed<=32; seed++) {
  const input=Array.from({length:4},(_,r)=>Array.from({length:4},(_,c)=>[0,2,4,8][(seed*(r+1)+c*3)%4]));
  for (const direction of ['left','right','up','down']) {
    const result=move(input,direction);
    assert.equal(result.board.flat().reduce((a,b)=>a+b,0),input.flat().reduce((a,b)=>a+b,0));
    assert.equal(result.board.length,4); assert.ok(result.board.every(r=>r.length===4)); count++;
  }
}
console.log(JSON.stringify({passed:true, cases:count}));
