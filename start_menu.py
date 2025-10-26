import pygame as pg
import math, os, random
from typing import List, Optional, Tuple, Dict
from game_save import get_unlocked_avatars, is_level_unlocked

# --- Theme ---
COLOR_BG_DARK   = (10, 12, 18)
COLOR_TEXT_MAIN = (240, 248, 255)
COLOR_TEXT_SUB  = (190, 198, 210)
COLOR_CARD_BODY = (34, 38, 46)
COLOR_CARD_INNER= (52, 58, 66)
COLOR_BORDER    = (100, 112, 124)
COLOR_ACCENT    = (0, 255, 210)       # neon cyan-green
COLOR_ACCENT_2  = (255, 60, 200)      # magenta

BG_CANDIDATES = [
    "images/bg_start.png",
]

# UI/game speed for menu animations: values <1.0 slow animations
UI_GAME_SPEED = 0.7

LEVEL_DATA = [
    {"name": "The Beginning", "image": "images/background/level 1/20251019_210725_0002.png"},
    {"name": "Forest Frolic", "image": "images/background/level 2/20251019_211837_0002.png"},
    {"name": "Spike Gauntlet", "image": "images/background/level 3/20251020_092559_0002.png"},
    {"name": "Coin Craze", "image": "images/background/level 4/20251020_085609_0002.png"},
    {"name": " Final Challenge", "image": "images/background/level 5/20251020_090246_0002.png"},
]

# -------------------- UI Primitives --------------------

class LevelButton:
    """Custom level selection button with lock/unlock status"""
    def __init__(self, rect: pg.Rect, level_num: int, font: pg.font.Font, on_click):
        self.rect = pg.Rect(rect)
        self.level_num = level_num
        self.font = font
        self.on_click = on_click
        self.hover = False
        self.pressed = False
        self.unlocked = is_level_unlocked(level_num)
        
        level_info = LEVEL_DATA[self.level_num - 1]
        self.image = None
        if os.path.exists(level_info["image"]):
            try:
                img = pg.image.load(level_info["image"]).convert()
                self.image = pg.transform.smoothscale(img, (rect.width - 20, rect.height - 40))
            except pg.error:
                print(f"Warning: Could not load image for level {self.level_num}")

    def handle(self, event):
        if event.type == pg.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            if self.pressed and self.rect.collidepoint(event.pos) and self.unlocked:
                self.on_click(self.level_num)
            self.pressed = False

    def draw(self, surf: pg.Surface, t: float):
        # Refresh unlock status each draw
        self.unlocked = is_level_unlocked(self.level_num)
        
        # Colors based on unlock status
        if self.unlocked:
            bg_color = COLOR_ACCENT if self.hover else COLOR_CARD_BODY
            text_color = COLOR_BG_DARK if self.hover else COLOR_TEXT_MAIN
            border_color = COLOR_ACCENT_2 if self.hover else COLOR_BORDER
        else:
            bg_color = (50, 50, 50)
            text_color = (100, 100, 100)
            border_color = (80, 80, 80)
        
        # Draw button background
        pg.draw.rect(surf, bg_color, self.rect, border_radius=12)
        pg.draw.rect(surf, border_color, self.rect, 3, border_radius=12)
        
        level_info = LEVEL_DATA[self.level_num - 1]
        name = level_info["name"]

        if self.image:
            img_rect = self.image.get_rect(center=(self.rect.centerx, self.rect.centery - 10))
            surf.blit(self.image, img_rect)

        # Draw level name
        name_surf = self.font.render(name, True, text_color)
        name_rect = name_surf.get_rect(center=(self.rect.centerx, self.rect.bottom - 20))
        surf.blit(name_surf, name_rect)

        if not self.unlocked:
            lock_font = pg.font.SysFont("Arial", 72)
            lock_surf = lock_font.render("🔒", True, (0, 0, 0, 150))
            lock_rect = lock_surf.get_rect(center=self.rect.center)
            surf.blit(lock_surf, lock_rect)

class Button:
    def __init__(self, rect: pg.Rect, text: str, font: pg.font.Font,
                 on_click, *, glow=False, image_path=None,
                 base_color=COLOR_TEXT_MAIN,
                 accent_color=COLOR_ACCENT):
        self.rect = pg.Rect(rect)
        self.text = text
        self.font = font
        self.on_click = on_click
        self.glow = glow
        self.image_path = image_path
        self.base_color = base_color
        self.accent_color = accent_color
        self.hover = False
        self.pressed = False

    def handle(self, event):
        if event.type == pg.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            if self.pressed and self.rect.collidepoint(event.pos):
                self.on_click()
            self.pressed = False

    def draw(self, surf: pg.Surface, t: float):
        radius = 16
        bg = (26, 28, 36)
        fg = self.base_color
        border = self.accent_color if self.hover else COLOR_BORDER

        pg.draw.rect(surf, bg, self.rect, border_radius=radius)
        pg.draw.rect(surf, border, self.rect, width=2, border_radius=radius)

        if self.image_path:
            try:
                img = pg.image.load(self.image_path).convert_alpha()
                img = pg.transform.smoothscale(img, (self.rect.width - 20, self.rect.height - 20))
                img_rect = img.get_rect(center=self.rect.center)
                surf.blit(img, img_rect)
            except Exception:
                # fallback to text
                txt_surf = self.font.render(self.text, True, fg)
                txt_rect = txt_surf.get_rect(center=self.rect.center)
                surf.blit(txt_surf, txt_rect)
        else:
            txt_surf = self.font.render(self.text, True, fg)
            txt_rect = txt_surf.get_rect(center=self.rect.center)
            surf.blit(txt_surf, txt_rect)

class Picker:
    def __init__(self, title: str, items: List[str], size: Tuple[int,int]):
        self.title = title
        self.items = items
        self.idx = 0
        self.size = size
        self.font_title = pg.font.SysFont("arial", 40, bold=True)
        self.font_hint = pg.font.SysFont("arial", 20)

    @property
    def value(self):
        if not self.items: return ""
        return self.items[self.idx % len(self.items)]

    def next(self):
        if self.items: self.idx = (self.idx + 1) % len(self.items)

    def prev(self):
        if self.items: self.idx = (self.idx - 1) % len(self.items)

    def draw(self, surf: pg.Surface):
        W, H = self.size
        overlay = pg.Surface((W, H), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surf.blit(overlay, (0, 0))

        card_w, card_h = int(W*0.62), int(H*0.6)
        card = pg.Rect((W-card_w)//2, (H-card_h)//2, card_w, card_h)
        
        pg.draw.rect(surf, COLOR_CARD_BODY, card, border_radius=16)
        pg.draw.rect(surf, COLOR_ACCENT, card, width=3, border_radius=16)
        inner_rect = card.inflate(-20, -20)
        pg.draw.rect(surf, COLOR_CARD_INNER, inner_rect, border_radius=12)

        title_s = self.font_title.render(self.title, True, COLOR_TEXT_MAIN)
        title_r = title_s.get_rect(midtop=(W//2, card.top-48))
        surf.blit(title_s, title_r)

        hint = "← / → switch    •    ENTER/SPACE confirm    •    ESC close"
        hint_s = self.font_hint.render(hint, True, COLOR_TEXT_SUB)
        hint_r = hint_s.get_rect(midtop=(W//2, card.bottom+12))
        surf.blit(hint_s, hint_r)

        ax = card.left - 36; ay = card.centery
        bx = card.right + 36; by = card.centery
        pg.draw.polygon(surf, COLOR_TEXT_MAIN, [(ax+16, ay), (ax, ay-14), (ax, ay+14)])
        pg.draw.polygon(surf, COLOR_TEXT_MAIN, [(bx-16, by), (bx, by-14), (bx, by+14)])

        sel = self.value
        avatar_dir = os.path.join("images", "avatar")
        candidate = os.path.join(avatar_dir, sel)
        if not os.path.isfile(candidate):
            candidate = os.path.join("images", sel)
        if os.path.isfile(candidate):
            try:
                thumb = pg.image.load(candidate).convert_alpha()
                thumb_size = int(min(card_w, card_h) * 0.5)
                thumb = pg.transform.smoothscale(thumb, (thumb_size, thumb_size))
                thumb_rect = thumb.get_rect(center=(card.centerx, card.centery - 20))
                surf.blit(thumb, thumb_rect)
            except Exception:
                pass

        base, ext = os.path.splitext(sel)
        display_name = base
        if len(display_name) > 24:
            display_name = display_name[:21] + "..."
            
        fname_font = pg.font.SysFont("arial", 24, bold=True)
        fname_text = fname_font.render(display_name, True, COLOR_TEXT_MAIN)
        fname_rect = fname_text.get_rect(midtop=(card.centerx, card.bottom - 50))
        surf.blit(fname_text, fname_rect)


def try_load_bg(size: Tuple[int,int]) -> Optional[pg.Surface]:
    W, H = size
    for path in BG_CANDIDATES:
        if os.path.isfile(path):
            img = pg.image.load(path).convert()
            iw, ih = img.get_size()
            scale = max(W/iw, H/ih)
            new_size = (int(iw*scale), int(ih*scale))
            img = pg.transform.smoothscale(img, new_size)
            x = (new_size[0] - W)//2
            y = (new_size[1] - H)//2
            img = img.subsurface(pg.Rect(x, y, W, H)).copy()
            return img
    return None

def run_start_menu(screen: pg.Surface,
                   stages: Optional[List[str]] = None) -> Dict[str, object]:
    pg.display.set_caption("Jump Rush — Start Menu")
    clock = pg.time.Clock()
    W, H = screen.get_size()

    selected_level = 1
    open_picker: Optional[Picker] = None

    try:
        title_font = pg.font.Font("PUSAB_.ttf", 72)
        btn_font = pg.font.Font("PUSAB_.ttf", 28)
        name_font = pg.font.Font("PUSAB_.ttf", 18)
    except pg.error:
        print("Warning: PUSAB_.ttf font not found. Falling back to system fonts.")
        title_font = pg.font.SysFont("arial", 72, bold=True)
        btn_font = pg.font.SysFont("arial", 28, bold=True)
        name_font = pg.font.SysFont("arial", 18, bold=True)

    result = {"start": False, "level": selected_level, "quit": False, "avatar_path": None}

    def draw_leaderboard(data):
        overlay = pg.Surface((W, H), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))

        card_size = min(int(W * 0.6), int(H * 0.6))  # Larger size
        card = pg.Rect(W - card_size - 10, 10, card_size, card_size)  # Top right
        pg.draw.rect(screen, (26, 28, 36), card, border_radius=16)
        pg.draw.rect(screen, COLOR_BORDER, card, width=2, border_radius=16)

        # Close button
        close_btn_rect = pg.Rect(card.right - 50, card.top + 10, 40, 40)
        pg.draw.rect(screen, (200, 50, 50), close_btn_rect, border_radius=8)
        pg.draw.rect(screen, (255, 100, 100), close_btn_rect, width=2, border_radius=8)
        close_text = pg.font.SysFont("arial", 24, bold=True).render("X", True, (255, 255, 255))
        close_text_rect = close_text.get_rect(center=close_btn_rect.center)
        screen.blit(close_text, close_text_rect)

        title = data.get("title", "Leaderboard")
        title_s = btn_font.render(title, True, COLOR_TEXT_MAIN)
        title_r = title_s.get_rect(center=(card.centerx, card.top + 50))
        screen.blit(title_s, title_r)

        items = data.get("items", [])
        y_start = title_r.bottom + 20
        for i, item in enumerate(items):
            item_s = name_font.render(item, True, COLOR_TEXT_SUB)
            item_r = item_s.get_rect(topleft=(card.left + 20, y_start + i * 25))
            screen.blit(item_s, item_r)

        # Add BHX at bottom
        bhx_text = name_font.render("BHX", True, COLOR_TEXT_SUB)
        bhx_rect = bhx_text.get_rect(center=(card.centerx, card.bottom - 20))
        screen.blit(bhx_text, bhx_rect)

    def on_start():
        result["start"] = True

    def on_select_level(level_num):
        nonlocal selected_level
        selected_level = level_num
        result["level"] = level_num
        on_start()

    def on_pick_avatar():
        nonlocal open_picker
        unlocked_avatars = get_unlocked_avatars()
        avatar_files = []
        avatar_dir = os.path.join("images", "avatar")
        for avatar_name in unlocked_avatars:
            avatar_path = os.path.join(avatar_dir, avatar_name)
            if os.path.exists(avatar_path):
                avatar_files.append(avatar_name)
            elif os.path.exists(os.path.join("images", avatar_name)):
                avatar_files.append(avatar_name)
        if not avatar_files:
            avatar_files = ["avatar.png"]
        open_picker = Picker("Select Avatar", avatar_files, (W, H))
        open_picker.idx = 0

    def on_show_leaderboard():
        nonlocal open_picker
        import game_save
        best_times = game_save.get_best_times()
        total_coins = game_save.get_total_coins()
        items = [f"Total Coins: {total_coins}"]
        for lvl in range(1, len(LEVEL_DATA) + 1):
            time = best_times.get(str(lvl))
            if time is not None:
                items.append(f"Level {lvl}: {time:.2f} seconds")
            else:
                items.append(f"Level {lvl}: Not completed yet")
        open_picker = {"title": "Leaderboard", "items": items, "type": "leaderboard"}

    level_btn_w, level_btn_h = 160, 140
    levels_per_row = 3
    level_gap = 30
    level_buttons = []

    n_levels = len(LEVEL_DATA)
    rows = (n_levels + levels_per_row - 1) // levels_per_row
    level_y = int(H * 0.25)

    for row in range(rows):
        # how many items in this row
        start_idx = row * levels_per_row
        remaining = n_levels - start_idx
        items_in_row = min(levels_per_row, remaining)

        # center this row
        row_total_w = items_in_row * level_btn_w + (items_in_row - 1) * level_gap
        row_start_x = (W - row_total_w) // 2

        for col in range(items_in_row):
            i = start_idx + col
            level_num = i + 1
            x = row_start_x + col * (level_btn_w + level_gap)
            y = level_y + row * (level_btn_h + level_gap)
            level_buttons.append(
                LevelButton(pg.Rect(x, y, level_btn_w, level_btn_h), 
                           level_num, name_font, on_select_level)
            )

    def on_quit():
        result["quit"] = True

    # compute responsive sizes/positions so buttons won't overlap
    btn_w, btn_h = int(W * 0.33), 60
    gap = 24
    # position near bottom with some padding
    # move buttons a bit lower so they don't overlap level thumbnails
    y_pos = H - btn_h - 30
    total_w = btn_w * 2 + gap
    start_x = (W - total_w) // 2

    buttons = [
        Button(pg.Rect(start_x, y_pos, btn_w, btn_h), "Select Avatar", btn_font, on_pick_avatar),
        Button(pg.Rect(start_x + btn_w + gap, y_pos, btn_w, btn_h), "Quit", btn_font, on_quit),
    ]
    
    # Separate leaderboard button in top right, square
    leaderboard_btn = Button(pg.Rect(W - 60, 10, 50, 50), "", btn_font, on_show_leaderboard, image_path="images/bxh.png")
    
    bg_img = try_load_bg((W, H))

    while True:
        dt = clock.tick(60) / 1000.0

        for event in pg.event.get():
            if event.type == pg.QUIT:
                result["quit"] = True
                return result

            if open_picker:
                if isinstance(open_picker, dict) and open_picker.get("type") == "leaderboard":
                    # allow ESC to close
                    if event.type == pg.KEYDOWN:
                        if event.key == pg.K_ESCAPE:
                            open_picker = None
                    # handle mouse click on the close button — compute same card position as draw_leaderboard
                    elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                        card_size = min(int(W * 0.6), int(H * 0.6))
                        # draw_leaderboard places the card at top-right: W - card_size - 10, 10
                        card = pg.Rect(W - card_size - 10, 10, card_size, card_size)
                        close_btn_rect = pg.Rect(card.right - 50, card.top + 10, 40, 40)
                        if close_btn_rect.collidepoint(event.pos):
                            open_picker = None
                    continue
                elif isinstance(open_picker, Picker):
                    if event.type == pg.KEYDOWN:
                        if event.key == pg.K_ESCAPE:
                            open_picker = None
                        if event.key in (pg.K_RETURN, pg.K_KP_ENTER, pg.K_SPACE):
                            val = open_picker.value
                            avatar_dir = os.path.join("images", "avatar")
                            candidate = os.path.join(avatar_dir, val)
                            if not os.path.isfile(candidate):
                                candidate = os.path.join("images", val)
                            result["avatar_path"] = candidate
                            import game_save
                            save_data = game_save.load_game_data()
                            save_data["selected_avatar"] = val
                            game_save.save_game_data(save_data)
                            open_picker = None
                        elif event.key in (pg.K_LEFT, pg.K_a):
                            open_picker.prev()
                        elif event.key in (pg.K_RIGHT, pg.K_d):
                            open_picker.next()
                    continue

            for b in buttons:
                b.handle(event)
            
            leaderboard_btn.handle(event)
            
            for lb in level_buttons:
                lb.handle(event)

        if result["quit"] or result["start"]:
            return result

        if bg_img:
            screen.blit(bg_img, (0, 0))
        else:
            screen.fill(COLOR_BG_DARK)

        title = "JUMP RUSH"
        title_s = title_font.render(title, True, COLOR_TEXT_MAIN)
        title_r = title_s.get_rect(center=(W//2, int(H*0.1)))
        screen.blit(title_s, title_r)

        level_title = btn_font.render("Select a Level", True, COLOR_TEXT_SUB)
        title_rect = level_title.get_rect(center=(W//2, int(H*0.22)))
        screen.blit(level_title, title_rect)
        
        for lb in level_buttons:
            lb.draw(screen, 0)

        for b in buttons:
            b.draw(screen, 0)

        leaderboard_btn.draw(screen, 0)

        if open_picker:
            if isinstance(open_picker, Picker):
                open_picker.draw(screen)
            elif isinstance(open_picker, dict) and open_picker.get("type") == "leaderboard":
                draw_leaderboard(open_picker)

        pg.display.flip()