"""Optional pygame visualization for watching the Pong simulation.

Rendering is entirely decoupled from physics: this module only reads
PongState and draws it. It never affects simulation logic.
"""

from __future__ import annotations

from pong_rl import physics

WHITE = (255, 255, 255)
BACKGROUND = (13, 13, 18)


class PygameRenderer:
    def __init__(self) -> None:
        import pygame

        pygame.init()
        pygame.display.set_caption("Pong RL")
        self._pygame = pygame
        self._screen = pygame.display.set_mode(
            (int(physics.GAME_WIDTH), int(physics.GAME_HEIGHT))
        )
        self._clock = pygame.time.Clock()
        self._font = pygame.font.SysFont("monospace", 48)

    def draw(self, state: physics.PongState) -> None:
        pygame = self._pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                return

        self._screen.fill(BACKGROUND)

        pygame.draw.rect(
            self._screen,
            WHITE,
            (
                physics.LEFT_PADDLE_X - physics.PADDLE_WIDTH / 2,
                state.left_paddle_y - physics.PADDLE_HEIGHT / 2,
                physics.PADDLE_WIDTH,
                physics.PADDLE_HEIGHT,
            ),
        )
        pygame.draw.rect(
            self._screen,
            WHITE,
            (
                physics.RIGHT_PADDLE_X - physics.PADDLE_WIDTH / 2,
                state.right_paddle_y - physics.PADDLE_HEIGHT / 2,
                physics.PADDLE_WIDTH,
                physics.PADDLE_HEIGHT,
            ),
        )
        pygame.draw.rect(
            self._screen,
            WHITE,
            (
                state.ball.x - physics.BALL_SIZE / 2,
                state.ball.y - physics.BALL_SIZE / 2,
                physics.BALL_SIZE,
                physics.BALL_SIZE,
            ),
        )

        score_surface = self._font.render(
            f"{state.left_score}   {state.right_score}", True, WHITE
        )
        score_rect = score_surface.get_rect(centerx=int(physics.GAME_WIDTH / 2), y=20)
        self._screen.blit(score_surface, score_rect)

        pygame.display.flip()
        self._clock.tick(60)

    def close(self) -> None:
        self._pygame.quit()
