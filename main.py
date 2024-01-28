import os
import sys
import random
import pygame
import math

pygame.init()
pygame.key.set_repeat(200, 70)

# переменные-константы
FPS = 50
WIDTH = 800
HEIGHT = 800
STEP = 5
PILLAR_OP_COOLDOWN = 100
ANIM_LAG = 6
ANIM_PHASES = 2
GLOW_LOW = 150
GLOW_HIGH = 255
GLOW_LAG = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pause_screen = pygame.Surface((WIDTH, HEIGHT))
pause_screen.fill(pygame.Color(0, 0, 0))
pause_screen.set_alpha(80)
clock = pygame.time.Clock()

player = None
all_sprites = pygame.sprite.Group()
tiles_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
oil_busts_group = pygame.sprite.Group()
pillar_group = pygame.sprite.Group()


def load_image(name, color_key=-1):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname).convert()
    except pygame.error as message:
        print('Cannot load image:', name)
        raise SystemExit(message)

    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


def load_level(filename):
    filename = "data/" + filename
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    max_width = max(map(len, level_map))
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


def generate_level(level):
    new_player, x, y = None, None, None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '.':
                Tile('empty', x, y)
            elif level[y][x] == '#':
                Tile('wall', x, y)
            elif level[y][x] == '@':
                Tile('empty', x, y)
                new_player = Player(x, y)
    return new_player, x, y


def terminate():
    pygame.quit()
    sys.exit()


def start_screen():
    intro_text = ["Lights", "",
                  "Девочка, помешанная на гирлядах, решила захватить мир!!",
                  "ВСЕ БУДЕТ МЕРЦАТЬ. Ну, в теории...",
                  "А для начала, помоги ей украсить свой участок"]
    starts_image = pygame.transform.scale(load_image('lawn.png'), (WIDTH, HEIGHT))
    screen.blit(starts_image, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()
        clock.tick(FPS)


pillar_image = load_image("pillar.png")
pillar_image_pickable = load_image("pillar.png")
pillar_image_fixed = load_image("additional_pillar.png")
player_image_front_st = load_image('девочка вперед стоя.png')
player_image_front_go = load_image('девочка вперед идет.png')
player_image_back_right = load_image('девочка назад справа.png')
player_image_back_left = load_image('девочка назад слева.png')
player_image_left_st = load_image('девочка налево стоя.png')
player_image_left_go = load_image('девочка налево идет.png')
player_image_right_st = load_image('девочка направо стоя.png')
player_image_right_go = load_image('девочка направо идет.png')
animation = {"L": [player_image_left_st, player_image_left_go],
             "R": [player_image_right_st, player_image_right_go],
             "U": [player_image_back_left, player_image_back_right],
             "D": [player_image_front_st, player_image_front_go]}

dx = {"L": -1, "U": 0, "D": 0, "R": 1}
dy = {"L": 0, "U": -1, "D": 1, "R": 0}


background_image = pygame.transform.scale(load_image('lawn.png'), (WIDTH, HEIGHT))

tile_width = tile_height = 50


class Level():
    def __init__(self):
        pass



class Pillar(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, fixed):
        super().__init__(pillar_group, all_sprites)
        self.fixed = fixed
        self.image = pillar_image_fixed if fixed else pillar_image
        self.rect = self.image.get_rect()
        self.rect.x = pos_x
        self.rect.y = pos_y
        self.hitbox = self.rect.inflate(-40, -10)
        self.pickable = False
        self.attached = False
        self.nearby = False

    def update(self, player):
        if not self.fixed:
            if self.hitbox.colliderect(player.hitbox):
                self.pickable = True
                self.nearby = True
                self.image = pillar_image_pickable
                t = pygame.time.get_ticks()
                al = (math.sin(t / (GLOW_LAG * math.pi)) + 1) / 2
                self.image.set_alpha(GLOW_LOW + (GLOW_HIGH - GLOW_LOW) * al)
            else:
                self.image = pillar_image
                self.pickable = False
                self.nearby = False
        else:
            if self.hitbox.colliderect(player.hitbox):
                self.nearby = True
            else:
                self.nearby = False


class Lights:
    def __init__(self, beg_x, beg_y, end_x, end_y, lit=False):
        self.beg_x = beg_x
        self.beg_y = beg_y
        self.end_x = end_x
        self.end_y = end_y
        self.lit = lit

    def get_lenght(self):
        return (pygame.math.Vector2(self.beg_x, self.beg_y) - pygame.math.Vector2(self.end_x, self.end_y)).magnitude()

    def draw(self):
        pygame.draw.line(screen, pygame.Color("orange"), (self.beg_x, self.beg_y), (self.end_x, self.end_y), 5)


class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, additionals, length, time):
        super().__init__(player_group, all_sprites)
        self.image = player_image_front_st
        self.rect = self.image.get_rect()
        self.rect.x = pos_x
        self.rect.y = pos_y
        self.hitbox = self.rect.inflate(-50, -10)
        self.speed = STEP
        self.phase = 0
        self.phase1 = 0
        self.direction = "D"
        self.lights = False
        self.additional_pillars = additionals
        self.lights_length = length
        self.time_limit = time * FPS
        self.autopilot = False
        self.singlestep = False
        self.destination = pygame.math.Vector2(pos_x, pos_y)
        self.pillar_op_time = 0
        self.carry_lights = None

    def input(self, event, pillars, lights):
        keys = pygame.key.get_pressed()
        if keys:
            if keys[pygame.K_a]:
                self.direction = "L"
                self.singlestep = True
                self.autopilot = False
            if keys[pygame.K_s]:
                self.direction = "D"
                self.singlestep = True
                self.autopilot = False
            if keys[pygame.K_d]:
                self.direction = "R"
                self.singlestep = True
                self.autopilot = False
            if keys[pygame.K_w]:
                self.direction = "U"
                self.singlestep = True
                self.autopilot = False
            if keys[pygame.K_SPACE]:
                if (pygame.time.get_ticks() - self.pillar_op_time) > PILLAR_OP_COOLDOWN:
                    picked = False
                    for p in pillars:
                        if p.pickable:
                            p.kill()
                            self.additional_pillars += 1
                            picked = True
                            self.pillar_op_time = pygame.time.get_ticks()
                    if (not picked) and (self.additional_pillars > 0):
                        self.additional_pillars -= 1
                        newp = Pillar(player.rect.x, player.rect.y, False)
                        self.pillar_op_time = pygame.time.get_ticks()
            if keys[pygame.K_q]:
                if (pygame.time.get_ticks() - self.pillar_op_time) > PILLAR_OP_COOLDOWN:
                    if not self.carry_lights:
                        for p in pillars:
                            if p.nearby:
                                self.carry_lights = Lights(p.rect.center[0], p.rect.center[1],
                                                             self.rect.center[0], self.rect.center[1])
                                lights.append(self.carry_lights)
                                p.lights = self.carry_lights
                                self.pillar_op_time = pygame.time.get_ticks()
                                break
                    else:
                        for p in pillars:
                            if p.nearby:
                                print("try to attach")
                                self.carry_lights.end_x = p.rect.center[0]
                                self.carry_lights.end_y = p.rect.center[1]
                                p.lights = self.carry_lights
                                self.lights_length -= self.carry_lights.get_lenght()
                                self.carry_lights = None
                                self.pillar_op_time = pygame.time.get_ticks()
                                break

        if event.type == pygame.MOUSEBUTTONDOWN:
            self.autopilot = True
            self.destination = event.pos

    def update(self):
        if self.singlestep:
            self.singlestep = False
            self.rect.x += dx[self.direction] * self.speed
            self.rect.y += dy[self.direction] * self.speed
            player.image = animation[self.direction][self.phase]
            self.phase1 += 1
            if self.phase1 >= ANIM_LAG:
                self.phase1 = 0
                self.phase += 1
                if self.phase >= ANIM_PHASES:
                    self.phase = 0
        elif self.autopilot:
            dest_v = pygame.math.Vector2(self.destination)
            player_v = pygame.math.Vector2(self.rect.center)
            if (dest_v - player_v).magnitude() > self.speed:
                delta_dir = (dest_v - player_v).normalize()
                delta = delta_dir * self.speed
                self.rect.x += delta[0]
                self.rect.y += delta[1]
                if delta_dir*pygame.math.Vector2(1,1) > 0:
                    if delta_dir * pygame.math.Vector2(1, -1) > 0:
                        self.direction = "R"
                    else:
                        self.direction = "D"
                else:
                    if delta_dir * pygame.math.Vector2(1, -1) > 0:
                        self.direction = "U"
                    else:
                        self.direction = "L"
            else:
                self.autopilot = False
                self.rect.x = self.destination[0] - 100
                self.rect.y = self.destination[1] - 100

            player.image = animation[self.direction][self.phase]
            self.phase1 += 1
            if self.phase1 >= ANIM_LAG:
                self.phase1 = 0
                self.phase += 1
                if self.phase >= ANIM_PHASES:
                    self.phase = 0
        self.hitbox = self.rect.inflate(-50, -10)
        if self.carry_lights:
            self.carry_lights.end_x = self.rect.center[0]
            self.carry_lights.end_y = self.rect.center[1]


running = True
pause = False
start_screen()
player = Player(300, 300, 3, 1000, 60)
pillar0 = Pillar(600, 600, True)
pillar1 = Pillar(100, 100, True)
lights_group = []

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                pause = not pause
        if not pause:
            player.input(event, pillar_group, lights_group)
    player.update()
    for p in pillar_group:
        p.update(player)

    screen.fill(pygame.Color(0, 0, 0))
    screen.blit(background_image, (0, 0))
    pillar_group.draw(screen)
    for light in lights_group:
        light.draw()
    player_group.draw(screen)
    if pause:
        screen.blit(pause_screen, (0, 0))
    pygame.display.flip()
    clock.tick(FPS)

terminate()