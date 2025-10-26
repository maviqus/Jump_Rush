
# game_over_menu.py (with background image, EN)
import pygame as pg
import os
from typing import Optional, Tuple, Dict

COLOR_BG_DIM   = (0, 0, 0, 170)
COLOR_PANEL    = (28, 32, 40)
COLOR_BORDER   = (90, 100, 112)
COLOR_TEXT     = (235, 242, 250)
COLOR_SUB      = (186, 194, 204)
COLOR_ACCENT   = (0, 255, 210)
COLOR_ACCENT_2 = (255, 60, 200)

BG_CANDIDATES = [
    "images/bg_start.png",
]

class Button:
    def __init__(self, rect: pg.Rect, text: str, font: pg.font.Font, on_click):
        self.rect = pg.Rect(rect)
        self.text = text
        self.font = font
        self.on_click = on_click
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

    def draw(self, surf: pg.Surface):
        radius = 14
        bg = (36, 40, 50)
        border = COLOR_ACCENT if self.hover else COLOR_BORDER
        pg.draw.rect(surf, bg, self.rect, border_radius=radius)
        pg.draw.rect(surf, border, self.rect, width=2, border_radius=radius)
        label = self.font.render(self.text, True, COLOR_TEXT)
        surf.blit(label, label.get_rect(center=self.rect.center))

def _try_load_bg(size: Tuple[int,int]) -> Optional[pg.Surface]:
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
            return img.subsurface(pg.Rect(x, y, W, H)).copy()
    return None

def run_game_over(screen: pg.Surface,
                  total_score: Optional[int]=None,
                  best_score: Optional[int]=None,
                  tip: Optional[str]=None) -> Dict[str, object]:
    """Modal Game Over UI. Returns {'action': 'retry'|'home'|None, 'quit': bool}"""
    clock = pg.time.Clock()
    W, H = screen.get_size()
    title_font = pg.font.SysFont("arial", 48, bold=True)
    label_font = pg.font.SysFont("arial", 24, bold=True)
    value_font = pg.font.SysFont("arial", 28)
    small_font = pg.font.SysFont("arial", 18)

    result = {"action": None, "quit": False}

    # Bố cục bảng
    panel_w, panel_h = int(W*0.60), int(H*0.50)
    panel = pg.Rect((W-panel_w)//2, (H-panel_h)//2, panel_w, panel_h)

    # Bố cục nút bấm
    btn_w, btn_h, gap = 220, 56, 24
    btn_y = panel.bottom - btn_h - 24
    x_center = panel.centerx
    retry_rect = pg.Rect(x_center - btn_w - gap//2, btn_y, btn_w, btn_h)
    home_rect  = pg.Rect(x_center + gap//2,         btn_y, btn_w, btn_h)

    def do_retry(): result["action"] = "retry"
    def do_home():  result["action"] = "home"
    retry_btn = Button(retry_rect, "Retry", label_font, do_retry)
    home_btn  = Button(home_rect,  "Home",   label_font, do_home)
    buttons = [retry_btn, home_btn]

    # Hình nền (tùy chọn)
    bg_img = _try_load_bg((W, H))

    t = 0.0
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        t += dt
        for event in pg.event.get():
            if event.type == pg.QUIT:
                result["quit"] = True
                return result
            for b in buttons:
                b.handle(event)
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE or event.key == pg.K_r:
                    do_retry()
                elif event.key == pg.K_h or event.key == pg.K_ESCAPE:
                    do_home()

        if result["action"] is not None:
            return result

        # --- Hình nền ---
        if bg_img:
            screen.blit(bg_img, (0, 0))
    # Lớp phủ làm mờ
        dim = pg.Surface((W, H), pg.SRCALPHA); dim.fill(COLOR_BG_DIM)
        screen.blit(dim, (0, 0))

    # Bảng
        pg.draw.rect(screen, COLOR_PANEL, panel, border_radius=18)
        pg.draw.rect(screen, COLOR_BORDER, panel, width=2, border_radius=18)

    # Thanh nổi bật phía trên
        bar1 = pg.Rect(panel.left+16, panel.top+16, panel.width-32, 6)
        pg.draw.rect(screen, COLOR_ACCENT, bar1, border_radius=3)
        pg.draw.rect(screen, COLOR_ACCENT_2, bar1.inflate(18, 0), width=2, border_radius=4)

    # Tiêu đề
        title = title_font.render("GAME OVER", True, COLOR_TEXT)
        screen.blit(title, title.get_rect(midtop=(panel.centerx, panel.top+40)))

    # Điểm số
        y = panel.top + 120
        if total_score is not None:
            label = label_font.render("Total Score", True, COLOR_SUB)
            val   = value_font.render(str(total_score), True, COLOR_TEXT)
            screen.blit(label, label.get_rect(midtop=(panel.centerx, y))); y += 30
            screen.blit(val, val.get_rect(midtop=(panel.centerx, y))); y += 40
        if best_score is not None:
            label = label_font.render("Best", True, COLOR_SUB)
            val   = value_font.render(str(best_score), True, COLOR_TEXT)
            screen.blit(label, label.get_rect(midtop=(panel.centerx, y))); y += 30
            screen.blit(val, val.get_rect(midtop=(panel.centerx, y))); y += 30

    # Mẹo
        if tip:
            tip_s = small_font.render(tip, True, COLOR_SUB)
            screen.blit(tip_s, tip_s.get_rect(midbottom=(panel.centerx, panel.bottom-88)))

    # Các nút bấm
        for b in buttons: b.draw(screen)

    # (Đã xóa) gợi ý phím tắt ở dưới cùng
        pg.display.flip()
