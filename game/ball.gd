extends Node2D

signal goal_scored(scoring_side: String)

@export var left_paddle_path: NodePath
@export var right_paddle_path: NodePath

const START_SPEED: float = 400.0
const MAX_SPEED: float = 800.0
const SPEED_INCREASE: float = 25.0

const HALF_SIZE := Vector2(8.0, 8.0)
const PADDLE_HALF_SIZE := Vector2(10.0, 50.0)

var velocity: Vector2 = Vector2.ZERO
var screen_size: Vector2 = Vector2(1152, 648)
var moving: bool = false

@onready var left_paddle: Node2D = get_node(left_paddle_path)
@onready var right_paddle: Node2D = get_node(right_paddle_path)

func _ready() -> void:
	screen_size = get_viewport_rect().size

func _process(delta: float) -> void:
	if not moving:
		return

	position += velocity * delta

	if position.y - HALF_SIZE.y <= 0.0:
		position.y = HALF_SIZE.y
		velocity.y = abs(velocity.y)
	elif position.y + HALF_SIZE.y >= screen_size.y:
		position.y = screen_size.y - HALF_SIZE.y
		velocity.y = -abs(velocity.y)

	if velocity.x < 0.0:
		_check_paddle_bounce(left_paddle)
	else:
		_check_paddle_bounce(right_paddle)

	if position.x < -HALF_SIZE.x:
		goal_scored.emit("right")
		reset_ball()
	elif position.x > screen_size.x + HALF_SIZE.x:
		goal_scored.emit("left")
		reset_ball()

func _check_paddle_bounce(paddle: Node2D) -> void:
	var within_x: bool = absf(position.x - paddle.position.x) <= (HALF_SIZE.x + PADDLE_HALF_SIZE.x)
	var within_y: bool = absf(position.y - paddle.position.y) <= (HALF_SIZE.y + PADDLE_HALF_SIZE.y)
	if within_x and within_y:
		velocity.x = -velocity.x
		var speed := velocity.length() + SPEED_INCREASE
		speed = min(speed, MAX_SPEED)

		var offset := (position.y - paddle.position.y) / PADDLE_HALF_SIZE.y
		var direction := Vector2(sign(velocity.x), offset).normalized()
		velocity = direction * speed

		position.x = paddle.position.x + sign(velocity.x) * (PADDLE_HALF_SIZE.x + HALF_SIZE.x)

func reset_ball() -> void:
	moving = false
	position = screen_size / 2.0
	velocity = Vector2.ZERO

func launch(direction_sign: int = 1) -> void:
	var angle := randf_range(-0.3, 0.3)
	velocity = Vector2(direction_sign, angle).normalized() * START_SPEED
	moving = true
