import os
import sys
import random
import pygame

pygame.init()
pygame.key.set_repeat(200, 70)

# переменные-константы
FPS = 50
WIDTH = 800
HEIGHT = 800
STEP = 5

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


tile_images = {'wall': load_image('box.png'), 'empty': load_image('grass.png')}
player_image_front_st = load_image('девочка вперед стоя.png')
player_image_front_go = load_image('девочка вперед идет.png')
player_image_back_right = load_image('девочка назад справа.png')
player_image_back_left = load_image('девочка назад слева.png')
player_image_left_st = load_image('девочка налево стоя.png')
player_image_left_go = load_image('девочка налево идет.png')
player_image_right_st = load_image('девочка направо стоя.png')
player_image_right_go = load_image('девочка направо идет.png')
phase_left = [player_image_left_st, player_image_left_go]
phase_right = [player_image_right_st, player_image_right_go]
phase_back = [player_image_back_left, player_image_back_right]
phase_front = [player_image_front_st, player_image_front_go]
phase = 0
phase1 = 0

background_image = load_image('lawn.png')
pillar_image = load_image('pillar.png')

tile_width = tile_height = 50


class Level(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(tiles_group, all_sprites)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, additionals, length, time):
        super().__init__(player_group, all_sprites)
        self.image = player_image_front_st
        self.rect = self.image.get_rect()
        self.rect.x = pos_x
        self.rect.y = pos_y
        self.speed = STEP
        self.phase = 0
        self.phase1 = 0
        self.direction = pygame.math.Vector2(0, 0)
        self.lights = False
        self.additional_pillars = additionals
        self.lights_length = length
        self.time_limit = time * FPS
        self.autopilot = False

    def input(self):
        pass

    def update(self, direction):
        self.rect = self.rect.move(random.randrange(3) - 1, random.randrange(3) - 1)
        if direction:
            self.image = self.image_boom


running = True
pause = False
start_screen()
player = Player(300, 300, 3, 1000, 60)
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                pause = not pause
        if not pause:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    player.rect.x -= STEP
                    player.image = phase_left[phase]
                    phase1 += 1
                    if phase1 > 3:
                        phase1 = 0
                        phase += 1
                        if phase > 1:
                            phase = 0
                if event.key == pygame.K_d:
                    player.rect.x += STEP
                    player.image = phase_right[phase]
                    phase1 += 1
                    if phase1 > 3:
                        phase1 = 0
                        phase += 1
                        if phase > 1:
                            phase = 0
                if event.key == pygame.K_w:
                    player.rect.y -= STEP
                    player.image = phase_back[phase]
                    phase1 += 1
                    if phase1 > 3:
                        phase1 = 0
                        phase += 1
                        if phase > 1:
                            phase = 0
                if event.key == pygame.K_s:
                    player.rect.y += STEP
                    player.image = phase_front[phase]
                    phase1 += 1
                    if phase1 > 3:
                        phase1 = 0
                        phase += 1
                        if phase > 1:
                            phase = 0


    screen.fill(pygame.Color(0, 0, 0))
    screen.blit(background_image, (0, 0))
    tiles_group.draw(screen)
    player_group.draw(screen)
    if pause:
        screen.blit(pause_screen, (0, 0))
    pygame.display.flip()
    clock.tick(FPS)

terminate()