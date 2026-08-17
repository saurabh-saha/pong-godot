extends Node2D

@export var move_up_action: String = "left_up"
@export var move_down_action: String = "left_down"
@export var speed: float = 450.0

## When true, this paddle ignores input and is driven by ai_policy instead.
var ai_controlled: bool = false
var ai_policy: AIPolicy = null
var ball: Node2D = null
var opponent_paddle: Node2D = null
var is_right_side: bool = false

var screen_height: float = 648.0
var half_height: float = 50.0

func _ready() -> void:
	screen_height = get_viewport_rect().size.y

func _process(delta: float) -> void:
	var direction := 0.0

	if ai_controlled and ai_policy != null and ball != null:
		var observation := AIPolicy.build_observation(
			ball.position, ball.velocity, position.y, opponent_paddle.position.y, is_right_side
		)
		var action := ai_policy.choose_action(observation)
		if action == AIPolicy.UP:
			direction = -1.0
		elif action == AIPolicy.DOWN:
			direction = 1.0
	else:
		if Input.is_action_pressed(move_up_action):
			direction -= 1.0
		if Input.is_action_pressed(move_down_action):
			direction += 1.0

	position.y += direction * speed * delta
	position.y = clamp(position.y, half_height, screen_height - half_height)
