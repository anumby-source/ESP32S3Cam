import pygame
import sys
import time
import math
import random

# Initialisation
pygame.init()

# Constantes
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Permis Robot - Version Pygame Complète"

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# Créer la fenêtre
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(SCREEN_TITLE)
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)
big_font = pygame.font.SysFont(None, 50)

class Robot:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed_level = 1  # 0=arrêt, 1=lent, 2=rapide
        self.direction = 0    # 0:haut, 1:droite, 2:bas, 3:gauche
        self.penalty = 0
        self.bonus = 0
        self.start_time = time.time()
        self.color = BLUE
        self.blink_time = 0
        self.level = 1
        self.current_sign = None
        self.stop_time = 0

class Sign:
    def __init__(self, x, y, sign_type):
        self.x = x
        self.y = y
        self.type = sign_type
        self.detected = False
        self.last_blink = 0

class Pieton:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 20
        self.moving = True
        self.move_direction = 1

    def move(self):
        if self.moving:
            self.x += self.move_direction
            if self.x < 50 or self.x > SCREEN_WIDTH - 50:
                self.move_direction *= -1

def create_level(level):
    signs = []
    pietons = []

    if level == 1:
        signs = [
            Sign(150, 150, "Limite 30"),
            Sign(300, 150, "Passage piétons"),
            Sign(450, 150, "Cédez le passage"),
            Sign(450, 300, "Priorité à droite"),
            Sign(300, 300, "Interdit"),
            Sign(150, 300, "Giratoire"),
            Sign(150, 450, "Stop")
        ]
        pietons = [Pieton(300, 130)]
    elif level == 2:
        signs = [
            Sign(200, 100, "Limite 30"),
            Sign(350, 100, "Passage piétons"),
            Sign(500, 150, "Cédez le passage"),
            Sign(500, 300, "Priorité à droite"),
            Sign(350, 350, "Interdit"),
            Sign(200, 350, "Giratoire"),
            Sign(200, 500, "Stop")
        ]
        pietons = [Pieton(350, 90), Pieton(500, 280)]
    else:
        signs = [
            Sign(100, 100, "Limite 30"),
            Sign(250, 100, "Passage piétons"),
            Sign(400, 150, "Cédez le passage"),
            Sign(550, 200, "Priorité à droite"),
            Sign(550, 350, "Interdit"),
            Sign(400, 400, "Giratoire"),
            Sign(250, 450, "Stop"),
            Sign(100, 300, "Limite 30"),
            Sign(300, 200, "Passage piétons")
        ]
        pietons = [Pieton(250, 90), Pieton(550, 330), Pieton(300, 180)]

    return signs, pietons

def draw_parcours(level):
    if level == 1:
        pygame.draw.line(screen, GRAY, (100, 100), (200, 100), 5)
        pygame.draw.line(screen, GRAY, (200, 100), (200, 200), 5)
        pygame.draw.line(screen, GRAY, (200, 200), (500, 200), 5)
        pygame.draw.line(screen, GRAY, (500, 200), (500, 300), 5)
        pygame.draw.line(screen, GRAY, (500, 300), (200, 300), 5)
        pygame.draw.line(screen, GRAY, (200, 300), (200, 400), 5)
        pygame.draw.line(screen, GRAY, (200, 400), (100, 400), 5)
        pygame.draw.line(screen, GREEN, (100, 450), (200, 450), 5)
    elif level == 2:
        pygame.draw.line(screen, GRAY, (100, 100), (500, 100), 5)
        pygame.draw.line(screen, GRAY, (500, 100), (500, 300), 5)
        pygame.draw.line(screen, GRAY, (500, 300), (100, 300), 5)
        pygame.draw.line(screen, GRAY, (100, 300), (100, 500), 5)
        pygame.draw.line(screen, GREEN, (100, 500), (200, 500), 5)
    else:
        pygame.draw.line(screen, GRAY, (100, 100), (300, 100), 5)
        pygame.draw.line(screen, GRAY, (300, 100), (300, 300), 5)
        pygame.draw.line(screen, GRAY, (300, 300), (500, 300), 5)
        pygame.draw.line(screen, GRAY, (500, 300), (500, 500), 5)
        pygame.draw.line(screen, GRAY, (500, 500), (100, 500), 5)
        pygame.draw.line(screen, GREEN, (100, 500), (100, 100), 5)

def draw_sign(sign):
    # Animation de clignotement
    if time.time() - sign.last_blink < 0.5:
        color = YELLOW
    else:
        color = RED
        if time.time() - sign.last_blink > 1:
            sign.last_blink = time.time()

    pygame.draw.rect(screen, color, (sign.x - 15, sign.y - 15, 30, 30))
    font_small = pygame.font.SysFont(None, 12)
    text = font_small.render(sign.type, True, BLACK)
    screen.blit(text, (sign.x - text.get_width()//2, sign.y - 10))

def draw_pieton(pieton):
    pygame.draw.circle(screen, RED, (pieton.x, pieton.y), 10)
    pygame.draw.line(screen, RED, (pieton.x, pieton.y-10), (pieton.x, pieton.y+10), 2)
    pygame.draw.line(screen, RED, (pieton.x, pieton.y), (pieton.x+10, pieton.y-5), 2)
    pygame.draw.line(screen, RED, (pieton.x, pieton.y), (pieton.x-10, pieton.y-5), 2)

def draw_robot(robot):
    if robot.penalty > 0 and time.time() - robot.blink_time < 1:
        color = RED
    else:
        color = robot.color
        if time.time() - robot.blink_time > 1:
            robot.blink_time = time.time()

    pygame.draw.circle(screen, color, (robot.x, robot.y), 15)

    # Dessiner la flèche de direction
    if robot.direction == 0:  # Haut
        pygame.draw.polygon(screen, color, [
            (robot.x, robot.y + 15),
            (robot.x - 10, robot.y - 5),
            (robot.x + 10, robot.y - 5)
        ])
    elif robot.direction == 1:  # Droite
        pygame.draw.polygon(screen, color, [
            (robot.x - 15, robot.y),
            (robot.x + 5, robot.y - 10),
            (robot.x + 5, robot.y + 10)
        ])
    elif robot.direction == 2:  # Bas
        pygame.draw.polygon(screen, color, [
            (robot.x, robot.y - 15),
            (robot.x - 10, robot.y + 5),
            (robot.x + 10, robot.y + 5)
        ])
    elif robot.direction == 3:  # Gauche
        pygame.draw.polygon(screen, color, [
            (robot.x + 15, robot.y),
            (robot.x - 5, robot.y - 10),
            (robot.x - 5, robot.y + 10)
        ])

    # Afficher le niveau de vitesse
    speed_text = font.render(str(robot.speed_level), True, BLACK)
    screen.blit(speed_text, (robot.x - 5, robot.y - 25))

def draw_hud(robot):
    time_elapsed = time.time() - robot.start_time
    total_time = time_elapsed + robot.penalty - robot.bonus

    # Afficher le temps, pénalités et bonus
    hud_text = font.render(
        f"Temps: {time_elapsed:.1f}s | Pénalités: +{robot.penalty}s | Bonus: +{robot.bonus}s",
        True, BLACK
    )
    screen.blit(hud_text, (10, 10))

    # Afficher le niveau actuel
    level_text = big_font.render(f"Niveau {robot.level}", True, PURPLE)
    screen.blit(level_text, (SCREEN_WIDTH//2 - level_text.get_width()//2, 10))

    # Afficher les instructions
    instr_text = font.render(
        "1/2/3: Vitesse | Flèches: Direction | R: Réinitialiser",
        True, BLACK
    )
    screen.blit(instr_text, (10, SCREEN_HEIGHT - 30))

    # Chronomètre visuel
    pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH - 220, 10, 210, 30), 2)
    pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH - 220, 10, 210 * min(1, time_elapsed / 60), 30))

def main():
    robot = Robot(100, 100)
    signs, pietons = create_level(robot.level)
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    robot.direction = 2
                elif event.key == pygame.K_RIGHT:
                    robot.direction = 1
                elif event.key == pygame.K_DOWN:
                    robot.direction = 0
                elif event.key == pygame.K_LEFT:
                    robot.direction = 3
                elif event.key == pygame.K_1:
                    robot.speed_level = 0
                elif event.key == pygame.K_2:
                    robot.speed_level = 1
                elif event.key == pygame.K_3:
                    robot.speed_level = 2
                elif event.key == pygame.K_r:
                    robot = Robot(100, 100)
                    signs, pietons = create_level(robot.level)

        # Déplacer le robot
        speeds = [0, 2, 4]
        if robot.direction == 0:
            robot.y += speeds[robot.speed_level]
        elif robot.direction == 1:
            robot.x += speeds[robot.speed_level]
        elif robot.direction == 2:
            robot.y -= speeds[robot.speed_level]
        elif robot.direction == 3:
            robot.x -= speeds[robot.speed_level]

        # Limiter le robot à l'écran
        robot.x = max(50, min(SCREEN_WIDTH - 50, robot.x))
        robot.y = max(50, min(SCREEN_HEIGHT - 50, robot.y))

        # Déplacer les piétons
        for pieton in pietons:
            pieton.move()

        # Détecter les collisions avec les panneaux
        for sign in signs:
            if not sign.detected and math.sqrt((sign.x - robot.x)**2 + (sign.y - robot.y)**2) < 30:
                sign.detected = True
                robot.current_sign = sign.type
                print(f"Panneau détecté: {sign.type}")

                if sign.type == "Limite 30":
                    robot.speed_level = 1
                    robot.bonus += 1
                elif sign.type == "Passage piétons":
                    for pieton in pietons:
                        if math.sqrt((pieton.x - robot.x)**2 + (pieton.y - robot.y)**2) < 50:
                            robot.speed_level = 0
                            robot.bonus += 2
                        else:
                            robot.penalty += 5
                elif sign.type == "Stop":
                    robot.speed_level = 0
                    robot.stop_time = time.time()
                    robot.penalty += 5 if robot.speed_level != 0 else 0

        # Vérifier la fin du niveau
        if robot.level == 1 and 100 <= robot.x <= 200 and 440 <= robot.y <= 460:
            finish_level(robot)
        elif robot.level == 2 and 100 <= robot.x <= 200 and 490 <= robot.y <= 510:
            finish_level(robot)
        elif robot.level == 3 and 100 <= robot.x <= 300 and 90 <= robot.y <= 110:
            finish_level(robot)

        # Dessiner tout
        screen.fill(WHITE)
        draw_parcours(robot.level)
        for sign in signs:
            draw_sign(sign)
        for pieton in pietons:
            draw_pieton(pieton)
        draw_robot(robot)
        draw_hud(robot)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

def finish_level(robot):
    temps_total = time.time() - robot.start_time + robot.penalty - robot.bonus
    print(f"🏁 Niveau {robot.level} terminé en {temps_total:.2f} secondes !")
    if robot.penalty == 0:
        print("🎉 Permis Robot Or !")
    elif robot.penalty <= 2:
        print("🥈 Permis Robot Argent !")
    else:
        print("🥉 Permis Robot Bronze !")

    if robot.level < 3:
        robot.level += 1
        robot.x, robot.y = 100, 100
        robot.start_time = time.time()
        robot.penalty = 0
        robot.bonus = 0
        robot.speed_level = 1
    else:
        print("🎊 Félicitations ! Vous avez terminé tous les niveaux !")
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
