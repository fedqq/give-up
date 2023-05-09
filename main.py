from collections.abc import Iterable
import tkinter as tk
from tkinter import ttk, CENTER, TOP, BOTTOM, LEFT, RIGHT, BOTH, X, Y
import sv_ttk
from enum import IntEnum
from copy import copy
from ctypes import windll

windll.shcore.SetProcessDpiAwareness(1)

PLAYER_SIZE = 30

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
        self.levels[0].add_block(0, 800, 500, 200)\
                      .add_block(100, 700, 500, 50)
        
        self.canvas = tk.Canvas(self.root, width = self.size, height = self.size)
        self.canvas.pack()
        
        sv_ttk.use_dark_theme()
        
        start_btn = ttk.Button(self.canvas, text = 'Start Game', command = start, style = 'Accent.TButton')
        start_btn.place(relx=0.5, rely=0.5, anchor = CENTER)
        
        self.root.bind('<space>', func(self.space))
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
        self.root.after(4, self.check_move)
        
    def space(self):
        if self.grounded:
            self.y_speed = -20
            
    def move(self, right = False):
        if -8 <= self.x_speed <= 8:
            self.x_speed += 1 if right else -1
        
    def start_game(self):
        self.player = [100, 100]
        self.y_speed = 0
        self.x_speed = 0
        
        self.pressed = {RIGHT: False, LEFT: False}
        
        self.draw_lvl(self.levels[0])
        self.physics_loop() 
        self.check_move()
        
    def physics_loop(self):
        self.canvas.delete('player')
        self.grounded = False
        
        if self.y_speed < 7:
            self.y_speed += 1
            
        def test_player(p, block):
            players = [p, [p[0] + PLAYER_SIZE, p[1]], [p[0] + PLAYER_SIZE, p[1] + PLAYER_SIZE], [p[0], p[1] + PLAYER_SIZE]]
            players_in = [in_block(player, block) for player in players]
            for player in players:
                if not 0 <= player[0] <= 1000 or not 0 <= player[1] <= 1000:
                    return True
            return True in players_in
        
        if self.y_speed != 0:
            self.player[1] += self.y_speed
            move = self.y_speed / abs(self.y_speed)
            move *= -1
            for block in self.level.blocks:
                happened = False
                while test_player(self.player, block):
                    self.player[1] += move
                    self.grounded = True
                    self.y_speed = 0
                    happened = True
                if happened:
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
        
    def draw_lvl(self, level):
        self.level = copy(level)
        level.blocks = [[(coord / 1000) * self.size for coord in block] for block in level.blocks]
        self.canvas.delete('level')
        for block in level.blocks:
            self.canvas.create_rectangle(block[0], block[1], block[0] + block[2], block[1] + block[3], fill = 'gray', tag = 'level')
    
class Level:
    def __init__(self) -> None:
        self.blocks = []
        
    def add_block(self, x, y, width, height):
        block = [x, y, width, height]
        self.blocks.append(block)
        return self
        
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