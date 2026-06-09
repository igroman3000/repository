from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random

# Инициализация движка
app = Ursina()

# --- ТЕМНОТА И АТМОСФЕРА ---
scene.fog_color = color.black
scene.fog_density = 0.045  

# Настройки коридора
CORRIDOR_WIDTH = 4
CORRIDOR_LENGTH = 300  

# Глобальные переменные состояния игры
game_state = "MENU"  
game_over_flag = False
start_delay = 2.0
obstacles = []
snake_tail = []

# Освещение для главного меню (чтобы кнопки не были черными)
menu_light = DirectionalLight(color=color.white)
menu_light.look_at(Vec3(1, -1, 1))

# --- ИНТЕРФЕЙС И ГЛАВНОЕ МЕНЮ (НА КАНВАСЕ camera.ui) ---
distance_text = Text(text='', position=(-0.8, 0.45), scale=2, color=color.yellow, enabled=False)

# Текст для победы/смерти теперь создается на 2D экране, чтобы не зависать в воздухе
end_game_text = Text(text='', position=(-0.4, 0), scale=3, color=color.red, enabled=False, parent=camera.ui)

# Элементы главного меню
menu_parent = Entity(parent=camera.ui)
menu_title = Text(parent=menu_parent, text='SNAKE HORROR', position=(-0.25, 0.25), scale=5, color=color.red)
start_button = Button(parent=menu_parent, text='START GAME', color=color.dark_gray, scale=(0.3, 0.1), position=(0, 0))
exit_button = Button(parent=menu_parent, text='EXIT', color=color.black, scale=(0.3, 0.1), position=(0, -0.15))

# Окружение
floor = Entity(model='cube', position=(0, -0.5, CORRIDOR_LENGTH / 2), scale=(CORRIDOR_WIDTH, 1, CORRIDOR_LENGTH), collider='box', enabled=False)
left_wall = Entity(model='cube', position=(-CORRIDOR_WIDTH / 2 - 0.5, 2, CORRIDOR_LENGTH / 2), scale=(1, 4, CORRIDOR_LENGTH), collider='box', enabled=False)
right_wall = Entity(model='cube', position=(CORRIDOR_WIDTH / 2 + 0.5, 2, CORRIDOR_LENGTH / 2), scale=(1, 4, CORRIDOR_LENGTH), collider='box', enabled=False)

# ИСПРАВЛЕНИЕ ПРОБЛЕМЫ 3 (ТЕКСТУРЫ): Настраиваем правильный масштаб повторения (тайлинг)
floor.texture = 'пол.png'
floor.texture_scale = (CORRIDOR_WIDTH, CORRIDOR_LENGTH / 4) # Нормальный масштаб для пола
left_wall.texture = 'стена.png'
left_wall.texture_scale = (CORRIDOR_LENGTH / 2, 4) # Кирпичи больше не растягиваются в кашу
right_wall.texture = 'стена.png'
right_wall.texture_scale = (CORRIDOR_LENGTH / 2, 4)

# ИГРОК И МОНСТР
player = FirstPersonController(enabled=False)
player.cursor.visible = False

# ИСПРАВЛЕНИЕ ПРОБЛЕМЫ 1 (РОСТ): Опускаем камеру на человеческий уровень (глаза на высоте 1.6-1.7м)
player.height = 1.7
camera.y = 1.6

# Фонарик игрока
flashlight = SpotLight(parent=camera, position=(0,0,0), direction=(0,0,1), color=color.white, attenuation=(1, 0, 0.025))

snake_head = Entity(model='sphere', texture='noise', color=color.rgb(120, 0, 0), position=(0, 1.2, -20), scale=2.5, collider='box', enabled=False)
snake_speed_base = 8.5
snake_speed = snake_speed_base

def generate_obstacles():
    global obstacles
    for obs in obstacles:
        destroy(obs)
    obstacles.clear()
    
    for z_pos in range(30, CORRIDOR_LENGTH - 15, 12):
        obs = Entity(
            model='cube',
            texture='ящик.png',  
            position=(random.choice([-1.2, 0, 1.2]), 1, z_pos),
            scale=(random.uniform(1.2, 1.5), 2, 1.2),
            collider='box'
        )
        obs.speed_x = random.choice([-1.5, 1.5]) if random.random() > 0.4 else 0
        obstacles.append(obs)

def generate_tail():
    global snake_tail
    for seg in snake_tail:
        destroy(seg)
    snake_tail.clear()
    for i in range(7):  
        segment = Entity(
            model='sphere',
            texture='noise',
            color=color.rgb(160, 10, 10),
            position=(0, 1.2, -20 - (i * 2)),
            scale=2.2 - (i * 0.15)
        )
        snake_tail.append(segment)

def start_game():
    global game_state, game_over_flag, start_delay, snake_speed
    menu_parent.disable()
    menu_light.disable() 
    end_game_text.disable() # Прячем старый текст победы/смерти
    
    game_state = "PLAYING"
    game_over_flag = False
    start_delay = 2.0
    snake_speed = snake_speed_base
    
    floor.enable()
    left_wall.enable()
    right_wall.enable()
    distance_text.enable()
    
    player.enable()
    player.position = (0, 0, 10) # ИСПРАВЛЕНИЕ: Ставим игрока на пол (Y=0 вместо Y=2.0)
    player.speed = 12
    mouse.locked = True
    
    snake_head.enable()
    snake_head.parent = scene
    snake_head.position = (0, 1.2, -20)
    snake_head.scale = 2.5
    snake_head.color = color.rgb(120, 0, 0)
    
    scene.fog_density = 0.045
    
    generate_obstacles()
    generate_tail()

# ИСПРАВЛЕНИЕ ПРОБЛЕМЫ 2 (СБРОС И ПРОБЕЛ): Полная зачистка старых объектов при возврате в меню
def back_to_menu():
    global game_state
    game_state = "MENU"
    
    player.disable()
    snake_head.disable()
    end_game_text.disable()
    
    # Полностью уничтожаем хвост и ящики, чтобы они не оставались в мире
    for seg in snake_tail: destroy(seg)
    for obs in obstacles: destroy(obs)
    snake_tail.clear()
    obstacles.clear()
    
    floor.disable()
    left_wall.disable()
    right_wall.disable()
    distance_text.disable()
    
    menu_light.enable() 
    menu_parent.enable()
    mouse.locked = False

start_button.on_click = start_game
exit_button.on_click = application.quit

def input(key):
    if key == 'escape':
        application.quit()

def update():
    global snake_speed, game_over_flag, start_delay
    
    if game_state != "PLAYING":
        return

    if game_over_flag:
        # Теперь при нажатии ПРОБЕЛА или ENTER всё корректно сбросится и откроется меню
        if held_keys['space'] or held_keys['enter']:
            back_to_menu()
        return

    if start_delay > 0:
        start_delay -= time.dt
        distance_text.text = f'RUN FORWARD IN: {round(start_delay, 1)}s'
        return

    # Логика преследования
    snake_speed += time.dt * 0.06  
    
    prev_pos = Vec3(snake_head.position)
    snake_head.z += snake_speed * time.dt

    for segment in snake_tail:
        target_pos = prev_pos
        prev_pos = Vec3(segment.position)
        segment.position = lerp(segment.position, target_pos, time.dt * 15)

    # Движущиеся препятствия
    for obs in obstacles:
        if obs.speed_x != 0:
            obs.x += obs.speed_x * time.dt
            if abs(obs.x) > (CORRIDOR_WIDTH / 2 - 0.6):
                obs.speed_x *= -1  

    # Интерфейс
    remaining_dist = int(CORRIDOR_LENGTH - player.z)
    distance_to_snake = int(player.z - snake_head.z)
    
    if remaining_dist > 0:
        distance_text.text = f'To Exit: {remaining_dist}m | Monster: {distance_to_snake}m'
    
    if distance_to_snake < 18:
        camera.x += random.uniform(-0.035, 0.035)
        camera.y += random.uniform(-0.035, 0.035)

    # Условие проигрыша и СКРИМЕР
    if snake_head.z >= player.z - 2.2:
        game_over_flag = True
        player.speed = 0
        mouse.locked = False
        
        scene.fog_density = 0 
        snake_head.parent = camera
        snake_head.position = (0, 0, 1.3)
        snake_head.scale = 4.5
        snake_head.color = color.white
        
        ursfx([(0.0, 0.0), (0.1, 0.9), (0.15, 0.75), (0.6, 0.75), (1.0, 0.0)], volume=0.95, wave='noise', pitch=0, pitch_change=0, speed=1)
        
        end_game_text.text = 'YOU DIE.\nPRESS SPACE FOR MENU.'
        end_game_text.color = color.red
        end_game_text.enable()

    # Условие победы
    if player.z >= CORRIDOR_LENGTH:
        game_over_flag = True
        player.speed = 0
        mouse.locked = False
        
        end_game_text.text = 'YOU ESCAPED!\nPRESS SPACE FOR MENU.'
        end_game_text.color = color.gold
        end_game_text.enable()

# Запуск игры
app.run()