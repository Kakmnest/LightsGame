import os
import sys
import pygame
import math
import csv

pygame.init()
pygame.key.set_repeat(200, 70)

# переменные-константы
FPS = 50
WIDTH = 800
HEIGHT = 800
STEP = 5
PILLAR_OP_COOLDOWN = 200
ANIM_LAG = 6
ANIM_PHASES = 2
GLOW_LOW = 150
GLOW_HIGH = 255
GLOW_LAG = 60
LIGHTS_COLORS = [pygame.Color("Red"), pygame.Color("Blue"), pygame.Color("Orange"),
                 pygame.Color("Green"), pygame.Color("Yellow")]
END_LEVEL_ANIMATION_TIME = 3

# глобальный признак работы игры
running = True

# параметры экрана
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pause_screen = pygame.Surface((WIDTH, HEIGHT))
pause_screen.fill(pygame.Color(0, 0, 0))
pause_screen.set_alpha(80)
clock = pygame.time.Clock()

# загрузка уровней из файла .csv
with open('data/levels data.csv', encoding="utf8") as csvfile:
    levels_data = list(csv.DictReader(csvfile, delimiter=';', quotechar='"'))
for level in range(len(levels_data)):
    levels_data[level]["player_properties"] = dict(item.split(":") for item in
                                                levels_data[level]["player_properties_s"].split(","))
    levels_data[level]["pillars"] = list(levels_data[level]["pillars_s"].split(","))


# функция загрузки изображений из папки data
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


# функция выхода из игры
def terminate():
    pygame.quit()
    sys.exit()


# отрисовка начального экрана
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
        string_rendered = font.render(line, 1, pygame.Color('yellow'))
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

# загрузка всех изображений с помощью load_image()
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
wingirl_image = load_image('wingirl.png', 0)

# настройка анимации игрока
animation = {"L": [player_image_left_st, player_image_left_go],
             "R": [player_image_right_st, player_image_right_go],
             "U": [player_image_back_left, player_image_back_right],
             "D": [player_image_front_st, player_image_front_go]}

# изменения координат при движении в направлениях влево-вверх-вниз-вправо
dx = {"L": -1, "U": 0, "D": 0, "R": 1}
dy = {"L": 0, "U": -1, "D": 1, "R": 0}

background_image = pygame.transform.scale(load_image('lawn.png'), (WIDTH, HEIGHT))


# функция отрисовки статус-бара
def draw_statusbar(remaining_time, remaining_length, remaining_pillars):
    f = pygame.font.Font(None, 30)
    t_text = f.render(f"Осталось секунд: {remaining_time:.2f}", True, (255, 255, 255))
    l_text = f.render(f"Осталось гирлянды: {str(int(remaining_length))}", True, (255, 255, 255))
    p_text = f.render(f"Осталось столбиков: {str(int(remaining_pillars))}", True, (255, 255, 255))

    screen.blit(t_text, (10, 10))
    screen.blit(l_text, (400, 10))
    screen.blit(p_text, (400, 700))


# класс столбиков
class Pillar(pygame.sprite.Sprite):
    def __init__(self, pillars_group, pos_x, pos_y, fixed):
        super().__init__(pillars_group)
        self.fixed = fixed  # fixed - красные стационарные, not fixed - желтые подвижные
        self.image = pillar_image_fixed if fixed else pillar_image
        self.rect = self.image.get_rect()
        self.rect.x = pos_x
        self.rect.y = pos_y
        self.hitbox = self.rect.inflate(-40, -10)
        self.pickable = False
        self.attached = False
        self.nearby = False
        self.connected = [self]
        self.lightsattached = []
        self.reachable = False

    # метод для проверки близости, отрисовки мигания близких желтых столбиков
    def update(self, player):
        if not self.fixed:
            if self.hitbox.colliderect(player.hitbox) :
                self.nearby = True
                if len(self.connected) == 1:
                    self.pickable = True
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

    # метод проверки расстояния до другого столбика
    def distance_to(self, other):
        return (pygame.math.Vector2(self.rect.x, self.rect.y) -
                pygame.math.Vector2(other.rect.x, other.rect.y)).magnitude()

    # метод разметки достижимости для проверки соединения столбиков (DFS из интернета)
    def mark(self):
        self.reachable = True
        for p in self.connected:
            if not p.reachable:
                p.mark()

    # метод снятия пометки достижимости
    def unmark(self):
        self.reachable = False


# класс гирлянды (точнее, ее отрезков)
class Lights:
    def __init__(self, beg_x, beg_y, end_x, end_y, lit=False):
        self.beg_x = beg_x
        self.beg_y = beg_y
        self.end_x = end_x
        self.end_y = end_y
        self.lit = lit
        self.beg = None
        self.end = None

    # получение длины
    def get_length(self):
        return (pygame.math.Vector2(self.beg_x, self.beg_y) - pygame.math.Vector2(self.end_x, self.end_y)).magnitude()

    # отрисовка гирлянды - оранжевой линии с разноцветынми огоньками по сторонам
    def draw(self, ending):
        if ending:
            cord_color = pygame.Color("orange")
        else:
            cord_color = pygame.Color("darkgrey")
        pygame.draw.line(screen, cord_color, (self.beg_x, self.beg_y), (self.end_x, self.end_y), 5)
        begv = pygame.math.Vector2(self.beg_x, self.beg_y)
        endv = pygame.math.Vector2(self.end_x, self.end_y)
        dirv = endv - begv
        lng = dirv.magnitude()
        if lng>0:
            dirv *= 20/lng
            leftrightv = dirv.rotate(90)
            for i in range(int(lng/20)):
                pygame.draw.circle(screen, LIGHTS_COLORS[i % len(LIGHTS_COLORS)], begv + i*dirv + 0.5*leftrightv, 5)
                if ending:
                    t = pygame.time.get_ticks()
                    if math.sin(t/100) > 0:
                        pygame.draw.circle(screen, LIGHTS_COLORS[i % len(LIGHTS_COLORS)], begv + i*dirv + 0.5*leftrightv, 8)
                leftrightv = -leftrightv


# класс игрока
class Player(pygame.sprite.Sprite):
    def __init__(self, player_group, pos_x, pos_y, additionals, length, time):
        super().__init__(player_group)
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
        self.time_limit = time
        self.autopilot = False
        self.singlestep = False
        self.destination = pygame.math.Vector2(pos_x, pos_y)
        self.pillar_op_time = 0
        self.carry_lights = None  # константа, говорящая о том, есть ли гирлянда в руках

    # обработка клавиш и событий (частичное замещение игрового цикла)
    # asdw - стрелки
    # пробел - взять или поставить желтый стоблик
    # q - прицепить гирлянду
    # z - отцепить гирлянду
    # клик мышкой - автопилот в сторону клика
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
                    if not picked and self.additional_pillars > 0:
                        self.additional_pillars -= 1
                        newp = Pillar(pillars, self.rect.x + 50, self.rect.y + 50, False)
                        self.pillar_op_time = pygame.time.get_ticks()
            if keys[pygame.K_q]:
                if (pygame.time.get_ticks() - self.pillar_op_time) > PILLAR_OP_COOLDOWN:
                    if not self.carry_lights:
                        for p in pillars:
                            if p.nearby:
                                self.carry_lights = Lights(p.rect.center[0], p.rect.center[1],
                                                             self.rect.center[0], self.rect.center[1])
                                self.carry_lights.beg = p
                                lights.append(self.carry_lights)
                                p.lightsattached.append(self.carry_lights)
                                self.pillar_op_time = pygame.time.get_ticks()
                                break
                    else:
                        for p in pillars:
                            if p.nearby and p.distance_to(self.carry_lights.beg) < self.lights_length:
                                if self.carry_lights.beg not in p.connected:
                                    self.carry_lights.end_x = p.rect.center[0]
                                    self.carry_lights.end_y = p.rect.center[1]
                                    p.connected.append(self.carry_lights.beg)
                                    self.carry_lights.beg.connected.append(p)
                                    p.lightsattached.append(self.carry_lights )
                                    self.carry_lights.end = p
                                    self.lights_length -= self.carry_lights.get_length()
                                    self.carry_lights = None
                                    self.pillar_op_time = pygame.time.get_ticks()
                                    break
            if keys[pygame.K_z]:
                if (pygame.time.get_ticks() - self.pillar_op_time) > PILLAR_OP_COOLDOWN:
                    if not self.carry_lights:
                        for p in pillars:
                            if p.nearby and len(p.lightsattached) > 0:

                                self.carry_lights = p.lightsattached[-1]
                                self.lights_length += self.carry_lights.get_length()
                                p.lightsattached.pop()
                                p.connected[-1].connected.remove(p)
                                p.connected.pop()
                                if self.carry_lights.beg == p:
                                    self.carry_lights.beg = self.carry_lights.end
                                    self.carry_lights.beg_x = self.carry_lights.end_x
                                    self.carry_lights.beg_y = self.carry_lights.end_y

                                self.carry_lights.end = None
                                self.carry_lights.end_x = self.rect.center[0]
                                self.carry_lights.end_y = self.rect.center[1]
                                self.pillar_op_time = pygame.time.get_ticks()
                                break
                    else:
                        p = self.carry_lights.beg
                        if p.nearby:
                            lights.remove(self.carry_lights)
                            p.lightsattached.remove(self.carry_lights)
                            self.carry_lights = None
                            self.pillar_op_time = pygame.time.get_ticks()
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.autopilot = True
            self.destination = event.pos
        return 0

    # обновление статусов игрока
    # при единичном перемещении клавиатурой - смещение на dx, dy по направлению
    # при автопилоте - смещение в сторону последнего пункта назначения
    # шаг анимации при движении, с пропуском AMIN_LAG шагов до следующей фазы анимации
    # если тянем гирлянду - обновление конца гирлянды
    def update(self):
        if self.singlestep:
            self.singlestep = False
            self.rect.x += dx[self.direction] * self.speed
            self.rect.y += dy[self.direction] * self.speed
            if self.carry_lights:
                self.carry_lights.end_x = self.rect.center[0]
                self.carry_lights.end_y = self.rect.center[1]
            if self.carry_lights and self.lights_length < self.carry_lights.get_length():
                self.rect.x -= dx[self.direction] * self.speed
                self.rect.y -= dy[self.direction] * self.speed
            self.image = animation[self.direction][self.phase]
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
                if self.carry_lights:
                    self.carry_lights.end_x = self.rect.center[0]
                    self.carry_lights.end_y = self.rect.center[1]
                if self.carry_lights and self.lights_length < self.carry_lights.get_length():
                    self.rect.x -= delta[0]
                    self.rect.y -= delta[1]
                    self.autopilot = False
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
            self.image = animation[self.direction][self.phase]
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


# класс уровня
class Level():
    def __init__(self, player_properties, pillars):
        self.player_group = pygame.sprite.Group()
        self.pillars_group = pygame.sprite.Group()
        self.player = Player(self.player_group, int(player_properties["x"]), int(player_properties["y"]),
                             int(player_properties["pillars"]), int(player_properties["length"]),
                             int(player_properties["time_limit"]))
        for p in pillars:
            x, y = p.split(" ")
            Pillar(self.pillars_group, int(x), int(y), True)
        self.lights_group = []
        self.time_elapsed = 0

    # проверка завершения - все красные столбики связаны в одну сеть
    def completion_check(self):
        connected_all = True
        for p in self.pillars_group:
            if p.fixed:
                p.mark()
                break
        for p in self.pillars_group:
            if p.fixed and not p.reachable:
                connected_all = False
        for p in self.pillars_group:
            p.unmark()
        return connected_all

    # подсчет очков за уровень
    def calc_score(self):
        return self.player.time_limit * 10 + self.player.lights_length * 3

    # основной игровой цикл одного уровня
    # опрашиваем клавишу p для паузы
    # опрашиваем ввод для игрока player.input()
    # делаем update для игрока, столбиков
    # продвигаем и проверяем время
    # все отрисовываем

    def run(self):
        pause = False
        end_level = False
        time_elapsed = 0
        global running
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    return 0
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        pause = not pause
                if not pause and not end_level:
                    self.player.input(event, self.pillars_group, self.lights_group)
                    if self.completion_check():
                        end_level = True
                        end_level_time = self.player.time_limit
            if end_level:
                if self.player.time_limit < end_level_time - END_LEVEL_ANIMATION_TIME:
                    return self.calc_score()
            if not pause:
                self.player.update()
            for p in self.pillars_group:
                p.update(self.player)
            if not pause:
                self.player.time_limit -= time_elapsed
                if self.player.time_limit < 0 and not end_level:
                    return 0

            screen.fill(pygame.Color(0, 0, 0))
            screen.blit(background_image, (0, 0))
            self.pillars_group.draw(screen)
            for light in self.lights_group:
                light.draw(end_level)
            self.player_group.draw(screen)
            if pause:
                screen.blit(pause_screen, (0, 0))
            if not end_level:
                if self.player.carry_lights:
                    draw_statusbar(self.player.time_limit,
                                   self.player.lights_length - self.player.carry_lights.get_length(),
                                   self.player.additional_pillars)
                else:
                    draw_statusbar(self.player.time_limit, self.player.lights_length, self.player.additional_pillars)
            pygame.display.flip()
            time_elapsed = clock.tick(FPS) / 1000


# экран прохождения уровня
def levelpassed_screen(result):
    intro_text = ["Поздравляем!!!", "",
                  "Наша девочка, смогла украсить свой участок!",
                  "УЧАСТОК МЕРЦАЕТ, мы становимся ближе к нашей цели.",
                  f"Вы прошли уровень, набрав следующие очки: {int(result)}", "",
                  "Для перехода на следующий уровень, нажмите клавишу N"]
    image = pygame.transform.scale(load_image('level passed!.png'), (WIDTH, HEIGHT))
    image.set_alpha(160)
    screen.blit(image, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 70
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('yellow'))
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
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_n:
                    return
        pygame.display.flip()
        clock.tick(FPS)


# экран проигрыша
def lose_screen():
    intro_text = ["Lights", "", "", "", "", "", "", "", "", "", "", "", "",
                  "", "", "", "", "", "", "", "", "",
                  "Ну вы и лох... Игра же совсем сырая, проиграть тупо невозможно",
                  "Чтобы начать заново, нажмите клавишу R"]
    starts_image = pygame.transform.scale(load_image('lose screen.png'), (WIDTH, HEIGHT))
    screen.blit(starts_image, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('yellow'))
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
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return
        pygame.display.flip()
        clock.tick(FPS)


# экран победы в игре
def win_screen(result):
    score_text = ["ПОЗДРАВЛЯЕМ!!",
                  f"Вы набрали {int(result)} очков!"]
    starts_image = pygame.transform.scale(load_image('level passed!.png'), (WIDTH, HEIGHT))
    screen.blit(starts_image, (0, 0))
    wingirl_image_scaled = pygame.transform.scale(wingirl_image, (700, 800))
    screen.blit(wingirl_image_scaled, (50, 0))
    font = pygame.font.Font(None, 70)
    text_coord = 650
    for line in score_text:
        string_rendered = font.render(line, 1, pygame.Color('yellow'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 100
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


# верхний игровой цикл по уровням
while running:
    score = 0
    start_screen()
    lost = False
    for leveldata in levels_data:
        level = Level(leveldata["player_properties"], leveldata["pillars"])
        result = level.run()
        if not running:
            lost = True
            break
        if result > 0:
            if not leveldata == levels_data[-1]:
                levelpassed_screen(result)
            score += result
            level = None
        else:
            lose_screen()
            lost = True
            level = None
            break
    if not lost:
        win_screen(score)
        running = False

terminate()