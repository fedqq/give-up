from collections.abc import Iterable
import tkinter as tk
from tkinter import ttk, CENTER, TOP, BOTTOM, LEFT, RIGHT, BOTH, X, Y
import sv_ttk
from enum import IntEnum
from copy import copy
from ctypes import windll

windll.shcore.SetProcessDpiAwareness(1)

PLAYER_SIZE = 30

class Level:
    def __init__(self) -> None:
        self.blocks = []
        self.spikes = []
        
    def add_block(self, x, y, width, height):
        self.blocks.append([x, y, width, height])
        return self
    
    def add_spikes(self, x, y, width, height):
        self.spikes.append([x, y, width, height])
        return self

class Game:
    def __init__(self) -> None:
        def start():
            start_btn.destroy()
            self.start_game()
            
        self.root = tk.Tk()
        self.root.title('Give Up')
        self.root.resizable(False, False)
        
        self.size = (self.root.winfo_screenheight() / 10) * 9
        
        self.levels = [Level() for _ in range(0, 8)]
        self.levels[0].add_block(0, 900, 500, 100)\
                      .add_block(600, 900, 200, 50)\
                      .add_spikes(100, 600, 500, 90)
        
        self.canvas = tk.Canvas(self.root, width = self.size, height = self.size)
        self.canvas.pack()
        
        sv_ttk.use_dark_theme()
        
        start_btn = ttk.Button(self.canvas, text = 'Start Game', command = start, style = 'Accent.TButton')
        start_btn.place(relx=0.5, rely=0.5, anchor = CENTER)
        
        self.root.bind('<space>', func(self.press_key, TOP))
        self.root.bind('<Up>', func(self.press_key, TOP))
        self.root.bind('<KeyRelease-space>', func(self.release_key, TOP))
        self.root.bind('<KeyRelease-Up>', func(self.release_key, TOP))
        self.root.bind('<Right>', func(self.press_key, RIGHT))
        self.root.bind('<Left>', func(self.press_key, LEFT))
        self.root.bind('<KeyRelease-Right>', func(self.release_key, RIGHT))
        self.root.bind('<KeyRelease-Left>', func(self.release_key, LEFT))
        
        self.root.mainloop()
        
    def press_key(self, key):
        self.pressed[key] = True
    
    def release_key(self, key):
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
        if self.grounded:
            self.y_speed = int((-20 / 1000) * self.size)
            
    def move(self, right = False):
        if -8 <= self.x_speed <= 8:
            self.x_speed += 1 if right else -1
        
    def start_game(self):
        self.player = [100, 100]
        self.y_speed = 0
        self.x_speed = 0
        
        self.pressed = {RIGHT: False, LEFT: False, TOP: False}
        
        self.draw_lvl(self.levels[0])
        self.physics_loop() 
        self.check_move()
        
    def physics_loop(self):
        self.canvas.delete('player')
        self.grounded = False
        
        if self.y_speed < 7:
            self.y_speed += 1
            
        def test_player(p, block, check_floor = True):
            players = [p, [p[0] + PLAYER_SIZE, p[1]], [p[0] + PLAYER_SIZE, p[1] + PLAYER_SIZE], [p[0], p[1] + PLAYER_SIZE]]
            players_in = [in_block(player, block) for player in players]
            if check_floor:
                for player in players:
                    if not 0 <= player[0] <= 1000 or not 0 <= player[1] <= 1000:
                        return True
            return True in players_in
        
        if self.y_speed != 0:
            move = self.y_speed / abs(self.y_speed)
            move *= -1
            for _ in range(abs(self.y_speed)):
                self.player[1] += move*-1
                for spike in self.level.spikes:
                    if test_player(self.player, spike, False):
                        self.root.destroy()
                failed = False
                for block in self.level.blocks:
                    if test_player(self.player, block):
                        failed = True
                        if self.y_speed >= 0:
                            self.grounded = True
                        self.y_speed = 0
                if failed:
                    self.player[1] += move
                    break
        
        if self.x_speed != 0:
            self.player[0] += self.x_speed
            move = self.x_speed / abs(self.x_speed)
            move *= -1
            for block in self.level.blocks:
                happened = False
                while test_player(self.player, block):
                    self.player[0] += move
                    self.x_speed = 0
                    happened = True
                if happened:
                    break
                
        self.x_speed *= 0.9
        
        x, y = self.player
        x = (x/1000) * self.size
        y = (y/1000) * self.size
        size = (PLAYER_SIZE / 1000) * self.size
        self.canvas.create_rectangle(x, y, x + size, y + size, fill = 'blue', tag = 'player')
        
        self.root.after(13, self.physics_loop)
        
    def draw_lvl(self, level: Level):
        self.level = copy(level)
        level.blocks = [[int((coord / 1000) * self.size) for coord in block] for block in level.blocks]
        level.spikes = [[int((coord / 1000) * self.size) for coord in spike] for spike in level.spikes]
        self.canvas.delete('level')
        for block in level.blocks:
            self.canvas.create_rectangle(block[0], block[1], block[0] + block[2], block[1] + block[3], fill = 'gray', tag = 'level')
        for spike in level.spikes:
            self.canvas.create_rectangle(spike[0], spike[1], spike[0] + spike[2], spike[1] + spike[3], fill = '#e86056', tag = 'level')
            size = int(self.size / 400) * 2
            dash = int(size * 10)
            width = int(size / 4)
            self.canvas.create_line(spike[0] + width, spike[1], spike[0] + spike[2], spike[1], fill = '#e86056', tag = 'level', width = size, dash = dash, capstyle = tk.BUTT)
        
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