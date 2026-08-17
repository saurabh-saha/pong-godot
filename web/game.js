// Ported from game/game.gd, game/ball.gd, game/paddle.gd.

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const msgEl = document.getElementById("msg");

const WIDTH = canvas.width;
const HEIGHT = canvas.height;
const WIN_SCORE = 5;

const BALL_START_SPEED = 400.0;
const BALL_MAX_SPEED = 800.0;
const BALL_SPEED_INCREASE = 25.0;
const BALL_HALF = 8.0;
const PADDLE_HALF_W = 10.0;
const PADDLE_HALF_H = 50.0;
const PADDLE_SPEED = 450.0;

const Mode = { PVP: "pvp", PVC: "pvc" };

const keys = new Set();
window.addEventListener("keydown", (e) => keys.add(e.code));
window.addEventListener("keyup", (e) => keys.delete(e.code));

function clamp(v, lo, hi) {
  return Math.min(hi, Math.max(lo, v));
}

const ball = {
  x: WIDTH / 2,
  y: HEIGHT / 2,
  vx: 0,
  vy: 0,
  moving: false,
};

const leftPaddle = { x: 40, y: HEIGHT / 2 };
const rightPaddle = { x: WIDTH - 40, y: HEIGHT / 2 };

let leftScore = 0;
let rightScore = 0;
let gameOver = false;
let modeSelected = false;
let mode = null;

let aiPolicy = null;
let aiReady = false;

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

function updatePaddles(dt) {
  let leftDir = 0;
  if (keys.has("KeyW")) leftDir -= 1;
  if (keys.has("KeyS")) leftDir += 1;
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
    if (keys.has("ArrowUp")) rightDir -= 1;
    if (keys.has("ArrowDown")) rightDir += 1;
  }
  rightPaddle.y = clamp(rightPaddle.y + rightDir * PADDLE_SPEED * dt, PADDLE_HALF_H, HEIGHT - PADDLE_HALF_H);
}

function onGoalScored(side) {
  if (side === "left") leftScore += 1;
  else rightScore += 1;

  if (leftScore >= WIN_SCORE || rightScore >= WIN_SCORE) {
    endGame(side);
  } else {
    const dir = side === "left" ? -1 : 1;
    setTimeout(() => startRound(dir), 1000);
  }
}

function startRound(directionSign) {
  resetBall();
  launchBall(directionSign);
}

function endGame(winningSide) {
  gameOver = true;
  const winnerName = winningSide === "left" ? "Left Player" : "Right Player";
  msgEl.textContent = `${winnerName} Wins!\nPress Space to Restart`;
}

function restartGame() {
  leftScore = 0;
  rightScore = 0;
  gameOver = false;
  msgEl.textContent = "";
  startRound(1);
}

async function selectMode(selected) {
  modeSelected = true;
  mode = selected;
  msgEl.textContent = "";

  if (mode === Mode.PVC) {
    aiPolicy = new AIPolicy();
    aiReady = await aiPolicy.loadModel("ai_model.json");
    if (!aiReady) {
      msgEl.textContent = "Could not load AI model, playing Player vs Player";
      mode = Mode.PVP;
    }
  }

  startRound(1);
}

let prevKeyState = { one: false, two: false, space: false };
function handleModeAndRestartInput() {
  const one = keys.has("Digit1");
  const two = keys.has("Digit2");
  const space = keys.has("Space");

  if (!modeSelected) {
    if (one && !prevKeyState.one) selectMode(Mode.PVP);
    else if (two && !prevKeyState.two) selectMode(Mode.PVC);
  } else if (gameOver && space && !prevKeyState.space) {
    restartGame();
  }

  prevKeyState = { one, two, space };
}

function draw() {
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  ctx.strokeStyle = "#444";
  ctx.setLineDash([10, 10]);
  ctx.beginPath();
  ctx.moveTo(WIDTH / 2, 0);
  ctx.lineTo(WIDTH / 2, HEIGHT);
  ctx.stroke();
  ctx.setLineDash([]);

  ctx.fillStyle = "#fff";
  ctx.fillRect(leftPaddle.x - PADDLE_HALF_W, leftPaddle.y - PADDLE_HALF_H, PADDLE_HALF_W * 2, PADDLE_HALF_H * 2);
  ctx.fillRect(rightPaddle.x - PADDLE_HALF_W, rightPaddle.y - PADDLE_HALF_H, PADDLE_HALF_W * 2, PADDLE_HALF_H * 2);

  ctx.fillRect(ball.x - BALL_HALF, ball.y - BALL_HALF, BALL_HALF * 2, BALL_HALF * 2);

  ctx.font = "48px monospace";
  ctx.fillText(String(leftScore), WIDTH / 2 - 80, 60);
  ctx.fillText(String(rightScore), WIDTH / 2 + 50, 60);

  if (!modeSelected) {
    msgEl.textContent = "Press 1: Player vs Player\nPress 2: Player vs Computer";
  }
}

let lastTime = performance.now();
function loop(now) {
  const dt = Math.min((now - lastTime) / 1000, 1 / 30);
  lastTime = now;

  handleModeAndRestartInput();
  if (modeSelected && !gameOver) {
    updatePaddles(dt);
    updateBall(dt);
  }
  draw();

  requestAnimationFrame(loop);
}

requestAnimationFrame(loop);
