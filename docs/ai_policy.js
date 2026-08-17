// Reimplements the trained PPO actor's forward pass by hand, ported from
// game/ai_policy.gd, from weights exported by pong-rl/scripts/export_weights.py
// (see ai_model.json). Plain linear algebra: Linear -> Tanh -> Linear -> Tanh -> Linear -> argmax.

const AIPolicy = (() => {
  const STAY = 0;
  const UP = 1;
  const DOWN = 2;

  const GAME_WIDTH = 1152.0;
  const GAME_HEIGHT = 648.0;
  const BALL_MAX_SPEED = 800.0;

  function clamp(v, lo, hi) {
    return Math.min(hi, Math.max(lo, v));
  }

  function linearTanh(x, weight, bias) {
    const out = new Array(weight.length);
    for (let i = 0; i < weight.length; i++) {
      const row = weight[i];
      let sum = bias[i];
      for (let j = 0; j < row.length; j++) sum += row[j] * x[j];
      out[i] = Math.tanh(sum);
    }
    return out;
  }

  function linear(x, weight, bias) {
    const out = new Array(weight.length);
    for (let i = 0; i < weight.length; i++) {
      const row = weight[i];
      let sum = bias[i];
      for (let j = 0; j < row.length; j++) sum += row[j] * x[j];
      out[i] = sum;
    }
    return out;
  }

  class AIPolicy {
    constructor() {
      this._layers = [];
      this._outputWeight = [];
      this._outputBias = [];
      this._loaded = false;
    }

    async loadModel(path) {
      const res = await fetch(path);
      if (!res.ok) {
        console.error(`AIPolicy: could not fetch ${path}`);
        return false;
      }
      const data = await res.json();
      this._layers = data.layers;
      this._outputWeight = data.output_layer.weight;
      this._outputBias = data.output_layer.bias;
      this._loaded = true;
      return true;
    }

    // Returns STAY/UP/DOWN given the same 6-feature observation contract used in
    // training: [ball_x, ball_y, ball_vx, ball_vy, my_paddle_y, opponent_paddle_y].
    chooseAction(observation) {
      if (!this._loaded) return STAY;

      let x = observation;
      for (const layer of this._layers) {
        x = linearTanh(x, layer.weight, layer.bias);
      }

      const logits = linear(x, this._outputWeight, this._outputBias);

      let bestIndex = 0;
      let bestValue = logits[0];
      for (let i = 1; i < logits.length; i++) {
        if (logits[i] > bestValue) {
          bestValue = logits[i];
          bestIndex = i;
        }
      }
      return bestIndex;
    }

    // Builds the normalized observation for a paddle controlled by this policy.
    // `mirrored` should be true when this policy controls the RIGHT paddle,
    // since the model was only ever trained playing the LEFT paddle.
    static buildObservation(ballPos, ballVel, myPaddleY, opponentPaddleY, mirrored) {
      let ballX = ballPos.x;
      let ballVx = ballVel.x;
      if (mirrored) {
        ballX = GAME_WIDTH - ballX;
        ballVx = -ballVx;
      }

      return [
        clamp(ballX / GAME_WIDTH, 0.0, 1.0),
        clamp(ballPos.y / GAME_HEIGHT, 0.0, 1.0),
        clamp(ballVx / BALL_MAX_SPEED, -1.0, 1.0),
        clamp(ballVel.y / BALL_MAX_SPEED, -1.0, 1.0),
        clamp(myPaddleY / GAME_HEIGHT, 0.0, 1.0),
        clamp(opponentPaddleY / GAME_HEIGHT, 0.0, 1.0),
      ];
    }
  }

  AIPolicy.STAY = STAY;
  AIPolicy.UP = UP;
  AIPolicy.DOWN = DOWN;

  return AIPolicy;
})();
