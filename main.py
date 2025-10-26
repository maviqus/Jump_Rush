#  filename: main.py
#  author: Yonah Aviv
#  date created: 2020-11-10 6:21 p.m.
#  last modified: 2020-11-18
#  Pydash: Similar to Geometry Dash, a rhythm based platform game, but programmed using the pygame library in Python


"""CONTROLS
Anywhere -> ESC: exit
Main menu -> 1: go to previous level. 2: go to next level. SPACE: start game.
Game -> SPACE/UP: jump, and activate orb
    orb: jump in midair when activated
If you die or beat the level, press SPACE to restart or go to the next level

"""

import csv
import os
import random
from start_menu import run_start_menu  # Jump Rush menu import
from congratulations_menu import run_congratulations  # Congratulations screen import
from game_save import load_game_data, save_game_data, add_coins, complete_level, get_total_coins, get_selected_avatar, set_best_time, get_best_times  # Save system

# import the pygame module
import pygame

# will make it easier to use pygame functions
from pygame.math import Vector2
from pygame.draw import rect
from game_over_menu import run_game_over  # Game Over UI
import time

# initializes the pygame module
pygame.init()

# creates a screen variable of size 800 x 600
screen = pygame.display.set_mode([800, 600])

# controls the main game while loop
done = False

# controls whether or not to start the game from the main menu
start = False

# sets the frame rate of the program
clock = pygame.time.Clock()

"""
CONSTANTS
"""
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

"""lambda functions are anonymous functions that you can assign to a variable.
e.g.
1. x = lambda x: x + 2  # takes a parameter x and adds 2 to it
2. print(x(4))
>>6
"""
color = lambda: tuple([random.randint(0, 255) for i in range(3)])  # lambda function for random color, not a constant.
GRAVITY = Vector2(0, 0.86)  # Vector2 is a pygame
# tile size (width and height of map tiles / sprites)
TILE_SIZE = 32
TILE_HALF = TILE_SIZE // 2
# player visual size (smaller than tile if desired)
PLAYER_SIZE = 20
PLAYER_HALF = PLAYER_SIZE // 2
# Debug / tuning flags
DEBUG_EASY_MODE = False  # toggled by pressing E
DEBUG_NOCLIP = False     # toggled by pressing G (full noclip)
DEBUG_INVINCIBLE = False  # toggled by V (test mode: no damage at all)
DEBUG_PASS_SPIKES = False  # toggled by X (ignore spike deaths only)
GRAVITY_BASE = GRAVITY.y
JUMP_BASE = 13.5  # was 10, slight increase for clearing 2-tile spike gaps
EASY_GRAVITY = 0.3
EASY_JUMP = 12
# game speed scaling: values < 1.0 slow the game, values > 1.0 speed it up
GAME_SPEED = 0.7
# base horizontal speed for the player (will be multiplied by GAME_SPEED)
PLAYER_SPEED = 6

"""
Main player class
"""


class Player(pygame.sprite.Sprite):
    """Class for player. Holds update method, win and die variables, collisions and more."""
    win: bool
    died: bool

    def __init__(self, image, platforms, pos, *groups):
        """
        :param image: block face avatar
        :param platforms: obstacles such as coins, blocks, spikes, and orbs
        :param pos: starting position
        :param groups: takes any number of sprite groups.
        """
        super().__init__(*groups)
        self.onGround = False  # player on ground?
        self.platforms = platforms  # obstacles but create a class variable for it
        self.died = False  # player died?
        self.win = False  # player beat level?
        # scale player separately from tile size so we can make the player smaller
        self.image = pygame.transform.smoothscale(image, (PLAYER_SIZE, PLAYER_SIZE))
        self.rect = self.image.get_rect(center=pos)  # get rect gets a Rect object from the image
        self.jump_amount = JUMP_BASE  # jump strength
        self.particles = []  # player trail
        self.isjump = False  # is the player jumping?
        self.vel = Vector2(0, 0)  # velocity starts at zero

    def draw_particle_trail(self, x, y, color=(255, 255, 255)):
        """draws a trail of particle-rects in a line at random positions behind the player"""

        self.particles.append(
                [[x - 5, y - 8], [random.randint(0, 25) / 10 - 1, random.choice([0, 0])],
                 random.randint(5, 8)])

        for particle in self.particles:
            particle[0][0] += particle[1][0]
            particle[0][1] += particle[1][1]
            particle[2] -= 0.5
            particle[1][0] -= 0.4
            rect(alpha_surf, color,
                 ([int(particle[0][0]), int(particle[0][1])], [int(particle[2]) for i in range(2)]))
            if particle[2] <= 0:
                self.particles.remove(particle)

    def collide(self, yvel, platforms):
        global coins, level_coins, DEBUG_NOCLIP

        # If noclip debugging is enabled, skip all collision handling so the
        # player can pass through objects for map testing.
        if DEBUG_NOCLIP:
            return

        for p in platforms:
            if pygame.sprite.collide_rect(self, p):
                """pygame sprite builtin collision method,
                sees if player is colliding with any obstacles"""
                if isinstance(p, Orb) and (keys[pygame.K_UP] or keys[pygame.K_SPACE]):
                    pygame.draw.circle(alpha_surf, (255, 255, 0), p.rect.center, 18)
                    screen.blit(pygame.image.load("images/editor-0.9s-47px.gif"), p.rect.center)
                    self.jump_amount = 12  # gives a little boost when hit orb
                    self.jump()
                    self.jump_amount = 10  # return jump_amount to normal

                if isinstance(p, End):
                    self.win = True

                if isinstance(p, Spike):
                    # If player is invincible, full noclip, or configured to pass spikes,
                    # ignore spike deaths. Otherwise check effective spike rect.
                    if DEBUG_NOCLIP or DEBUG_INVINCIBLE or DEBUG_PASS_SPIKES:
                        pass
                    else:
                        # shrink spike effective rect (top part only)
                        spike_effective = p.rect.inflate(-14, -8).copy()
                        spike_effective.bottom = p.rect.bottom - 6
                        if self.rect.colliderect(spike_effective):
                            self.died = True

                if isinstance(p, Coin):
                    # Update persistent coin count
                    save_data = add_coins(1)
                    global coins, new_avatar_unlocked
                    coins = save_data["total_coins"]
                    level_coins += 1
                    
                    # Check if avatar was unlocked
                    if save_data.get("new_unlock"):
                        new_avatar_unlocked = save_data["new_unlock"]

                    # erases a coin
                    p.rect.x = 0
                    p.rect.y = 0

                if isinstance(p, Platform):  # these are the blocks (may be confusing due to self.platforms)

                    if yvel > 0:
                        """if player is going down(yvel is +)"""
                        self.rect.bottom = p.rect.top  # dont let the player go through the ground
                        self.vel.y = 0  # rest y velocity because player is on ground

                        # set self.onGround to true because player collided with the ground
                        self.onGround = True

                        # reset jump
                        self.isjump = False
                    elif yvel < 0:
                        """if yvel is (-),player collided while jumping"""
                        self.rect.top = p.rect.bottom  # player top is set the bottom of block like it hits it head
                    else:
                        """otherwise, if player collides with a block, he/she dies."""
                        self.vel.x = 0
                        self.rect.right = p.rect.left  # dont let player go through walls
                        if not DEBUG_NOCLIP:
                            if not DEBUG_INVINCIBLE:
                                self.died = True

    def jump(self):
        self.vel.y = -self.jump_amount  # players vertical velocity is negative so ^

    def update(self):
        """update player"""
        if self.isjump:
            if self.onGround:
                """if player wants to jump and player is on the ground: only then is jump allowed"""
                self.jump()

        if not self.onGround:  # only accelerate with gravity if in the air
            self.vel += GRAVITY  # Gravity falls

            # max falling speed
            if self.vel.y > 100: self.vel.y = 100

        # do x-axis collisions
        self.collide(0, self.platforms)

        # increment in y direction
        self.rect.top += self.vel.y

        # assuming player in the air, and if not it will be set to inversed after collide
        self.onGround = False

        # do y-axis collisions
        self.collide(self.vel.y, self.platforms)

        # Kill the player if they fall off the bottom of the visible playfield.
        if self.rect.top > screen.get_height():
            if not (DEBUG_NOCLIP or DEBUG_INVINCIBLE):
                self.died = True

        # check if we won or if player won
        eval_outcome(self.win, self.died)


"""
Obstacle classes
"""


# Parent class
class Draw(pygame.sprite.Sprite):
    """parent class to all obstacle classes; Sprite class"""

    def __init__(self, image, pos, *groups):
        super().__init__(*groups)
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)


#  ====================================================================================================================#
#  classes of all obstacles. this may seem repetitive but it is useful(to my knowledge)
#  ====================================================================================================================#
# children
class Platform(Draw):
    """block"""

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


class Spike(Draw):
    """spike"""

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


class Coin(Draw):
    """coin. get 6 and you win the game"""

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


class Orb(Draw):
    """orb. click space or up arrow while on it to jump in midair"""

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


class Trick(Draw):
    """block, but its a trick because you can go through it"""

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


class End(Draw):
    "place this at the end of the level"

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)


"""
Functions
"""


def init_level(map):
    """this is similar to 2d lists. it goes through a list of lists, and creates instances of certain obstacles
    depending on the item in the list"""
    x = 0
    y = 0

    for row in map:
        for col in row:

            if col == "0":
                Platform(block, (x, y), elements)

            if col == "Coin":
                Coin(coin, (x, y), elements)

            if col == "Spike":
                Spike(spike, (x, y), elements)
            if col == "Orb":
                orbs.append([x, y])

                Orb(orb, (x, y), elements)

            if col == "T":
                Trick(trick, (x, y), elements)

            if col == "End":
                End(avatar, (x, y), elements)
            x += TILE_SIZE
        y += TILE_SIZE
        x = 0


def blitRotate(surf, image, pos, originpos: tuple, angle: float):
    """
    rotate the player
    :param surf: Surface
    :param image: image to rotate
    :param pos: position of image
    :param originpos: x, y of the origin to rotate about
    :param angle: angle to rotate
    """
    # calcaulate the axis aligned bounding box of the rotated image
    w, h = image.get_size()
    box = [Vector2(p) for p in [(0, 0), (w, 0), (w, -h), (0, -h)]]
    box_rotate = [p.rotate(angle) for p in box]

    # make sure the player does not overlap, uses a few lambda functions(new things that we did not learn about number1)
    min_box = (min(box_rotate, key=lambda p: p[0])[0], min(box_rotate, key=lambda p: p[1])[1])
    max_box = (max(box_rotate, key=lambda p: p[0])[0], max(box_rotate, key=lambda p: p[1])[1])
    # calculate the translation of the pivot
    pivot = Vector2(originpos[0], -originpos[1])
    pivot_rotate = pivot.rotate(angle)
    pivot_move = pivot_rotate - pivot

    # calculate the upper left origin of the rotated image
    origin = (pos[0] - originpos[0] + min_box[0] - pivot_move[0], pos[1] - originpos[1] - max_box[1] + pivot_move[1])

    # get a rotated image
    rotated_image = pygame.transform.rotozoom(image, angle, 1)

    # rotate and blit the image
    surf.blit(rotated_image, origin)


def won_screen():
    """show this screen when beating a level"""
    global attempts, level, fill, start, done, start_time
    attempts = 0
    player_sprite.clear(player.image, screen)
    
    # Calculate time taken
    time_taken = time.time() - start_time
    
    # Save best time
    set_best_time(level + 1, time_taken)

    # Mark level as completed (pass time_taken required by save system)
    complete_level(level + 1, time_taken)  # level is 0-indexed, save as 1-indexed
    
    # Show congratulations screen
    choice = run_congratulations(screen, 
                               level_completed=level + 1,  # level is 0-indexed, display as 1-indexed
                               coins_collected=level_coins, 
                               total_coins=coins,
                               new_avatar_unlocked=new_avatar_unlocked)
    
    if choice.get('action') == 'quit':
        done = True
        return
    elif choice.get('action') == 'next_level':
        # Move to next level
        level += 1
        if level >= len(levels):
            # All levels completed! Could show final congratulations
            level = 0  # Loop back to first level for now
        reset()
    elif choice.get('action') == 'retry':
        # Retry current level
        reset()
    elif choice.get('action') == 'home':
        # Return to start menu
        try:
            global avatar
            _menu = run_start_menu(screen)
            if _menu.get("quit"):
                done = True
                return
            else:
                chosen_avatar_path = _menu.get("avatar_path")
                if chosen_avatar_path:
                    try:
                        avatar = pygame.image.load(chosen_avatar_path).convert_alpha()
                    except Exception:
                        pass # keep current avatar
                else:
                    selected_avatar = get_selected_avatar()
                    try:
                        avatar_path = os.path.join("images", "avatar", selected_avatar)
                        if not os.path.exists(avatar_path):
                            avatar_path = os.path.join("images", selected_avatar)
                        avatar = pygame.image.load(avatar_path).convert_alpha()
                    except Exception:
                        avatar = pygame.image.load(os.path.join("images", "avatar.png")).convert_alpha()
                start = True
                # Keep current level, just reset
                reset()
        except Exception as e:
            print(f"Error returning to menu: {e}")
            done = True


def death_screen():
    """Game Over modal with Retry/Home"""
    global attempts, fill, start, done, screen, level
    # Reset any fill/overlay used by previous UI if exists
    fill = 0
    # Prepare scores if available (safe)
    total_score = globals().get('score', None)
    best_score  = globals().get('best', None)
    # Show modal

    choice = run_game_over(screen, total_score=total_score, best_score=best_score)
    if choice.get("quit"):
        done = True
        return
    action = choice.get("action")
    if action == "retry":
        start = True
        reset()
        return
    if action == "home":
        # Return to start menu, then reset/start
        try:
            global avatar
            _menu = run_start_menu(screen)
            if _menu.get("quit"):
                done = True
                return
            else:
                # Get selected level from menu (1-indexed, convert to 0-indexed)
                chosen_level = _menu.get("level", level + 1)
                level = max(0, min(chosen_level - 1, len(levels) - 1))
                # Reload avatar if selected in menu
                chosen_avatar_path = _menu.get("avatar_path")
                if chosen_avatar_path:
                    try:
                        avatar = pygame.image.load(chosen_avatar_path).convert_alpha()
                    except Exception:
                        pass  # keep current avatar
                else:
                    selected_avatar = get_selected_avatar()
                    try:
                        avatar_path = os.path.join("images", "avatar", selected_avatar)
                        if not os.path.exists(avatar_path):
                            avatar_path = os.path.join("images", selected_avatar)
                        avatar = pygame.image.load(avatar_path).convert_alpha()
                    except Exception:
                        avatar = pygame.image.load(os.path.join("images", "avatar.png")).convert_alpha()
                start = True
                reset()
        except Exception:
            # If start menu fails, fall back to retry
            pass
        return

def eval_outcome(won: bool, died: bool):
    """simple function to run the win or die screen after checking won or died"""
    if won:
        won_screen()
    if died:
        death_screen()


def block_map(level_num):
    """
    :type level_num: rect(screen, BLACK, (0, 0, 32, 32))
    open a csv file that contains the right level map
    """
    lvl = []
    with open(level_num, newline='') as csvfile:
        trash = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in trash:
            lvl.append(row)
    return lvl


def start_screen():
    """main menu. option to switch level, and controls guide, and game overview."""
    global level
    if not start:
        screen.fill(BLACK)
        if pygame.key.get_pressed()[pygame.K_1]:
            level = 0
        if pygame.key.get_pressed()[pygame.K_2]:
            level = 1
        if pygame.key.get_pressed()[pygame.K_3]:
            level = min(2, len(levels) - 1)
        if pygame.key.get_pressed()[pygame.K_4]:
            level = min(3, len(levels) - 1)
        if pygame.key.get_pressed()[pygame.K_5]:
            level = min(4, len(levels) - 1)
        if pygame.key.get_pressed()[pygame.K_6]:
            level = min(5, len(levels) - 1)

        welcome = font.render(f"Welcome to Pydash. choose level({level + 1}) by keypad", True, WHITE)

        controls = font.render("Controls: jump: Space/Up exit: Esc", True, GREEN)

        screen.blits([[welcome, (100, 100)], [controls, (100, 400)], [tip, (100, 500)]])

        level_memo = font.render(f"Level {level + 1}.", True, (255, 255, 0))
        screen.blit(level_memo, (100, 200))


def reset():
    """resets the sprite groups, music, etc. for death and new level"""
    global player, elements, player_sprite, level, level_coins, new_avatar_unlocked, start_time
    level_coins = 0  # reset coins for new level
    new_avatar_unlocked = None  # reset avatar unlock status
    start_time = time.time()  # Record start time for level

    if level == 1:
        pygame.mixer.music.load(os.path.join("music", "castle-town.mp3"))
    pygame.mixer_music.play()
    player_sprite = pygame.sprite.Group()
    elements = pygame.sprite.Group()
    player = Player(avatar, elements, (150, 150), player_sprite)
    init_level(
            block_map(
                    level_num=levels[level]))


def move_map():
    """moves obstacles along the screen"""
    for sprite in elements:
        sprite.rect.x -= CameraX


def draw_stats(surf, money=0):
    """
    draws progress bar for level, number of attempts, displays coins collected, and progressively changes progress bar
    colors
    """
    global fill
    progress_colors = [pygame.Color("red"), pygame.Color("orange"), pygame.Color("yellow"), pygame.Color("lightgreen"),
                       pygame.Color("green")]

    tries = font.render(f" Attempt {str(attempts)}", True, WHITE)
    BAR_LENGTH = 600
    BAR_HEIGHT = 10
    for i in range(1, money):
        screen.blit(coin, (BAR_LENGTH, 25))
    fill += 0.5
    outline_rect = pygame.Rect(0, 0, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pygame.Rect(0, 0, fill, BAR_HEIGHT)
    # avoid out-of-range by clamping the index
    max_idx = len(progress_colors) - 1
    idx = int(fill / 100)
    if idx < 0: idx = 0
    if idx > max_idx: idx = max_idx
    col = progress_colors[idx]
    rect(surf, col, fill_rect, 0, 4)
    rect(surf, WHITE, outline_rect, 3, 4)
    screen.blit(tries, (BAR_LENGTH, 0))

def draw_leaderboard_widget(surf):
    """Draw a small leaderboard widget in top right corner during gameplay"""
    import game_save
    best_times = game_save.get_best_times()
    total_coins = game_save.get_total_coins()
    
    W, H = surf.get_size()
    # Square box: 200x200 in top left
    box_rect = pygame.Rect(10, 10, 200, 200)
    pygame.draw.rect(surf, (26, 28, 36), box_rect, border_radius=8)
    pygame.draw.rect(surf, (100, 100, 120), box_rect, width=2, border_radius=8)
    
    # Title: "bang xep hang"
    title_font = pygame.font.SysFont("arial", 16, bold=True)
    title = title_font.render("bang xep hang", True, (255, 255, 255))
    title_rect = title.get_rect(center=(box_rect.centerx, box_rect.top + 20))
    surf.blit(title, title_rect)
    
    # Items
    items = [f"Xu: {total_coins}"]
    for lvl in range(1, 7):
        time = best_times.get(str(lvl))
        if time is not None:
            items.append(f"Lv{lvl}: {time:.1f}s")
        else:
            items.append(f"Lv{lvl}: Chua")
    
    y_start = title_rect.bottom + 10
    item_font = pygame.font.SysFont("arial", 12)
    for i, item in enumerate(items[:6]):  # Limit to 6 items to fit
        item_surf = item_font.render(item, True, (200, 200, 200))
        item_rect = item_surf.get_rect(topleft=(box_rect.left + 10, y_start + i * 15))
        surf.blit(item_surf, item_rect)

def wait_for_key():
    """separate game loop for waiting for a key press while still running game loop
    """
    global level, start
    waiting = True
    # --- video/display safety guard ---
    global screen, done
    if not pygame.get_init():
        pygame.init()
    if not pygame.display.get_init():
        pygame.display.init()
        try:
            screen  # ensure exists
        except NameError:
            try:
                WIDTH, HEIGHT
            except NameError:
                WIDTH, HEIGHT = 1280, 720
            screen = pygame.display.set_mode((WIDTH, HEIGHT))
    while waiting:
        clock.tick(60)
        pygame.display.flip()

        if not start:
            start_screen()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True; waiting = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    start = True
                    waiting = False
                if event.key == pygame.K_ESCAPE:
                    done = True; waiting = False


def coin_count(coins):
    """counts coins"""
    if coins >= 3: 
        coins = 3
    coins += 1
    return coins


def resize(img, size=(TILE_SIZE, TILE_SIZE)):
    """resize images
    :param img: image to resize
    :type img: im not sure, probably an object
    :param size: default is 32 because that is the tile size
    :type size: tuple
    :return: resized img

    :rtype:object?
    """
    resized = pygame.transform.smoothscale(img, size)
    return resized


"""
Global variables
"""
font = pygame.font.SysFont("lucidaconsole", 20)

# square block face is main character the icon of the window is the block face
avatar = pygame.image.load(os.path.join("images", "avatar.png")).convert_alpha()  # load the main character
pygame.display.set_icon(avatar)
#  this surface has an alpha value with the colors, so the player trail will fade away using opacity
alpha_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

# sprite groups
player_sprite = pygame.sprite.Group()
elements = pygame.sprite.Group()

# images
spike = pygame.image.load(os.path.join("images", "obj-spike.png"))
spike = resize(spike, (TILE_SIZE, TILE_SIZE))
coin = pygame.image.load(os.path.join("images", "coin.png"))
coin = pygame.transform.smoothscale(coin, (TILE_SIZE, TILE_SIZE))
block = pygame.image.load(os.path.join("images", "block_1.png"))
block = pygame.transform.smoothscale(block, (TILE_SIZE, TILE_SIZE))
orb = pygame.image.load((os.path.join("images", "orb-yellow.png")))
orb = pygame.transform.smoothscale(orb, (TILE_SIZE, TILE_SIZE))
trick = pygame.image.load((os.path.join("images", "obj-breakable.png")))
trick = pygame.transform.smoothscale(trick, (TILE_SIZE, TILE_SIZE))

#  ints
fill = 0
num = 0
CameraX = 0
attempts = 0
coins = get_total_coins()  # Load total coins from save file
level_coins = 0  # coins collected in current level
new_avatar_unlocked = None  # track if avatar was unlocked this level
angle = 0
level = 0
start_time = 0  # Track level start time
level_start_time = 0

# list
particles = []
orbs = []
win_cubes = []

# initialize level with
levels = ["level_1.csv", "level_2.csv", "level_3.csv", "level_4.csv", "level_5.csv"]
level_list = block_map(levels[level])
level_width = (len(level_list[0]) * TILE_SIZE)
level_height = len(level_list) * TILE_SIZE
init_level(level_list)

# set window title suitable for game
pygame.display.set_caption('Pydash: Geometry Dash in Python')

# initialize the font variable to draw text later
text = font.render('image', False, (255, 255, 0))

# music
music = pygame.mixer_music.load(os.path.join("music", "bossfight-Vextron.mp3"))
pygame.mixer_music.play()

# bg image
# Backgrounds: load per-level backgrounds from images/background, fallback to images/bg.png
def load_backgrounds(folder="images/background", default_path=os.path.join("images", "bg.png")):
    """Load per-level backgrounds.
    Supports either image files directly in `folder` (sorted order) or subfolders named "level <n>" with image files inside.
    Returns (bgs, default_bg) where bgs is a list indexed by level (0-based).
    """
    bgs = []
    try:
        if os.path.isdir(folder):
            # Check for subfolders like 'level 1', 'level 2', ...
            entries = sorted(os.listdir(folder))
            # If entries are directories, treat each as a level folder
            level_dirs = [e for e in entries if os.path.isdir(os.path.join(folder, e))]
            if level_dirs:
                for d in level_dirs:
                    dpath = os.path.join(folder, d)
                    imgs = sorted([f for f in os.listdir(dpath) if os.path.isfile(os.path.join(dpath, f))])
                    if imgs:
                        # pick first image that loads successfully
                        loaded = None
                        for fn in imgs:
                            fpath = os.path.join(dpath, fn)
                            try:
                                img = pygame.image.load(fpath).convert()
                                img = pygame.transform.smoothscale(img, screen.get_size())
                                loaded = img
                                break
                            except Exception:
                                continue
                        if loaded:
                            bgs.append(loaded)
                        else:
                            # placeholder for missing image
                            surf = pygame.Surface(screen.get_size())
                            surf.fill(BLACK)
                            bgs.append(surf)
            else:
                # No subfolders; treat files directly as ordered backgrounds
                files = sorted([f for f in entries if os.path.isfile(os.path.join(folder, f))])
                for fn in files:
                    try:
                        img = pygame.image.load(os.path.join(folder, fn)).convert()
                        img = pygame.transform.smoothscale(img, screen.get_size())
                        bgs.append(img)
                    except Exception:
                        pass
    except Exception:
        pass
    # load default as separate surface for fallback
    try:
        default_bg = pygame.image.load(default_path).convert()
        default_bg = pygame.transform.smoothscale(default_bg, screen.get_size())
    except Exception:
        # create a plain surface if default missing
        default_bg = pygame.Surface(screen.get_size())
        default_bg.fill(BLACK)
    return bgs, default_bg

# load backgrounds for levels
backgrounds, default_bg = load_backgrounds()

# create object of player class
player = Player(avatar, elements, (150, 150), player_sprite)

# show tip on start and on death
tip = font.render("tip: tap and hold for the first few seconds of the level", True, BLUE)

# -------------------- Jump Rush Start Menu Integration --------------------
import sys, pygame
pygame.display.set_caption("Jump Rush — Menu")

_stages = [f"Level {i}" for i in range(1, len(levels) + 1)]

_menu = run_start_menu(screen, stages=_stages)

if _menu.get("quit"):
    pass; sys.exit()

# Get selected level from menu (1-indexed, convert to 0-indexed)
chosen_level = _menu.get("level", 1)
level = max(0, min(chosen_level - 1, len(levels) - 1))

# Load avatar from avatar_path or selected avatar from save file
chosen_avatar_path = _menu.get("avatar_path")
if chosen_avatar_path:
    try:
        avatar = pygame.image.load(chosen_avatar_path).convert_alpha()
    except Exception:
        # fallback to default if load fails
        avatar = pygame.image.load(os.path.join("images", "avatar.png")).convert_alpha()
else:
    # Load selected avatar from save file
    selected_avatar = get_selected_avatar()
    try:
        # Try images/avatar/ directory first
        avatar_path = os.path.join("images", "avatar", selected_avatar)
        if not os.path.exists(avatar_path):
            # Fallback to images/ directory
            avatar_path = os.path.join("images", selected_avatar)
        avatar = pygame.image.load(avatar_path).convert_alpha()
    except Exception:
        # Ultimate fallback
        avatar = pygame.image.load(os.path.join("images", "avatar.png")).convert_alpha()

# Example of swapping avatar if you have assets:
# if chosen_char == "Slime":
#     avatar = pygame.image.load(os.path.join("images", "slime.png")).convert_alpha()

start = True
reset()
# --------------------------------------------------------------------------
while not done:
    keys = pygame.key.get_pressed()
    # Handle debug toggles (once per keydown, so we rely on event loop below to flip states)
    # Apply easy mode values
    if DEBUG_EASY_MODE:
        GRAVITY.y = EASY_GRAVITY * GAME_SPEED
        player.jump_amount = EASY_JUMP * GAME_SPEED
    else:
        GRAVITY.y = GRAVITY_BASE * GAME_SPEED
        player.jump_amount = JUMP_BASE * GAME_SPEED

    if not start:
        wait_for_key()
        reset()

        start = True

    # horizontal speed scaled by GAME_SPEED
    player.vel.x = PLAYER_SPEED * GAME_SPEED

    eval_outcome(player.win, player.died)
    if keys[pygame.K_UP] or keys[pygame.K_SPACE]:
        player.isjump = True

    # Reduce the alpha of all pixels on this surface each frame.
    # Control the fade2 speed with the alpha value.

    alpha_surf.fill((255, 255, 255, 1), special_flags=pygame.BLEND_RGBA_MULT)

    player_sprite.update()
    CameraX = player.vel.x  # for moving obstacles (already scaled by GAME_SPEED)
    move_map()  # apply CameraX to all elements

    # Choose per-level background if available, otherwise fallback to default
    try:
        # Force level 1 (index 0) to use the default background
        if level == 0:
            bg_to_draw = default_bg
        else:
            bg_to_draw = backgrounds[level] if 0 <= level < len(backgrounds) else default_bg
    except Exception:
        bg_to_draw = default_bg
    screen.blit(bg_to_draw, (0, 0))  # Clear the screen(with the bg)

    player.draw_particle_trail(player.rect.left - 1, player.rect.bottom + 2,
                               WHITE)
    screen.blit(alpha_surf, (0, 0))  # Blit the alpha_surf onto the screen.
    draw_stats(screen, coin_count(coins))

    if player.isjump:
        # rotate the player by an angle and blit it if player is jumping
        angle -= 8.1712  # this may be the angle needed to do a 360 deg turn in the length covered in one jump by player
        blitRotate(screen, player.image, player.rect.center, (PLAYER_HALF, PLAYER_HALF), angle)
    else:
        # if player.isjump is false, then just blit it normally (by using Group().draw() for sprites)
        player_sprite.draw(screen)  # draw player sprite group
    elements.draw(screen)  # draw all other obstacles

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                """User friendly exit"""
                done = True
            elif event.key == pygame.K_e:
                DEBUG_EASY_MODE = not DEBUG_EASY_MODE
            elif event.key == pygame.K_g:
                # Full noclip: bypass collisions entirely
                DEBUG_NOCLIP = not DEBUG_NOCLIP
            elif event.key == pygame.K_x:
                # Toggle passing spikes only (still collide with platforms)
                DEBUG_PASS_SPIKES = not DEBUG_PASS_SPIKES
            elif event.key == pygame.K_v:
                # Toggle invincibility
                DEBUG_INVINCIBLE = not DEBUG_INVINCIBLE
            elif event.key == pygame.K_F1:
                level = 0
                reset()
            elif event.key == pygame.K_F2:
                level = 1
                reset()
            elif event.key == pygame.K_F3:
                level = min(2, len(levels) - 1)
                reset()
            elif event.key == pygame.K_F4:
                level = min(3, len(levels) - 1)
                reset()
            elif event.key == pygame.K_F5:
                level = min(4, len(levels) - 1)
                reset()
            elif event.key == pygame.K_F6:
                level = min(5, len(levels) - 1)
                reset()
            if event.key == pygame.K_2:
                """change level by keypad"""
                player.jump_amount += 1

            if event.key == pygame.K_1:
                """change level by keypad"""

                player.jump_amount -= 1

    pygame.display.flip()
    clock.tick(60)
pygame.quit()