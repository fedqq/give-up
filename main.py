from __future__ import division
from collections.abc import Iterable
import tkinter as tk
from tkinter import ttk, CENTER, TOP, BOTTOM, LEFT, RIGHT, BOTH, X, Y
import sv_ttk
from copy import copy, deepcopy
from ctypes import windll

windll.shcore.SetProcessDpiAwareness(1)

PLAYER_SIZE = 30
DEBUG = True

BLOCK, PAD, MOVEMENT, SPIKES, TOGGLE, GOAL, TRIGGER = 'block', 'pad', 'movement', 'spikes', 'toggle', 'goal', 'trigger'

default_colors = {BLOCK: 'gray', SPIKES: '#e86056', PAD: 'yellow', GOAL: 'green', TRIGGER: ('red', 'green')}

class LevelElement:
    def __init__(self, type, *args, **kwargs) -> None:
        if type not in MOVEMENT + TOGGLE:
            if 'color' in kwargs:
                self.color = kwargs['color']
            else:
                self.color = default_colors[type]
        if type == MOVEMENT or type == TOGGLE:
            self.delay = kwargs['delay']
        
        if type == MOVEMENT:
            self.reps = kwargs['reps']
            self.moves = kwargs['moves']
            
        if type == BLOCK or type == PAD or type == SPIKES or type == GOAL:
            self.dimensions = list(args)
            
        if type == PAD:
            self.jheight = kwargs['jheight']
            
        if type == TRIGGER:
            self.dimensions = args
            self.disable_tag = kwargs['disabletag']
            if 'color' in kwargs:
                self.color = kwargs['color']
            else:
                self.color = default_colors[type]
        
        self.tag = kwargs['tag']

class Level:
    def __init__(self) -> None:
        self.blocks =   [[0, 200, 150, 50, 'none']]
        self.blocks =   [LevelElement(BLOCK, 0, 200, 150, 50, tag = 'none')]
        self.spikes:    list[LevelElement] = []
        self.pads:      list[LevelElement] = []
        self.toggles:   list[LevelElement] = []
        self.movements: list[LevelElement] = []
        self.triggers:  list[LevelElement] = []
        self.goal =     LevelElement(GOAL, 970, 900, 20, 20, tag = 'goal')
        
    def add_block(self, x, y, width, height, tag = 'none', color = default_colors[BLOCK]):
        self.blocks.append(LevelElement(BLOCK, x, y, width, height, tag = tag, color = color))
        return self
    
    def add_movement(self, firstmove, reps = 10, delay = 10, tag = ''): 
        move = []
        backmove = [-move for move in firstmove]
        for _ in range(reps):
            move.append(firstmove)
        for _ in range(reps):
            move.append(backmove)
            
        self.movements.append(LevelElement(MOVEMENT, tag = tag, delay = delay, reps = reps, moves = move))
        return self
    
    def add_spikes(self, x, y, width, height, tag = 'none', color = default_colors[SPIKES]):
        self.spikes.append(LevelElement(SPIKES, x, y, width, height, tag = tag, color = color))
        return self
    
    def add_pad(self, x, y, width, height, jheight = -25, tag = 'none', color = default_colors[PAD]):
        self.pads.append(LevelElement(PAD, x, y, width, height, tag = tag, jheight = jheight, color = color))
        return self
    
    def set_goal(self, x, y, width, height):
        self.goal = [x, y, width, height, 'goal']
        return self
    
    def add_time_toggle(self, tag, time):
        self.toggles.append(LevelElement(TOGGLE, delay = time, tag = tag))
        return self
    
    def add_trigger(self, x, y, width, height, disabletag, color = default_colors[TRIGGER], tag = 'none'):
        self.triggers.append(LevelElement(TRIGGER, x, y, width, height, disabletag = disabletag, color = color, tag = tag))

class Game:
    def __init__(self) -> None:
        def start():
            start_btn.destroy()
            self.start_game()
            
        self.root = tk.Tk()
        self.root.title('Give Up')
        self.root.resizable(False, False)
        
        self.playing = False
        self.current_level = 0
        
        self.size = (self.root.winfo_screenheight() / 10) * 9
         
        self.canvas = tk.Canvas(self.root, width = self.size, height = self.size)
        self.canvas.pack()
        
        self.reset_levels()
        
        sv_ttk.use_dark_theme()
        
        start_btn = ttk.Button(self.canvas, text = 'Start Game', command = start, style = 'Big.Accent.TButton')
        start_btn.place(relx=0.5, rely=0.5, anchor = CENTER)
        
        self.root.bind('<space>', func(self.press_key, TOP))
        self.root.bind('<Up>', func(self.press_key, TOP))
        self.root.bind('<KeyRelease-space>', func(self.release_key, TOP))
        self.root.bind('<KeyRelease-Up>', func(self.release_key, TOP))
        self.root.bind('<Right>', func(self.press_key, RIGHT))
        self.root.bind('<Left>', func(self.press_key, LEFT))
        self.root.bind('<KeyRelease-Right>', func(self.release_key, RIGHT))
        self.root.bind('<KeyRelease-Left>', func(self.release_key, LEFT))
        
        self.big_font = ('Segoe UI', self.proportion(15))
        self.small_font = ('Segoe UI', self.proportion(8))
        
        style = ttk.Style(self.root)
        style.theme_use('sun-valley-dark')
        style.configure('Big.Accent.TButton', font = self.big_font)
        style.configure('Small.Accent.TButton', font = self.small_font)
        
        self.root.mainloop()
        
    def press_key(self, key):
        if not self.playing:
            return
        self.pressed[key] = True
    
    def release_key(self, key):
        if not self.playing:
            return
        self.pressed[key] = False
        
    def check_move(self):
        if self.pressed[RIGHT]:
            self.move(True)
        if self.pressed[LEFT]:
            self.move()
        if self.pressed[TOP]:
            self.space()
        
        self.root.after(4, self.check_move)
        
    def space(self):
        if self.available_jumps != 0:
            self.pressed[TOP] = False
            self.y_speed = -16
            self.available_jumps -= 1
            
    def move(self, right = False):
        if -8 <= self.x_speed <= 8:
            self.x_speed += 1 if right else -1
            
    def reset_levels(self):
        self.levels = [Level() for _ in range(0, 8)]
        self.levels[0].add_block(0, 900, 500, 100, 'test')\
                      .add_block(600, 800, 200, 50)\
                      .add_movement([4, -4], tag = 'test', reps = 20, delay = 20)\
                      .add_trigger(100, 600, 500, 100, 'test')
                      
        self.levels[1].add_block(30, 900, 500, 100)\
                      .add_block(500, 800, 200, 50)\
                      .add_spikes(300, 600, 500, 90)
            
    def die(self):
        def restart():
            btn.destroy()
            lbl.destroy()
            self.start_game()
        self.playing = False
        lbl = ttk.Label(self.canvas, text = 'You Died', font = self.big_font)
        btn = ttk.Button(self.canvas, text = 'Restart', style = 'Small.Accent.TButton', command = restart)
        lbl.place(relx = 0.5, rely = 0.3, anchor = CENTER)
        btn.place(relx = 0.5, rely = 0.5, anchor = CENTER)
        
    def start_game(self):
        self.player = [100, 100]
        self.y_speed = 0
        self.x_speed = 0
        self.grounded = False
        self.playing = True
        self.available_jumps = 0
        self.disabled_tags = ['test']
        
        self.pressed = {RIGHT: False, LEFT: False, TOP: False}
        
        self.reset_levels()
        self.load_lvl(self.levels[self.current_level])
        self.physics_loop()
        self.check_move()
        
        if DEBUG:
            def p(e):
                print((e.x / self.size)*1000, (e.y / self.size)*1000)
            self.root.bind('<Button-1>', p)
        
    def test_player(self, p, element: LevelElement, check_floor = True):
        if element.tag in self.disabled_tags:
            return False
        half = PLAYER_SIZE / 2
        players = [p, [p[0] + PLAYER_SIZE, p[1]], [p[0] + PLAYER_SIZE, p[1] + PLAYER_SIZE], [p[0], p[1] + PLAYER_SIZE] ,[p[0] + half, p[1] + half]]
        players_in = [in_block(player, element.dimensions) for player in players]
        if check_floor:
            for player in players:
                if not 0 <= player[0] <= 1000 or not 0 <= player[1] <= 1000:
                    return True
        return True in players_in
        
    def physics_loop(self):
        
        if not self.playing:
            return
        self.canvas.delete('player')
        
        if self.y_speed < 12 and not self.grounded:
            self.y_speed += 1
            
        self.grounded = False
        
        test_player = self.test_player
        
        for pad in self.level.pads:
            if test_player(self.player, pad, False):
                self.y_speed = self.proportion(pad.jheight)
                self.available_jumps = 2
        
        if self.y_speed != 0:
            move = self.y_speed / abs(self.y_speed)
            move *= -1
            move = int(move)
            
            for _ in range(abs(self.y_speed)):
                self.player[1] += move*-1
                for spike in self.level.spikes:
                    if test_player(self.player, spike, False):
                        self.die()
                        return
                failed = False
                for block in self.level.blocks:
                    if test_player(self.player, block):
                        failed = True
                        if self.y_speed >= 0:
                            self.grounded = True
                            self.available_jumps = 2
                        self.y_speed = 1
                if failed:
                    self.player[1] += move
                    break
        
        if self.x_speed != 0:
            self.player[0] += self.x_speed
            move = self.x_speed / abs(self.x_speed)
            move *= -1
            for block in self.level.blocks:
                happened = False
                count = 0
                while test_player(self.player, block):
                    if count > 8:
                        self.die()
                        break
                    count += 1
                    self.player[0] += move
                    self.x_speed = 0
                    happened = True
                if happened:
                    break
                
        for trigger in self.level.triggers:
            if self.test_player(self.player, trigger, False):
                trigger.timer += 1
                if trigger.timer == 1:
                    trigger.func()
            else:
                trigger.timer = 0
                
        self.x_speed *= 0.9
        
        if test_player(self.player, self.level.goal, False):
            self.playing = False
            def go_next():
                self.current_level += 1
                self.start_game()
                btn.destroy()
            
            btn = ttk.Button(self.canvas, text = 'Next Level', style = 'Small.Accent.TButton', command = go_next)
            btn.place(relx = 0.5, rely = 0.5, anchor = CENTER)
            return
        
        x, y = copy(self.player)
        x = self.proportion(x, False)
        y = self.proportion(y, False)
        size = self.proportion(PLAYER_SIZE)
        offset = abs(int((self.y_speed / 1.8) / 1.2))
        self.canvas.create_rectangle(x + offset, y - offset, x + size - offset, y + size + offset, fill = 'blue', tag = 'player')
        
        self.root.after(13, self.physics_loop)
        
    def load_lvl(self, lvl: Level):
        
        self.canvas.delete('level')
        
        self.disabled_tags = []
        
        def positions(elem):
            return (elem[0], elem[1], elem[0] + elem[2], elem[1] + elem[3])
        
        self.level = copy(lvl)
        draw_lvl = deepcopy(lvl)
        
        draw_lvl.goal.dimensions = [self.proportion(n) for n in draw_lvl.goal.dimensions]
        
        for block in draw_lvl.blocks:
            block.dimensions = [self.proportion(coord) for coord in block.dimensions]
            tag = ['level', block.tag]
            self.canvas.create_rectangle(positions(block.dimensions), fill = block.color, tag = tag)
            
        for spike in draw_lvl.spikes:
            spike.dimensions = [self.proportion(coord) for coord in spike.dimensions]
            tag = ['level', spike.tag]
            self.canvas.create_rectangle(positions(spike.dimensions), fill = spike.color, tag = tag)
            size = int(self.size / 400) * 2
            dash = int(size * 10)
            width = int(size / 4)
            sizes = spike.dimensions
            self.canvas.create_line(sizes[0] + width, sizes[1], sizes[0] + sizes[2], sizes[1], fill = spike.color, tag = tag, width = size, dash = dash, capstyle = tk.BUTT)
        
        for pad in draw_lvl.pads:
            pad.dimensions = [self.proportion(coord) for coord in pad.dimensions]
            tag = ['level', pad[4]]
            self.canvas.create_rectangle(positions(pad.dimensions), fill = pad.color, tag = tag)
            
        for toggle in draw_lvl.toggles:
            def callback(delay, tag):
                if not self.playing:
                    return
                if tag in self.disabled_tags:
                    self.disabled_tags.remove(tag)
                    self.canvas.itemconfigure(tag, state = 'normal')
                else:
                    self.disabled_tags.append(tag)
                    self.canvas.itemconfigure(tag, state = 'hidden')
                self.root.after(delay, callback, delay, tag)
            self.root.after(toggle.delay, callback, toggle.delay, toggle.tag)
            
        for movement in draw_lvl.movements:
            moves = movement.moves
            tag = movement.tag
            delay = movement.delay
            a = 'none'
            
            touch = False
            
            if tag == 'goal':
                a = self.level.goal
                b = self.level.goal
            else:
                for test in self.level.blocks:
                    if test.tag == tag:
                        touch = True
                        a = (self.level.blocks.index(test), 'blocks')
                        b = test
                        
                for test in self.level.spikes:
                    if test.tag == tag:
                        a = (self.level.spikes.index(test), 'spikes')
                        b = test
                        
                for test in self.level.pads:
                    if test.tag == tag:
                        a = (self.level.pads.index(test), 'pads')
                        b = test
                        
                for test in self.level.triggers:
                    if test.tag == tag:
                        a = (self.level.triggers.index(test), 'triggers')
                        b = test
                
            if a == 'none':
                return
            
            def move_callback(count):
                if not self.playing:
                    return
                x, y = moves[count % len(moves)]
                
                if x != 0:
                    was_in = self.test_player(self.player, b, False)
                    if type(a) is tuple:
                        match a[1]:
                            case 'pads':
                                self.level.pads[a[0]].dimensions[0] += x
                            case 'blocks':
                                self.level.blocks[a[0]].dimensions[0] += x
                            case 'spikes':
                                self.level.spikes[a[0]].dimensions[0] += x
                            case 'triggers':
                                self.level.triggers[a[0]].dimensions[0] += x
                    else:
                        self.level.goal.dimensions[0] += x
                    if touch:
                        is_in = self.test_player(self.player, b, False)
                        if not was_in and is_in:
                            self.player[0] += x
                        if is_in and was_in:
                            self.die()
                            return
                
                if y != 0:
                    was_in = self.test_player(self.player, b, False)
                    if type(a) is tuple:
                        match a[1]:
                            case 'pads':
                                self.level.pads[a[0]].dimensions[1] += y
                            case 'blocks':
                                self.level.blocks[a[0]].dimensions[1] += y
                            case 'spikes':
                                self.level.spikes[a[0]].dimensions[1] += y
                            case 'triggers':
                                self.level.triggers[a[0]].dimensions[1] += y
                    else:
                        self.level.goal.dimensions[1] += y
                    if touch:
                        is_in = self.test_player(self.player, b, False)
                        if is_in:
                            if was_in:
                                self.die()
                                return
                            else:
                                self.player[1] += y
                    
                self.canvas.move(tag, self.proportion(x, False), self.proportion(y, False))
                self.root.after(delay, move_callback, count + 1)
                      
            move_callback(0)
        
        for index, trigger in enumerate(draw_lvl.triggers):
            trigger.dimensions = [self.proportion(coord) for coord in trigger.dimensions]
            
            x, y, width, height = trigger.dimensions
            
            sprite = self.canvas.create_rectangle(x, y, x + width, y + height, fill = trigger.color[0], tag = trigger.tag)
            trig = self.level.triggers[index]
            trig.enabled = False
            trig.counter = 0
            self.canvas.itemconfig(trigger.disable_tag, state = 'hidden')
            def callback():
                if trig.enabled:
                    trig.enabled = False
                    self.canvas.itemconfig(sprite, fill = trigger.color[1])
                    self.canvas.itemconfig(trig.disable_tag, state = 'hidden')
                    self.disabled_tags.append(trig.disable_tag)
                else:
                    trig.enabled = True
                    self.canvas.itemconfig(sprite, fill = trigger.color[0])
                    self.canvas.itemconfig(trig.disable_tag, state = 'normal')
                    if trig.disable_tag in self.disabled_tags:
                        self.disabled_tags.remove(trig.disable_tag)
                    
            trig.func = callback
        
        x, y, width, height = draw_lvl.goal.dimensions
        self.canvas.create_rectangle(x, y, x + width, y + height, fill = draw_lvl.goal.color, tag = ('level', 'goal'))
        
    def proportion(self, n, i = True):
        if type(n) is str:
            return n
        n = n/1000 * self.size
        if i:
            return int(n)
        return n
        
def func(f, *args):
    return lambda *a: f(*args)

def in_block(player, block, check = BOTH):
    xin, yin = False, False
    if block[1] <= player[1] <= (block[1] + block[3]):
        yin = True
    if block[0] <= player[0] <= (block[0] + block[2]):
        xin = True
    if check == BOTH:
        return xin and yin
    if check == Y:
        return yin
    if check == X:
        return xin
    
Game()