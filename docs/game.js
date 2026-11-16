// Ported from game/game.gd, game/ball.gd, game/paddle.gd.
// Physics and the AI hookup are unchanged from the Godot game; this file adds
// a start screen, on-screen labels and key hints, a countdown, pause,
// a game-over screen, and touch controls.

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const $ = (id) => document.getElementById(id);
const startScreen = $("startScreen");
const pauseScreen = $("pauseScreen");
const overScreen = $("overScreen");
const countdownEl = $("countdown");
const barKeys = $("barKeys");
const pauseBtn = $("pauseBtn");

const WIDTH = canvas.width;   // logical size; the AI was trained on 1152x648
const HEIGHT = canvas.height;
const WIN_SCORE = 5;

const BALL_START_SPEED = 400.0;
const BALL_MAX_SPEED = 800.0;
const BALL_SPEED_INCREASE = 25.0;
const BALL_HALF = 8.0;
const PADDLE_HALF_W = 10.0;
const PADDLE_HALF_H = 50.0;
const PADDLE_SPEED = 450.0;

const LEFT_COLOR = "#22d3ee";
const RIGHT_COLOR = "#f472b6";

const Mode = { PVP: "pvp", PVC: "pvc" };
// "menu" -> "countdown" -> "playing" <-> "paused" -> "over"
let state = "menu";
let mode = null;

let aiPolicy = null;
let aiReady = false;

// ---------------------------------------------------------------- input ---
const keys = new Set();
const GAME_KEYS = new Set(["ArrowUp", "ArrowDown", "Space"]);
window.addEventListener("keydown", (e) => {
  if (GAME_KEYS.has(e.code)) e.preventDefault(); // don't scroll the page
  if (!e.repeat) onKeyPress(e.code);
  keys.add(e.code);
});
window.addEventListener("keyup", (e) => keys.delete(e.code));
window.addEventListener("blur", () => { keys.clear(); if (state === "playing") pause(); });

function onKeyPress(code) {
  if (state === "menu") {
    if (code === "Digit1" || code === "Numpad1") selectMode(Mode.PVP);
    if (code === "Digit2" || code === "Numpad2") selectMode(Mode.PVC);
  } else if (state === "over") {
    if (code === "Space" || code === "Enter") restartGame();
    if (code === "KeyM") showMenu();
  } else if (code === "KeyP" || code === "Escape") {
    if (state === "playing") pause();
    else if (state === "paused") resume();
  }
}

// Touch / mouse drag: the paddle on that half of the table follows your finger.
const touchTargets = { left: null, right: null };
function sideFor(clientX) {
  const r = canvas.getBoundingClientRect();
  return clientX - r.left < r.width / 2 ? "left" : "right";
}
function canvasY(clientY) {
  const r = canvas.getBoundingClientRect();
  return ((clientY - r.top) / r.height) * HEIGHT;
}
const activePointers = new Map(); // pointerId -> side
canvas.addEventListener("pointerdown", (e) => {
  if (state !== "playing" && state !== "countdown") return;
  let side = sideFor(e.clientX);
  if (mode === Mode.PVC) side = "left"; // vs computer: anywhere controls you
  activePointers.set(e.pointerId, side);
  touchTargets[side] = canvasY(e.clientY);
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener("pointermove", (e) => {
  const side = activePointers.get(e.pointerId);
  if (side) touchTargets[side] = canvasY(e.clientY);
});
const endPointer = (e) => {
  const side = activePointers.get(e.pointerId);
  activePointers.delete(e.pointerId);
  if (side && ![...activePointers.values()].includes(side)) touchTargets[side] = null;
};
canvas.addEventListener("pointerup", endPointer);
canvas.addEventListener("pointercancel", endPointer);

// Buttons in the overlays
document.querySelectorAll(".mode").forEach((b) =>
  b.addEventListener("click", () => selectMode(b.dataset.mode)));
document.querySelectorAll('[data-action="menu"]').forEach((b) => b.addEventListener("click", showMenu));
$("resumeBtn").addEventListener("click", resume);
$("againBtn").addEventListener("click", restartGame);
pauseBtn.addEventListener("click", () => (state === "paused" ? resume() : pause()));

// ------------------------------------------------------------- game data ---
function clamp(v, lo, hi) {
  return Math.min(hi, Math.max(lo, v));
}

const ball = { x: WIDTH / 2, y: HEIGHT / 2, vx: 0, vy: 0, moving: false };
const leftPaddle = { x: 40, y: HEIGHT / 2 };
const rightPaddle = { x: WIDTH - 40, y: HEIGHT / 2 };

let leftScore = 0;
let rightScore = 0;
let serveTimer = null;
let playTime = 0; // seconds of play, used to fade the in-game key hints

function resetBall() {
  ball.moving = false;
  ball.x = WIDTH / 2;
  ball.y = HEIGHT / 2;
  ball.vx = 0;
  ball.vy = 0;
}

function launchBall(directionSign) {
  const angle = (Math.random() * 2 - 1) * 0.3;
  const len = Math.hypot(directionSign, angle);
  ball.vx = (directionSign / len) * BALL_START_SPEED;
  ball.vy = (angle / len) * BALL_START_SPEED;
  ball.moving = true;
}

function checkPaddleBounce(paddle) {
  const withinX = Math.abs(ball.x - paddle.x) <= BALL_HALF + PADDLE_HALF_W;
  const withinY = Math.abs(ball.y - paddle.y) <= BALL_HALF + PADDLE_HALF_H;
  if (!(withinX && withinY)) return;

  ball.vx = -ball.vx;
  let speed = Math.hypot(ball.vx, ball.vy) + BALL_SPEED_INCREASE;
  speed = Math.min(speed, BALL_MAX_SPEED);

  const offset = (ball.y - paddle.y) / PADDLE_HALF_H;
  const dirLen = Math.hypot(Math.sign(ball.vx), offset) || 1;
  ball.vx = (Math.sign(ball.vx) / dirLen) * speed;
  ball.vy = (offset / dirLen) * speed;

  ball.x = paddle.x + Math.sign(ball.vx) * (PADDLE_HALF_W + BALL_HALF);
}

function updateBall(dt) {
  if (!ball.moving) return;

  ball.x += ball.vx * dt;
  ball.y += ball.vy * dt;

  if (ball.y - BALL_HALF <= 0) {
    ball.y = BALL_HALF;
    ball.vy = Math.abs(ball.vy);
  } else if (ball.y + BALL_HALF >= HEIGHT) {
    ball.y = HEIGHT - BALL_HALF;
    ball.vy = -Math.abs(ball.vy);
  }

  if (ball.vx < 0) checkPaddleBounce(leftPaddle);
  else checkPaddleBounce(rightPaddle);

  if (ball.x < -BALL_HALF) {
    onGoalScored("right");
    resetBall();
  } else if (ball.x > WIDTH + BALL_HALF) {
    onGoalScored("left");
    resetBall();
  }
}

// Keyboard direction, or follow a touch target at normal paddle speed.
function paddleDir(paddle, up, down, target) {
  if (target !== null) {
    const diff = target - paddle.y;
    return Math.abs(diff) < 4 ? 0 : Math.sign(diff) * Math.min(1, Math.abs(diff) / 20);
  }
  return (down ? 1 : 0) - (up ? 1 : 0);
}

function updatePaddles(dt) {
  // Vs computer the left player may use W/S or the arrow keys.
  const leftUp = keys.has("KeyW") || (mode === Mode.PVC && keys.has("ArrowUp"));
  const leftDown = keys.has("KeyS") || (mode === Mode.PVC && keys.has("ArrowDown"));
  const leftDir = paddleDir(leftPaddle, leftUp, leftDown, touchTargets.left);
  leftPaddle.y = clamp(leftPaddle.y + leftDir * PADDLE_SPEED * dt, PADDLE_HALF_H, HEIGHT - PADDLE_HALF_H);

  let rightDir = 0;
  if (mode === Mode.PVC && aiReady) {
    const obs = AIPolicy.buildObservation(
      { x: ball.x, y: ball.y },
      { x: ball.vx, y: ball.vy },
      rightPaddle.y,
      leftPaddle.y,
      true
    );
    const action = aiPolicy.chooseAction(obs);
    if (action === AIPolicy.UP) rightDir = -1;
    else if (action === AIPolicy.DOWN) rightDir = 1;
  } else {
    rightDir = paddleDir(rightPaddle, keys.has("ArrowUp"), keys.has("ArrowDown"), touchTargets.right);
  }
  rightPaddle.y = clamp(rightPaddle.y + rightDir * PADDLE_SPEED * dt, PADDLE_HALF_H, HEIGHT - PADDLE_HALF_H);
}

// --------------------------------------------------------------- flow ---
function names() {
  return mode === Mode.PVC ? { left: "YOU", right: "AI 🤖" } : { left: "PLAYER 1", right: "PLAYER 2" };
}

function setOverlay(el) {
  [startScreen, pauseScreen, overScreen].forEach((o) => o.classList.toggle("show", o === el));
}

function renderBarKeys() {
  if (!mode) { barKeys.innerHTML = ""; return; }
  barKeys.innerHTML = mode === Mode.PVC
    ? `<span><b style="color:${LEFT_COLOR}">You</b>: <kbd>W</kbd><kbd>S</kbd> or <kbd>↑</kbd><kbd>↓</kbd> · drag on touch</span>`
    : `<span><b style="color:${LEFT_COLOR}">Left</b>: <kbd>W</kbd><kbd>S</kbd></span>
       <span><b style="color:${RIGHT_COLOR}">Right</b>: <kbd>↑</kbd><kbd>↓</kbd></span>`;
  barKeys.innerHTML += `<span>First to ${WIN_SCORE}</span>`;
}

function showMenu() {
  clearTimeout(serveTimer);
  state = "menu";
  mode = null;
  leftScore = rightScore = 0;
  resetBall();
  leftPaddle.y = rightPaddle.y = HEIGHT / 2;
  countdownEl.classList.remove("show");
  pauseBtn.hidden = true;
  renderBarKeys();
  setOverlay(startScreen);
}

async function selectMode(selected) {
  if (state !== "menu") return;
  mode = selected;
  setOverlay(null);
  renderBarKeys();

  if (mode === Mode.PVC && !aiReady) {
    aiPolicy = new AIPolicy();
    aiReady = await aiPolicy.loadModel("ai_model.json");
    if (!aiReady) {
      alert("Could not load the AI model, so this will be a 2-player game.");
      mode = Mode.PVP;
      renderBarKeys();
    }
  }
  restartGame();
}

// 3-2-1 before the first serve, so players can find their keys.
function countdown(then) {
  state = "countdown";
  pauseBtn.hidden = false;
  let n = 3;
  countdownEl.textContent = n;
  countdownEl.classList.add("show");
  const tick = () => {
    n -= 1;
    if (n > 0) {
      countdownEl.textContent = n;
      serveTimer = setTimeout(tick, 700);
    } else {
      countdownEl.textContent = "GO!";
      serveTimer = setTimeout(() => {
        countdownEl.classList.remove("show");
        state = "playing";
        then();
      }, 400);
    }
  };
  serveTimer = setTimeout(tick, 700);
}

function restartGame() {
  clearTimeout(serveTimer);
  leftScore = 0;
  rightScore = 0;
  playTime = 0;
  resetBall();
  setOverlay(null);
  countdown(() => launchBall(Math.random() < 0.5 ? -1 : 1));
}

function onGoalScored(side) {
  if (side === "left") leftScore += 1;
  else rightScore += 1;

  if (leftScore >= WIN_SCORE || rightScore >= WIN_SCORE) {
    endGame(side);
  } else {
    const dir = side === "left" ? -1 : 1; // same serve direction as the Godot game
    serveTimer = setTimeout(() => { if (state === "playing" && !ball.moving) launchBall(dir); }, 1000);
  }
}

function endGame(winningSide) {
  state = "over";
  pauseBtn.hidden = true;
  const n = names();
  let title;
  if (mode === Mode.PVC) title = winningSide === "left" ? "You win! 🎉" : "The AI wins 🤖";
  else title = `${winningSide === "left" ? n.left : n.right} wins! 🎉`;
  $("overTitle").textContent = title;
  $("overScore").textContent = `${n.left} ${leftScore} – ${rightScore} ${n.right}`;
  setOverlay(overScreen);
}

let pausedBallMoving = false;
function pause() {
  if (state !== "playing") return;
  state = "paused";
  pausedBallMoving = ball.moving;
  pauseBtn.innerHTML = "Resume <kbd>P</kbd>";
  setOverlay(pauseScreen);
}
function resume() {
  if (state !== "paused") return;
  state = "playing";
  ball.moving = pausedBallMoving;
  pauseBtn.innerHTML = "Pause <kbd>P</kbd>";
  setOverlay(null);
  // If we paused between points, the pending serve was skipped: serve now.
  if (!ball.moving) {
    clearTimeout(serveTimer);
    serveTimer = setTimeout(() => { if (state === "playing" && !ball.moving) launchBall(Math.random() < 0.5 ? -1 : 1); }, 600);
  }
}

// --------------------------------------------------------------- drawing ---
function drawPaddle(p, color) {
  ctx.save();
  ctx.fillStyle = color;
  ctx.shadowColor = color;
  ctx.shadowBlur = 18;
  ctx.fillRect(p.x - PADDLE_HALF_W, p.y - PADDLE_HALF_H, PADDLE_HALF_W * 2, PADDLE_HALF_H * 2);
  ctx.restore();
}

function drawKeyHint(x, y, labels, color, alpha) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.font = "600 18px ui-monospace, Menlo, monospace";
  ctx.textAlign = "center";
  const w = 34, h = 30, gap = 8;
  const total = labels.length * w + (labels.length - 1) * gap;
  let cx = x - total / 2;
  for (const label of labels) {
    ctx.fillStyle = "#1c1c2b";
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.roundRect(cx, y - h / 2, w, h, 6);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#fff";
    ctx.fillText(label, cx + w / 2, y + 6);
    cx += w + gap;
  }
  ctx.restore();
}

function draw() {
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  // Halves tinted by player colour
  ctx.fillStyle = "rgba(34, 211, 238, 0.035)";
  ctx.fillRect(0, 0, WIDTH / 2, HEIGHT);
  ctx.fillStyle = "rgba(244, 114, 182, 0.035)";
  ctx.fillRect(WIDTH / 2, 0, WIDTH / 2, HEIGHT);

  ctx.strokeStyle = "#333";
  ctx.lineWidth = 3;
  ctx.setLineDash([12, 14]);
  ctx.beginPath();
  ctx.moveTo(WIDTH / 2, 0);
  ctx.lineTo(WIDTH / 2, HEIGHT);
  ctx.stroke();
  ctx.setLineDash([]);

  // Scores and names
  if (mode) {
    const n = names();
    ctx.textAlign = "center";
    ctx.font = "700 64px ui-monospace, Menlo, monospace";
    ctx.fillStyle = LEFT_COLOR;
    ctx.fillText(String(leftScore), WIDTH / 2 - 90, 80);
    ctx.fillStyle = RIGHT_COLOR;
    ctx.fillText(String(rightScore), WIDTH / 2 + 90, 80);
    ctx.font = "600 16px ui-sans-serif, -apple-system, sans-serif";
    ctx.fillStyle = "#9a9ab5";
    ctx.fillText(n.left, WIDTH / 4, 36);
    ctx.fillText(n.right, (WIDTH * 3) / 4, 36);

    // Key hints next to each human paddle: fully visible at the start, fade after ~6s of play
    const alpha = state === "countdown" ? 1 : clamp(1 - (playTime - 6) / 2, 0, 1);
    if (alpha > 0) {
      const leftKeys = mode === Mode.PVC ? ["W", "S", "↑", "↓"] : ["W", "S"];
      drawKeyHint(WIDTH / 4, HEIGHT - 40, leftKeys, LEFT_COLOR, alpha);
      if (mode === Mode.PVP) drawKeyHint((WIDTH * 3) / 4, HEIGHT - 40, ["↑", "↓"], RIGHT_COLOR, alpha);
    }
  }

  drawPaddle(leftPaddle, LEFT_COLOR);
  drawPaddle(rightPaddle, RIGHT_COLOR);

  ctx.save();
  ctx.fillStyle = "#fff";
  ctx.shadowColor = "#fff";
  ctx.shadowBlur = 14;
  ctx.fillRect(ball.x - BALL_HALF, ball.y - BALL_HALF, BALL_HALF * 2, BALL_HALF * 2);
  ctx.restore();
}

let lastTime = performance.now();
function loop(now) {
  const dt = Math.min((now - lastTime) / 1000, 1 / 30);
  lastTime = now;

  if (state === "playing") {
    playTime += dt;
    updatePaddles(dt);
    updateBall(dt);
  } else if (state === "countdown") {
    updatePaddles(dt); // let players get into position
  }
  draw();

  requestAnimationFrame(loop);
}

renderBarKeys();
requestAnimationFrame(loop);
