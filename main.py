import os
from random import randint, choice

import pgzrun
from pygame import Rect
from pgzero import music
from pgzero import tone
from pgzero.actor import Actor
from pgzero.keyboard import Keyboard
from pgzero.screen import Screen

screen: Screen
keyboard: Keyboard

os.environ["SDL_VIDEO_CENTERED"] = "1"

WIDTH = 1024
HEIGHT = 768
TITLE = "Casse Brique"

HIT_BRICK = tone.create("A5", 0.2)
HIT_PADDLE = tone.create("F4", 0.3)


class Color:
    @staticmethod
    def pastel_random() -> tuple[int, int, int]:
        return (randint(180, 255), randint(180, 255), randint(180, 255))

    @staticmethod
    def dark_random() -> str:
        return choice(
            ("RED", "GREEN", "BLUE", "ORANGE", "BROWN", "PINK", "BLACK", "PURPLE")
        )


class Paddle:
    def __init__(self):
        """Initialise la raquette avec une position et une taille."""
        self.width = WIDTH // 5
        self.height = HEIGHT // 40
        self.rect = Rect(
            (WIDTH - self.width) // 2, HEIGHT - 2 * self.height, self.width, self.height
        )
        self.speed = 10

    def move(self, direction: bool):
        """Fait bouger la raquette selon la direction (gauche = `False` ou gauche = `False`)."""
        if direction and self.rect.x + self.width + self.speed < WIDTH:
            self.rect.x += self.speed
        elif self.rect.x > self.speed:
            self.rect.x -= self.speed

    def follow_mouse(self, mouse_x: int):
        game.paddle.rect.x = mouse_x - game.paddle.width // 2

    def draw(self):
        """Dessine la raquette sur l'écran."""
        screen.draw.filled_rect(self.rect, "grey")


class Brick:
    def __init__(self, position: tuple, size: tuple):
        """Initialise une brique avec une position et une taille."""
        self.rect = Rect(position, size)
        self.is_destroyed = False
        self.color = Color.pastel_random()

    def destroy(self):
        """Marque la brique comme détruite."""
        pass

    def draw(self):
        """Dessine la brique sur l'écran si elle n'est pas détruite."""
        if self.is_destroyed:
            return
        screen.draw.filled_rect(self.rect, self.color)


class Ball:
    def __init__(self):
        """Initialise la balle avec une position et une vitesse."""
        self.radius = WIDTH // 80
        self.rect = Rect(
            (WIDTH - self.radius) // 2,
            HEIGHT - 8 * self.radius,
            self.radius,
            self.radius,
        )
        self.speed: list[int] = [1, -1]
        self.norm_speed()
        self.color = Color.dark_random()

    def move(self):
        """Met à jour la position de la balle en fonction de sa vitesse."""
        self.rect.x += self.speed[0]
        self.rect.y += self.speed[1]

    def check_collision(self, paddle: Paddle, bricks: list[Brick]) -> int:
        """Vérifie les collisions avec la raquette, les briques ou les bords de l'écran."""
        if self.rect.colliderect(paddle.rect):
            ball_center = self.rect.x + self.rect.width // 2
            paddle_center = paddle.rect.x + paddle.rect.width // 2
            self.speed[1] *= -1
            self.speed[0] += (ball_center - paddle_center) // 10
            HIT_PADDLE.play()
        if self.rect.x <= 0 or self.rect.x + self.radius >= WIDTH:
            self.speed[0] *= -1
        if self.rect.y <= 0:
            self.speed[1] *= -1

        score = 0
        for brick in bricks:
            if brick.is_destroyed:
                continue
            if self.rect.colliderect(brick.rect):
                brick.is_destroyed = True
                self.speed[1] *= -1
                score += 1
                self.color = Color.dark_random()
                HIT_BRICK.play()
        self.norm_speed()
        return score

    def norm_speed(self):
        if self.speed[0] and abs(self.speed[1] / self.speed[0]) < 0.01:
            self.speed = [0, -1]
        sq_norm = (self.speed[0] ** 2 + self.speed[1] ** 2) ** 0.5
        self.speed[0] *= 1 / sq_norm * 4
        self.speed[1] *= 1 / sq_norm * 4

    def draw(self):
        """Dessine la balle sur l'écran."""
        screen.draw.filled_circle((self.rect.x, self.rect.y), self.radius, self.color)


class BreakoutGame:
    def __init__(self):
        """Initialise le jeu avec les objets de la balle, des briques et de la raquette."""
        self.paddle: Paddle
        self.ball: Ball
        self.bricks: list[Brick]
        self.is_playing: bool
        self.is_won: bool

        self.paddle_width = WIDTH // 6
        self.paddle_height = 50
        self.paddle_margin = self.paddle_width // 6
        self.unicorn = Actor("licorne", center=(WIDTH // 2, HEIGHT // 4))

        self.reset()

    def reset(self):
        self.is_playing = False
        self.is_won = False
        self.paddle = Paddle()
        self.ball = Ball()
        self.bricks = self.create_bricks()
        self.score = 0

    def create_bricks(self):
        return [
            Brick(
                (
                    x * (self.paddle_width + self.paddle_margin) + self.paddle_margin,
                    y * (self.paddle_height + self.paddle_margin)
                    + self.paddle_margin / 2,
                ),
                (self.paddle_width, self.paddle_height),
            )
            for x in range(WIDTH // (self.paddle_width + self.paddle_margin))
            for y in range(4)
        ]

    def update(self):
        """Met à jour l'état du jeu à chaque frame."""
        self.keyboard()
        if not self.is_playing:
            return
        if self.ball.rect.y > HEIGHT:
            self.reset()
        self.score += self.ball.check_collision(self.paddle, self.bricks)
        self.ball.move()
        if self.score == len(self.bricks):
            self.reset()
            music.stop()
            music.play("victory")
            self.is_won = True

    def keyboard(self):
        if keyboard.Escape or keyboard.Q:
            exit()
        if keyboard.Left:
            self.paddle.move(False)
        if keyboard.Right:
            self.paddle.move(True)
        if not self.is_playing and keyboard.Space:
            self.is_playing = True
            self.is_won = False
            music.stop()
            music.play("mario")

    def draw_score(self):
        screen.draw.text(
            str(self.score), center=(WIDTH / 15, HEIGHT / 2), **self.default_text()
        )

    def draw_is_playing(self):
        if self.is_playing:
            return
        text = "APPUYER SUR ESPACE" if not self.is_won else "BRAVO"
        screen.draw.text(text, center=(WIDTH / 2, HEIGHT * 0.75), **self.default_text())

    def default_text(self) -> dict:
        return {
            "fontsize": 60,
            "owidth": 0.8,
            "ocolor": "WHITE",
            "color": "BLACK",
        }

    def draw(self):
        """Dessine tous les éléments du jeu sur l'écran."""
        self.paddle.draw()
        self.ball.draw()
        for brick in self.bricks:
            brick.draw()
        self.draw_score()
        self.draw_is_playing()
        if self.is_won:
            self.unicorn.draw()


game = BreakoutGame()
stars = Actor("stars")


def update():
    """Appelé à chaque frame pour mettre à jour le jeu."""
    game.update()


def draw():
    """Appelé à chaque frame pour dessiner le jeu."""
    stars.draw()
    screen.draw.rect(Rect(0, 0, WIDTH, HEIGHT), "BLACK")
    game.draw()


def on_mouse_move(pos: tuple[int, int]):
    game.paddle.follow_mouse(pos[0])


pgzrun.go()
