extends RefCounted
class_name AIPolicy

## Reimplements the trained PPO actor's forward pass by hand, from weights
## exported by pong-rl/scripts/export_weights.py (see ai_model.json).
## Godot has no PyTorch/SB3 runtime, so this is plain linear algebra:
## Linear -> Tanh -> Linear -> Tanh -> Linear -> argmax.

const STAY := 0
const UP := 1
const DOWN := 2

const GAME_WIDTH := 1152.0
const GAME_HEIGHT := 648.0
const BALL_MAX_SPEED := 800.0

var _layers: Array = []
var _output_weight: Array = []
var _output_bias: Array = []
var _loaded: bool = false

func load_model(path: String) -> bool:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("AIPolicy: could not open %s" % path)
		return false

	var data = JSON.parse_string(file.get_as_text())
	if data == null:
		push_error("AIPolicy: could not parse %s" % path)
		return false

	_layers = data["layers"]
	_output_weight = data["output_layer"]["weight"]
	_output_bias = data["output_layer"]["bias"]
	_loaded = true
	return true

func _linear_tanh(x: Array, weight: Array, bias: Array) -> Array:
	var output := []
	output.resize(weight.size())
	for i in range(weight.size()):
		var row: Array = weight[i]
		var sum: float = bias[i]
		for j in range(row.size()):
			sum += row[j] * x[j]
		output[i] = tanh(sum)
	return output

func _linear(x: Array, weight: Array, bias: Array) -> Array:
	var output := []
	output.resize(weight.size())
	for i in range(weight.size()):
		var row: Array = weight[i]
		var sum: float = bias[i]
		for j in range(row.size()):
			sum += row[j] * x[j]
		output[i] = sum
	return output

## Returns STAY/UP/DOWN given the same 6-feature observation contract used in
## training: [ball_x, ball_y, ball_vx, ball_vy, my_paddle_y, opponent_paddle_y],
## normalized the same way as pong_rl/env.py.
func choose_action(observation: Array) -> int:
	if not _loaded:
		return STAY

	var x := observation
	for layer in _layers:
		x = _linear_tanh(x, layer["weight"], layer["bias"])

	var logits := _linear(x, _output_weight, _output_bias)

	var best_index := 0
	var best_value: float = logits[0]
	for i in range(1, logits.size()):
		if logits[i] > best_value:
			best_value = logits[i]
			best_index = i
	return best_index

## Builds the normalized observation for a paddle controlled by this policy.
## `mirrored` should be true when this policy controls the RIGHT paddle,
## since the model was only ever trained playing the LEFT paddle — mirroring
## the x-axis reframes "right paddle" as "my paddle" from the model's point of view,
## exactly like pong_rl/env.py's build_observation(for_left=False) does.
static func build_observation(
	ball_position: Vector2,
	ball_velocity: Vector2,
	my_paddle_y: float,
	opponent_paddle_y: float,
	mirrored: bool
) -> Array:
	var ball_x := ball_position.x
	var ball_vx := ball_velocity.x
	if mirrored:
		ball_x = GAME_WIDTH - ball_x
		ball_vx = -ball_vx

	return [
		clamp(ball_x / GAME_WIDTH, 0.0, 1.0),
		clamp(ball_position.y / GAME_HEIGHT, 0.0, 1.0),
		clamp(ball_vx / BALL_MAX_SPEED, -1.0, 1.0),
		clamp(ball_velocity.y / BALL_MAX_SPEED, -1.0, 1.0),
		clamp(my_paddle_y / GAME_HEIGHT, 0.0, 1.0),
		clamp(opponent_paddle_y / GAME_HEIGHT, 0.0, 1.0),
	]
