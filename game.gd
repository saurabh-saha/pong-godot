extends Node2D

const WIN_SCORE: int = 5

enum Mode { PLAYER_VS_PLAYER, PLAYER_VS_COMPUTER }

@onready var ball: Node2D = $Ball
@onready var left_paddle: Node2D = $LeftPaddle
@onready var right_paddle: Node2D = $RightPaddle
@onready var left_score_label: Label = $UI/LeftScore
@onready var right_score_label: Label = $UI/RightScore
@onready var message_label: Label = $UI/Message

var left_score: int = 0
var right_score: int = 0
var game_over: bool = false
var mode_selected: bool = false

func _ready() -> void:
	ball.goal_scored.connect(_on_goal_scored)
	message_label.text = "Press 1: Player vs Player\nPress 2: Player vs Computer"

func _process(_delta: float) -> void:
	if not mode_selected:
		if Input.is_action_just_pressed("mode_pvp"):
			_select_mode(Mode.PLAYER_VS_PLAYER)
		elif Input.is_action_just_pressed("mode_vs_computer"):
			_select_mode(Mode.PLAYER_VS_COMPUTER)
		return

	if game_over and Input.is_action_just_pressed("restart"):
		_restart_game()

func _select_mode(mode: Mode) -> void:
	mode_selected = true
	message_label.text = ""

	if mode == Mode.PLAYER_VS_COMPUTER:
		_enable_ai_opponent()

	_start_round(1)

func _enable_ai_opponent() -> void:
	var policy := AIPolicy.new()
	if policy.load_model("res://ai_model.json"):
		right_paddle.ai_controlled = true
		right_paddle.ai_policy = policy
		right_paddle.ball = ball
		right_paddle.opponent_paddle = left_paddle
		right_paddle.is_right_side = true
	else:
		push_error("Could not load ai_model.json; falling back to Player vs Player")

func _on_goal_scored(scoring_side: String) -> void:
	if scoring_side == "left":
		left_score += 1
	else:
		right_score += 1

	_update_score_labels()

	if left_score >= WIN_SCORE or right_score >= WIN_SCORE:
		_end_game(scoring_side)
	else:
		var launch_direction := -1 if scoring_side == "left" else 1
		await get_tree().create_timer(1.0).timeout
		_start_round(launch_direction)

func _start_round(direction_sign: int) -> void:
	ball.reset_ball()
	ball.launch(direction_sign)

func _end_game(winning_side: String) -> void:
	game_over = true
	var winner_name := "Left Player" if winning_side == "left" else "Right Player"
	message_label.text = "%s Wins!\nPress Space to Restart" % winner_name

func _restart_game() -> void:
	left_score = 0
	right_score = 0
	game_over = false
	message_label.text = ""
	_update_score_labels()
	_start_round(1)

func _update_score_labels() -> void:
	left_score_label.text = str(left_score)
	right_score_label.text = str(right_score)
