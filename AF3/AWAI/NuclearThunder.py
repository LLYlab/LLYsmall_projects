import pygame
import sys
import random
import math
from pygame.locals import *

pygame.init()

# ==================== 世界与屏幕 ====================
WORLD_W, WORLD_H = 3000, 2000
SCREEN_W, SCREEN_H = 1200, 800
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("红蓝对抗 - 火控导弹·炸弹抛射")

# ==================== 字体 ====================
try:
    FONT = pygame.font.SysFont('simhei', 18)
    BIG_FONT = pygame.font.SysFont('simhei', 30)
except:
    FONT = pygame.font.SysFont('Arial', 18)
    BIG_FONT = pygame.font.SysFont('Arial', 30)

WHITE = (255,255,255); BLACK = (0,0,0)
RED = (220,50,50); BLUE = (50,50,220)
GREEN = (0,200,0); GRAY = (150,150,150)
YELLOW = (255,255,0); ORANGE = (255,150,0)
DARK_RED = (200,0,0); LIGHT_BLUE = (100,200,255)

# ==================== 相机 ====================
camera_x, camera_y = 0, 0
zoom = 1.0
dragging = False
last_mouse = (0,0)

def world_to_screen(wx, wy):
    sx = (wx - camera_x) * zoom + SCREEN_W // 2
    sy = (wy - camera_y) * zoom + SCREEN_H // 2
    return int(sx), int(sy)

def screen_to_world(sx, sy):
    wx = (sx - SCREEN_W // 2) / zoom + camera_x
    wy = (sy - SCREEN_H // 2) / zoom + camera_y
    return wx, wy

def handle_camera(event):
    global camera_x, camera_y, zoom, dragging, last_mouse
    if event.type == MOUSEWHEEL:
        mx, my = pygame.mouse.get_pos()
        wx, wy = screen_to_world(mx, my)
        zoom *= 1.1 if event.y > 0 else 0.9
        zoom = max(0.3, min(3.0, zoom))
        camera_x = wx - (mx - SCREEN_W//2) / zoom
        camera_y = wy - (my - SCREEN_H//2) / zoom
    elif event.type == MOUSEBUTTONDOWN and event.button == 2:
        dragging, last_mouse = True, event.pos
    elif event.type == MOUSEBUTTONUP and event.button == 2:
        dragging = False
    elif event.type == MOUSEMOTION and dragging:
        dx = event.pos[0] - last_mouse[0]
        dy = event.pos[1] - last_mouse[1]
        camera_x -= dx / zoom
        camera_y -= dy / zoom
        last_mouse = event.pos

# ==================== 全局列表 ====================
aircraft_list, bullets, bombs_list, buildings, ground_units, missiles = [], [], [], [], [], []
deploy_types, selected_deploy = [], 0
red_res, blue_res = 500, 500
RES_RATE = 5
red_detected_buildings, blue_detected_buildings = set(), set()

TYPE_NAMES = {
    'standard':'标准战斗机','speedy':'高速战斗机','heavy':'重型战斗机',
    'attacker':'攻击机','bomber':'轰炸机','dogfighter':'狗斗机',
    'jet':'德国喷气','missile_plane':'导弹飞机','attacker_rear':'攻击机改',
    'airbase':'基地机场','forward_airbase':'前线机场','resource_base':'资源基地',
    'missile_aa':'导弹防空塔','long_range_aa':'远程导弹防空塔','gun_aa':'机炮防空塔',
    'rally':'部队集结点','gun_aa_rally':'机炮AA集结点','missile_aa_rally':'导弹AA集结点',
    'radar':'预警雷达','tank':'坦克','gun_aa_vehicle':'机炮防空车',
    'missile_aa_vehicle':'导弹防空车','infantry':'机动步兵'
}

AIRCRAFT_CONFIG = {
    'standard': {'speed':2,'max_hp':100,'turn_rate':2,'attack_range':100,'attack_dmg':10,
                 'attack_angle':5,'ground_dmg':0.01,'ground_radius':15,'size':7,'shape':'triangle',
                 'role':'fighter','ammo':500,'bombs':1,'bomb_dmg':150,'bomb_radius':40,
                 'cooldown':5,'visibility':5},
    'speedy': {'speed':4,'max_hp':60,'turn_rate':1,'attack_range':80,'attack_dmg':8,
               'attack_angle':5,'ground_dmg':0.006,'ground_radius':10,'size':5,'shape':'narrow',
               'role':'fighter','ammo':400,'bombs':1,'bomb_dmg':120,'bomb_radius':35,
               'cooldown':5,'visibility':3},
    'heavy': {'speed':2.5,'max_hp':200,'turn_rate':1,'attack_range':150,'attack_dmg':30,
              'attack_angle':5,'ground_dmg':0.02,'ground_radius':20,'size':10,'shape':'triangle',
              'role':'fighter','ammo':300,'bombs':2,'bomb_dmg':200,'bomb_radius':50,
              'cooldown':20,'has_secondary':True,'sec_dmg':5,'sec_cooldown':5,'visibility':8},
    'attacker': {'speed':1.5,'max_hp':150,'turn_rate':1,'attack_range':120,'attack_dmg':40,
                 'attack_angle':5,'ground_dmg':0.5,'ground_radius':30,'size':11,'shape':'triangle',
                 'role':'attacker','ammo':400,'bombs':2,'bomb_dmg':250,'bomb_radius':60,
                 'cooldown':20,'visibility':10},
    'advanced_attacker': {'speed':1.6,'max_hp':160,'turn_rate':1,'attack_range':140,'attack_dmg':45,
                         'attack_angle':10,'ground_dmg':0.6,'ground_radius':40,'size':11,'shape':'triangle',
                         'role':'attacker','ammo':350,'bombs':2,'bomb_dmg':350,'bomb_radius':80,
                         'cooldown':18,'visibility':12,'guided_bombs':True,'bomb_speed':4,'bomb_turn':3,'bomb_range':3000},
    'bomber': {'speed':1.5,'max_hp':300,'turn_rate':0.5,'attack_range':60,'attack_dmg':10,
               'attack_angle':15,'ground_dmg':0.6,'ground_radius':80,'size':9,'shape':'wide_triangle',
               'role':'bomber','ammo':200,'bombs':8,'bomb_dmg':400,'bomb_radius':100,
               'cooldown':20,'visibility':20},
    'dogfighter': {'speed':1.8,'max_hp':80,'turn_rate':5,'attack_range':90,'attack_dmg':8,
                   'attack_angle':5,'ground_dmg':0.004,'ground_radius':10,'size':6,'shape':'small_triangle',
                   'role':'fighter','ammo':600,'bombs':1,'bomb_dmg':100,'bomb_radius':30,
                   'cooldown':5,'visibility':4},
    'jet': {'speed':5.5,'max_hp':80,'turn_rate':0.8,'attack_range':100,'attack_dmg':10,
            'attack_angle':5,'ground_dmg':0.006,'ground_radius':10,'size':6,'shape':'narrow',
            'role':'fighter','ammo':400,'bombs':1,'bomb_dmg':130,'bomb_radius':35,
            'cooldown':5,'visibility':3},
    'missile_plane': {'speed':2.5,'max_hp':120,'turn_rate':2,'attack_range':350,'attack_dmg':0,
                      'attack_angle':30,'ground_dmg':0,'ground_radius':0,'size':9,'shape':'triangle',
                      'role':'fighter','weapon_type':'missile','ammo':8,'bombs':0,'bomb_dmg':0,'bomb_radius':0,
                      'cooldown':50,'visibility':6},
    'attacker_rear': {'speed':1.5,'max_hp':150,'turn_rate':1,'attack_range':120,'attack_dmg':40,
                      'attack_angle':180,'ground_dmg':0.5,'ground_radius':30,'size':11,'shape':'triangle',
                      'role':'attacker','ammo':500,'bombs':2,'bomb_dmg':220,'bomb_radius':55,
                      'cooldown':10,'visibility':10}
}

MISSILE_TYPES = {
    'A-IR':   {'speed':7,'turn':10,'range':400,'type':'ir','view':30,'color':(255,100,100)},
    'A-IRB':  {'speed':7,'turn':10,'range':400,'type':'ir','view':6,'color':(255,50,50)},
    'G-IR':   {'speed':8,'turn':12,'range':600,'type':'ir','view':30,'color':(255,80,80)},
    'G-IRA':  {'speed':5,'turn':8,'range':1500,'type':'ir','view':30,'color':(200,60,60)},
    'G-RA':   {'speed':9,'turn':15,'range':600,'type':'radar','color':(200,200,255)},
    'GC-IR':  {'speed':7,'turn':10,'range':700,'type':'ir','view':30,'color':(255,120,120)},
    'GC-R':   {'speed':8,'turn':5,'range':500,'type':'radar','search_angle':20,'beam':1,'color':(150,150,255)}
}

def add_resource(obj):
    global red_res, blue_res
    reward = 0
    if isinstance(obj, Aircraft): reward = 50
    elif isinstance(obj, GroundUnit):
        if obj.type == 'tank': reward = 40
        elif obj.type in ('gun_aa_vehicle','missile_aa_vehicle'): reward = 30
        elif obj.type == 'infantry': reward = 15
    elif isinstance(obj, Building):
        if obj.type == 'airbase': reward = 200
        elif obj.type == 'forward_airbase': reward = 100
        elif obj.type == 'resource_base': reward = 150
        elif 'aa' in obj.type or 'AA' in obj.type: reward = 50
        elif 'rally' in obj.type: reward = 30
        else: reward = 20
    if obj.team == 'red': blue_res += reward
    else: red_res += reward

# ==================== 子弹类（增加对炸弹的拦截） ====================
class Bullet:
    def __init__(self, x, y, angle, speed, damage, team, is_aa=False, target=None, max_range=None):
        self.x, self.y, self.angle, self.speed = x, y, angle, speed
        self.damage, self.team, self.alive = damage, team, True
        self.is_aa = is_aa  # 是否为防空机炮子弹
        self.target = target
        # 子弹飞行里程与最大射程（用于机炮子弹到达射程后销毁）
        self.traveled = 0.0
        self.max_range = max_range

    def update(self):
        if not self.alive: return
        rad = math.radians(self.angle)
        dx = self.speed * math.cos(rad)
        dy = self.speed * math.sin(rad)
        self.x += dx
        self.y += dy
        self.traveled += math.hypot(dx, dy)
        # 若设置了最大射程，达到后销毁（机炮子弹行为）
        if self.max_range is not None and self.traveled >= self.max_range:
            self.alive = False
            return
        if self.x<0 or self.x>WORLD_W or self.y<0 or self.y>WORLD_H:
            self.alive=False; return
        # 检查碰撞炸弹
        for bomb in bombs_list:
            if not bomb.alive: continue
            if math.hypot(bomb.x - self.x, bomb.y - self.y) < 10:
                if self.is_aa:
                    # 如果子弹有指定目标且目标为该炸弹，提高拦截概率
                    if self.target is bomb:
                        prob = 0.6
                    else:
                        # 爆炸临近提高拦截概率
                        bt = getattr(bomb,'timer',999)
                        if bt < 15: prob = 0.35
                        else: prob = 0.08
                    if random.random() < prob:
                        bomb.alive = False
                        self.alive = False
                        return
        # 碰撞飞机/地面/建筑
        for obj in aircraft_list+ground_units+buildings:
            if not obj.alive or obj.team==self.team: continue
            if math.hypot(obj.x-self.x, obj.y-self.y) < getattr(obj,'size',10)+2:
                obj.hp -= self.damage
                self.alive=False
                if isinstance(obj, Aircraft):
                    obj.full_aware_timer=180; obj.last_hit_time=pygame.time.get_ticks()
                if obj.hp<=0: obj.alive=False; add_resource(obj)
                break
    def draw(self):
        if not self.alive: return
        sx, sy = world_to_screen(self.x, self.y)
        pygame.draw.circle(screen, YELLOW, (sx,sy), max(2,int(3*zoom)))

# ==================== 炸弹类（抛射物理） ====================
class Bomb:
    def __init__(self, x, y, angle, speed, damage, radius, team):
        self.x, self.y = x, y
        self.angle = angle
        self.speed = speed      # 水平初速度
        self.damage = damage
        self.radius = radius
        self.team = team
        self.alive = True
        self.timer = 30         # 飞行帧数后爆炸

    # 允许外部指定飞行时间（帧数）
    def set_timer(self, t):
        self.timer = max(1, int(t))

    def update(self):
        if not self.alive: return
        # 运动：受二次方空气阻力影响（速度 v 的阻力与 v^2 成正比）
        rad = math.radians(self.angle)
        # 简单的二次阻力模型：每帧速度减少 k * v^2
        # 调低 k 值以减少速度衰减过快的问题
        k = 0.005
        v = max(0.0, self.speed)
        dv = k * v * v
        v = max(0.0, v - dv)
        # 更新当前速度以供下一帧使用
        self.speed = v
        self.x += v * math.cos(rad)
        self.y += v * math.sin(rad)
        self.timer -= 1
        if self.timer <= 0:
            for obj in ground_units+buildings:
                if not obj.alive or obj.team==self.team: continue
                d = math.hypot(obj.x - self.x, obj.y - self.y)
                if d <= self.radius:
                    obj.hp -= self.damage * (1 - d/self.radius)
                    if obj.hp<=0: obj.alive=False; add_resource(obj)
            self.alive=False

    def draw(self):
        if not self.alive: return
        sx, sy = world_to_screen(self.x, self.y)
        pygame.draw.circle(screen, ORANGE, (sx,sy), max(3,int(5*zoom)))


class GuidedBomb(Bomb):
    """制导炸弹：速度较慢，但能够一定转向追踪目标，飞行距离更远"""
    def __init__(self, x, y, angle, speed, damage, radius, team, target, turn=3, max_range=2000, powered_dist=500):
        super().__init__(x, y, angle, speed, damage, radius, team)
        self.target = target
        self.turn = turn
        self.traveled = 0
        self.max_range = max_range
        # 动力段距离（单位：世界坐标距离），动力段内维持较高速度与较强转向
        self.powered_dist = powered_dist
        self.powered_traveled = 0
        # 当前速度（动力段与非动力段不同处理）
        self.cur_speed = speed
        # 初始速度用于动力段的加速上限计算
        self.init_speed = speed
        # 非动力段可用的舵面转向能力（较小）
        self.wing_turn = max(0.6, turn * 0.35)
        # 阻力系数（非动力段）
        self.drag_k = 0.005

    def update(self):
        if not self.alive: return
        # 若目标失效，则按照惯性飞行并受阻力影响
        if not self.target or not self.target.alive:
            rad = math.radians(self.angle)
            # 非动力段也受阻力
            dv = self.drag_k * self.cur_speed * self.cur_speed
            self.cur_speed = max(0.0, self.cur_speed - dv)
            self.x += self.cur_speed * math.cos(rad)
            self.y += self.cur_speed * math.sin(rad)
            self.traveled += self.cur_speed
            self.timer -= 1
            if self.traveled >= self.max_range or self.timer <= 0:
                # 爆炸判定落地
                for obj in ground_units+buildings:
                    if not obj.alive or obj.team==self.team: continue
                    d = math.hypot(obj.x - self.x, obj.y - self.y)
                    if d <= self.radius:
                        obj.hp -= self.damage * (1 - d/self.radius)
                        if obj.hp<=0: obj.alive=False; add_resource(obj)
                self.alive = False
            return

        # 有效目标：先判断是否处于动力段
        target_angle = math.degrees(math.atan2(self.target.y - self.y, self.target.x - self.x))
        diff = (target_angle - self.angle + 540) % 360 - 180
        if self.powered_traveled < self.powered_dist:
            # 动力段：可用较大转向能力与恒定速度
            if diff > self.turn: self.angle += self.turn
            elif diff < -self.turn: self.angle -= self.turn
            else: self.angle = target_angle
            # 在动力段略微加速，直到达到初始速度的 1.2 倍
            max_power_speed = self.init_speed * 1.2
            accel = 0.02 * self.init_speed
            if self.cur_speed < max_power_speed:
                self.cur_speed = min(max_power_speed, self.cur_speed + accel)
            rad = math.radians(self.angle)
            dx = self.cur_speed * math.cos(rad); dy = self.cur_speed * math.sin(rad)
            self.x += dx; self.y += dy
            moved = math.hypot(dx,dy)
            self.traveled += moved; self.powered_traveled += moved
        else:
            # 非动力段：受阻力并仅通过弹翼进行有限修正
            if diff > self.wing_turn: self.angle += self.wing_turn
            elif diff < -self.wing_turn: self.angle -= self.wing_turn
            else: self.angle = target_angle
            # 阻力衰减速度
            dv = self.drag_k * self.cur_speed * self.cur_speed
            self.cur_speed = max(0.0, self.cur_speed - dv)
            rad = math.radians(self.angle)
            dx = self.cur_speed * math.cos(rad); dy = self.cur_speed * math.sin(rad)
            self.x += dx; self.y += dy
            moved = math.hypot(dx,dy)
            self.traveled += moved

        # 每帧减计时器，超时或到达射程则爆炸
        self.timer -= 1
        if self.traveled >= self.max_range or self.timer <= 0:
            for obj in ground_units+buildings:
                if not obj.alive or obj.team==self.team: continue
                d = math.hypot(obj.x - self.x, obj.y - self.y)
                if d <= self.radius:
                    obj.hp -= self.damage * (1 - d/self.radius)
                    if obj.hp<=0: obj.alive=False; add_resource(obj)
            self.alive = False
            return

        # 爆炸判定：接近目标即爆
        if math.hypot(self.target.x - self.x, self.target.y - self.y) <= 15:
            for obj in ground_units+buildings:
                if not obj.alive or obj.team==self.team: continue
                d = math.hypot(obj.x - self.x, obj.y - self.y)
                if d <= self.radius:
                    obj.hp -= self.damage * (1 - d/self.radius)
                    if obj.hp<=0: obj.alive=False; add_resource(obj)
            self.alive = False

    def draw(self):
        if not self.alive: return
        sx, sy = world_to_screen(self.x, self.y)
        pygame.draw.circle(screen, DARK_RED, (sx,sy), max(3,int(5*zoom)))

# ==================== 导弹类（颜色） ====================
class Missile:
    def __init__(self, x, y, angle, target, team, mtype='A-IR'):
        self.x,self.y,self.angle,self.target,self.team = x,y,angle,target,team
        self.alive=True
        cfg=MISSILE_TYPES[mtype]
        self.speed,self.turn,self.max_range = cfg['speed'],cfg['turn'],cfg['range']
        self.is_ir = cfg['type']=='ir'
        self.damage,self.traveled = 100,0
        self.color = cfg.get('color', YELLOW)
    def update(self):
        if not self.alive or not self.target or not self.target.alive:
            self.alive=False; return
        # 若目标是未制导的炸弹（Bomb），则不要对其进行制导/攻击
        BombClass = globals().get('Bomb')
        if BombClass is not None and isinstance(self.target, BombClass) and not getattr(self.target, 'is_guided', False):
            # 取消导弹
            self.alive = False
            return
        if self.is_ir and isinstance(self.target, Aircraft) and self.target.flare_timer>0:
            if math.hypot(self.target.x-self.x, self.target.y-self.y) < 200:
                self.alive=False; return
        target_angle = math.degrees(math.atan2(self.target.y-self.y, self.target.x-self.x))
        diff = (target_angle - self.angle + 540)%360 - 180
        if diff>self.turn: self.angle+=self.turn
        elif diff<-self.turn: self.angle-=self.turn
        else: self.angle = target_angle
        rad = math.radians(self.angle)
        dx = self.speed*math.cos(rad); dy = self.speed*math.sin(rad)
        self.x+=dx; self.y+=dy; self.traveled+=math.hypot(dx,dy)
        if math.hypot(self.target.x-self.x, self.target.y-self.y) < 15:
            # 先尝试按常规 hp 属性处理
            if hasattr(self.target, 'hp'):
                self.target.hp -= self.damage
            # 或者调用通用接口
            elif hasattr(self.target, 'take_damage'):
                self.target.take_damage(self.damage)
            else:
                # 若目标是炸弹并且有爆炸方法，则触发爆炸；否则标记为死亡
                if BombClass is not None and isinstance(self.target, BombClass):
                    if hasattr(self.target, 'explode'):
                        self.target.explode()
                    else:
                        self.target.alive = False
            # 命中后导弹消失
            self.alive = False
            self.alive=False
            if isinstance(self.target, Aircraft):
                self.target.full_aware_timer=180; self.target.last_hit_time=pygame.time.get_ticks()
            if self.target.hp<=0: self.target.alive=False; add_resource(self.target)
        elif self.traveled >= self.max_range:
            self.alive=False
    def draw(self):
        if not self.alive: return
        s=4; local=[(s*1.5,0),(-s*1.5,-s),(-s*1.5,s)]
        rad=math.radians(self.angle); cos_a,sin_a=math.cos(rad),math.sin(rad)
        world=[(self.x+lx*cos_a-ly*sin_a, self.y+lx*sin_a+ly*cos_a) for lx,ly in local]
        sw=[world_to_screen(wx,wy) for wx,wy in world]
        pygame.draw.polygon(screen, self.color, sw)

# ==================== 建筑类（火控转向锁定、子弹发射、弹药显示） ====================
class Building:
    def __init__(self, x, y, btype, team):
        self.x, self.y, self.type, self.team = x, y, btype, team
        self.alive = True; self.angle = 0; self.reload = 0
        self.src_angle = random.uniform(0,360)
        self.fire_locked = None
        self.missile_clip = []; self.clip_reload = 0
        self.spawn_timer = 0
        self.tracked_targets = []
        if btype=='airbase': self.max_hp, self.size = 6000, 40
        elif btype=='forward_airbase': self.max_hp, self.size = 3000, 30
        elif btype=='resource_base': self.max_hp, self.size = 1000, 25
        elif btype=='missile_aa':
            self.max_hp, self.size = 500, 20
            self.attack_range, self.cooldown = 300, 120
            self.missile_range, self.src_range = 600, 300
            self.missile_main, self.missile_special = 'G-IR','G-RA'
        elif btype=='long_range_aa':
            self.max_hp, self.size = 400, 22
            self.attack_range, self.cooldown = 400, 180
            self.missile_range, self.src_range = 1500, 400
            self.missile_main, self.missile_special = 'G-IRA','G-RA'
        elif btype=='gun_aa':
            self.max_hp, self.size = 300, 18
            self.attack_range, self.damage, self.cooldown = 200, 15, 8   # 伤害提升，发射子弹
            # 将探测（拦截）半径扩大为射程的 1.3 倍，以提高探测范围
            self.src_range = int(self.attack_range * 1.3)
        elif btype=='radar':
            self.max_hp, self.size = 200, 20
            self.scan_range = 2500; self.attack_range = 0
        elif 'rally' in btype: self.max_hp, self.size = 400, 15
        self.hp = self.max_hp
        self.color = (200,50,50) if team=='red' else (50,50,200)
        if btype=='resource_base': self.color = (0,200,200)
        if 'rally' in btype: self.color = GRAY
        if btype=='radar': self.color = (0,100,0)
        self.fill_clip()

    def fill_clip(self):
        if hasattr(self,'missile_main'):
            self.missile_clip = [self.missile_main]*3 + [self.missile_special]

    def update(self):
        if not self.alive: return
        if 'rally' in self.type:
            self.spawn_timer += 1
            if self.spawn_timer >= 3600: self.spawn_timer=0; self.spawn_rally()
            return
        if self.type == 'radar':
            self.src_angle = (self.src_angle+0.5)%360; self.scan_radar(); return
        if hasattr(self,'src_range'):
            self.src_angle = (self.src_angle+1)%360
            self.update_fire_control()

    def spawn_rally(self):
        x,y,t = self.x,self.y,self.team
        if self.type=='rally':
            for _ in range(3): ground_units.append(GroundUnit(x+random.randint(-20,20),y+random.randint(-20,20),'tank',t))
            for _ in range(5): ground_units.append(GroundUnit(x+random.randint(-20,20),y+random.randint(-20,20),'infantry',t))
        elif self.type=='gun_aa_rally':
            for _ in range(2): ground_units.append(GroundUnit(x+random.randint(-20,20),y+random.randint(-20,20),'gun_aa_vehicle',t))
            for _ in range(2): ground_units.append(GroundUnit(x+random.randint(-20,20),y+random.randint(-20,20),'infantry',t))
        elif self.type=='missile_aa_rally':
            ground_units.append(GroundUnit(x+random.randint(-10,10),y+random.randint(-10,10),'missile_aa_vehicle',t))
            for _ in range(3): ground_units.append(GroundUnit(x+random.randint(-10,10),y+random.randint(-10,10),'infantry',t))

    def scan_radar(self):
        self.tracked_targets = [t for t in self.tracked_targets if t.alive and math.hypot(t.x-self.x, t.y-self.y)<=self.scan_range]
        for a in aircraft_list:
            if not a.alive or a.team==self.team or len(self.tracked_targets)>=5: continue
            dx,dy = a.x-self.x, a.y-self.y
            dist = math.hypot(dx,dy)
            if dist<=self.scan_range:
                angle_to = math.degrees(math.atan2(dy,dx))
                if abs((angle_to-self.src_angle+540)%360-180)<=90 and a not in self.tracked_targets:
                    self.tracked_targets.append(a)
        for t in self.tracked_targets: t.visibility_buff = max(t.visibility_buff, 500)

    def update_fire_control(self):
        # 选择炮管目标：优先被探测（visibility_buff>0）且在src_range内
        best_target = None
        best_priority = -1
        # 首先考虑炸弹（优先拦截即将落地的炸弹）
        for bomb in bombs_list:
            if not bomb.alive or bomb.team == self.team: continue
            dx, dy = bomb.x - self.x, bomb.y - self.y
            dist = math.hypot(dx, dy)
            if dist > getattr(self,'src_range', 0): continue
            bt = getattr(bomb,'timer',999)
            # 如果炸弹临近爆炸，优先级显著提高
            priority = 12 if bt < 30 else 5
            priority -= dist / 100
            if priority > best_priority:
                best_priority = priority
                best_target = bomb
        # 其次考虑飞机目标
        for a in aircraft_list:
            if not a.alive or a.team == self.team: continue
            dx, dy = a.x - self.x, a.y - self.y
            dist = math.hypot(dx, dy)
            if dist > getattr(self,'src_range', 0): continue
            priority = 0
            if a.visibility_buff > 0:
                priority = 10
            elif a in self.tracked_targets:
                priority = 5
            priority -= dist / 100
            if priority > best_priority:
                best_priority = priority
                best_target = a
        # 转向目标
        if best_target:
            # 始终显示瞄准（不要求炮管与瞄准线平行）
            self.fire_locked = best_target
            target_angle = math.degrees(math.atan2(best_target.y-self.y, best_target.x-self.x))
            diff = (target_angle - self.angle + 540)%360 - 180
            # 快速转向炮座
            turn_rate = 3
            if diff > turn_rate: self.angle += turn_rate
            elif diff < -turn_rate: self.angle -= turn_rate
            else: self.angle = target_angle
            # 火控只有在炮座与目标角度接近并且在射程内时才发射
            if abs((target_angle - self.angle + 540)%360 - 180) < 5 and math.hypot(best_target.x-self.x, best_target.y-self.y) <= self.attack_range:
                # 发射
                self.attack_target()
        else:
            # 无目标缓慢旋转
            self.angle = (self.angle + 1) % 360

    def attack_target(self):
        if self.type == 'gun_aa':
            if self.fire_locked and self.reload <= 0:
                # 发射子弹
                rad = math.radians(self.angle)
                bx, by = self.x + 10*math.cos(rad), self.y + 10*math.sin(rad)
                # 机炮子弹带上目标与最大射程，达到射程即销毁
                bullets.append(Bullet(bx, by, self.angle, 8, self.damage, self.team, is_aa=True, target=self.fire_locked, max_range=self.attack_range))
                self.reload = self.cooldown
        elif self.type in ('missile_aa','long_range_aa'):
            if self.fire_locked and self.missile_clip and self.reload <= 0:
                mtype = self.missile_clip.pop(0)
                missiles.append(Missile(self.x, self.y, self.angle, self.fire_locked, self.team, mtype))
                self.reload = self.cooldown
                if not self.missile_clip: self.clip_reload = self.cooldown * 4
        if self.reload > 0: self.reload -= 1
        if self.clip_reload > 0:
            self.clip_reload -= 1
            if self.clip_reload == 0: self.fill_clip()

    def draw(self):
        if not self.alive: return
        sx, sy = world_to_screen(self.x, self.y)
        r = max(4, int(self.size * zoom))
        pygame.draw.rect(screen, self.color, (sx - r//2, sy - r//2, r, r))
        # 攻击范围圈
        if hasattr(self,'attack_range') and self.attack_range > 0:
            rad_r = int(self.attack_range * zoom)
            if rad_r > 5:
                surf = pygame.Surface((rad_r*2, rad_r*2), SRCALPHA)
                pygame.draw.circle(surf, (0,255,0,10), (rad_r, rad_r), rad_r)
                screen.blit(surf, (sx - rad_r, sy - rad_r))
        # 雷达/ SRC 扇形
        if self.type == 'radar':
            scan_r = int(self.scan_range * zoom)
            if scan_r > 5:
                surf = pygame.Surface((scan_r*2, scan_r*2), SRCALPHA)
                points = [(scan_r, scan_r)]
                a1 = math.radians(self.src_angle-90); a2 = math.radians(self.src_angle+90)
                points.append((scan_r + scan_r*math.cos(a1), scan_r + scan_r*math.sin(a1)))
                points.append((scan_r + scan_r*math.cos(a2), scan_r + scan_r*math.sin(a2)))
                pygame.draw.polygon(surf, (0,100,0,10), points)
                pygame.draw.polygon(surf, (0,150,0,80), points, width=max(1,int(2*zoom)))
                screen.blit(surf, (sx - scan_r, sy - scan_r))
        elif hasattr(self,'src_range') and self.src_range > 0:
            sr = int(self.src_range * zoom)
            if sr > 5:
                surf = pygame.Surface((sr*2, sr*2), SRCALPHA)
                points = [(sr, sr)]
                a1 = math.radians(self.src_angle-15); a2 = math.radians(self.src_angle+15)
                points.append((sr + sr*math.cos(a1), sr + sr*math.sin(a1)))
                points.append((sr + sr*math.cos(a2), sr + sr*math.sin(a2)))
                pygame.draw.polygon(surf, (100,100,255,10), points)
                pygame.draw.polygon(surf, (150,150,255,80), points, width=max(1,int(2*zoom)))
                screen.blit(surf, (sx - sr, sy - sr))
        # 炮管
        if hasattr(self,'angle') and hasattr(self,'attack_range') and self.attack_range > 0:
            rad = math.radians(self.angle)
            ex = sx + r * 1.2 * math.cos(rad) * zoom
            ey = sy + r * 1.2 * math.sin(rad) * zoom
            pygame.draw.line(screen, BLACK, (sx, sy), (ex, ey), max(1, int(2*zoom)))
        # 导弹瞄准线
        if self.fire_locked and self.fire_locked.alive and self.type in ('missile_aa','long_range_aa'):
            tx, ty = world_to_screen(self.fire_locked.x, self.fire_locked.y)
            draw_dashed_line(screen, DARK_RED, (sx,sy), (tx,ty), dash_length=4, width=max(1,int(1*zoom)))
        # 弹药显示
        if hasattr(self,'missile_clip'):
            ammo_text = f"{len(self.missile_clip)}/4"
            txt = FONT.render(ammo_text, True, WHITE)
            screen.blit(txt, (sx - 10, sy - r - 15))
        # 血条
        bar_w = r
        pygame.draw.rect(screen, BLACK, (sx - bar_w//2, sy - r//2 - 6, bar_w, 3))
        pygame.draw.rect(screen, GREEN, (sx - bar_w//2, sy - r//2 - 6, int(bar_w * self.hp/self.max_hp), 3))

# ---------- 地面单位类（类似改造）----------
class GroundUnit:
    def __init__(self, x, y, utype, team):
        self.x,self.y,self.type,self.team = x,y,utype,team
        self.alive = True; self.angle = random.uniform(0,360); self.turret_angle = self.angle
        self.reload = 0; self.src_angle = random.uniform(0,360) if 'aa' in utype else 0
        self.fire_locked = None; self.missile_clip = []; self.clip_reload = 0
        self.evasive_timer = 0
        if utype=='tank':
            self.max_hp,self.speed,self.attack_range,self.damage = 300,0.8,200,40
            self.size,self.cooldown = 8,40; self.bullet_speed,self.bullet_damage = 6,40
        elif utype=='gun_aa_vehicle':
            self.max_hp,self.speed,self.attack_range,self.damage = 200,1.2,250,15
            self.size,self.cooldown = 10,8; self.bullet_speed,self.bullet_damage,self.src_range = 8,15,250
            # 将探测范围扩展为机炮射程的 1.3 倍
            self.src_range = int(self.attack_range * 1.3)
        elif utype=='missile_aa_vehicle':
            self.max_hp,self.speed,self.attack_range,self.damage = 180,1.2,350,30
            self.size,self.cooldown = 10,120; self.src_range = 350
            self.missile_main,self.missile_special = 'GC-IR','GC-R'
        elif utype=='infantry':
            self.max_hp,self.speed,self.attack_range,self.damage = 100,0.6,150,5
            self.size,self.cooldown = 6,5; self.bullet_speed,self.bullet_damage = 10,5
        self.hp = self.max_hp
        self.color = (200,50,50) if team=='red' else (50,50,200)
        if utype=='infantry': self.color = GRAY
        self.fill_clip()

    def fill_clip(self):
        if self.type=='missile_aa_vehicle':
            self.missile_clip = [self.missile_main]*3 + [self.missile_special]

    def update(self):
        if not self.alive: return
        # AA车辆遇到即将落地的炸弹会尝试机动规避
        if 'aa' in self.type and self.evasive_timer == 0:
            for bomb in bombs_list:
                if not bomb.alive or bomb.team == self.team: continue
                d = math.hypot(bomb.x - self.x, bomb.y - self.y)
                # 当炸弹较近且即将爆炸时尝试规避
                if d < 200 and getattr(bomb,'timer',999) < 20:
                    # 远离炸弹方向机动
                    away_angle = math.degrees(math.atan2(self.y - bomb.y, self.x - bomb.x))
                    rad = math.radians(away_angle)
                    self.x += self.speed * 4 * math.cos(rad)
                    self.y += self.speed * 4 * math.sin(rad)
                    self.evasive_timer = 30
                    break
        if self.evasive_timer > 0:
            self.evasive_timer -= 1
            # 稍微减慢其他行为
            if self.type in ('gun_aa_vehicle','missile_aa_vehicle'):
                self.src_angle = (self.src_angle+2)%360
            return
        if self.type in ('gun_aa_vehicle','missile_aa_vehicle'):
            self.src_angle = (self.src_angle+2)%360
            self.update_fire_control()
        else:
            self.combat_ground()

    def update_fire_control(self):
        # 同建筑逻辑
        best_target = None
        best_priority = -1
        # 优先考虑附近的炸弹
        for bomb in bombs_list:
            if not bomb.alive or bomb.team == self.team: continue
            dx, dy = bomb.x - self.x, bomb.y - self.y
            dist = math.hypot(dx, dy)
            if dist > getattr(self,'src_range', 0): continue
            bt = getattr(bomb,'timer',999)
            priority = 14 if bt < 30 else 6
            priority -= dist / 100
            if priority > best_priority:
                best_priority = priority
                best_target = bomb
        # 然后考虑飞机
        for a in aircraft_list:
            if not a.alive or a.team == self.team: continue
            dx, dy = a.x - self.x, a.y - self.y
            dist = math.hypot(dx, dy)
            if dist > getattr(self,'src_range', 0): continue
            priority = 0
            if a.visibility_buff > 0: priority = 10
            priority -= dist / 100
            if priority > best_priority:
                best_priority = priority
                best_target = a
        if best_target:
            # 始终显示瞄准线
            self.fire_locked = best_target
            target_angle = math.degrees(math.atan2(best_target.y-self.y, best_target.x-self.x))
            diff = (target_angle - self.angle + 540)%360 - 180
            turn_rate = 4
            if diff > turn_rate: self.angle += turn_rate
            elif diff < -turn_rate: self.angle -= turn_rate
            else: self.angle = target_angle
            # 炮塔独立转动，逐步指向目标
            tdiff = (target_angle - self.turret_angle + 540)%360 - 180
            turret_turn = 6
            if tdiff > turret_turn: self.turret_angle += turret_turn
            elif tdiff < -turret_turn: self.turret_angle -= turret_turn
            else: self.turret_angle = target_angle
            # 当炮塔与目标基本对准且在射程内时开火
            if abs((target_angle - self.turret_angle + 540)%360 - 180) < 8 and math.hypot(best_target.x-self.x, best_target.y-self.y) <= self.attack_range:
                self.attack_target()
        else:
            self.angle = (self.angle + 2) % 360
            self.follow_friends()

    def attack_target(self):
        if self.type == 'gun_aa_vehicle' and self.reload <= 0:
            target = self.fire_locked
            # 发射时尽量直接瞄准目标以提高拦截概率
            shot_angle = math.degrees(math.atan2(target.y - self.y, target.x - self.x)) if target else self.turret_angle
            rad = math.radians(shot_angle)
            bx, by = self.x + 10*math.cos(rad), self.y + 10*math.sin(rad)
            # 机炮车辆的子弹也携带最大射程，超过射程后销毁
            bullets.append(Bullet(bx, by, shot_angle, self.bullet_speed, self.bullet_damage, self.team, is_aa=True, target=target, max_range=self.attack_range))
            self.reload = self.cooldown
        elif self.type == 'missile_aa_vehicle' and self.missile_clip and self.reload <= 0:
            mtype = self.missile_clip.pop(0)
            missiles.append(Missile(self.x, self.y, self.turret_angle, self.fire_locked, self.team, mtype))
            self.reload = self.cooldown
            if not self.missile_clip: self.clip_reload = self.cooldown * 4
        if self.reload > 0: self.reload -= 1
        if self.clip_reload > 0:
            self.clip_reload -= 1
            if self.clip_reload == 0: self.fill_clip()

    def follow_friends(self):
        friends = [g for g in ground_units if g.alive and g.team==self.team and g!=self and not ('aa' in g.type)]
        if friends:
            friend = min(friends, key=lambda g: math.hypot(g.x-self.x, g.y-self.y))
            target_angle = math.degrees(math.atan2(friend.y-self.y, friend.x-self.x))
            diff = (target_angle - self.angle + 540)%360 - 180
            if diff > 2: self.angle += 2
            elif diff < -2: self.angle -= 2
            else: self.angle = target_angle
            rad = math.radians(self.angle)
            self.x += self.speed*0.5*math.cos(rad); self.y += self.speed*0.5*math.sin(rad)

    def combat_ground(self):
        enemies = [g for g in ground_units if g.alive and g.team!=self.team] + \
                  [b for b in buildings if b.alive and b.team!=self.team]
        if not enemies: return
        closest = min(enemies, key=lambda e: math.hypot(e.x-self.x, e.y-self.y))
        dist = math.hypot(closest.x-self.x, closest.y-self.y)
        target_angle = math.degrees(math.atan2(closest.y-self.y, closest.x-self.x))
        diff = (target_angle - self.angle + 540)%360 - 180
        if diff > 2: self.angle += 2
        elif diff < -2: self.angle -= 2
        else: self.angle = target_angle
        self.turret_angle = target_angle
        if dist > self.attack_range:
            rad = math.radians(self.angle)
            self.x += self.speed*math.cos(rad); self.y += self.speed*math.sin(rad)
        else:
            if self.reload > 0: self.reload -= 1
            else:
                rad = math.radians(self.turret_angle)
                bx, by = self.x + 10*math.cos(rad), self.y + 10*math.sin(rad)
                bullets.append(Bullet(bx, by, self.turret_angle, self.bullet_speed, self.bullet_damage, self.team))
                self.reload = self.cooldown

    def draw(self):
        if not self.alive: return
        sx,sy = world_to_screen(self.x, self.y)
        r = max(3, int(self.size*zoom))
        pygame.draw.circle(screen, self.color, (sx,sy), r)
        if hasattr(self,'src_range') and self.src_range>0:
            sr = int(self.src_range*zoom)
            if sr>5:
                surf = pygame.Surface((sr*2,sr*2), SRCALPHA)
                points = [(sr,sr)]
                a1 = math.radians(self.src_angle-15); a2 = math.radians(self.src_angle+15)
                points.append((sr + sr*math.cos(a1), sr + sr*math.sin(a1)))
                points.append((sr + sr*math.cos(a2), sr + sr*math.sin(a2)))
                pygame.draw.polygon(surf, (100,100,255,10), points)
                pygame.draw.polygon(surf, (150,150,255,80), points, width=max(1,int(2*zoom)))
                screen.blit(surf, (sx-sr, sy-sr))
        rad = math.radians(self.turret_angle)
        end_x = sx + r*1.5*math.cos(rad)*zoom; end_y = sy + r*1.5*math.sin(rad)*zoom
        pygame.draw.line(screen, BLACK, (sx,sy), (end_x,end_y), max(1,int(2*zoom)))
        # 导弹瞄准线
        if self.fire_locked and self.fire_locked.alive and self.type=='missile_aa_vehicle':
            tx, ty = world_to_screen(self.fire_locked.x, self.fire_locked.y)
            draw_dashed_line(screen, DARK_RED, (sx,sy), (tx,ty), dash_length=4, width=max(1,int(1*zoom)))
        # 弹药显示
        if self.type == 'missile_aa_vehicle':
            ammo_text = f"{len(self.missile_clip)}/4"
            txt = FONT.render(ammo_text, True, WHITE)
            screen.blit(txt, (sx - 10, sy - r - 15))
        pygame.draw.rect(screen, BLACK, (sx-r, sy-r-5, 2*r, 2))
        pygame.draw.rect(screen, GREEN, (sx-r, sy-r-5, int(2*r*self.hp/self.max_hp), 2))

# ==================== 辅助函数：虚线 ====================
def draw_dashed_line(surf, color, start_pos, end_pos, dash_length=5, width=1):
    x1, y1 = start_pos; x2, y2 = end_pos
    dx = x2 - x1; dy = y2 - y1
    dist = math.hypot(dx, dy)
    if dist == 0: return
    cos_t = dx / dist; sin_t = dy / dist
    step = dash_length * 2
    i = 0
    while i < dist:
        sx = x1 + cos_t * i; sy = y1 + sin_t * i
        seg_len = min(dash_length, dist - i)
        ex = x1 + cos_t * (i + seg_len); ey = y1 + sin_t * (i + seg_len)
        pygame.draw.line(surf, color, (sx, sy), (ex, ey), width)
        i += step


def estimate_flight_frames(dist, v0, k=0.005, max_frames=5000):
    """用离散模拟估算在二次阻力 k 下，初速度 v0 覆盖距离 dist 需要的帧数。
    返回估算帧数（最小为1）。"""
    if dist <= 0:
        return 1
    v = max(0.0, v0)
    total = 0.0
    frames = 0
    while total < dist and v > 0.01 and frames < max_frames:
        dv = k * v * v
        v = max(0.0, v - dv)
        total += v
        frames += 1
    if frames >= max_frames:
        # 退回保守估算
        return max(1, int(dist / max(0.1, v0)))
    return max(1, frames)


def can_reach_distance_before_speed_decay(dist, v0, k=0.005, min_speed_frac=0.15, max_frames=5000):
    """模拟判断：在阻力 k 下，初速度 v0 覆盖距离 dist 时，速度是否在未降到 v0*min_speed_frac 之前完成。
    若能在速度未跌破阈值前覆盖距离，则返回 True，否则返回 False。"""
    if dist <= 0:
        return True
    v = max(0.0, v0)
    min_allowed = v0 * min_speed_frac
    total = 0.0
    frames = 0
    while total < dist and v > 0.01 and frames < max_frames:
        dv = k * v * v
        v = max(0.0, v - dv)
        total += v
        frames += 1
        if v <= min_allowed:
            # 在到达目标前速度已降到或低于允许最小速度，判为不可接受
            return False
    return total >= dist

# ==================== 飞机类（炸弹改为抛射） ====================
class Aircraft:
    def __init__(self, x, y, angle, type_key, team):
        cfg = AIRCRAFT_CONFIG[type_key]
        self.type,self.team = type_key, team
        self.x,self.y,self.angle = x,y,angle
        self.speed,self.max_hp,self.hp = cfg['speed'], cfg['max_hp'], cfg['max_hp']
        self.turn_rate,self.attack_range,self.attack_dmg = cfg['turn_rate'], cfg['attack_range'], cfg['attack_dmg']
        self.attack_angle = cfg['attack_angle']
        self.ground_dmg,self.ground_radius = cfg['ground_dmg'], cfg['ground_radius']
        self.size,self.shape,self.role = cfg['size'], cfg['shape'], cfg['role']
        self.weapon_type = cfg.get('weapon_type','bullet')
        self.cooldown_time = cfg.get('cooldown',10)
        self.has_secondary = cfg.get('has_secondary',False)
        self.sec_dmg,self.sec_cooldown = cfg.get('sec_dmg',0), cfg.get('sec_cooldown',5)
        self.max_ammo,self.ammo = cfg['ammo'], cfg['ammo']
        self.max_bombs,self.bombs = cfg['bombs'], cfg['bombs']
        self.bomb_dmg,self.bomb_radius = cfg['bomb_dmg'], cfg['bomb_radius']
        self.reload_timer,self.sec_reload = 0,0
        self.alive = True; self.nav_target = None
        self.evasive_timer,self.evasive_angle = 0,0
        self.visibility = cfg.get('visibility',5)
        self.visibility_buff = 0
        self.detected_enemies = set()
        self.full_aware_timer = 0; self.last_hit_time = 0
        self.flares,self.flare_timer = 2,0
        self.color = (200,50,50) if team=='red' else (50,50,200)
        if type_key=='missile_plane': self.color = (0,0,255)
        elif type_key=='jet': self.color = (192,192,192)
        # 机载雷达：导弹飞机配备机载雷达，能在更远距离被动探测目标（360度）
        if type_key == 'missile_plane':
            # 基于经验值设置机载雷达探测半径
            self.radar_range = 800
            # 默认导弹类型（用于导弹飞机发射时的默认武器）
            self.missile_type = 'G-IR'
        # 返航标志（返回机场维修）
        self.returning_to_base = False

    def is_cas(self): return self.role in ('attacker','bomber')
    # ... 情报方法同前（省略，与上一版本相同）
    def is_trk(self, other):
        if self.full_aware_timer>0: return True
        for a in aircraft_list:
            if a.alive and a.team==self.team and a!=self and other in a.detected_enemies: return True
        return False
    def is_locked(self, other):
        if getattr(other,'visibility_buff',0)>0: return True
        if other in self.detected_enemies: return True
        return False
    def get_detect_multipliers(self, other):
        if self.is_locked(other): return 7,7,7
        if self.is_trk(other): return 5,5,3
        return 5,2,0.5
    def can_detect(self, other):
        if not other.alive or other.team==self.team: return False
        # 若是导弹飞机并配备机载雷达，则使用雷达范围进行360度探测
        if hasattr(self, 'radar_range'):
            return math.hypot(other.x - self.x, other.y - self.y) <= self.radar_range + getattr(other, 'visibility_buff', 0)
        mod = 2.0 if isinstance(other, Building) else (1.2 if isinstance(other, Aircraft) and other.type=='bomber' else 1.0)
        dx,dy = other.x-self.x, other.y-self.y
        angle_to = math.degrees(math.atan2(dy,dx))
        diff = abs((angle_to - self.angle + 540)%360 - 180)
        fm,sm,rm = self.get_detect_multipliers(other)
        mul = fm if diff<60 else (sm if diff<120 else rm)
        return math.hypot(dx,dy) <= self.attack_range * mul * mod + getattr(other,'visibility_buff',0)

    def update_detection(self):
        self.detected_enemies.clear()
        for b in buildings:
            if b.alive and b.type=='airbase' and b.team!=self.team: self.detected_enemies.add(b)
        db = red_detected_buildings if self.team=='blue' else blue_detected_buildings
        for b in db:
            if b.alive: self.detected_enemies.add(b)
        if self.full_aware_timer>0:
            self.full_aware_timer-=1
            for other in aircraft_list+ground_units+buildings:
                if other.alive and other.team!=self.team:
                    if math.hypot(other.x-self.x, other.y-self.y) <= 300 + self.visibility:
                        self.detected_enemies.add(other)
                        if isinstance(other, Building) and other.type!='airbase':
                            (red_detected_buildings if self.team=='red' else blue_detected_buildings).add(other)
            return
        for other in aircraft_list+ground_units+buildings:
            if not other.alive or other.team==self.team: continue
            if self.can_detect(other):
                self.detected_enemies.add(other)
                if isinstance(other, Building) and other.type!='airbase':
                    (red_detected_buildings if self.team=='red' else blue_detected_buildings).add(other)

    def update(self):
        if not self.alive: return
        for b in buildings:
            if b.alive and b.team==self.team and b.type in ('airbase','forward_airbase'):
                if math.hypot(b.x-self.x, b.y-self.y) < b.size+20:
                    self.ammo,self.bombs = self.max_ammo,self.max_bombs
                    self.returning_to_base = False
        self.update_detection()
        # 返航行为：在没有弹药或没有敌机时返航维修
        # 轰炸机若无炸弹立即返航；战斗机在无炸弹且未探测到敌空军时返航
        enemy_aircraft_known = any(isinstance(o, Aircraft) and o.team!=self.team for o in self.detected_enemies)
        # 找到最近的友军机场
        def nearest_base():
            bases = [b for b in buildings if b.alive and b.team==self.team and b.type in ('airbase','forward_airbase')]
            if not bases: return None
            return min(bases, key=lambda b: math.hypot(b.x-self.x, b.y-self.y))
        if self.bombs <= 0:
            if self.role == 'bomber':
                nb = nearest_base()
                if nb:
                    self.nav_target = nb
                    self.returning_to_base = True
            else:
                # 战斗机类在无炸弹且未探测到敌空军时返航
                if not enemy_aircraft_known:
                    nb = nearest_base()
                    if nb:
                        self.nav_target = nb
                        self.returning_to_base = True
        else:
            # 有炸弹时取消返航标志
            self.returning_to_base = False
        # 热诱
        if self.flares>0 and self.flare_timer<=0:
            for m in missiles:
                if m.alive and m.target is self and m.is_ir and math.hypot(m.x-self.x, m.y-self.y) < 150:
                    self.flares-=1; self.flare_timer=60; break
        if self.flare_timer>0: self.flare_timer-=1
        # 反导
        if not self.is_cas() and self.evasive_timer<=0:
            for m in missiles:
                if m.alive and m.target is self and m.team!=self.team:
                    self.evasive_timer,self.evasive_angle = 60, random.choice([-90,90]); break
        if self.evasive_timer>0:
            self.evasive_timer-=1
            self.angle += self.evasive_angle * (self.turn_rate*2/60)
            rad = math.radians(self.angle)
            self.x += self.speed*math.cos(rad); self.y += self.speed*math.sin(rad)
            return
        candidates = [e for e in self.detected_enemies if e.alive and e.team!=self.team]
        if not self.returning_to_base:
            self.nav_target = min(candidates, key=lambda e: math.hypot(e.x-self.x, e.y-self.y)) if candidates else None
        evade_gun = False
        if self.nav_target and isinstance(self.nav_target, (Building, GroundUnit)):
            if hasattr(self.nav_target,'angle') and self.nav_target.angle is not None and ('aa' in self.nav_target.type or 'AA' in self.nav_target.type):
                dx,dy = self.x-self.nav_target.x, self.y-self.nav_target.y
                angle_to_me = math.degrees(math.atan2(dy,dx))
                if abs((angle_to_me - self.nav_target.angle + 540)%360-180) < 30:
                    evade_gun = True
                    perp = angle_to_me + 90
                    self.nav_target = type('obj',(object,),{'x':self.nav_target.x+100*math.cos(math.radians(perp)), 'y':self.nav_target.y+100*math.sin(math.radians(perp)), 'alive':True})()
        if self.nav_target:
            ta = math.degrees(math.atan2(self.nav_target.y-self.y, self.nav_target.x-self.x))
            diff = (ta - self.angle + 540)%360 - 180
            if diff>self.turn_rate: self.angle += self.turn_rate
            elif diff<-self.turn_rate: self.angle -= self.turn_rate
            else: self.angle += diff
        rad = math.radians(self.angle)
        self.x += self.speed*math.cos(rad); self.y += self.speed*math.sin(rad)
        if self.reload_timer>0: self.reload_timer-=1
        if self.sec_reload>0: self.sec_reload-=1
        # 攻击
        if self.nav_target and self.nav_target.alive and self.nav_target in self.detected_enemies and not evade_gun and not self.returning_to_base:
            if isinstance(self.nav_target, Aircraft) or (isinstance(self.nav_target,(GroundUnit,Building)) and self.ground_dmg>0):
                dist = math.hypot(self.nav_target.x-self.x, self.nav_target.y-self.y)
                if dist < self.attack_range:
                    angle_to = math.degrees(math.atan2(self.nav_target.y-self.y, self.nav_target.x-self.x))
                    if abs((angle_to - self.angle + 540)%360-180) <= self.attack_angle and self.reload_timer==0:
                        # 常规武器：机炮/机炮二次武器
                        if self.weapon_type != 'missile':
                            bullets.append(Bullet(self.x, self.y, self.angle, self.speed+6, self.attack_dmg, self.team))
                            self.ammo -= 1; self.reload_timer = self.cooldown_time
                            if self.has_secondary and self.sec_reload==0:
                                bullets.append(Bullet(self.x, self.y, self.angle, self.speed+6, self.sec_dmg, self.team))
                                self.sec_reload = self.sec_cooldown
                        else:
                            # 导弹发射逻辑（只对空中目标）
                            if isinstance(self.nav_target, Aircraft) and self.ammo > 0:
                                mtype = getattr(self, 'missile_type', 'G-IR')
                                # 使用目标方向作为初始导弹角度
                                missiles.append(Missile(self.x, self.y, angle_to, self.nav_target, self.team, mtype))
                                self.ammo -= 1
                                self.reload_timer = self.cooldown_time
        # 投弹（抛射 / 制导）
        if self.bombs>0 and self.nav_target and self.nav_target.alive and not evade_gun and not self.returning_to_base:
            if isinstance(self.nav_target,(GroundUnit,Building)) and self.nav_target in self.detected_enemies:
                # 计算与目标的距离
                dist_to_target = math.hypot(self.nav_target.x - self.x, self.nav_target.y - self.y)
                # 严禁在机场附近投弹（防止在机场上空投放大量炸弹）
                BAN_RADIUS = 300
                nearest_airbase_dist = float('inf')
                for bb in buildings:
                    if not bb.alive: continue
                    if bb.type in ('airbase','forward_airbase'):
                        dbb = math.hypot(bb.x - self.x, bb.y - self.y)
                        if dbb < nearest_airbase_dist: nearest_airbase_dist = dbb
                if nearest_airbase_dist < BAN_RADIUS:
                    # 距离机场太近，禁止投弹
                    pass
                else:
                    # 如果是制导攻击机，投放制导炸弹（初始速度较高并制导）
                    if getattr(self, 'type', '') == 'advanced_attacker':
                        if dist_to_target < 2000:
                            bomb_speed = AIRCRAFT_CONFIG['advanced_attacker']['bomb_speed']
                            aim_angle = math.degrees(math.atan2(self.nav_target.y - self.y, self.nav_target.x - self.x))
                            gb = GuidedBomb(self.x, self.y, aim_angle, bomb_speed, self.bomb_dmg, self.bomb_radius, self.team, self.nav_target, turn=AIRCRAFT_CONFIG['advanced_attacker']['bomb_turn'], max_range=AIRCRAFT_CONFIG['advanced_attacker']['bomb_range'])
                            # 估算飞行帧数（考虑空气阻力）
                            est = estimate_flight_frames(dist_to_target, bomb_speed, k=0.005)
                            gb.set_timer(est + 3)
                            bombs_list.append(gb)
                            self.bombs -= 1
                    else:
                        # 传统抛射炸弹：在距离合适时投掷
                        # 若飞机与目标方向基本一致（如俯冲/冲刺攻击），允许更近距离投弹
                        aim_angle = math.degrees(math.atan2(self.nav_target.y - self.y, self.nav_target.x - self.x))
                        angle_diff = (aim_angle - self.angle + 540) % 360 - 180
                        aligned = abs(angle_diff) < 15
                        # 若机头朝向正确，则允许在距离大于标准射程 0.3 倍的位置投弹（近距俯冲可提前释放）
                        standard_range = getattr(self, 'attack_range', 400)
                        threshold = 0.3 * standard_range
                        max_vert = 300 if aligned else 150
                        if aligned:
                            # 机头对准且距离大于阈值时允许投弹
                            if dist_to_target > threshold and abs(self.y - self.nav_target.y) < max_vert:
                                allow_drop = True
                            else:
                                allow_drop = False
                        else:
                            # 未对准时沿用原来的近距投弹规则
                            allow_drop = (dist_to_target < 400 and abs(self.y - self.nav_target.y) < max_vert)
                        if allow_drop:
                            # 抛投炸弹前将飞机朝向指向目标方向（可改为逐步转向以更真实）
                            bomb_speed = max(0.1, self.speed)
                            # 额外校验：确保在当前速度与阻力条件下，炸弹在到达目标前不会降到过低速度
                            if not can_reach_distance_before_speed_decay(dist_to_target, bomb_speed, k=0.005, min_speed_frac=0.15):
                                # 如果无法在速度未显著衰减前到达目标，跳过本次投弹
                                pass
                            else:
                                self.angle = aim_angle
                                b = Bomb(self.x, self.y, self.angle, bomb_speed, self.bomb_dmg, self.bomb_radius, self.team)
                                # 估算飞行帧数（考虑空气阻力）
                                est = estimate_flight_frames(dist_to_target, bomb_speed, k=0.005)
                                b.set_timer(est + 2)
                                bombs_list.append(b)
                                self.bombs -= 1

    def draw(self):
        if not self.alive: return
        s = self.size
        if self.shape=='narrow': local=[(s*1.2,0),(-s*0.6,-s*0.6),(-s*0.3,0),(-s*0.6,s*0.6)]
        elif self.shape=='wide_triangle': local=[(s*1.0,0),(-s*0.8,-s*1.2),(-s*0.8,s*1.2)]
        elif self.shape=='small_triangle': local=[(s*0.9,0),(-s*0.5,-s*0.5),(-s*0.5,s*0.5)]
        else: local=[(s*0.7,0),(-s*0.7,-s*0.7),(-s*0.7,s*0.7)]
        rad=math.radians(self.angle); cos_a,sin_a=math.cos(rad),math.sin(rad)
        world=[(self.x+lx*cos_a-ly*sin_a, self.y+lx*sin_a+ly*cos_a) for lx,ly in local]
        sw=[world_to_screen(wx,wy) for wx,wy in world]
        pygame.draw.polygon(screen, self.color, sw)
        sx,sy=world_to_screen(self.x,self.y)
        bar_w=max(6,int(self.size*zoom))
        pygame.draw.rect(screen, BLACK, (sx-bar_w//2, sy-bar_w-8, bar_w,3))
        pygame.draw.rect(screen, GREEN, (sx-bar_w//2, sy-bar_w-8, int(bar_w*self.hp/self.max_hp),3))
        # 弹药显示
        ammo_str = f"A:{self.ammo} B:{self.bombs}"
        txt = FONT.render(ammo_str, True, YELLOW)
        screen.blit(txt, (sx - 15, sy - 25))
        if self.flare_timer>0:
            pygame.draw.circle(screen, ORANGE, (sx, sy+int(self.size*zoom)), max(2,int(4*zoom)))

# ==================== 初始化 ====================
def init_game():
    buildings.append(Building(300, WORLD_H//2, 'airbase', 'red'))
    for i in [-1,1]:
        bx,by=800, WORLD_H//2 + i*400
        buildings.append(Building(bx,by,'forward_airbase','red'))
        buildings.append(Building(bx-60,by-60,'gun_aa','red')); buildings.append(Building(bx+60,by-60,'gun_aa','red'))
        buildings.append(Building(bx,by+60,'missile_aa','red'))
    buildings.append(Building(1200, WORLD_H//2,'forward_airbase','red'))
    buildings.append(Building(1200, WORLD_H//2-60,'gun_aa','red'))
    buildings.append(Building(200,300,'long_range_aa','red')); buildings.append(Building(200, WORLD_H-300,'long_range_aa','red'))
    for j in range(4): buildings.append(Building(1400, 400+j*200,'gun_aa','red'))
    buildings.append(Building(800, WORLD_H//2,'radar','red'))

    buildings.append(Building(WORLD_W-300, WORLD_H//2, 'airbase', 'blue'))
    for i in [-1,1]:
        bx,by=WORLD_W-800, WORLD_H//2 + i*400
        buildings.append(Building(bx,by,'forward_airbase','blue'))
        buildings.append(Building(bx-60,by-60,'gun_aa','blue')); buildings.append(Building(bx+60,by-60,'gun_aa','blue'))
        buildings.append(Building(bx,by+60,'missile_aa','blue'))
    buildings.append(Building(WORLD_W-1200, WORLD_H//2,'forward_airbase','blue'))
    buildings.append(Building(WORLD_W-1200, WORLD_H//2-60,'gun_aa','blue'))
    buildings.append(Building(WORLD_W-200,300,'long_range_aa','blue')); buildings.append(Building(WORLD_W-200, WORLD_H-300,'long_range_aa','blue'))
    for j in range(4): buildings.append(Building(WORLD_W-1400, 400+j*200,'gun_aa','blue'))
    buildings.append(Building(WORLD_W-800, WORLD_H//2,'radar','blue'))

    for _ in range(3):
        ground_units.append(GroundUnit(600+random.randint(-50,50), WORLD_H//2+random.randint(-100,100),'tank','red'))
        ground_units.append(GroundUnit(WORLD_W-600+random.randint(-50,50), WORLD_H//2+random.randint(-100,100),'tank','blue'))

def build_deploy_list():
    global deploy_types
    deploy_types = [
        'standard','speedy','heavy','attacker','advanced_attacker','bomber','dogfighter','jet','missile_plane','attacker_rear',
        'airbase','forward_airbase','resource_base','missile_aa','long_range_aa','gun_aa',
        'rally','gun_aa_rally','missile_aa_rally','radar',
        'tank','gun_aa_vehicle','missile_aa_vehicle','infantry'
    ]

def deploy_unit(wx, wy, team):
    t = deploy_types[selected_deploy]
    if t in AIRCRAFT_CONFIG: aircraft_list.append(Aircraft(wx, wy, random.uniform(0,360), t, team))
    elif t in ('tank','gun_aa_vehicle','missile_aa_vehicle','infantry'): ground_units.append(GroundUnit(wx, wy, t, team))
    else: buildings.append(Building(wx, wy, t, team))

# ==================== 主循环 ====================
def main():
    global selected_deploy, red_res, blue_res
    clock = pygame.time.Clock()
    build_deploy_list()
    init_game()
    resource_timer = 0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        resource_timer += dt
        if resource_timer >= 1.0:
            red_res += RES_RATE; blue_res += RES_RATE
            resource_timer -= 1.0

        for event in pygame.event.get():
            if event.type == QUIT: running = False
            handle_camera(event)
            if event.type == KEYDOWN and event.key == K_TAB:
                selected_deploy = (selected_deploy + 1) % len(deploy_types)
            if event.type == MOUSEBUTTONDOWN and not dragging and event.button in (1,3):
                mx, my = pygame.mouse.get_pos()
                wx, wy = screen_to_world(mx, my)
                deploy_unit(wx, wy, 'red' if event.button == 1 else 'blue')

        for a in aircraft_list: a.update()
        for g in ground_units: g.update()
        for b in buildings: b.update()
        for bullet in bullets: bullet.update()
        for bomb in bombs_list: bomb.update()
        for m in missiles: m.update()

        aircraft_list[:] = [a for a in aircraft_list if a.alive]
        ground_units[:] = [g for g in ground_units if g.alive]
        buildings[:] = [b for b in buildings if b.alive]
        bullets[:] = [b for b in bullets if b.alive]
        bombs_list[:] = [b for b in bombs_list if b.alive]
        missiles[:] = [m for m in missiles if m.alive]

        red_base = any(b.type=='airbase' and b.team=='red' and b.alive for b in buildings)
        blue_base = any(b.type=='airbase' and b.team=='blue' and b.alive for b in buildings)
        if not red_base or not blue_base:
            winner = "蓝方" if not red_base else "红方"
            screen.fill(WHITE)
            screen.blit(BIG_FONT.render(f"{winner}胜利！", True, RED), (SCREEN_W//2-60, SCREEN_H//2-20))
            pygame.display.flip(); pygame.time.wait(3000)
            running = False

        screen.fill(WHITE)
        for b in buildings: b.draw()
        for g in ground_units: g.draw()
        for a in aircraft_list: a.draw()
        for bullet in bullets: bullet.draw()
        for bomb in bombs_list: bomb.draw()
        for m in missiles: m.draw()

        cn = TYPE_NAMES.get(deploy_types[selected_deploy], deploy_types[selected_deploy])
        screen.blit(FONT.render(f"部署: {cn} | Tab切换 | 左红右蓝 | 滚轮缩放", True, BLACK), (10,10))
        screen.blit(FONT.render(f"红资源:{int(red_res)} 蓝资源:{int(blue_res)}", True, RED if red_res>blue_res else BLUE), (10,35))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
