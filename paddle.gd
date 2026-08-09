extends Node2D

@export var move_up_action: String = "left_up"
@export var move_down_action: String = "left_down"
@export var speed: float = 450.0

var screen_height: float = 648.0
var half_height: float = 50.0

func _ready() -> void:
	screen_height = get_viewport_rect().size.y

func _process(delta: float) -> void:
	var direction := 0.0
	if Input.is_action_pressed(move_up_action):
		direction -= 1.0
	if Input.is_action_pressed(move_down_action):
		direction += 1.0

	position.y += direction * speed * delta
	position.y = clamp(position.y, half_height, screen_height - half_height)
