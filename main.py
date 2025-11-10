
import pygame 
import sys
import math
import time

# ---------- CONFIGURACIÓN ----------
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 480
FPS = 60

PLAYER_COLOR_A = (10, 180, 255)
PLAYER_COLOR_B = (255, 50, 50)
BALL_COLOR = (255, 255, 255)
BACKGROUND = (35, 100, 45)
LINE_COLOR = (230, 247, 217)
TEXT_COLOR = (255, 255, 255)

HALF_TIME = 60  # segundos (1 minuto)

# ---------- CLASES ----------
class Player:
    def __init__(self, name, x, y, team, role='medio', speed=2.5):
        self.name = name
        self.x = x
        self.y = y
        self.team = team  # 'A' o 'B'
        self.role = role
        self.speed = speed
        self.width = 16
        self.height = 16

    def rect(self):
        return pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)


class Ball:
    def __init__(self, x, y, owner=None):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.owner = owner

# ---------- INICIO PYGAME ----------
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Captain Tsubasa PixelGame - Rect Edition")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 28)

# ---------- ESTADO DEL JUEGO ----------
PLAYER = Player('Tsubasa', 120, SCREEN_HEIGHT//2, 'A', role='medio')
TEAM_A = [PLAYER]
TEAM_B = []
NPCS = []

roles_A = ['defensa','defensa','medio','medio','delantero']
roles_B = ['defensa','defensa','medio','medio','delantero']

for i in range(5):
    TEAM_A.append(Player(f'Comp{i}', 120, 80 + i*70, 'A', role=roles_A[i]))
    p = Player(f'Rival{i}', 780, 80 + i*70, 'B', role=roles_B[i])
    TEAM_B.append(p)
    NPCS.append(TEAM_A[i+1])
    NPCS.append(p)

PORT_A = Player('PortA', 60, SCREEN_HEIGHT//2, 'A', role='portero', speed=2)
PORT_B = Player('PortB', SCREEN_WIDTH-60, SCREEN_HEIGHT//2, 'B', role='portero', speed=2)
TEAM_A.append(PORT_A)
TEAM_B.append(PORT_B)
NPCS.extend([PORT_A, PORT_B])

BALL = Ball(PLAYER.x + 10, PLAYER.y, owner=PLAYER)
score = {'A': 0, 'B': 0}
game_paused = False
game_time = HALF_TIME
last_time_tick = time.time()

keys = {'w':False,'a':False,'s':False,'d':False,'x':False}

def draw_field():
    screen.fill(BACKGROUND)
    pygame.draw.rect(screen, LINE_COLOR, (50,50,SCREEN_WIDTH-100,SCREEN_HEIGHT-100), 4)
    pygame.draw.circle(screen, LINE_COLOR, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 40, 2)
    pygame.draw.line(screen, LINE_COLOR, (SCREEN_WIDTH//2,50),(SCREEN_WIDTH//2, SCREEN_HEIGHT-50),2)
    pygame.draw.rect(screen, (200,200,200), (SCREEN_WIDTH-30, SCREEN_HEIGHT//2 - 50, 10, 100))
    pygame.draw.rect(screen, (200,200,200), (20, SCREEN_HEIGHT//2 - 50, 10, 100))

def draw_player(p):
    color = PLAYER_COLOR_A if p.team == 'A' else PLAYER_COLOR_B
    pygame.draw.rect(screen, color, p.rect())

def draw_ball(b):
    pygame.draw.circle(screen, BALL_COLOR, (int(b.x), int(b.y)), 6)

def draw_scoreboard():
    text = f"Equipo A {score['A']}  -  {score['B']} Equipo B"
    surf = font.render(text, True, TEXT_COLOR)
    rect = surf.get_rect(center=(SCREEN_WIDTH//2, 25))
    screen.blit(surf, rect)

def draw_timer():
    surf = font.render(f"Tiempo: {game_time}", True, TEXT_COLOR)
    rect = surf.get_rect(center=(SCREEN_WIDTH//2, 50))
    screen.blit(surf, rect)

def show_toast(text, duration=1.2):
    surf = font.render(text, True, TEXT_COLOR)
    rect = surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
    screen.blit(surf, rect)
    pygame.display.flip()
    pygame.time.delay(int(duration*1000))

def reset_positions(starting_team):
    BALL.x, BALL.y = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
    BALL.vx, BALL.vy = 0, 0
    BALL.owner = None
    PLAYER.x, PLAYER.y = (120, SCREEN_HEIGHT//2)
    PORT_A.x, PORT_A.y = (60, SCREEN_HEIGHT//2)
    PORT_B.x, PORT_B.y = (SCREEN_WIDTH-60, SCREEN_HEIGHT//2)
    if starting_team == 'A': BALL.owner = TEAM_A[0]
    else: BALL.owner = TEAM_B[0]

def check_goal_and_restart():
    goal_top = (SCREEN_HEIGHT // 2) - 50
    goal_bottom = (SCREEN_HEIGHT // 2) + 50
    if BALL.x > SCREEN_WIDTH - 40 and goal_top < BALL.y < goal_bottom:
        score['A'] += 1
        show_toast("¡Gol del Equipo A!")
        reset_positions('B')
        return True
    if BALL.x < 40 and goal_top < BALL.y < goal_bottom:
        score['B'] += 1
        show_toast("¡Gol del Equipo B!")
        reset_positions('A')
        return True
    return False

def npc_update(npc):
    if game_paused: return
    dx, dy = BALL.x - npc.x, BALL.y - npc.y
    dist = math.hypot(dx, dy) or 1
    npc.x += dx / dist * npc.speed * 0.3
    npc.y += dy / dist * npc.speed * 0.3
    npc.x = max(50, min(SCREEN_WIDTH-50, npc.x))
    npc.y = max(50, min(SCREEN_HEIGHT-50, npc.y))

def update_possession():
    if BALL.owner is None:
        nearest = None
        nd = 9999
        for p in TEAM_A + TEAM_B:
            d = math.hypot(BALL.x - p.x, BALL.y - p.y)
            if d < 14 and d < nd:
                nd, nearest = d, p
        if nearest:
            BALL.owner = nearest

def move_player():
    if game_paused: return
    sp = PLAYER.speed
    dx = (keys['d'] - keys['a']) * sp
    dy = (keys['s'] - keys['w']) * sp
    PLAYER.x = max(50, min(SCREEN_WIDTH-50, PLAYER.x + dx))
    PLAYER.y = max(50, min(SCREEN_HEIGHT-50, PLAYER.y + dy))

def kick_ball(power=6):
    if BALL.owner != PLAYER: return
    BALL.owner = None
    BALL.vx = power * (1 if PLAYER.team == 'A' else -1)
    BALL.vy = 0

def gameLoop():
    global game_paused, game_time, last_time_tick
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w: keys['w']=True
                if event.key == pygame.K_s: keys['s']=True
                if event.key == pygame.K_a: keys['a']=True
                if event.key == pygame.K_d: keys['d']=True
                if event.key == pygame.K_x: keys['x']=True; kick_ball()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_w: keys['w']=False
                if event.key == pygame.K_s: keys['s']=False
                if event.key == pygame.K_a: keys['a']=False
                if event.key == pygame.K_d: keys['d']=False
                if event.key == pygame.K_x: keys['x']=False

        now = time.time()
        if now - last_time_tick >= 1:
            if game_time > 0:
                game_time -= 1
            last_time_tick = now

        move_player()
        for npc in NPCS:
            npc_update(npc)

        if BALL.owner:
            BALL.x = BALL.owner.x + (10 if BALL.owner.team=='A' else -10)
            BALL.y = BALL.owner.y
        else:
            BALL.x += BALL.vx
            BALL.y += BALL.vy
            BALL.vx *= 0.97
            BALL.vy *= 0.97

        update_possession()
        check_goal_and_restart()

        draw_field()
        for p in TEAM_A + TEAM_B: draw_player(p)
        draw_ball(BALL)
        draw_scoreboard()
        draw_timer()
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    print("Controles: W A S D = mover | X = disparar")
    gameLoop()

