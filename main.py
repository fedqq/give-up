from __future__ import division
import shelve
import tkinter as tk
from tkinter import ttk, CENTER, TOP, BOTTOM, LEFT, RIGHT, BOTH, X, Y
import sv_ttk
from copy import copy, deepcopy
from ctypes import windll
from time import time
from math import floor
from colour import Color
from PIL import ImageTk, ImageFilter, Image
import pyautogui

'''windll.shcore.SetProcessDpiAwareness(False)'''

PLAYER_SIZE = 30
DEBUG = True
TRANSPARENT = '#ab23ff'

BLOCK, PAD, MOVEMENT, SPIKES, TOGGLE, GOAL, TRIGGER, TRIGGERFLIP, FLIPPER, COIN = 'block', 'pad', 'movement', 'spikes', 'toggle', 'goal', 'trigger', 'triggerflip', 'flipper', 'coin'

VISIBLE = BLOCK+PAD+SPIKES+GOAL+TRIGGER+FLIPPER+COIN
INVISIBLE = MOVEMENT+TOGGLE
TOUCHTOGGLE = BLOCK+PAD+FLIPPER+TRIGGER

default_colors = {BLOCK: 'gray', SPIKES: '#e86056', PAD: 'yellow', GOAL: None, TRIGGER: ('green', 'red'), TRIGGERFLIP: ('red', 'green'), FLIPPER: ('#44aff2'), COIN: 'yellow'}

class LevelElement:
    def __init__(self, type, *args, **kwargs) -> None:
        self.tag = kwargs['tag']
        self.last_press = 0
        kwargs.setdefault('color', default_colors.get(type))
        
        if type in INVISIBLE:
            self.delay = kwargs['delay']
            
        if type in VISIBLE:
            self.dimensions = list(args)
            if len(self.dimensions) < 4:
                self.dimensions.append(PLAYER_SIZE)
                self.dimensions.append(PLAYER_SIZE)
            self.color = default_colors[type]
        
        if type == MOVEMENT:
            self.reps = kwargs['reps']
            self.moves = kwargs['moves']
            
        if type == PAD:
            self.jheight = kwargs['jheight']
            
        if type == TRIGGER:
            self.last_press = 0
            self.disable_tag = kwargs['disabletag']
            self.enabled = kwargs['enabled']
        
        if type in TOUCHTOGGLE: 
            self.touch_disable = kwargs['touchdisable']
            if self.touch_disable:
                self.disable_delay = kwargs['disabledelay']

class Level:
    def __init__(self) -> None:
        self.blocks =   [LevelElement(BLOCK, 0, 160, 150, 50, tag = 'none', touchdisable = False)]
        elemlist    = list[LevelElement]
        
        self.spikes:    elemlist = []
        self.pads:      elemlist = []
        self.toggles:   elemlist = []
        self.movements: elemlist = []
        self.triggers:  elemlist = []
        self.flippers:  elemlist = []
        self.coins:     elemlist = []
        
        self.goal = LevelElement(GOAL, 970, 900, 20, 20, tag = 'goal')
        
        self.unlocked = False
        
    def unlock(self):
        self.unlocked = True
        
    def add_block(self, x, y, width, height, tag = 'none', color = default_colors[BLOCK], touchdisable = False, disabledelay = 2000):
        self.blocks.append(LevelElement(BLOCK, x, y, width, height, tag = tag, color = color, touchdisable = touchdisable, disabledelay = disabledelay))
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
    
    def add_pad(self, x, y, width, height, jheight = -25, tag = 'none', color = default_colors[PAD], touchdisable = False, disabledelay = 2000):
        if width == 0:
            width = PLAYER_SIZE
        if height == 0:
            height = PLAYER_SIZE
        self.pads.append(LevelElement(PAD, x, y, width, height, \
                            tag = tag, \
                            jheight = jheight, \
                            color = color, \
                            touchdisable = touchdisable, \
                            disabledelay = disabledelay))
        return self
    
    def set_goal(self, x, y, width, height):
        if width == 0:
            width = PLAYER_SIZE
        if height == 0:
            height = PLAYER_SIZE
        self.goal = LevelElement(GOAL, x, y, width, height, tag = 'goal')
        return self
    
    def add_time_toggle(self, tag, time):
        self.toggles.append(LevelElement(TOGGLE, delay = time, tag = tag))
        return self
    
    def add_coin(self, x, y, tag):
        self.coins.append(LevelElement(COIN, x, y, tag = tag))
        return self
    
    def add_trigger(self, x, y, width, height, disabletag, color = default_colors[TRIGGER], tag = 'none', enabled = False, touchdisable = False, disabledelay = 2000):
        if width == 0:
            width = PLAYER_SIZE
        if height == 0:
            height = PLAYER_SIZE
        self.triggers.append(LevelElement(TRIGGER, x, y, width, height, \
                            disabletag = disabletag, \
                            color = color, \
                            tag = tag, \
                            enabled = enabled, \
                            touchdisable = touchdisable, \
                            disabledelay = disabledelay))
        return self
    
    def add_ground_spikes(self, color = default_colors[SPIKES], tag = 'none'):
        self.add_spikes(0, 950, 1000, 50, color = color, tag = tag)
        return self
    
    def add_flipper(self, x, y, width, height, tag = 'none', color = default_colors[FLIPPER], touchdisable = False, disabledelay = 2000):
        if width == 0:
            width = PLAYER_SIZE
        if height == 0:
            height = PLAYER_SIZE
        self.flippers.append(LevelElement(FLIPPER, x, y, width, height, tag = tag, color = color, touchdisable = touchdisable, disabledelay = disabledelay))
        return self

class Game:
    def __init__(self) -> None:
        def start():
            start_btn.destroy()
            self.canvas.delete('start')
            self.show_select_menu()
            
        self.root = tk.Tk()
        self.root.title('Give Up')
        self.root.resizable(False, False)
        
        self.playing = False
        self.current_level = 0
        
        self.size = (self.root.winfo_screenheight() / 10) * 9
         
        self.canvas = tk.Canvas(self.root, width = self.size, height = self.size)
        self.canvas.create_window(0, 0, width = self.size, height = self.size, anchor = 'nw')
        self.canvas.update_idletasks()
        self.canvas.pack()
        
        self.cwidth, self.cheight = self.canvas.winfo_reqwidth(), self.canvas.winfo_reqheight()
        
        self.goal_img = tk.PhotoImage(file = 'goalflag.png')        
        
        self.reset_levels()
        
        self.records = [None for _ in self.levels]
        self.coin_records = [0 for _ in self.levels]
        self.attempts = [0 for _ in self.levels]

        self.load_data()
        
        sv_ttk.use_dark_theme()
        
        fnt = 'Segoe UI'
        self.huge_font = (fnt, self.proportion(45))
        self.big_font = (fnt, self.proportion(35))
        self.small_font = (fnt, self.proportion(25))
        self.medium_font = (fnt, self.proportion(20))
        self.mini_font = (fnt, self.proportion(17))
        
        try:
            self.last_image = tk.PhotoImage(file = 'last.png')
        except tk.TclError:
            self.last_image = tk.PhotoImage(width = self.cheight, height = self.cwidth)
            
        self.canvas.create_image(0, 0, image = self.last_image, anchor = tk.NW, tag = 'last')
        
        start_btn = ttk.Button(self.canvas, text = 'Start Game', command = start, style = 'Big.Accent.TButton')
        start_btn.place(relx=0.5, rely=0.5, anchor = CENTER)
        
        settings_btn = ttk.Button(self.root, text = 'Settings', command = self.show_settings)
        
        self.canvas.create_text(self.cwidth / 2, self.cheight / 5, text = 'Platformer', font = self.huge_font, tag = 'start', anchor = tk.CENTER, fill = 'white')
        
        self.root.bind('<space>', func(self.press_key, TOP))
        self.root.bind('<Escape>', func(self.pause))
        self.root.bind('<Up>', func(self.press_key, TOP))
        self.root.bind('<KeyRelease-space>', func(self.release_key, TOP))
        self.root.bind('<KeyRelease-Up>', func(self.release_key, TOP))
        self.root.bind('<Right>', func(self.press_key, RIGHT))
        self.root.bind('<Left>', func(self.press_key, LEFT))
        self.root.bind('<KeyRelease-Right>', func(self.release_key, RIGHT))
        self.root.bind('<KeyRelease-Left>', func(self.release_key, LEFT))
        self.root.bind('<Destroy>', func(self.save_data))
        
        style = ttk.Style(self.root)
        style.theme_use('sun-valley-dark')
        style.configure('Huge.Accent.TButton', font = self.huge_font)
        style.configure('Big.Accent.TButton', font = self.big_font)
        style.configure('Small.Accent.TButton', font = self.small_font)
        style.configure('Mini.Accent.TButton', font = self.mini_font)
        
        self.root.mainloop()
        
    def show_settings(self):
        def clear_data():
            with shelve.open('savedata') as db:
                db['records'] = 0
                db['coinrecords'] = 0
                db['unlocked'] = 0
                db['attempts'] = 0
        
        toplvl = tk.Toplevel(self.root, width = self.cwidth / 2, height = self.cheight / 2)
        toplvl.resizable(False, False)
        toplvl.grab_set()
        toplvl.title('Settings')
        clearbtn = ttk.Button(toplvl, text = 'Clear Save Data', style = 'Small.Accent.TButton', command = clear_data, width = 16)
        clearbtn.place(relx = 0.5, rely = 0.2, anchor = tk.CENTER)
        
    def press_key(self, key):
        if not self.playing:
            return
        self.pressed[key] += 1
        
        for _ in range(len([obj for obj in self.pressed if self.pressed[obj] == 1])):
            self.presses += 1
    
    def release_key(self, key):
        if not self.playing:
            return
        self.pressed[key] = 0
        
    def check_keys(self):
        if self.pressed[RIGHT]:
            self.move_x(True)
        if self.pressed[LEFT]:
            self.move_x()
        if self.pressed[TOP]:
            self.move_y()
        
        self.root.after(4, self.check_keys)
        
    def move_y(self):
        if self.jumps != 0:
            self.pressed[TOP] = False
            self.y_speed = -16 * self.gravity
            self.jumps -= 1
            
    def move_x(self, right = False):
        if -8 <= self.x_speed <= 8:
            self.x_speed += 0.75 if right else -0.75
            
    def save_data(self):
        with shelve.open('savedata') as db:
            db['records'] = self.records
            db['coinrecords'] = self.coin_records
            db['attempts'] = self.attempts
            db['unlocked'] = len([0 for a in self.levels if a.unlocked])
    
    def load_data(self):
        with shelve.open('savedata') as db:
            if 'records' in db:
                self.records = db['records']
            if 'coinrecords' in db:
                self.coin_records = db['coinrecords']
            if 'attempts' in db:
                self.attempts = db['attempts']
            if 'unlocked' in db:
                self.unlocked = db['unlocked']
                for index in range(db['unlocked']):
                    self.levels[index].unlock()
            
    def show_select_menu(self):
        self.canvas.delete('last')
        frame = ttk.Frame(self.canvas)
        title = ttk.Label(self.canvas, text = 'Select Level', font = self.big_font)
        
        for col in range(3):
            frame.columnconfigure(col, weight = 1)
        for row in range(9):
            frame.rowconfigure(row, weight = 1)
            
        for index in range(len(self.levels)):
            def show_info(index = index):
                window = tk.Toplevel(self.root, background = '#1C1C1C', width = self.cwidth / 3, height = self.cheight / 3)
                window.title(f'Level {index + 1} Information')
                window.resizable(False, False)
                window.grab_set()
                
                ttk.Label(window, text = f'Level {index + 1} Information', font = self.small_font).place(relx = 0.5, rely = 0.1, anchor = CENTER)
                ttk.Label(window, text = f'Total Attempts: {self.attempts[index]}', font = self.medium_font).place(relx = 0.5, rely = 0.3, anchor = CENTER)
                
                if not self.records[index] == None:
                    ttk.Label(window, text = f'Most Coins Collected: {self.coin_records[index]}', font = self.medium_font).place(relx = 0.5, rely = 0.4, anchor = CENTER)
                    ttk.Label(window, text = f'Best Run: {self.records[index]} clicks', font = self.medium_font).place(relx = 0.5, rely = 0.5, anchor = CENTER)
                    
                ttk.Button(window, text = 'Close', command = window.destroy, style = 'Small.Accent.TButton').place(relx = 0.5, rely = 0.8, anchor = CENTER)
                
            def open_level(index = index):
                frame.destroy()
                title.destroy()
                self.current_level = index  
                self.playing = True
                self.load_lvl(self.levels[index])
                self.start_game()
                
            x = index % 3
            y = floor(index / 3)
            state = 'normal' if self.levels[index].unlocked else 'disabled'
                
            btn = ttk.Button(frame, text = str(index + 1), style = 'Big.Accent.TButton', command = open_level, width = 4, state = state)
            btn.grid(column = x, row = y, padx = 30, pady = 25, sticky = tk.NSEW)
            infobtn = ttk.Button(frame, text = 'Info', style = 'Mini.Accent.TButton', state = state, width = 4, command = show_info)
            infobtn.grid(column = x, row = y, sticky = tk.NE)
            
        title.place(relx = 0.5, rely = 0.1, anchor = tk.CENTER)
        frame.place(relx = 0.5, rely = 0.7, anchor = tk.CENTER, relheight = 0.9, relwidth = 0.9)
            
    def reset_levels(self):
        self.levels = [Level() for _ in range(0, 6)]
        
        self.levels[0]\
            .add_block(220, 0, 70, 700)\
            .add_block(85, 350, 135, 50)\
            .add_block(0, 550, 135, 50)\
            .add_spikes(150, 160, 70, 50, 'spikes1')\
            .add_time_toggle('spikes1', 1000)\
            .add_ground_spikes()\
            .add_block(0, 900, 135, 50)\
            .add_flipper(250, 800, 0, 0)\
            .add_coin(560, 285, 'coin1')\
            .add_pad(730, 200, 0, 0)\
            .add_block(830, 420, 170, 50)\
            .set_goal(950, 470, 50, 50)\
            .add_spikes(360, 400, 200, 50)
            
        self.levels[1]\
            .add_spikes(0, 300, 1000, 50, 'bigspikes')\
            .add_block(640, 390, 360, 50)\
            .add_trigger(520, 100, 0, 0, 'bigspikes', enabled = True, color = default_colors[TRIGGERFLIP])\
            .add_block(0, 700, 200, 50)\
            .add_block(400, 900, 200, 50, 'moveblock')\
            .add_movement((4, 0), reps = 20, delay = 30, tag = 'moveblock')\
            .add_spikes(300, 600, 700, 90)\
            .add_ground_spikes()
        
        self.levels[2]\
            .add_block(100, 700, 100, 50, 'test')\
            .add_block(220, 0, 70, 500)\
            .add_block(600, 400, 200, 50)\
            .add_block(855, 199, 200, 50, 'block')\
            .add_trigger(180, 10, 0, 0, 'test')\
            .add_trigger(10, 450, 0, 0, 'pad')\
            .set_goal(960, 10, 30, 30)\
            .add_pad(400, 830, 50, 50, tag = 'pad', jheight = -35)\
            .add_movement((1, 0), tag = 'test', delay = 40, reps = 30)\
            .add_time_toggle('block', 1000)\
            .add_ground_spikes()\
            .add_coin(600, 100, 'coin1')
            
        self.unlocked = len([0 for a in self.levels if a.unlocked])
        
        self.load_data()
            
    def show_blur(self):
        self.root.attributes('-topmost', 1)
        self.root.attributes('-topmost', 0)
        
        x, y = self.canvas.winfo_x() + self.root.winfo_rootx(), self.canvas.winfo_y() + self.root.winfo_rooty()
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        
        ss = pyautogui.screenshot(region=(x, y, width, height))
        blurimg = ss.filter(ImageFilter.GaussianBlur(radius = 20))
        self.ss = ImageTk.PhotoImage(blurimg)
        
        self.canvas.create_image(0, 0, image = self.ss, anchor = tk.NW, tag = 'img')
        self.canvas.update()
        
        pyautogui.screenshot(region=(x, y, width, height), imageFilename = 'last.png')
            
    def die(self):
        def delete():
            self.canvas.delete('all')
            restartbtn.destroy()
            exitbtn.destroy()
            selectbtn.destroy()
        
        def restart():
            delete()
            self.playing = True
            self.load_lvl(self.levels[self.current_level])
            self.start_game()
            
        def show_select():
            delete()
            self.show_select_menu()
        
        self.attempts[self.current_level] += 1
        self.show_blur()
        self.load_lvl(self.levels[self.current_level])
        self.canvas.tag_raise('img')
        self.playing = False
        for key in self.afters:
            self.root.after_cancel(self.afters[key])
        self.canvas.create_text(self.cwidth/2, self.cheight/3, anchor = CENTER, text = 'You Died', tag = 'img', font = self.big_font, fill = 'white')
        
        restartbtn = ttk.Button(self.canvas, text = 'Restart', style = 'Small.Accent.TButton', command = restart, width = 16)
        restartbtn.place(relx = 0.5, rely = 0.5, anchor = CENTER)
        
        exitbtn = ttk.Button(self.canvas, text = 'Exit', style = 'Small.Accent.TButton', command = self.root.destroy, width = 16)
        exitbtn.place(relx = 0.5, rely = 0.6, anchor = CENTER)
        
        selectbtn = ttk.Button(self.canvas, text = 'Level Select Menu', style = 'Small.Accent.TButton', command = show_select, width = 16)
        selectbtn.place(relx = 0.5, rely = 0.7, anchor = CENTER)
        
    def start_game(self):
        self.player     = [100, 100]
        self.y_speed    = 0
        self.x_speed    = 0
        self.jumps      = 0
        self.grounded   = False
        self.playing    = True

        self.afters = {}
        self.pressed = {RIGHT: False, LEFT: False, TOP: False}
        
        self.cwidth, self.cheight = self.canvas.winfo_width(), self.canvas.winfo_height()
        
        self.reset_levels()
        self.physics_loop()
        self.check_keys()
        
        if DEBUG:
            def p(e):
                print((e.x / self.size)*1000, (e.y / self.size)*1000)
            self.root.bind('<Button-1>', p)
        
    def test_player(self, element: LevelElement, check_floor = False, p = 'n'):
        if element.tag in self.disabled_tags:
            return False
        
        if p == 'n':
            p = self.player
        
        half = PLAYER_SIZE / 2
        players = [p, [p[0] + PLAYER_SIZE, p[1]], [p[0] + PLAYER_SIZE, p[1] + PLAYER_SIZE], [p[0], p[1] + PLAYER_SIZE], [p[0] + half, p[1] + half]]
        
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
        
        condition = self.y_speed > -12
        if self.gravity == 1:
            condition = self.y_speed < 12
        
        if condition and not self.grounded:
            self.y_speed += 1 * self.gravity
            
        self.grounded = False
        
        for pad in self.level.pads:
            if self.test_player(pad):
                if pad.touch_disable:
                    self.canvas.itemconfigure(pad.tag, state = 'hidden')
                    self.disabled_tags.append(pad.tag)
                self.y_speed = pad.jheight * self.gravity
                self.jumps = 2
                    
        for flipper in self.level.flippers:
            if self.test_player(flipper):
                if time() - flipper.last_press > 0.5:
                    self.gravity *= -1
                    flipper.last_press = time()
                if flipper.touch_disable:
                    self.canvas.itemconfigure(flipper.tag, state = 'hidden')
                    self.disabled_tags.append(flipper.tag)
                    
        for coin in self.level.coins:
            if self.test_player(coin):
                self.canvas.itemconfigure(coin.tag, state = 'hidden')
                self.disabled_tags.append(coin.tag)
                self.coins_collected += 1
        
        if self.y_speed != 0:
            move = self.y_speed / abs(self.y_speed)
            move *= -1
            move = int(move)
            
            for _ in range(abs(self.y_speed)):
                self.player[1] += move * -1
                
                for spike in self.level.spikes:
                    if self.test_player(spike):
                        self.die()
                        return
                    
                failed = False
                for block in self.level.blocks:
                    if self.test_player(block, True):
                        if block.touch_disable and self.test_player(block):
                            
                            id = f'{block.tag}+{block.disable_delay}disable'
                            
                            def disable(block = block, id = id):
                                self.canvas.itemconfigure(block.tag, state = 'hidden')
                                self.disabled_tags.append(block.tag)
                                if id in self.afters:
                                    del self.afters[id]
                                    
                            if not id in self.afters:
                                self.afters[id] = self.root.after(block.disable_delay, disable)
                                
                        failed = True
                        if self.y_speed * self.gravity >= 0:
                            self.grounded = True
                            self.jumps = 2
                            
                        self.y_speed = 1 * self.gravity
                        
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
                while self.test_player(block, True):
                    if block.touch_disable:
                        def disable(block = block):
                            self.canvas.itemconfigure(block.tag, state = 'hidden')
                            self.disabled_tags.append(block.tag)
                            id = f'{block.tag}+{block.disable_delay}disable'
                            del self.afters[id]
                        id = f'{block.tag}+{block.disable_delay}disable'
                        if not id in self.afters:
                            self.afters[id] = self.root.after(block.disable_delay, disable)
                    if count > 8:
                        self.die()
                        break
                    count += 1
                    self.player[0] += move
                    self.x_speed = 0
                    happened = True
                if happened:
                    break
                
        self.x_speed *= 0.9
        
        for trigger in self.level.triggers:
            if self.test_player(trigger):
                if time() - trigger.last_press > 0.5:
                    trigger.func()
                    trigger.last_press = time()
                if trigger.touch_disable:
                    self.canvas.itemconfigure(trigger.tag, state = 'hidden')
                    self.disabled_tags.append(trigger.tag)
        
        if self.test_player(self.level.goal):
            self.touch_goal()
            return
        
        x, y = copy(self.player)
        x = self.proportion(x, False)
        y = self.proportion(y, False)
        size = self.proportion(PLAYER_SIZE)
        offset = abs(int(self.y_speed / 2))
        self.round_rectangle(x + offset, y - offset, x + size - offset, y + size + offset, fill = 'blue', tag = 'player', radius = 3)
        
        self.last = time()
        
        self.afters['physics'] = self.root.after(11, self.physics_loop)
        
    def win(self):
        for key in self.afters:
            self.root.after_cancel(key)
        self.playing = False
        self.canvas.delete('all')
        self.canvas.create_image(0, 0, image = self.last_image, anchor = tk.NW)
        self.canvas.create_text(self.cwidth / 2, self.cheight / 3, font = self.huge_font, fill = 'white', text = 'You Won!')
        ttk.Button(self.canvas, text = 'Exit', style = 'Big.Accent.TButton', command = self.root.destroy).place(relx = 0.5, rely = 0.5, anchor = CENTER)
        
    def touch_goal(self):
        self.playing = False
        
        def callback():
            self.canvas.delete('img')
            nextbtn.destroy()
            selbtn.destroy()
            restartbtn.destroy()
            exitbtn.destroy()
        
        def go_next():
            callback()
            self.current_level += 1
            if self.current_level in range(len(self.levels)):
                self.load_lvl(self.levels[self.current_level])
                self.start_game()
            else:
                self.win()
            
        def show_select():
            self.canvas.delete('all')
            callback()
            try:
                self.unlocked += 1
                for index in range(self.unlocked):
                    self.levels[index].unlock()
            except IndexError:
                pass
            self.show_select_menu()
            
        def restart():
            callback()
            self.playing = True
            self.load_lvl(self.levels[self.current_level])
            self.start_game()
            
        record = self.records[self.current_level]
        coin_record = self.coin_records[self.current_level]
        
        self.attempts[self.current_level] += 1
        
        if record == None or self.presses < record:
            self.records[self.current_level] = self.presses
            
        if self.coins_collected > coin_record:
            self.coin_records[self.current_level] = self.coins_collected
        
        self.show_blur()
        inc = self.cheight / 10
        lbl = lambda x, y, text, font, fill = 'white': self.canvas.create_text(x, y, text = text, font = font, tag = 'img', fill = fill, justify = CENTER)
        lbl(self.cwidth / 2, inc, f'You won in {self.presses} clicks', self.big_font)
        lbl(self.cwidth / 2, inc * 2, f'Your record is {self.records[self.current_level]} clicks', self.big_font)
        if not len(self.level.coins) == 0:
            lbl(self.cwidth / 2, inc * 3, f'You got {self.coins_collected} out of {len(self.level.coins)} coins', self.big_font)
            lbl(self.cwidth / 2, inc * 4, f'Your record is {self.coin_records[self.current_level]} coins', self.big_font)
        
        lbl(self.cwidth / 2, self.cheight / 1.1, f'Total Attempts: {self.attempts[self.current_level]}', self.small_font)
        nextbtn = ttk.Button(self.canvas, text = 'Next Level', style = 'Small.Accent.TButton', command = go_next, width = 15)
        nextbtn.place(relx = 0.5, rely = 0.5, anchor = CENTER)
        selbtn = ttk.Button(self.canvas, text = 'Level Selection', style = 'Small.Accent.TButton', command = show_select, width = 15)
        selbtn.place(relx = 0.5, rely = 0.6, anchor = CENTER)
        restartbtn = ttk.Button(self.canvas, text = 'Restart', style = 'Small.Accent.TButton', command = restart, width = 15)
        restartbtn.place(relx = 0.5, rely = 0.7, anchor = CENTER)
        exitbtn = ttk.Button(self.canvas, text = 'Exit', style = 'Small.Accent.TButton', command = self.root.destroy, width = 15)
        exitbtn.place(relx = 0.5, rely = 0.8, anchor = CENTER)
        
    def pause(self):
        if not self.playing:
            return

        def callback():
            self.canvas.delete('all')
            restartbtn.destroy()
            exitbtn.destroy()
            selbtn.destroy()
            resbtn.destroy()
            
        def show_select():
            callback()
            for index in range(self.unlocked):
                self.levels[index].unlock()
            self.show_select_menu()
            
        def restart():
            callback()
            self.playing = True
            self.load_lvl(self.levels[self.current_level])
            self.start_game()
            
        def resume():
            self.playing = True
            self.canvas.delete('img')
            restartbtn.destroy()
            exitbtn.destroy()
            selbtn.destroy()
            resbtn.destroy()
        
        self.root.after_cancel(self.afters['physics'])
        self.show_blur()
        self.playing = False
        self.canvas.create_text(self.cwidth / 2, self.cheight / 10, text = 'You Won', font = self.big_font, tag = 'img', fill = 'white')
        selbtn = ttk.Button(self.canvas, text = 'Level Selection', style = 'Small.Accent.TButton', command = show_select, width = 15)
        selbtn.place(relx = 0.5, rely = 0.6, anchor = CENTER)
        resbtn = ttk.Button(self.canvas, text = 'Resume', style = 'Small.Accent.TButton', command = resume, width = 15)
        resbtn.place(relx = 0.5, rely = 0.5, anchor = CENTER)
        restartbtn = ttk.Button(self.canvas, text = 'Restart', style = 'Small.Accent.TButton', command = restart, width = 15)
        restartbtn.place(relx = 0.5, rely = 0.7, anchor = CENTER)
        exitbtn = ttk.Button(self.canvas, text = 'Exit', style = 'Small.Accent.TButton', command = self.root.destroy, width = 15)
        exitbtn.place(relx = 0.5, rely = 0.8, anchor = CENTER)
        
    def load_lvl(self, lvl: Level):
        self.canvas.itemconfigure('all', state = 'normal')
        self.afters = {}
        self.disabled_tags = []
        self.canvas.delete('level')
        self.presses = 0
        self.coins_collected = 0
        self.gravity = 1
        
        def positions(elem):
            return (elem[0], elem[1], elem[0] + elem[2], elem[1] + elem[3])
        
        self.level = copy(lvl)
        draw_lvl = deepcopy(lvl)
        
        draw_lvl.goal.dimensions = [self.proportion(n) for n in draw_lvl.goal.dimensions]
        
        for block in draw_lvl.blocks:
            block.dimensions = [self.proportion(coord) for coord in block.dimensions]
            tag = ['level', block.tag]
            self.round_rectangle(*positions(block.dimensions), fill = block.color, tag = tag)
            
        for spike in draw_lvl.spikes:
            spike.dimensions = [self.proportion(coord) for coord in spike.dimensions]
            tag = ['level', spike.tag]
            self.round_rectangle(*positions(spike.dimensions), fill = spike.color, tag = tag)
        
        for pad in draw_lvl.pads:
            pad.dimensions = [self.proportion(coord) for coord in pad.dimensions]
            tag = ['level', pad.tag]
            self.round_rectangle(*positions(pad.dimensions), fill = pad.color, tag = tag)
            
        for flipper in draw_lvl.flippers:
            flipper.dimensions = [self.proportion(coord) for coord in flipper.dimensions]
            tag = ['level', flipper.tag]
            self.round_rectangle(*positions(flipper.dimensions), fill = flipper.color, tag = tag)
            
        for coin in draw_lvl.coins:
            coin.dimensions = [self.proportion(coord) for coord in coin.dimensions]
            tag = tag = ['level', coin.tag]
            self.round_rectangle(*positions(coin.dimensions), fill = coin.color, tag = tag)
            
        for toggle in draw_lvl.toggles:
            def callback(delay = toggle.delay, tag = toggle.tag):
                if not self.playing:
                    return
                object = None
                for obj in draw_lvl.blocks:
                    if obj.tag == tag:
                        object = obj
                if tag in self.disabled_tags:
                    self.canvas.itemconfigure(tag, state = 'normal')
                    if tag in self.disabled_tags:
                        self.disabled_tags.remove(tag)
                    if object != None and self.test_player(self.player, object, False):
                        self.die()
                        return
                else:
                    self.disabled_tags.append(tag)
                    self.canvas.itemconfigure(tag, state = 'hidden')
                self.afters[f'{delay}.{tag}toggle'] = self.root.after(delay, callback, delay, tag)
            self.afters[f'{toggle.delay}.{toggle.tag}toggle'] = self.root.after(toggle.delay, callback, toggle.delay, toggle.tag)
            
        for movement in draw_lvl.movements:
            moves = movement.moves
            tag = movement.tag
            delay = movement.delay
            objinfo = 'none'
            
            touch = False
            
            if tag == 'goal':
                objinfo = self.level.goal
                obj = self.level.goal
            else:
                
                for test in self.level.blocks:
                    if test.tag == tag:
                        touch = True
                        objinfo = (self.level.blocks.index(test), 'blocks')
                        obj = test
                        
                for test in self.level.spikes:
                    if test.tag == tag:
                        objinfo = (self.level.spikes.index(test), 'spikes')
                        obj = test
                        
                for test in self.level.pads:
                    if test.tag == tag:
                        objinfo = (self.level.pads.index(test), 'pads')
                        obj = test
                        
                for test in self.level.triggers:
                    if test.tag == tag:
                        objinfo = (self.level.triggers.index(test), 'triggers')
                        obj = test
                        
                for test in self.level.flippers:
                    if test.tag == tag:
                        objinfo = (self.level.flippers.index(test), 'flippers')
                        obj = test
                
            if objinfo == 'none':
                return
            
            def move_callback(count, objinfo = objinfo, obj = obj, tag = tag, moves = moves, delay = delay, touch = touch):
                if not self.playing:
                    return
                x, y = moves[count % len(moves)]
                
                if x != 0:
                    was_in = self.test_player(self.player, obj, False)
                    if type(objinfo) is tuple:
                        match objinfo[1]:
                            case 'pads':
                                self.level.pads[objinfo[0]].dimensions[0] += x
                            case 'blocks':
                                self.level.blocks[objinfo[0]].dimensions[0] += x
                            case 'spikes':
                                self.level.spikes[objinfo[0]].dimensions[0] += x
                            case 'triggers':
                                self.level.triggers[objinfo[0]].dimensions[0] += x
                            case 'flippers':
                                self.level.flippers[objinfo[0]].dimensions[0] += x
                    else:
                        self.level.goal.dimensions[0] += x
                    if touch:
                        is_in = self.test_player(self.player, obj, False)
                        if not was_in and is_in:
                            self.player[0] += x
                        if is_in and was_in:
                            self.die()
                            return
                
                if y != 0:
                    was_in = self.test_player(self.player, obj, False)
                    if type(objinfo) is tuple:
                        match objinfo[1]:
                            case 'pads':
                                self.level.pads[objinfo[0]].dimensions[1] += y
                            case 'blocks':
                                self.level.blocks[objinfo[0]].dimensions[1] += y
                            case 'spikes':
                                self.level.spikes[objinfo[0]].dimensions[1] += y
                            case 'triggers':
                                self.level.triggers[objinfo[0]].dimensions[1] += y
                            case 'flippers':
                                self.level.flippers[objinfo[0]].dimensions[1] += y
                    else:
                        self.level.goal.dimensions[1] += y
                    if touch:
                        is_in = self.test_player(self.player, obj, False)
                        if is_in:
                            if was_in:
                                self.die()
                                return
                            else:
                                self.player[1] += y
                    
                self.canvas.move(tag, self.proportion(x, False), self.proportion(y, False))
                self.afters[f'{objinfo}.{tag}'] = self.root.after(delay, move_callback, count + 1, objinfo, obj, tag, moves, delay, touch)
                      
            self.afters[f'{objinfo}.{tag}'] = self.root.after(delay, move_callback, 0, objinfo, obj, tag, moves, delay, touch)
        
        for index, trigger in enumerate(draw_lvl.triggers):
            trigger.dimensions = [self.proportion(coord) for coord in trigger.dimensions]
            
            sprite = self.round_rectangle(*positions(trigger.dimensions), fill = trigger.color[0], tag = (trigger.tag, 'level'), radius = 5)
            trig = self.level.triggers[index]
            def callbacks(index = index, sprite = sprite):
                trig = self.level.triggers[index]
                if not self.playing:
                    return
                if trig.enabled:
                    self.level.triggers[index].enabled = False
                    col = trigger.color[1]
                    self.canvas.itemconfigure(sprite, fill = col, outline = deluminance(col))
                    self.canvas.itemconfigure(trig.disable_tag, state = 'hidden')
                    self.disabled_tags.append(trig.disable_tag)
                else:
                    self.level.triggers[index].enabled = True
                    col = trigger.color[0]
                    self.canvas.itemconfigure(sprite, fill = col, outline = deluminance(col))
                    self.canvas.itemconfigure(trig.disable_tag, state = 'normal')
                    if trig.disable_tag in self.disabled_tags:
                        self.disabled_tags.remove(trig.disable_tag)
                        
            callbacks()
            callbacks()
                    
            trig.func = callbacks
        
        x, y, width, height = draw_lvl.goal.dimensions
        self.goal_img = ImageTk.PhotoImage(Image.open('goalflag.png').resize((width, height), resample = Image.LANCZOS))
        self.canvas.create_image(x, y, image = self.goal_img, tag = ('level', 'goal'), anchor = tk.NW)
        
    #https://stackoverflow.com/questions/44099594/how-to-make-a-tkinter-canvas-rectangle-with-rounded-corners
    def round_rectangle(self, x1, y1, x2, y2, radius=PLAYER_SIZE / 4, **kwargs):
        radius *= 3
    
        points = [x1+radius, y1,
                x1+radius, y1,
                x2-radius, y1,
                x2-radius, y1,
                x2, y1,
                x2, y1+radius,
                x2, y1+radius,
                x2, y2-radius,
                x2, y2-radius,
                x2, y2,
                x2-radius, y2,
                x2-radius, y2,
                x1+radius, y2,
                x1+radius, y2,
                x1, y2,
                x1, y2-radius,
                x1, y2-radius,
                x1, y1+radius,
                x1, y1+radius,
                x1, y1]
        
        bd = deluminance(kwargs['fill'])

        return self.canvas.create_polygon(points, **kwargs, smooth=True, outline = bd, width = 2, state = 'normal')
        
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
    
def deluminance(col):
    color = Color(col)
    color.set_luminance(color.get_luminance() * 0.8)
    return color.get_hex()

Game()