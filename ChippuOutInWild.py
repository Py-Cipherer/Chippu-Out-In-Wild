import json
import os
import random
import sys
import math
import threading
import urllib.request
import pygame
from pygame.locals import *


# ------------------ OS PATH INITIALIZER -------------------------

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ----------- INITIALIZATION --------------
pygame.init()
pygame.mixer.init()

FPS = 32
V_WIDTH = 400
V_HEIGHT = 600
VIRTUAL_SCREEN = pygame.Surface((V_WIDTH, V_HEIGHT))

SCREEN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
pygame.display.set_caption("Chippu Out in Wild")
FPSCLOCK = pygame.time.Clock()

IS_FULLSCREEN    = True
GROUNDY          = int(V_HEIGHT * 0.8)
GAME_SPRITES     = {}
GAME_SOUNDS      = {}

MUSIC_VOLUME     = 0.5
SFX_VOLUME       = 0.4
HOMESCREEN_VISIT = 0
POWERUPS_ON_SCREEN = []
POWERUP_TYPES    = ['shield', 'phaser']
POWERUP_DURATION = {'shield': 10, 'phaser': 5}
ACTIVE_POWERUP   = None
POWERUP_END_TIME = 0
SHIELD_USED      = False
INVINCIBLE_UNTIL = 0
PAUSED           = False
G_OVER           = False
TAR_LVL          = 15

# Boss & Cinematic
PRE_BOSS_CLEANUP   = False
BOSS_ACTIVE        = False
BOSS_DEFEATED_TIME = 0
SCREEN_SHAKE       = 0
AMBIENCE_COLOR     = [0, 0, 0]
WARNING_TICKS      = 0

# Speed Settings
SCREEN_SPEED       = -2.5
INITIAL_PIPE_SPEED = -4.0
MAX_PIPE_SPEED     = -9.0
SPEED_INCREMENT    = -0.0002

# Colors
WHITE        = (255, 255, 255)
GREEN        = (0, 200, 0)
BRIGHT_GREEN = (0, 255, 0)
RED          = (200, 0, 0)
BRIGHT_RED   = (255, 0, 0)

# Fonts
FONT_HORROR = pygame.font.SysFont('chiller', 36, bold=True)
FONT_RETRO  = pygame.font.SysFont('ocraextended', 30)
FONT_NOTE   = pygame.font.SysFont('vinerhanditc', 36, bold=True)
FONT_SCORE  = pygame.font.Font(resource_path("assets/fonts/PressStart2P-Regular.ttf"), 18)
FONT_TIMER  = pygame.font.Font(resource_path("assets/fonts/VT323-Regular.ttf"), 28)
FONT_LABEL  = pygame.font.Font(resource_path("assets/fonts/PressStart2P-Regular.ttf"), 14)
FONT_LARGE  = pygame.font.Font(resource_path("assets/fonts/PressStart2P-Regular.ttf"), 22)
FONT_TAUNT  = pygame.font.Font(resource_path("assets/fonts/VT323-Regular.ttf"), 22)
FONT_SHOP   = pygame.font.Font(resource_path("assets/fonts/VT323-Regular.ttf"), 26)

# =====================================================================
# MUSIC MANAGER
# =====================================================================

MUSIC_TRACKS = {
    'home': "gallery/sounds/game_bgm.mp3",   # home screen/ UI/ Menu ke time
    'game': "gallery/sounds/chiptune_adv.mp3",  # gameplay ke time
    'boss': "gallery/sounds/game.wav",        # boss fight ke time
}
CURRENT_MUSIC_TRACK = None


def play_music(track_key):
    global CURRENT_MUSIC_TRACK
    if CURRENT_MUSIC_TRACK == track_key:
        return
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(resource_path(MUSIC_TRACKS[track_key]))
        pygame.mixer.music.play(loops=-1)
        pygame.mixer.music.set_volume(MUSIC_VOLUME)
        CURRENT_MUSIC_TRACK = track_key
    except Exception:
        pass


# =====================================================================
# SCALING ENGINE
# =====================================================================

def get_scaling_info():
    win_w, win_h = SCREEN.get_size()
    scale = min(win_w / V_WIDTH, win_h / V_HEIGHT)
    new_w = int(V_WIDTH * scale)
    new_h = int(V_HEIGHT * scale)
    offset_x = (win_w - new_w) // 2
    offset_y = (win_h - new_h) // 2
    return pygame.Rect(offset_x, offset_y, new_w, new_h), scale


def refresh_screen():
    SCREEN.fill((0, 0, 0))
    dest_rect, scale = get_scaling_info()
    scaled_surf = pygame.transform.scale(VIRTUAL_SCREEN, (dest_rect.width, dest_rect.height))
    SCREEN.blit(scaled_surf, (dest_rect.x, dest_rect.y))
    pygame.display.flip()


def get_virtual_mouse():
    m_pos = pygame.mouse.get_pos()
    dest_rect, scale = get_scaling_info()
    vx = (m_pos[0] - dest_rect.x) / scale
    vy = (m_pos[1] - dest_rect.y) / scale
    return vx, vy


def toggle_fullscreen():
    global SCREEN, IS_FULLSCREEN
    IS_FULLSCREEN = not IS_FULLSCREEN
    if IS_FULLSCREEN:
        SCREEN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
    else:
        SCREEN = pygame.display.set_mode((V_WIDTH, V_HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF)


# =====================================================================
# SPRITE TINTING HELPER
# =====================================================================

def tint_surface(surf, tint_color, alpha=180):
    tinted = surf.copy()
    overlay = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
    overlay.fill((*tint_color, alpha))
    tinted.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    add_layer = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
    add_layer.fill((*tint_color, 60))
    tinted.blit(add_layer, (0, 0))
    return tinted


# =====================================================================
# PARTICLE SYSTEM
# =====================================================================

class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'size', 'gravity')

    def __init__(self, x, y, vx, vy, life, color, size=3, gravity=0.15):
        self.x        = float(x)
        self.y        = float(y)
        self.vx       = vx
        self.vy       = vy
        self.life     = life
        self.max_life = life
        self.color    = color
        self.size     = size
        self.gravity  = gravity

    def update(self, dt):
        self.x   += self.vx * (dt / 16)
        self.y   += self.vy * (dt / 16)
        self.vy  += self.gravity * (dt / 16)
        self.life -= dt

    @property
    def alive(self):
        return self.life > 0

    def draw(self, surface):
        alpha    = max(0, int(255 * (self.life / self.max_life)))
        frac     = self.life / self.max_life
        cur_size = max(1, int(self.size * frac))
        col      = (*self.color[:3], alpha)
        s = pygame.Surface((cur_size * 2, cur_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, col, (cur_size, cur_size), cur_size)
        surface.blit(s, (int(self.x) - cur_size, int(self.y) - cur_size))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, vx_range, vy_range, life_range,
             color, count=1, size=3, gravity=0.15):
        for _ in range(count):
            vx   = random.uniform(*vx_range)
            vy   = random.uniform(*vy_range)
            life = random.randint(*life_range)
            self.particles.append(Particle(x, y, vx, vy, life, color, size, gravity))

    def update(self, dt):
        self.particles = [p for p in self.particles if p.alive]
        for p in self.particles:
            p.update(dt)

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

    def clear(self):
        self.particles.clear()


# =====================================================================
# CHIPPU ANIMATOR
# =====================================================================

class ChippuAnimator:
    FRAME_INTERVAL      = 120
    FAST_FRAME_INTERVAL = 60
    MAX_TILT_UP         = -25
    MAX_TILT_DOWN       = 40
    TILT_SPEED_UP       = 8
    TILT_SPEED_DOWN     = 3

    def __init__(self):
        self.frames         = []
        self.powerup_frames = {}
        self.current_frame  = 0
        self.frame_timer    = 0
        self.angle          = 0.0
        self.hurt_timer     = 0
        self.HURT_DURATION  = 400
        self.dying          = False
        self.death_angle    = 0.0
        self.death_alpha    = 255
        self.death_done     = False
        self.ghosts         = []
        self.ghost_timer    = 0
        self.GHOST_INTERVAL = 40
        self.particles      = ParticleSystem()
        self.trail_timer    = 0
        self.TRAIL_INTERVAL = 30

    def set_frames(self, frame_list):
        self.frames = frame_list

    def set_powerup_frame(self, powerup_name, surface):
        self.powerup_frames[powerup_name] = surface

    def on_flap(self, playerx, playery, dt):
        self.angle        = self.MAX_TILT_UP
        self.frame_timer  = 0
        self.current_frame = (self.current_frame + 1) % max(1, len(self.frames))
        cx = playerx
        cy = playery + 12
        self.particles.emit(cx, cy,
                            vx_range=(-3.5, -1.0), vy_range=(-2.0, 2.0),
                            life_range=(120, 260), color=(255, 240, 180),
                            count=7, size=4, gravity=0.05)

    def on_hurt(self):
        self.hurt_timer = self.HURT_DURATION
        self.particles.emit(0, 0, vx_range=(-4, 4), vy_range=(-4, 1),
                            life_range=(180, 350), color=(255, 60, 60),
                            count=12, size=5, gravity=0.2)
        self._hurt_burst_pending = True

    def on_death(self):
        self.dying       = True
        self.death_angle = 0.0
        self.death_alpha = 255

    def update(self, dt, playerx, playery, vel_y, active_powerup, ticks):
        interval = self.FAST_FRAME_INTERVAL if abs(vel_y) > 5 else self.FRAME_INTERVAL
        self.frame_timer += dt
        if self.frame_timer >= interval:
            self.frame_timer   = 0
            self.current_frame = (self.current_frame + 1) % max(1, len(self.frames))

        if vel_y < -3:
            target     = self.MAX_TILT_UP
            self.angle = max(target, self.angle - self.TILT_SPEED_UP)
        elif vel_y > 4:
            target     = self.MAX_TILT_DOWN
            self.angle = min(target, self.angle + self.TILT_SPEED_DOWN)
        else:
            if self.angle > 0:
                self.angle = max(0, self.angle - 1.5)
            elif self.angle < 0:
                self.angle = min(0, self.angle + 1.5)

        if self.hurt_timer > 0:
            self.hurt_timer -= dt

        if self.dying:
            self.death_angle += 12
            self.death_alpha  = max(0, self.death_alpha - 8)
            if self.death_alpha <= 0:
                self.death_done = True

        if active_powerup == 'phaser':
            self.ghost_timer += dt
            if self.ghost_timer >= self.GHOST_INTERVAL:
                self.ghost_timer = 0
                self.ghosts.append({'x': playerx, 'y': playery,
                                    'alpha': 160, 'frame': self.current_frame,
                                    'angle': self.angle})
            for g in self.ghosts:
                g['alpha'] -= 18
            self.ghosts = [g for g in self.ghosts if g['alpha'] > 0]
        else:
            self.ghosts.clear()
            self.ghost_timer = 0

        self.trail_timer += dt
        if self.trail_timer >= self.TRAIL_INTERVAL:
            self.trail_timer = 0
            trail_color = {
                'shield': (255, 230, 50),
                'phaser': (0, 220, 255),
            }.get(active_powerup, (200, 200, 255))
            self.particles.emit(playerx, playery + 12,
                                vx_range=(-2.5, -0.5), vy_range=(-0.8, 0.8),
                                life_range=(80, 180), color=trail_color,
                                count=2, size=3, gravity=0.0)

        self.particles.update(dt)

    def _get_base_surf(self, active_powerup):
        if active_powerup and active_powerup in self.powerup_frames:
            return self.powerup_frames[active_powerup]
        if not self.frames:
            return GAME_SPRITES.get('player', pygame.Surface((34, 24)))
        return self.frames[self.current_frame % len(self.frames)]

    def draw(self, surface, playerx, playery, active_powerup, ticks, invincible_until):
        cx = playerx + 17
        cy = playery + 12

        self.particles.draw(surface)

        for g in self.ghosts:
            if not self.frames:
                continue
            ghost_surf = self.frames[g['frame'] % len(self.frames)].copy()
            ghost_surf = pygame.transform.rotate(ghost_surf, -g['angle'])
            ghost_surf.set_alpha(int(g['alpha']))
            gr = ghost_surf.get_rect(center=(g['x'] + 17, g['y'] + 12))
            surface.blit(ghost_surf, gr)

        if active_powerup == 'shield' and not SHIELD_USED:
            pulse  = int(math.sin(ticks / 120.0) * 5)
            radius = 30 + pulse
            for i in range(3, 0, -1):
                aura_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
                alpha     = 60 + i * 30
                pygame.draw.circle(aura_surf, (255, 230, 0, alpha),
                                   (radius + 10, radius + 10), radius + (3 - i) * 3, 2 + i)
                surface.blit(aura_surf, (cx - radius - 10, cy - radius - 10))

        base = self._get_base_surf(active_powerup)

        if self.hurt_timer > 0:
            flash_on = (self.hurt_timer // 60) % 2 == 0
            if flash_on:
                base = tint_surface(base, (255, 50, 50), alpha=200)
            if getattr(self, '_hurt_burst_pending', False):
                self._hurt_burst_pending = False
                for p in self.particles.particles[-12:]:
                    p.x += cx
                    p.y += cy

        if ticks < invincible_until and self.hurt_timer <= 0:
            shimmer = (ticks // 80) % 2 == 0
            if shimmer:
                base = tint_surface(base, (200, 200, 255), alpha=120)

        if active_powerup == 'phaser':
            base = base.copy()
            base.set_alpha(110)

        if self.dying:
            rotated = pygame.transform.rotate(base, self.death_angle)
            rotated.set_alpha(self.death_alpha)
        else:
            rotated = pygame.transform.rotate(base, -self.angle)

        rect = rotated.get_rect(center=(cx, cy))
        surface.blit(rotated, rect)

    def draw_death(self, surface, playerx, playery):
        self.draw(surface, playerx, playery, None, pygame.time.get_ticks(), 0)


# =====================================================================
# BUTTON
# =====================================================================

class Button:
    def __init__(self, text, x, y, w, h, color, highlight_color, action=None):
        self.text            = text
        self.rect            = pygame.Rect(x, y, w, h)
        self.color           = color
        self.highlight_color = highlight_color
        self.action          = action
        self.font            = FONT_LABEL

    def draw(self, surface):
        vx, vy     = get_virtual_mouse()
        curr_color = self.highlight_color if self.rect.collidepoint(vx, vy) else self.color
        pygame.draw.rect(surface, curr_color, self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)
        text_surf = self.font.render(self.text, True, WHITE)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def click(self):
        vx, vy = get_virtual_mouse()
        if self.rect.collidepoint(vx, vy) and pygame.mouse.get_pressed()[0]:
            GAME_SOUNDS['btn_click'].play()
            if self.action:
                self.action()
            return True
        return False

    def hit(self, vx, vy):
        """Event-based click check — call this inside a MOUSEBUTTONDOWN handler."""
        return self.rect.collidepoint(vx, vy)


# =====================================================================
# BOSS PROJECTILE
# =====================================================================

class BossProjectile:
    def __init__(self, x, y, p_type):
        self.x         = x
        self.y         = y
        self.type      = p_type
        self.active    = True
        self.deflected = False

        if self.type == 'missile':
            self.vel_x = -7;   self.vel_y = 0
            self.width = 30;   self.height = 15
            self.color = (150, 150, 150)
        elif self.type == 'fire':
            self.vel_x = -10;  self.vel_y = random.choice([-2, -1, 0, 1, 2])
            self.width = 25;   self.height = 25
            self.color = (255, 100, 0)
        elif self.type == 'net':
            self.vel_x = -5;   self.vel_y = 0
            self.width = 20;   self.height = 20
            self.color = (200, 200, 200)
        elif self.type == 'electric':
            self.vel_x = -14;  self.vel_y = 0
            self.width = 40;   self.height = 10
            self.color = (0, 255, 255)

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        if self.type == 'net':
            self.width += 0.8;  self.height += 0.8;  self.y -= 0.4
        if self.type == 'fire':
            self.width += 0.5;  self.height += 0.5;  self.y -= 0.25
        if self.x < -100 or self.x > V_WIDTH + 100:
            self.active = False

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.get_rect(), border_radius=4)


# =====================================================================
# AI: PLAYER PROFILE
# =====================================================================

def make_player_profile():
    return {
        'avg_y':             [],
        'flap_intervals':    [],
        'last_flap_time':    0,
        'shield_used_count': 0,
        'dodge_dirs':        [],
    }

def record_flap(profile, ticks):
    if profile['last_flap_time'] > 0:
        interval = ticks - profile['last_flap_time']
        profile['flap_intervals'].append(interval)
        if len(profile['flap_intervals']) > 20:
            profile['flap_intervals'].pop(0)
    profile['last_flap_time'] = ticks

def record_position(profile, y):
    profile['avg_y'].append(y)
    if len(profile['avg_y']) > 120:
        profile['avg_y'].pop(0)

def get_avg_y(profile):
    if not profile['avg_y']:
        return V_HEIGHT // 2
    return sum(profile['avg_y']) / len(profile['avg_y'])

def get_avg_flap_interval(profile, last_n=5):
    if not profile['flap_intervals']:
        return 9999
    recent = profile['flap_intervals'][-last_n:]
    return sum(recent) / len(recent)


# =====================================================================
# AI: TAUNT ENGINE (Anthropic API, background thread)
# =====================================================================

_taunt_text   = ""
_taunt_expire = 0
_taunt_lock   = threading.Lock()

def _fetch_taunt_thread(profile):
    global _taunt_text, _taunt_expire
    avg_y         = int(get_avg_y(profile))
    shield_count  = profile['shield_used_count']
    avg_interval  = int(get_avg_flap_interval(profile))
    position_desc = "top" if avg_y < 200 else ("bottom" if avg_y > 400 else "middle")
    flap_desc     = ("rapid-flapper" if avg_interval < 600
                     else ("slow-flapper" if avg_interval > 1200 else "steady-flapper"))
    prompt = (
        f"You are a menacing game boss taunting the player mid-battle. "
        f"Player behaviour: tends to fly {position_desc}, is a {flap_desc}, "
        f"used shield {shield_count} time(s). "
        f"Write ONE short taunt (max 8 words) referencing their specific weakness. "
        f"Be dramatic, villainous, punchy. No quotes, no punctuation except exclamation marks."
    )
    try:
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 40,
            "messages": [{"role": "user", "content": prompt}]
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={"Content-Type": "application/json", "anthropic-version": "2023-06-01"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["content"][0]["text"].strip()
        with _taunt_lock:
            _taunt_text   = text
            _taunt_expire = pygame.time.get_ticks() + 3000
    except Exception:
        fallback = random.choice([
            "You cannot escape me!",
            "Predictable as ever!",
            "I know your every move!",
            "Your habits betray you!",
            "Too slow, little bird!",
        ])
        with _taunt_lock:
            _taunt_text   = fallback
            _taunt_expire = pygame.time.get_ticks() + 2500

def request_taunt_async(profile):
    threading.Thread(target=_fetch_taunt_thread, args=(profile,), daemon=True).start()

def get_current_taunt():
    with _taunt_lock:
        return _taunt_text if pygame.time.get_ticks() < _taunt_expire else ""


# =====================================================================
# AI: ATTACK CHOOSER
# =====================================================================

def choose_attack(profile):
    weights      = {'missile': 1, 'fire': 1, 'net': 1, 'electric': 1}
    avg_y        = get_avg_y(profile)
    shield_count = profile['shield_used_count']
    avg_interval = get_avg_flap_interval(profile)

    if avg_y < 200:           weights['electric'] += 3
    if avg_y > 400:           weights['fire']     += 3
    if 200 <= avg_y <= 400:   weights['missile']  += 2
    if shield_count >= 2:     weights['net']      += 4
    if avg_interval < 600:    weights['missile']  += 3
    if avg_interval > 1200:   weights['electric'] += 2

    pool = [a for a, w in weights.items() for _ in range(w)]
    return random.choice(pool)

def aimed_spawn_y(profile, boss_y, boss_height):
    if profile['avg_y']:
        return max(20, min(int(get_avg_y(profile)), GROUNDY - 20))
    return boss_y + boss_height // 2


# =====================================================================
# BOSS CLASS
# =====================================================================

class Boss:
    def __init__(self, player_profile=None):
        self.sprite  = GAME_SPRITES.get('boss', pygame.Surface((120, 120)))
        self.width   = 120
        self.height  = 120
        self.x       = V_WIDTH + 100          # starts further off-screen for drama
        self.y       = (GROUNDY // 2) - (self.height // 2)

        self.health          = 100
        self.speed           = 3.0             # slightly faster entry
        self.moving_in       = True
        self.entry_x         = V_WIDTH - self.width - 20
        self.time_alive      = 0
        self.survival_target = 30 * 1000

        self.attack_interval = 2500
        self.attack_timer    = 0
        self.current_state   = 'idle'
        self.state_timer     = 0
        self.projectiles     = []
        self.exposed_timer   = 0
        self.is_exposed      = False

        self.player_profile  = player_profile if player_profile else make_player_profile()
        self._taunt_cooldown = 0

        self.particles       = ParticleSystem()

        # Entry FX
        self.entry_particles = ParticleSystem()
        self._entry_shake    = 0

    def update(self, dt):
        self.time_alive += dt

        if self.moving_in:
            if self.x > self.entry_x:
                self.x -= self.speed
                # Emit dramatic entry sparks
                if random.random() < 0.35:
                    self.entry_particles.emit(
                        self.x, self.y + self.height // 2,
                        vx_range=(-6, 2), vy_range=(-4, 4),
                        life_range=(150, 350), color=(255, 80, 0),
                        count=3, size=5, gravity=0.1)
            else:
                self.moving_in = False
        else:
            t      = self.time_alive / 400.0
            self.y = (GROUNDY // 2) - (self.height // 2) + int(math.sin(t) * 90)
            self.attack_timer += dt
            if self.attack_timer >= self.attack_interval:
                self.trigger_attack()
                self.attack_timer = 0

        if self.current_state != 'idle':
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.current_state = 'idle'
                self.is_exposed    = True
                self.exposed_timer = 3000

        if self.is_exposed:
            self.exposed_timer -= dt
            if self.exposed_timer <= 0:
                self.is_exposed = False

        self.attack_interval = max(1000, 2500 - (100 - self.health) * 15)

        for proj in self.projectiles[:]:
            proj.update()
            if not proj.active:
                self.projectiles.remove(proj)

        if self._taunt_cooldown > 0:
            self._taunt_cooldown -= dt

        self.particles.update(dt)
        self.entry_particles.update(dt)

    def take_hit(self, damage):
        self.health -= damage
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        self.particles.emit(cx, cy,
                            vx_range=(-5, 5), vy_range=(-6, 2),
                            life_range=(200, 400),
                            color=(255, 200, 0), count=14, size=5, gravity=0.25)

    def trigger_attack(self):
        self.current_state = choose_attack(self.player_profile)
        self.state_timer   = 1000
        spawn_x = self.x
        spawn_y = aimed_spawn_y(self.player_profile, self.y, self.height)

        if self.current_state == 'missile':
            self.projectiles.append(BossProjectile(spawn_x, spawn_y - 20, 'missile'))
            self.projectiles.append(BossProjectile(spawn_x, spawn_y + 20, 'missile'))
        elif self.current_state == 'fire':
            for _ in range(8):
                self.projectiles.append(BossProjectile(spawn_x, spawn_y, 'fire'))
        elif self.current_state == 'net':
            self.projectiles.append(BossProjectile(spawn_x, spawn_y, 'net'))
        elif self.current_state == 'electric':
            self.projectiles.append(BossProjectile(spawn_x, spawn_y - 20, 'electric'))
            self.projectiles.append(BossProjectile(spawn_x, spawn_y + 20, 'electric'))

        if self._taunt_cooldown <= 0:
            request_taunt_async(self.player_profile)
            self._taunt_cooldown = 6000

    def get_rect(self):
        return pygame.Rect(self.x + 20, self.y + 20, self.width - 40, self.height - 40)

    def draw(self, surface):
        self.entry_particles.draw(surface)
        self.particles.draw(surface)
        surface.blit(self.sprite, (self.x, self.y))

        state_color = WHITE
        if self.current_state == 'missile':    state_color = (150, 150, 150)
        elif self.current_state == 'fire':     state_color = (255, 100, 0)
        elif self.current_state == 'net':      state_color = (200, 200, 200)
        elif self.current_state == 'electric': state_color = (0, 255, 255)

        if self.current_state != 'idle':
            pygame.draw.rect(surface, state_color, (self.x, self.y, self.width, self.height), 3)

        if self.is_exposed:
            if pygame.time.get_ticks() % 200 < 100:
                pygame.draw.rect(surface, BRIGHT_GREEN, (self.x + 40, self.y + 40, 40, 40), 3)

        for proj in self.projectiles:
            proj.draw(surface)

        pygame.draw.rect(surface, RED,   (self.x, self.y - 15, self.width, 8))
        pygame.draw.rect(surface, GREEN, (self.x, self.y - 15,
                                          int(self.width * (self.health / 100)), 8))
        pygame.draw.rect(surface, WHITE, (self.x, self.y - 15, self.width, 8), 1)

        taunt = get_current_taunt()
        if taunt:
            t_surf = FONT_TAUNT.render(taunt, True, (255, 80, 80))
            tx = max(0, min(self.x - 10, V_WIDTH - t_surf.get_width() - 4))
            ty = max(0, self.y - 38)
            backing = pygame.Surface((t_surf.get_width() + 8, t_surf.get_height() + 4), pygame.SRCALPHA)
            backing.fill((0, 0, 0, 160))
            surface.blit(backing, (tx - 4, ty - 2))
            surface.blit(t_surf, (tx, ty))

    def is_defeated(self):
        return self.time_alive >= self.survival_target


# =====================================================================
# UI HELPERS
# =====================================================================

def quit_game():
    pygame.quit()
    sys.exit()

def update_volumes():
    pygame.mixer.music.set_volume(MUSIC_VOLUME)
    for sound in GAME_SOUNDS.values():
        sound.set_volume(SFX_VOLUME)

def open_settings():
    global MUSIC_VOLUME, SFX_VOLUME
    btn_w, btn_h = 60, 40
    s_up  = Button("+",    280, 250, btn_w, btn_h, GREEN, BRIGHT_GREEN)
    s_dn  = Button("-",     60, 250, btn_w, btn_h, RED,   BRIGHT_RED)
    m_up  = Button("+",    280, 350, btn_w, btn_h, GREEN, BRIGHT_GREEN)
    m_dn  = Button("-",     60, 350, btn_w, btn_h, RED,   BRIGHT_RED)
    back  = Button("BACK", 100, 450, 200, 50, (50, 50, 50), (100, 100, 100))

    while True:
        VIRTUAL_SCREEN.blit(GAME_SPRITES['home'], (0, 0))
        overlay = pygame.Surface((V_WIDTH, V_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 200))
        VIRTUAL_SCREEN.blit(overlay, (0, 0))
        VIRTUAL_SCREEN.blit(FONT_LARGE.render("SETTINGS", True, WHITE), (V_WIDTH // 2 - 85, 100))
        VIRTUAL_SCREEN.blit(FONT_LABEL.render(f"SFX: {int(SFX_VOLUME*100)}%",    True, WHITE), (V_WIDTH // 2 - 80, 220))
        VIRTUAL_SCREEN.blit(FONT_LABEL.render(f"MUSIC: {int(MUSIC_VOLUME*100)}%", True, WHITE), (V_WIDTH // 2 - 90, 320))
        s_up.draw(VIRTUAL_SCREEN);  s_dn.draw(VIRTUAL_SCREEN)
        m_up.draw(VIRTUAL_SCREEN);  m_dn.draw(VIRTUAL_SCREEN)
        back.draw(VIRTUAL_SCREEN)
        pygame.draw.rect(VIRTUAL_SCREEN, WHITE, (130, 265, 140, 10), 2)
        pygame.draw.rect(VIRTUAL_SCREEN, GREEN, (132, 267, int(136 * SFX_VOLUME), 6))
        pygame.draw.rect(VIRTUAL_SCREEN, WHITE, (130, 365, 140, 10), 2)
        pygame.draw.rect(VIRTUAL_SCREEN, GREEN, (132, 367, int(136 * MUSIC_VOLUME), 6))

        for event in pygame.event.get():
            if event.type == QUIT:
                quit_game()
            if event.type == KEYDOWN and event.key == K_F11:
                toggle_fullscreen()
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                vx, vy = get_virtual_mouse()
                if s_up.hit(vx, vy):
                    SFX_VOLUME   = min(1.0, SFX_VOLUME + 0.1);   update_volumes(); GAME_SOUNDS['point'].play()
                if m_up.hit(vx, vy):
                    MUSIC_VOLUME = min(1.0, MUSIC_VOLUME + 0.1);  update_volumes()
                if s_dn.hit(vx, vy):
                    SFX_VOLUME   = max(0.0, SFX_VOLUME - 0.1);   update_volumes(); GAME_SOUNDS['point'].play()
                if m_dn.hit(vx, vy):
                    MUSIC_VOLUME = max(0.0, MUSIC_VOLUME - 0.1);  update_volumes()
                if back.hit(vx, vy):
                    GAME_SOUNDS['btn_click'].play()
                    return HomeScreen()

        refresh_screen()
        FPSCLOCK.tick(FPS)

def controlScreen():
    back = Button("BACK", 20, (V_HEIGHT // 2) - 20, 120, 60, (50, 50, 50), (100, 100, 100))
    while True:
        VIRTUAL_SCREEN.blit(GAME_SPRITES['controls'], (0, 0))
        back.draw(VIRTUAL_SCREEN)
        for event in pygame.event.get():
            if event.type == QUIT:
                quit_game()
            if event.type == KEYDOWN and event.key == K_F11:
                toggle_fullscreen()
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                vx, vy = get_virtual_mouse()
                if back.hit(vx, vy):
                    GAME_SOUNDS['btn_click'].play()
                    return HomeScreen()
        refresh_screen()
        FPSCLOCK.tick(FPS)


# =====================================================================
# UTILS
# =====================================================================

def resume_toggle():
    global PAUSED
    PAUSED = False

def loadHighScore():
    try:
        with open("highscore.json", "r") as f:
            return json.load(f).get("highscore", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0

def saveHighScore(s):
    with open("highscore.json", "w") as f:
        json.dump({"highscore": s}, f)

def getPipe(t='pair'):
    gap = 160
    px  = V_WIDTH + 10
    if t == 'pair':
        ly = random.randint(int(V_HEIGHT * 0.3), int(GROUNDY - gap - 20))
        return {'x': px, 'type': 'pair',
                'curr_h_up': ly - gap, 'curr_h_low': GROUNDY - ly,
                'target_h_up': ly - gap, 'target_h_low': GROUNDY - ly,
                'lower_y': ly, 'triggered': False}
    else:
        is_up = random.choice([True, False])
        h     = random.randint(130, 190)
        return {'x': px,
                'type': 'single_upper' if is_up else 'single_lower',
                'curr_h_up':    h if is_up else 0,
                'target_h_up':  h if is_up else 0,
                'curr_h_low':   h if not is_up else 0,
                'target_h_low': h if not is_up else 0,
                'lower_y': GROUNDY - h if not is_up else 0,
                'triggered': False}

def spawnPowerUp(x):
    ptype = random.choice(POWERUP_TYPES)
    py    = random.randint(100, GROUNDY - 100)
    POWERUPS_ON_SCREEN.append({'type': ptype, 'x': x, 'y': py})

def handleShieldHit(t, chippu_anim=None):
    global ACTIVE_POWERUP, SHIELD_USED, INVINCIBLE_UNTIL
    if ACTIVE_POWERUP == 'shield' and not SHIELD_USED:
        SHIELD_USED      = True
        ACTIVE_POWERUP   = None
        INVINCIBLE_UNTIL = t + 1000
        GAME_SOUNDS['flap'].play()
        if chippu_anim:
            chippu_anim.on_hurt()
        return True
    GAME_SOUNDS['die'].play()
    return False


# =====================================================================
# SCREENS
# =====================================================================

def HomeScreen():
    global HOMESCREEN_VISIT

    play_music('home')

    start_btn   = Button("START",        100, 230, 200, 50, GREEN, BRIGHT_GREEN)
    set_btn     = Button("SETTINGS",     100, 300, 200, 50, (50, 50, 50), (100, 100, 100))
    control_btn = Button("HOW TO PLAY?", 100, 370, 200, 50, (255, 165, 0), (255, 230, 0))
    quit_btn    = Button("QUIT",         100, 440, 200, 50, RED, BRIGHT_RED)

    while True:
        VIRTUAL_SCREEN.blit(GAME_SPRITES['home'], (0, 0))

        if HOMESCREEN_VISIT == 0:
            refresh_screen()
            HOMESCREEN_VISIT += 1
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == QUIT:
                        quit_game()
                    if event.type == KEYDOWN or event.type == MOUSEBUTTONDOWN:
                        GAME_SOUNDS['start'].play()
                        waiting = False
                FPSCLOCK.tick(FPS)
            pygame.event.clear()
            pygame.time.wait(80)

        overlay = pygame.Surface((V_WIDTH, V_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 80))
        VIRTUAL_SCREEN.blit(overlay, (0, 0))
        start_btn.draw(VIRTUAL_SCREEN)
        set_btn.draw(VIRTUAL_SCREEN)
        control_btn.draw(VIRTUAL_SCREEN)
        quit_btn.draw(VIRTUAL_SCREEN)

        for event in pygame.event.get():
            if event.type == QUIT:
                quit_game()
            if event.type == KEYDOWN:
                if event.key == K_F11:
                    toggle_fullscreen()
                if event.key in (K_RETURN, K_SPACE):
                    return
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                vx, vy = get_virtual_mouse()
                if start_btn.hit(vx, vy):
                    GAME_SOUNDS['btn_click'].play()
                    return
                if set_btn.hit(vx, vy):
                    GAME_SOUNDS['btn_click'].play()
                    open_settings()
                if control_btn.hit(vx, vy):
                    GAME_SOUNDS['btn_click'].play()
                    controlScreen()
                if quit_btn.hit(vx, vy):
                    GAME_SOUNDS['btn_click'].play()
                    quit_game()

        refresh_screen()
        FPSCLOCK.tick(FPS)


# =====================================================================
# MAIN GAME LOOP
# =====================================================================

def mainGame():
    global ACTIVE_POWERUP, POWERUP_END_TIME, PAUSED, SHIELD_USED
    global POWERUPS_ON_SCREEN, INVINCIBLE_UNTIL
    global BOSS_ACTIVE, PRE_BOSS_CLEANUP, BOSS_DEFEATED_TIME, TAR_LVL

    # --- Reset global state ---
    BOSS_ACTIVE        = False
    PRE_BOSS_CLEANUP   = False
    ACTIVE_POWERUP     = None
    SHIELD_USED        = False
    PAUSED             = False
    POWERUPS_ON_SCREEN.clear()

    play_music('game')

    player_profile = make_player_profile()

    chippu = ChippuAnimator()
    chippu.set_frames(GAME_SPRITES.get('player_frames', [GAME_SPRITES['player']]))
    for pu_name in ('shield', 'phaser'):
        key = f'player_{pu_name}'
        if key in GAME_SPRITES:
            chippu.set_powerup_frame(pu_name, GAME_SPRITES[key])

    bg_x      = 0.0
    dim       = pygame.Surface((V_WIDTH, V_HEIGHT))
    dim.fill((0, 0, 0))
    dim.set_alpha(100)
    score     = 0
    cached_hs = loadHighScore()

    playerx    = V_WIDTH // 5
    playery    = V_HEIGHT // 2
    playerVelY = -9
    playerVelX = 6
    cur_speed  = INITIAL_PIPE_SPEED
    diff_timer = 0
    next_pu    = pygame.time.get_ticks() + 8000
    pipes      = [getPipe('pair'), getPipe('pair')]
    pipes[1]['x'] += V_WIDTH // 2
    boss_obj   = None

    shake_timer    = 0
    SHAKE_DURATION = 400

    # --- Coin system ---
    coin_count    = 0
    coin_spawns   = []
    next_coin_t   = pygame.time.get_ticks() + 2000
    COIN_SIZE     = 22
    SHOP_PRICES   = {'shield': 3, 'phaser': 5}

    # --- Boss warning Scene ---
    boss_warning_active   = False
    boss_warning_start    = 0
    BOSS_WARNING_DURATION = 3500   # ms of dramatic warning before boss appears
    warn_particles        = ParticleSystem()

    # --- Storm system ---
    game_start_t    = pygame.time.get_ticks()
    storm_active    = False
    storm_end_t     = 0
    STORM_DURATION  = 5000          # 5 seconds per storm
    next_storm_t    = game_start_t + random.randint(60_000, 180_000)
    wind_streaks    = []            # list of dicts for wind particle rendering
    WIND_FORCE      = 2             # px pushed left per frame

    # --- Pause / shop buttons ---
    resume_btn      = Button("RESUME",  100, 310, 200, 50, GREEN,         BRIGHT_GREEN)
    quit_btn_p      = Button("QUIT",    100, 380, 200, 50, RED,           BRIGHT_RED)
    shop_shield_btn = Button("SHIELD",   75, 195, 250, 52, (30, 60, 150), (60, 110, 255))
    shop_phaser_btn = Button("PHASER",   75, 300, 250, 52, (30, 100, 50), (60, 200, 100))
    shop_close_btn  = Button("CLOSE",   150, 430, 100, 40, (80, 30, 30),  (160, 60, 60))
    shop_open       = False

    # ─────────────────────────────────────────────────────────────────
    while True:
        dt    = FPSCLOCK.get_time()
        ticks = pygame.time.get_ticks()

        # ══════════ SHOP ══════════
        if shop_open:
            for event in pygame.event.get():
                if event.type == QUIT:
                    quit_game()
                if event.type == KEYDOWN:
                    if event.key == K_F11:
                        toggle_fullscreen()
                    if event.key in (K_b, K_ESCAPE):
                        shop_open = False
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    vx, vy = get_virtual_mouse()
                    if shop_shield_btn.hit(vx, vy):
                        if coin_count >= SHOP_PRICES['shield']:
                            coin_count      -= SHOP_PRICES['shield']
                            ACTIVE_POWERUP   = 'shield'
                            SHIELD_USED      = False
                            POWERUP_END_TIME = ticks + POWERUP_DURATION['shield'] * 1000
                            GAME_SOUNDS['flap'].play()
                            shop_open = False
                        else:
                            GAME_SOUNDS['die'].play()
                    elif shop_phaser_btn.hit(vx, vy):
                        if coin_count >= SHOP_PRICES['phaser']:
                            coin_count      -= SHOP_PRICES['phaser']
                            ACTIVE_POWERUP   = 'phaser'
                            SHIELD_USED      = False
                            POWERUP_END_TIME = ticks + POWERUP_DURATION['phaser'] * 1000
                            GAME_SOUNDS['flap'].play()
                            shop_open = False
                        else:
                            GAME_SOUNDS['die'].play()
                    elif shop_close_btn.hit(vx, vy):
                        GAME_SOUNDS['btn_click'].play()
                        shop_open = False

            # Shop UI drawn on top of frozen game frame
            shop_bg = pygame.Surface((V_WIDTH, V_HEIGHT), pygame.SRCALPHA)
            shop_bg.fill((0, 0, 40, 225))
            VIRTUAL_SCREEN.blit(shop_bg, (0, 0))

            title_s = FONT_LARGE.render("SHOP", True, (255, 215, 0))
            VIRTUAL_SCREEN.blit(title_s, (V_WIDTH // 2 - title_s.get_width() // 2, 55))

            coin_hud = pygame.transform.scale(GAME_SPRITES['coin'], (22, 22))
            VIRTUAL_SCREEN.blit(coin_hud, (V_WIDTH // 2 - 50, 100))
            coins_s = FONT_LABEL.render(f"x {coin_count}", True, (255, 215, 0))
            VIRTUAL_SCREEN.blit(coins_s, (V_WIDTH // 2 - 18, 103))

            # Shield
            shop_shield_btn.draw(VIRTUAL_SCREEN)
            can_shield = coin_count >= SHOP_PRICES['shield']
            price_col  = (180, 220, 255) if can_shield else (200, 80, 80)
            p1 = FONT_SHOP.render(f"3 coins  |  10s protection", True, price_col)
            VIRTUAL_SCREEN.blit(p1, (78, 250))
            if not can_shield:
                nm = FONT_SHOP.render("NOT ENOUGH COINS", True, (255, 70, 70))
                VIRTUAL_SCREEN.blit(nm, (78, 268))

            # Phaser
            shop_phaser_btn.draw(VIRTUAL_SCREEN)
            can_phaser = coin_count >= SHOP_PRICES['phaser']
            price_col2 = (180, 255, 180) if can_phaser else (200, 80, 80)
            p2 = FONT_SHOP.render(f"5 coins  |  5s phase-through", True, price_col2)
            VIRTUAL_SCREEN.blit(p2, (78, 355))
            if not can_phaser:
                nm2 = FONT_SHOP.render("NOT ENOUGH COINS", True, (255, 70, 70))
                VIRTUAL_SCREEN.blit(nm2, (78, 373))

            shop_close_btn.draw(VIRTUAL_SCREEN)
            hint = FONT_SHOP.render("Press B or ESC to close", True, (140, 140, 140))
            VIRTUAL_SCREEN.blit(hint, (V_WIDTH // 2 - hint.get_width() // 2, 490))

            refresh_screen()
            FPSCLOCK.tick(FPS)
            continue

        # ══════════ PAUSE OVERLAY ══════════
        if PAUSED:
            for event in pygame.event.get():
                if event.type == QUIT:
                    quit_game()
                if event.type == KEYDOWN:
                    if event.key == K_F11:
                        toggle_fullscreen()
                    if event.key == K_ESCAPE:
                        PAUSED = False
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    vx, vy = get_virtual_mouse()
                    if resume_btn.hit(vx, vy):
                        GAME_SOUNDS['btn_click'].play()
                        PAUSED = False
                    elif quit_btn_p.hit(vx, vy):
                        GAME_SOUNDS['btn_click'].play()
                        quit_game()

            # Overlay on the frozen last frame
            ov = pygame.Surface((V_WIDTH, V_HEIGHT), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 145))
            VIRTUAL_SCREEN.blit(ov, (0, 0))
            pt = FONT_LARGE.render("PAUSED", True, WHITE)
            VIRTUAL_SCREEN.blit(pt, (V_WIDTH // 2 - pt.get_width() // 2, V_HEIGHT // 3 - 20))
            resume_btn.draw(VIRTUAL_SCREEN)
            quit_btn_p.draw(VIRTUAL_SCREEN)

            refresh_screen()
            FPSCLOCK.tick(10)
            continue

        # ══════════ FIX 5: BOSS WARNING CINEMATIC ══════════
        if boss_warning_active:
            elapsed  = ticks - boss_warning_start
            progress = min(1.0, elapsed / BOSS_WARNING_DURATION)

            play_music('boss')
            
            # Player can still move & flap during warning
            record_position(player_profile, playery)
            keys = pygame.key.get_pressed()
            if (keys[K_LEFT]  or keys[K_a]) and playerx > 0:
                playerx -= playerVelX
            if (keys[K_RIGHT] or keys[K_d]) and playerx < V_WIDTH - 40:
                playerx += playerVelX

            for event in pygame.event.get():
                if event.type == QUIT:
                    quit_game()
                if event.type == KEYDOWN:
                    if event.key == K_F11:
                        toggle_fullscreen()
                    if event.key in (K_SPACE, K_UP, K_w):
                        playerVelY = -8
                        chippu.on_flap(playerx, playery, dt)

            playerVelY  = min(playerVelY + 1, 12)
            playery    += playerVelY
            playery     = min(playery, GROUNDY - 25)

            # Shake intensifies near the end
            shk_x = shk_y = 0
            if progress > 0.45:
                mag   = int(10 * ((progress - 0.45) / 0.55))
                shk_x = random.randint(-mag, mag)
                shk_y = random.randint(-mag, mag)

            bg_x += SCREEN_SPEED
            if bg_x <= -V_WIDTH:
                bg_x = 0

            # Emit dramatic warning particles from edges
            if random.random() < 0.5:
                warn_particles.emit(
                    random.randint(0, V_WIDTH), random.choice([0, GROUNDY]),
                    vx_range=(-3, 3), vy_range=(-5, 5),
                    life_range=(200, 500), color=(255, 40, 0),
                    count=2, size=4, gravity=0.05)
            warn_particles.update(dt)

            # Render
            VIRTUAL_SCREEN.blit(GAME_SPRITES['background'],
                                 (int(bg_x) + shk_x, shk_y))
            VIRTUAL_SCREEN.blit(GAME_SPRITES['background'],
                                 (int(bg_x) + V_WIDTH + shk_x, shk_y))
            VIRTUAL_SCREEN.blit(GAME_SPRITES['base'], (shk_x, GROUNDY + shk_y))

            chippu.update(dt, playerx, playery, playerVelY, None, ticks)
            chippu.draw(VIRTUAL_SCREEN, playerx + shk_x, playery + shk_y,
                        None, ticks, 0)
            warn_particles.draw(VIRTUAL_SCREEN)

            # Pulsing red-black vignette
            flash_a = int(80 + 100 * abs(math.sin(elapsed / 180.0)) + 50 * progress)
            flash_a = min(210, flash_a)
            flash   = pygame.Surface((V_WIDTH, V_HEIGHT), pygame.SRCALPHA)
            flash.fill((160, 0, 0, flash_a))
            VIRTUAL_SCREEN.blit(flash, (0, 0))

            # Flashing warning text (alternates every 300 ms)
            if (ticks // 300) % 2 == 0:
                w1 = FONT_HORROR.render("!! DEVASTATOR APPROACHES !!", True, (255, 50, 50))
                VIRTUAL_SCREEN.blit(w1, (V_WIDTH // 2 - w1.get_width() // 2,
                                         V_HEIGHT // 3 + shk_y))
                w2 = FONT_LABEL.render("PREPARE FOR BATTLE", True, (255, 200, 0))
                VIRTUAL_SCREEN.blit(w2, (V_WIDTH // 2 - w2.get_width() // 2,
                                         V_HEIGHT // 2 + shk_y))

            # Countdown number
            remain_s = max(0, BOSS_WARNING_DURATION - elapsed)
            cnt_num  = math.ceil(remain_s / 1000)
            if cnt_num > 0:
                cnt_s = FONT_LARGE.render(str(cnt_num), True, WHITE)
                VIRTUAL_SCREEN.blit(cnt_s, (V_WIDTH // 2 - cnt_s.get_width() // 2,
                                            V_HEIGHT * 2 // 3))

            if elapsed >= BOSS_WARNING_DURATION:
                #Boss spawns at end of cinematic
                boss_warning_active = False
                BOSS_ACTIVE         = True
                boss_obj            = Boss(player_profile=player_profile)
                warn_particles.clear()

            refresh_screen()
            FPSCLOCK.tick(FPS)
            continue

        # ══════════ MAIN GAME EVENTS ══════════
        for event in pygame.event.get():
            if event.type == QUIT:
                quit_game()
            if event.type == KEYDOWN:
                if event.key == K_F11:
                    toggle_fullscreen()
                if event.key == K_ESCAPE:
                    GAME_SOUNDS['btn_click'].play()
                    PAUSED = True
                if event.key == K_b:
                    shop_open = True
                if event.key in (K_SPACE, K_UP, K_w):
                    playerVelY = -8
                    GAME_SOUNDS['svoosh'].play()
                    record_flap(player_profile, ticks)
                    chippu.on_flap(playerx, playery, dt)

        # ══════════ AI PROFILE ══════════
        record_position(player_profile, playery)

        # ══════════ SCROLL ══════════
        bg_x += SCREEN_SPEED
        if bg_x <= -V_WIDTH:
            bg_x = 0
        if cur_speed > MAX_PIPE_SPEED:
            cur_speed += SPEED_INCREMENT

        # ══════════ HORIZONTAL MOVEMENT ══════════
        keys = pygame.key.get_pressed()
        if keys[K_LEFT]  or keys[K_a]:
            if playerx > 0:          playerx -= playerVelX
        if keys[K_RIGHT] or keys[K_d]:
            if playerx < V_WIDTH - 40: playerx += playerVelX
        if keys[K_LSHIFT] or keys[K_RCTRL]:
            if playerx < V_WIDTH - 40: playerx += 2 * playerVelX

        # ══════════ STORM SYSTEM ══════════
        if not BOSS_ACTIVE and not boss_warning_active:
            if not storm_active and ticks >= next_storm_t:
                storm_active = True
                storm_end_t  = ticks + STORM_DURATION

            if storm_active:
                if ticks < storm_end_t:
                    # Push player left — must press right to counter
                    playerx = max(0, playerx - WIND_FORCE)

                    # Spawn wind streaks from right edge
                    if random.random() < 0.45:
                        life = random.randint(280, 550)
                        wind_streaks.append({
                            'x':        float(V_WIDTH + random.randint(0, 40)),
                            'y':        float(random.randint(0, GROUNDY)),
                            'vx':       -random.uniform(11, 20),
                            'vy':       random.uniform(-0.6, 0.6),
                            'life':     life,
                            'max_life': life,
                            'length':   random.randint(25, 65),
                        })
                else:
                    storm_active = False
                    wind_streaks.clear()
                    next_storm_t = ticks + random.randint(60_000, 180_000)

            # Advance wind streaks
            for ws in wind_streaks[:]:
                ws['x']   += ws['vx']
                ws['y']   += ws['vy']
                ws['life'] -= dt
                if ws['life'] <= 0 or ws['x'] < -100:
                    wind_streaks.remove(ws)

        # ══════════ POWER-UP EXPIRY ══════════
        if ACTIVE_POWERUP and ticks > POWERUP_END_TIME:
            ACTIVE_POWERUP = None

        # ══════════ BOSS TRIGGER -starts warning cinematic ══════════
        if (score > 0 and score % TAR_LVL == 0
                and not BOSS_ACTIVE and not boss_warning_active
                and ticks - BOSS_DEFEATED_TIME > 5000):
            boss_warning_active = True
            boss_warning_start  = ticks
            pipes.clear()
            storm_active = False       # cancel storm during boss sequence
            wind_streaks.clear()

        # ══════════ BOSS UPDATE ══════════
        if BOSS_ACTIVE and boss_obj:
            boss_obj.update(dt)
            if boss_obj.is_defeated():
                BOSS_ACTIVE        = False
                boss_obj           = None
                BOSS_DEFEATED_TIME = ticks
                score             += 30
                cached_hs          = loadHighScore()
                GAME_SOUNDS['point'].play()
                pipes.append(getPipe('pair'))
                pipes.append(getPipe('pair'))
                pipes[-1]['x'] += V_WIDTH // 2
                #Return to gameplay music after boss
                play_music('game')
                next_storm_t = ticks + random.randint(30_000, 90_000)

        # ══════════ PIPE MOVEMENT & TRAPS ══════════
        if not BOSS_ACTIVE:
            for p in pipes:
                p['x'] += cur_speed
                if score >= 10 and not p['triggered'] and p['x'] - playerx < 170:
                    p['triggered'] = True
                    if 'pair'   in p['type']: p['target_h_low'] += 65
                    elif 'upper' in p['type']: p['target_h_up']  += 90
                    else:                       p['target_h_low'] += 90
                if p['curr_h_up']  < p['target_h_up']:
                    p['curr_h_up']  += 7
                if p['curr_h_low'] < p['target_h_low']:
                    p['curr_h_low'] += 7
                    p['lower_y']     = GROUNDY - p['curr_h_low']

        # ══════════ POWER-UP SPAWN & COLLECT ══════════
        if ticks > next_pu:
            spawnPowerUp(V_WIDTH + 50)
            next_pu = ticks + random.randint(5000, 15000)

        for pu in POWERUPS_ON_SCREEN[:]:
            pu['x'] += cur_speed
            p_rect_c = pygame.Rect(playerx, playery, 34, 24)
            pu_rect  = pygame.Rect(pu['x'], pu['y'], 40, 40)
            if p_rect_c.colliderect(pu_rect):
                ACTIVE_POWERUP   = pu['type']
                SHIELD_USED      = False
                POWERUP_END_TIME = ticks + (POWERUP_DURATION[pu['type']] * 1000)
                POWERUPS_ON_SCREEN.remove(pu)
            elif pu['x'] < -50:
                POWERUPS_ON_SCREEN.remove(pu)

        # ══════════ COIN SPAWN & COLLECT ══════════
        if not BOSS_ACTIVE and ticks > next_coin_t:
            coin_spawns.append({'x': float(V_WIDTH + 20),
                                'y': random.randint(70, GROUNDY - 55)})
            next_coin_t = ticks + random.randint(1000, 3000)

        p_box_coin = pygame.Rect(playerx + 3, playery + 3, 28, 20)
        for c in coin_spawns[:]:
            c['x'] += cur_speed
            c_rect  = pygame.Rect(int(c['x']), c['y'], COIN_SIZE, COIN_SIZE)
            if p_box_coin.colliderect(c_rect):
                coin_count += 1
                GAME_SOUNDS['point'].play()
                coin_spawns.remove(c)
            elif c['x'] < -40:
                coin_spawns.remove(c)

        # ══════════ COLLISION DETECTION ══════════
        p_rect = pygame.Rect(playerx + 5, playery + 5, 25, 18)

        if BOSS_ACTIVE and boss_obj:
            for proj in boss_obj.projectiles:
                if not proj.deflected and p_rect.colliderect(proj.get_rect()):
                    if ACTIVE_POWERUP == 'shield' and not SHIELD_USED:
                        proj.deflected   = True
                        proj.vel_x       = 15
                        proj.vel_y       = 0
                        proj.color       = BRIGHT_GREEN
                        SHIELD_USED      = True
                        ACTIVE_POWERUP   = None
                        INVINCIBLE_UNTIL = ticks + 1000
                        GAME_SOUNDS['flap'].play()
                        player_profile['shield_used_count'] += 1
                        chippu.on_hurt()
                        shake_timer = ticks + SHAKE_DURATION
                    elif ACTIVE_POWERUP != 'phaser':
                        if not handleShieldHit(ticks, chippu):
                            return _run_death_anim(chippu, playerx, playery, score)

                if proj.deflected and boss_obj.get_rect().colliderect(proj.get_rect()):
                    boss_obj.take_hit(20)
                    proj.active = False
                    GAME_SOUNDS['point'].play()
                    if boss_obj.health <= 0:
                        boss_obj.time_alive = boss_obj.survival_target

        if BOSS_ACTIVE and boss_obj and p_rect.colliderect(boss_obj.get_rect()):
            keys = pygame.key.get_pressed()
            if boss_obj.is_exposed and (keys[K_LSHIFT] or keys[K_RCTRL]):
                boss_obj.take_hit(30)
                boss_obj.is_exposed = False
                GAME_SOUNDS['point'].play()
                playerx -= 200
                shake_timer = ticks + SHAKE_DURATION
                if boss_obj.health <= 0:
                    boss_obj.time_alive = boss_obj.survival_target
            else:
                if not handleShieldHit(ticks, chippu):
                    return _run_death_anim(chippu, playerx, playery, score)

        if ACTIVE_POWERUP != 'phaser' and not (ticks < INVINCIBLE_UNTIL) and not BOSS_ACTIVE:
            p_box = pygame.Rect(playerx + 5, playery + 5, 25, 18)
            for p in pipes:
                u_box = pygame.Rect(p['x'], 0, 52, p['curr_h_up'])
                l_box = pygame.Rect(p['x'], p['lower_y'], 52, p['curr_h_low'])
                if ((p['curr_h_up']  > 0 and p_box.colliderect(u_box)) or
                        (p['curr_h_low'] > 0 and p_box.colliderect(l_box))):
                    shake_timer = ticks + SHAKE_DURATION
                    if not handleShieldHit(ticks, chippu):
                        return _run_death_anim(chippu, playerx, playery, score)

        if ACTIVE_POWERUP != 'phaser':
            if playery >= GROUNDY - 25:
                if not handleShieldHit(ticks, chippu):
                    return _run_death_anim(chippu, playerx, playery, score)

        if playery >= V_HEIGHT and (ACTIVE_POWERUP == 'phaser' or ticks < INVINCIBLE_UNTIL):
            return _run_death_anim(chippu, playerx, playery, score)

        # ══════════ PIPE RECYCLE & SCORING ══════════
        if not BOSS_ACTIVE and len(pipes) > 0:
            if pipes[0]['x'] < -52:
                pipes.pop(0)
                p_type = 'single' if (score >= 10 and random.random() > 0.7) else 'pair'
                pipes.append(getPipe(p_type))
            if pipes[0]['x'] + 15 < playerx and 'scored' not in pipes[0]:
                score              += 1
                pipes[0]['scored']  = True
                GAME_SOUNDS['point'].play()
                if score == 10:
                    diff_timer = ticks

        # ══════════ PHYSICS ══════════
        playerVelY += 1
        playery    += playerVelY

        chippu.update(dt, playerx, playery, playerVelY, ACTIVE_POWERUP, ticks)

        # ══════════ SCREEN SHAKE ══════════
        shake_x = shake_y = 0
        if ticks < shake_timer:
            magnitude = 5 * ((shake_timer - ticks) / SHAKE_DURATION)
            shake_x   = random.randint(-int(magnitude), int(magnitude))
            shake_y   = random.randint(-int(magnitude), int(magnitude))

        # ══════════ RENDER ══════════
        VIRTUAL_SCREEN.blit(GAME_SPRITES['background'], (int(bg_x) + shake_x, shake_y))
        VIRTUAL_SCREEN.blit(GAME_SPRITES['background'], (int(bg_x) + V_WIDTH + shake_x, shake_y))
        VIRTUAL_SCREEN.blit(dim, (0, 0))

        #Draw wind streaks during storm
        if storm_active:
            for ws in wind_streaks:
                alpha  = max(0, int(210 * ws['life'] / ws['max_life']))
                sx, sy = int(ws['x']), int(ws['y'])
                ln     = ws['length']
                # Streak trailing to the right (direction the particle came from)
                streak_s = pygame.Surface((ln, 3), pygame.SRCALPHA)
                streak_s.fill((170, 205, 255, alpha))
                VIRTUAL_SCREEN.blit(streak_s, (sx, sy))
            # Blue-grey storm tint
            s_alpha = 28 + int(18 * abs(math.sin(ticks / 450.0)))
            s_tint  = pygame.Surface((V_WIDTH, V_HEIGHT), pygame.SRCALPHA)
            s_tint.fill((70, 90, 170, s_alpha))
            VIRTUAL_SCREEN.blit(s_tint, (0, 0))
            # Storm banner
            if (ticks // 500) % 2 == 0:
                storm_lbl = FONT_LARGE.render("STORM!", True, (120, 165, 255))
                VIRTUAL_SCREEN.blit(storm_lbl,
                                    (V_WIDTH // 2 - storm_lbl.get_width() // 2, 78))
            remain_storm = max(0, storm_end_t - ticks) // 1000
            rs = FONT_TIMER.render(f"Wind ends: {remain_storm}s", True, (160, 190, 255))
            VIRTUAL_SCREEN.blit(rs, (V_WIDTH // 2 - rs.get_width() // 2, 108))

        if BOSS_ACTIVE and boss_obj:
            boss_obj.draw(VIRTUAL_SCREEN)
        else:
            for p in pipes:
                if p['curr_h_up'] > 0:
                    u_img = pygame.transform.scale(GAME_SPRITES['pipe'][0],
                                                   (52, int(p['curr_h_up'])))
                    VIRTUAL_SCREEN.blit(u_img, (int(p['x']) + shake_x, shake_y))
                if p['curr_h_low'] > 0:
                    l_img = pygame.transform.scale(GAME_SPRITES['pipe'][1],
                                                   (52, int(p['curr_h_low'])))
                    VIRTUAL_SCREEN.blit(l_img, (int(p['x']) + shake_x,
                                                int(p['lower_y']) + shake_y))

        for pu in POWERUPS_ON_SCREEN:
            pu_img = pygame.transform.scale(GAME_SPRITES[pu['type']], (60, 60))
            VIRTUAL_SCREEN.blit(pu_img, (int(pu['x']), pu['y']))

        #Draw coin pickups in world
        coin_draw = pygame.transform.scale(GAME_SPRITES['coin'], (COIN_SIZE, COIN_SIZE))
        for c in coin_spawns:
            VIRTUAL_SCREEN.blit(coin_draw, (int(c['x']), c['y']))

        VIRTUAL_SCREEN.blit(GAME_SPRITES['base'], (shake_x, GROUNDY + shake_y))

        chippu.draw(VIRTUAL_SCREEN, playerx + shake_x, playery + shake_y,
                    ACTIVE_POWERUP, ticks, INVINCIBLE_UNTIL)

        # ══════════ HUD ══════════
        # Score
        digits  = [int(x) for x in str(score)]
        w_total = sum(GAME_SPRITES['numbers'][d].get_width() for d in digits)
        x_st    = (V_WIDTH - w_total) // 2
        for d in digits:
            VIRTUAL_SCREEN.blit(GAME_SPRITES['numbers'][d], (x_st, 20))
            x_st += GAME_SPRITES['numbers'][d].get_width()

        #Coin counter (top-right)
        coin_hud_img = pygame.transform.scale(GAME_SPRITES['coin'], (22, 22))
        VIRTUAL_SCREEN.blit(coin_hud_img, (V_WIDTH - 95, 10))
        coin_txt = FONT_LABEL.render(f"x{coin_count}", True, (255, 215, 0))
        VIRTUAL_SCREEN.blit(coin_txt, (V_WIDTH - 68, 12))
        shop_hint = FONT_TIMER.render("[B] SHOP", True, (190, 190, 90))
        VIRTUAL_SCREEN.blit(shop_hint, (V_WIDTH - shop_hint.get_width() - 4, 36))

        # Bottom bar
        VIRTUAL_SCREEN.blit(GAME_SPRITES['coin'], (10, GROUNDY + 10))
        hs_surf = FONT_NOTE.render(f"High Score: {cached_hs}", True, (255, 215, 0))
        VIRTUAL_SCREEN.blit(hs_surf, (10, V_HEIGHT - 50))

        if ACTIVE_POWERUP:
            ico = pygame.transform.scale(GAME_SPRITES[ACTIVE_POWERUP], (50, 50))
            VIRTUAL_SCREEN.blit(ico, (10, 10))
            rem = max(0, (POWERUP_END_TIME - ticks) // 1000)
            VIRTUAL_SCREEN.blit(FONT_TIMER.render(f"{rem}s", True, (0, 255, 255)), (50, 20))

        if diff_timer and ticks - diff_timer < 2000:
            msg = FONT_LARGE.render("TRAPS ACTIVE!!", True, (255, 0, 0))
            VIRTUAL_SCREEN.blit(msg, (V_WIDTH // 2 - msg.get_width() // 2, V_HEIGHT // 2))

        if BOSS_ACTIVE:
            badge = FONT_HORROR.render("DEVASTATOR", True, (255, 60, 60))
            VIRTUAL_SCREEN.blit(badge, (V_WIDTH - badge.get_width() - 6, 6))

        refresh_screen()
        FPSCLOCK.tick(FPS)


# =====================================================================
# DEATH & GAME-OVER
# =====================================================================

def _run_death_anim(chippu, playerx, playery, score):
    chippu.on_death()
    bg_x  = 0.0
    start = pygame.time.get_ticks()

    while not chippu.death_done:
        dt    = FPSCLOCK.get_time()
        ticks = pygame.time.get_ticks()
        if ticks - start > 1500:
            break

        for event in pygame.event.get():
            if event.type == QUIT:
                quit_game()

        VIRTUAL_SCREEN.blit(GAME_SPRITES['background'], (int(bg_x), 0))
        VIRTUAL_SCREEN.blit(GAME_SPRITES['background'], (int(bg_x) + V_WIDTH, 0))
        VIRTUAL_SCREEN.blit(GAME_SPRITES['base'], (0, GROUNDY))

        chippu.update(dt, playerx, playery, 4, None, ticks)
        chippu.draw(VIRTUAL_SCREEN, playerx, playery, None, ticks, 0)

        refresh_screen()
        FPSCLOCK.tick(FPS)

    return gameover(score)


def gameover(s):
    global G_OVER
    G_OVER = True
    if s > loadHighScore():
        saveHighScore(s)
    go_w      = GAME_SPRITES['gameover'].get_width()
    go_h      = GAME_SPRITES['gameover'].get_height()
    score_msg = FONT_LARGE.render(f"Score: {s}", True, (65, 25, 0))

    ovrlay = pygame.Surface((V_WIDTH, V_HEIGHT), pygame.SRCALPHA)
    ovrlay.fill((0, 0, 0, 150))
    VIRTUAL_SCREEN.blit(ovrlay, (0, 0))
    VIRTUAL_SCREEN.blit(GAME_SPRITES['gameover'],(0,0))
    VIRTUAL_SCREEN.blit(score_msg,(V_WIDTH // 2 - score_msg.get_width() // 2, 385))
    refresh_screen()
    pygame.time.delay(3000)
    pygame.event.clear()
    POWERUPS_ON_SCREEN.clear()
    G_OVER = False


# =====================================================================
# ASSET LOADER
# =====================================================================

def _make_powerup_bird(base_surf, tint, alpha=160):
    s = base_surf.copy()
    overlay = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    overlay.fill((*tint, alpha))
    s.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return s

def loadAssets():
    GAME_SPRITES['numbers'] = [
        pygame.transform.scale(
            pygame.image.load(resource_path(f"gallery/fritters/{i}.png")).convert_alpha(),
            (35, 50)) for i in range(10)]
    GAME_SPRITES['background'] = pygame.image.load(resource_path("gallery/fritters/bg.png")).convert()
    GAME_SPRITES['controls']   = pygame.image.load(resource_path("gallery/fritters/controls.jpg")).convert()
    GAME_SPRITES['base']       = pygame.image.load(resource_path("gallery/fritters/log_base.png")).convert_alpha()
    GAME_SPRITES['player']     = pygame.image.load(resource_path("gallery/fritters/bird.png")).convert_alpha()
    coin_sprite                = pygame.image.load(resource_path("gallery/fritters/coin.png")).convert_alpha()
    GAME_SPRITES['coin']       = pygame.transform.scale(coin_sprite, (30, 30))
    GAME_SPRITES['boss']       = pygame.image.load(resource_path("gallery/fritters/boss.png")).convert_alpha()
    GAME_SPRITES['home']       = pygame.image.load(resource_path("gallery/fritters/home.png")).convert_alpha()
    GAME_SPRITES['gameover']   = pygame.image.load(resource_path("gallery/fritters/title.png")).convert_alpha()

    p_img = pygame.image.load(resource_path("gallery/fritters/log.png")).convert_alpha()
    GAME_SPRITES['pipe'] = (pygame.transform.rotate(p_img, 180), p_img)

    GAME_SPRITES['shield'] = pygame.image.load(resource_path("gallery/fritters/shield.png")).convert_alpha()
    GAME_SPRITES['phaser'] = pygame.image.load(resource_path("gallery/fritters/phaser_suit.png")).convert_alpha()

    frames = []
    for i in range(10):
        path = resource_path(f"gallery/fritters/bird_frames/bird_{i}.png")
        if os.path.exists(path):
            frames.append(pygame.image.load(path).convert_alpha())
        else:
            break
    if not frames:
        frames = [GAME_SPRITES['player'], GAME_SPRITES['player']]
    GAME_SPRITES['player_frames'] = frames

    shield_path = resource_path("gallery/fritters/shield_bird.png")
    if os.path.exists(shield_path):
        GAME_SPRITES['player_shield'] = pygame.image.load(shield_path).convert_alpha()

    phaser_path = resource_path("gallery/fritters/phaser_bird.png")
    if os.path.exists(phaser_path):
        GAME_SPRITES['player_phaser'] = pygame.image.load(phaser_path).convert_alpha()

    for s in ['point', 'svoosh', 'die', 'start', 'flap', 'btn_click']:
        GAME_SOUNDS[s] = pygame.mixer.Sound(resource_path(f"gallery/sounds/{s}.mp3"))

    update_volumes()


# =====================================================================
# ENTRY POINT
# =====================================================================

if __name__ == "__main__":
    loadAssets()
    while True:
        HomeScreen()
        mainGame()
