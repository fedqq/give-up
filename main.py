from __future__ import division
import shelve
import tkinter as tk
from tkinter import ttk, CENTER, TOP, BOTTOM, LEFT, RIGHT, BOTH, X, Y
import sv_ttk
from copy import copy, deepcopy
from ctypes import windll
from time import time
from math import floor
from colour import Color, HSL, hsl2hex
from PIL import ImageTk, ImageFilter, Image
import pyautogui
import colorsys

OBJCOUNTER = 0

'''windll.shcore.SetProcessDpiAwareness(False)'''

PLAYER_SIZE = 30
DEBUG = True
TRANSPARENT = '#ab23ff'
DEFAULT_DELAY = 1500

BLOCK, PAD, MOVEMENT, SPIKES, TOGGLE, GOAL, TRIGGER, TRIGGERFLIP, FLIPPER, COIN = 'block', 'pad', 'movement', 'spikes', 'toggle', 'goal', 'trigger', 'triggerflip', 'flipper', 'coin'

VISIBLE = BLOCK+PAD+SPIKES+GOAL+TRIGGER+FLIPPER+COIN
INVISIBLE = MOVEMENT+TOGGLE
TOUCHTOGGLE = BLOCK+PAD+FLIPPER+TRIGGER

colors = {BLOCK: 'gray', SPIKES: '#e86056', PAD: 'yellow', GOAL: None, TRIGGER: ('green', 'red'), TRIGGERFLIP: ('red', 'green'), FLIPPER: ('#44aff2'), COIN: 'yellow'}

class Settings():
    def __init__(self) -> None:
        self.color_gradient = True
        self.jump_circles = True

class LevelElement:
    def __init__(self, type, *args, **kwargs) -> None:
        
        self.type = type
        
        self.tag = kwargs['tag']
        
        if self.tag == 'none':
            global OBJCOUNTER
            self.tag = f'objn.{OBJCOUNTER}'
            OBJCOUNTER += 1
            
        self.last_trigger = 0
        kwargs.setdefault('color', colors.get(type))
        
        if type in INVISIBLE:
            self.delay = kwargs['delay']
            
        if type in VISIBLE:
            self.dimensions = list(args)
            if len(self.dimensions) < 4:
                self.dimensions.append(PLAYER_SIZE)
                self.dimensions.append(PLAYER_SIZE)
            self.color = kwargs['color']
        
        if type == MOVEMENT:
            self.reps = kwargs['reps']
            self.moves = kwargs['moves']
            
        if type == PAD:
            self.jump_height = kwargs['jheight']
            
        if type == TRIGGER:
            self.last_trigger = 0
            self.disable_tag = kwargs['disabletag']
            self.enabled = kwargs['enabled']
        
        self.disable_delay = '404'
        if type in TOUCHTOGGLE: 
            self.touch_disable = kwargs['touchdisable']
            if self.touch_disable:
                self.disable_delay = kwargs['disabledelay']

class Level:
    def __init__(self) -> None:
        self.blocks  = [LevelElement(BLOCK, 10, 160, 140, 50, tag = 'none', touchdisable = False)]
        element_list = list[LevelElement]
        
        self.spikes:    element_list = []
        self.pads:      element_list = []
        self.toggles:   element_list = []
        self.movements: element_list = []
        self.triggers:  element_list = []
        self.flippers:  element_list = []
        self.coins:     element_list = []
        
        self.goal = LevelElement(GOAL, 970, 900, 20, 20, tag = 'goal')
        
        self.unlocked = False
        
    def unlock(self):
        self.unlocked = True
        
    def add_block(self, x, y, width, height, tag = 'none', color = colors[BLOCK], touchdisable = False, disabledelay = DEFAULT_DELAY):
        self.blocks.append(LevelElement(BLOCK, x, y, width, height, tag = tag, color = color, touchdisable = touchdisable, disabledelay = disabledelay))
        return self
    
    def add_movement(self, firstmove, reps = 10, delay = 10, tag = ''): 
        moves = []
        backmove = [-move for move in firstmove]
        for _ in range(reps):
            moves.append(firstmove)
        for _ in range(reps):
            moves.append(backmove)
            
        self.movements.append(LevelElement(MOVEMENT, tag = tag, delay = delay, reps = reps, moves = moves))
        return self
    
    def add_spikes(self, x, y, width, height, tag = 'none', color = colors[SPIKES]):
        self.spikes.append(LevelElement(SPIKES, x, y, width, height, tag = tag, color = color))
        return self
    
    def add_pad(self, x, y, width, height, jheight = -25, tag = 'none', color = colors[PAD], touchdisable = False, disabledelay = DEFAULT_DELAY):
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
    
    def add_trigger(self, x, y, width, height, disabletag, color = colors[TRIGGER], tag = 'none', enabled = False, touchdisable = False, disabledelay = DEFAULT_DELAY):
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
    
    def add_ground_spikes(self, color = colors[SPIKES], tag = 'none'):
        self.add_spikes(0, 950, 1000, 50, color = color, tag = tag)
        return self
    
    def add_flipper(self, x, y, width, height, tag = 'none', color = colors[FLIPPER], touchdisable = False, disabledelay = DEFAULT_DELAY):
        if width == 0:
            width = PLAYER_SIZE
        if height == 0:
            height = PLAYER_SIZE
        self.flippers.append(LevelElement(FLIPPER, x, y, width, height, tag = tag, color = color, touchdisable = touchdisable, disabledelay = disabledelay))
        return self

class Game:
    def __init__(self) -> None:
        
        def start_game():
            start_btn.destroy()
            self.canvas.delete('start')
            self.show_select_menu()
            
        self.root = tk.Tk()
        self.root.title('Give Up')
        self.root.resizable(False, False)
        
        self.playing = False
        self.settings = Settings()
        self.current_level = 0
        
        self.canvas_size = (self.root.winfo_screenheight() / 10) * 8
        
        font = 'Segoe UI Light'
        
        self.huge_font = (font, 45, 'bold')
        self.big_font = (font, 35, 'bold')
        self.small_font = (font, 25)
        self.medium_font = (font, 20)
        self.mini_font = (font, 17)
        self.super_mini_font = (font, 14)
         
        self.canvas = tk.Canvas(self.root, width = self.canvas_size, height = self.canvas_size, bg = '#1f1f1f')
        self.canvas.create_window(0, 0, width = self.canvas_size, height = self.canvas_size, anchor = 'nw')
        self.canvas.update_idletasks()
        self.canvas.pack(side = BOTTOM, pady = 10, padx = 10)
        
        self.cwidth, self.cheight = self.canvas.winfo_reqwidth(), self.canvas.winfo_reqheight()
        
        self.goal_img = tk.PhotoImage(file = 'goalflag.png') 
        
        self.root.update_idletasks()
        
        taskbar = ttk.Frame(self.root, width = self.root.winfo_width())
        taskbar.pack(side = TOP, expand = True, fill = tk.BOTH, padx = 10, pady = 10)
        
        self.exit_button(taskbar, self.root.destroy, style = 'SuperMini', width = 3).pack(side = RIGHT, padx = 10, pady = 5)
        ttk.Button(taskbar, text = '⚙', command = self.show_settings, style = 'SuperMini.Accent.TButton', width = 3).pack(side = RIGHT, padx = 10, pady = 5)
        ttk.Label(taskbar, text = 'Platformer', font = self.small_font).pack(side = LEFT, padx = 10, pady = 10)
        
        self.root.update_idletasks()
        
        width = self.root.winfo_width()
        middle = int(self.root.winfo_screenwidth() / 2 - width / 2)
        
        self.root.overrideredirect(True)
        self.root.geometry(f'+{middle}+10')
        
        def get_pos(event):
            #These two from: https://stackoverflow.com/questions/23836000/can-i-change-the-title-bar-in-tkinter
            window_x = self.root.winfo_x()
            window_y = self.root.winfo_y()
            click_x = event.x_root
            click_y = event.y_root

            self.relative_x = window_x - click_x
            self.relative_y = window_y - click_y
        
        def move_window(event):
            self.root.geometry(f'+{event.x_root + self.relative_x}+{event.y_root + self.relative_y}')
           
        def set_appwindow(root):
            #Code taken from https://stackoverflow.com/questions/30786337/tkinter-windows-how-to-view-window-in-windows-task-bar-which-has-no-title-bar
            #Necessary for better taskbar, full of windows jargon and complicated stuff I don't understand
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            hwnd = windll.user32.GetParent(root.winfo_id())
            style = windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
            style = style & ~WS_EX_TOOLWINDOW
            style = style | WS_EX_APPWINDOW
            windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)
            root.withdraw()
            root.after(10, root.deiconify)
            
        taskbar.bind('<B1-Motion>',  move_window)
        taskbar.bind('<Button-1>',   get_pos)
        
        self.root.after(1, set_appwindow, self.root)       
        
        self.reset_levels()
        
        self.click_records  = [None for _ in self.levels]
        self.coin_records   = [0 for _ in self.levels]
        self.attempts       = [0 for _ in self.levels]

        self.load_data()
        
        sv_ttk.use_dark_theme()
        
        try:
            self.last_image = tk.PhotoImage(file = 'last.png')
        except tk.TclError:
            self.last_image = tk.PhotoImage(width = self.cheight, height = self.cwidth)
            
        self.canvas.create_image(0, 0, image = self.last_image, anchor = tk.NW, tag = 'last')
        
        start_btn = ttk.Button(self.canvas, text = 'Start Game', command = start_game, style = 'Big.Accent.TButton')
        start_btn.place(relx = 0.5, rely = 0.5, anchor = CENTER)
        
        self.canvas.create_text(self.cwidth / 2, self.cheight / 5, text = 'Platformer', font = self.huge_font, tag = 'start', anchor = tk.CENTER, fill = 'white')
        
        self.root.bind('<Escape>', func(self.pause))
        self.root.bind('<space>', func(self.press_key, TOP))
        self.root.bind('<KeyRelease-space>', func(self.release_key, TOP))
        self.root.bind('<Up>', func(self.press_key, TOP))
        self.root.bind('<KeyRelease-Up>', func(self.release_key, TOP))
        self.root.bind('w', func(self.press_key, TOP))
        self.root.bind('<KeyRelease-w>', func(self.release_key, TOP))
        self.root.bind('<Right>', func(self.press_key, RIGHT))
        self.root.bind('<Left>', func(self.press_key, LEFT))
        self.root.bind('<KeyRelease-Right>', func(self.release_key, RIGHT))
        self.root.bind('<KeyRelease-Left>', func(self.release_key, LEFT))
        self.root.bind('d', func(self.press_key, RIGHT))
        self.root.bind('a', func(self.press_key, LEFT))
        self.root.bind('<KeyRelease-d>', func(self.release_key, RIGHT))
        self.root.bind('<KeyRelease-a>', func(self.release_key, LEFT))
        self.root.bind('<Destroy>', func(self.save_data))
        
        style = ttk.Style(self.root)
        style.theme_use('sun-valley-dark')
        style.configure('Huge.Accent.TButton', font = self.huge_font)
        style.configure('Big.Accent.TButton', font = self.big_font)
        style.configure('Small.Accent.TButton', font = self.small_font)
        style.configure('Mini.Accent.TButton', font = self.mini_font)
        style.configure('SuperMini.Accent.TButton', font = self.super_mini_font)
        style.configure('Button.TCheckbutton', font = self.super_mini_font)

        self.root.mainloop()
        
    def show_settings(self):
        def clear_data():
            with shelve.open('savedata') as db:
                db['records'] = []
                db['coinrecords'] = []
                db['unlocked'] = 0
                db['attempts'] = []
                self.attempts = [0 for _ in range(len(self.levels))]
                self.click_records = [None for _ in range(len(self.levels))]
                self.coin_records = [0 for _ in range(len(self.levels))]
                self.unlocked = 0
        
        gradient_bool = tk.BooleanVar(value = self.settings.color_gradient) 
        def toggle_color():
            self.settings.color_gradient = gradient_bool.get()
            
        circles_bool = tk.BooleanVar(value = self.settings.jump_circles)
        def toggle_circle():
            self.settings.jump_circles = circles_bool.get()
        
        window = tk.Toplevel(self.root, width = self.cwidth / 3, height = self.cheight / 3)
        window.resizable(False, False)
        window.grab_set()
        window.title('Settings')
        
        ttk.Label(window, text = 'Game Options', font = self.small_font, justify = CENTER).place(relx = 0.5, rely = 0.1, anchor = tk.CENTER)
        
        clear_btn = ttk.Button(window, text = 'Clear Save Data', style = 'Mini.Accent.TButton', command = clear_data, width = 16)
        clear_btn.place(relx = 0.5, rely = 0.6, anchor = tk.CENTER)
        
        gradient_check = ttk.Checkbutton(window, text = 'Player Color Gradient', command = toggle_color, variable = gradient_bool, style = 'Button.TCheckbutton')
        gradient_check.place(relx = 0.5, rely = 0.8, anchor = tk.CENTER)
        
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
        if self.jumps > 0:
            self.pressed[TOP] = False
            self.y_speed = -16 * self.gravity
            self.jumps -= 1
            if not self.grounded:
                self.circle_size = 2
                self.last_click = copy(self.player)
                self.start_circle()
            
    def move_x(self, right = False):
        if -8 <= self.x_speed <= 8:
            self.x_speed += 0.75 if right else -0.75
            
    def save_data(self):
        with shelve.open('savedata') as db:
            db['records'] = self.click_records
            db['coinrecords'] = self.coin_records
            db['attempts'] = self.attempts
            db['unlocked'] = len([0 for a in self.levels if a.unlocked])
    
    def load_data(self):
        with shelve.open('savedata') as db:
            if 'records' in db:
                self.click_records = db['records']
            if 'coinrecords' in db:
                self.coin_records = db['coinrecords']
            if 'attempts' in db:
                self.attempts = db['attempts']
            if 'unlocked' in db:
                self.unlocked = db['unlocked']
                self.levels[0].unlock() 
                for index in range(db['unlocked']):
                    self.levels[index].unlock()
            
    def show_select_menu(self):
        self.canvas.delete('level')
        
        frame = ttk.Frame(self.canvas, style = 'TFrame')
        
        self.canvas.create_text(self.cwidth / 2, self.cheight / 10, text = 'Select a level', font = self.big_font, anchor = tk.CENTER, tag = 'text', fill = 'white')
        
        for column in range(3):
            frame.columnconfigure(column, weight = 1)
        for row in range(floor(len(self.levels) / 3) + 5):
            frame.rowconfigure(row, weight = 1)
            
        self.last_image = tk.PhotoImage(file = 'last.png')
        
        self.canvas.create_image(0, 0, anchor = tk.NW, image = self.last_image, tag = 'img')
        self.canvas.tag_raise('text')
        
        self.crop_image = tk.PhotoImage(file = 'smaller.png')
        
        ttk.Label(frame, image = self.crop_image).place(x = 0, y = 0)
            
        for index in range(len(self.levels)):
            
            def show_info(index = index):
                window = tk.Toplevel(self.root, background = '#1C1C1C', width = self.cwidth / 3, height = self.cheight / 3)
                window.title(f'Level {index + 1} Information')
                window.resizable(False, False)
                window.grab_set()
                
                ttk.Label(window, text = f'Level {index + 1} Information', font = self.small_font).place(relx = 0.5, rely = 0.1, anchor = CENTER)
                ttk.Label(window, text = f'Total Attempts: {self.attempts[index]}', font = self.medium_font).place(relx = 0.5, rely = 0.3, anchor = CENTER)
                
                if not self.click_records[index] == None:
                    ttk.Label(window, text = f'Most Coins Collected: {self.coin_records[index]}', font = self.medium_font).place(relx = 0.5, rely = 0.4, anchor = CENTER)
                    ttk.Label(window, text = f'Best Run: {self.click_records[index]} clicks', font = self.medium_font).place(relx = 0.5, rely = 0.5, anchor = CENTER)
                    
                ttk.Button(window, text = 'Close', command = window.destroy, style = 'Small.Accent.TButton').place(relx = 0.5, rely = 0.8, anchor = CENTER)
                
            def open_level(index = index):
                frame.destroy()
                self.canvas.delete('text')
                self.current_level = index  
                self.playing = True
                self.load_level(self.levels[index])
                self.start_game()
                
            x = index % 3
            y = floor(index / 3)
            
            state = 'normal' if self.levels[index].unlocked else 'disabled'
                
            open_btn = ttk.Button(frame, text = str(index + 1), style = 'Big.Accent.TButton', command = open_level, width = 4, state = state)
            open_btn.grid(column = x, row = y, padx = 30, pady = 25, sticky = tk.NSEW)
            info_btn = ttk.Button(frame, text = 'Info', style = 'Mini.Accent.TButton', state = state, width = 4, command = show_info)
            info_btn.grid(column = x, row = y, sticky = tk.NE)
            
        frame.place(relx = 0.5, rely = 0.7, anchor = tk.CENTER, relwidth = 0.9, relheight = 0.9)
        
    def exit_button(self, master, cmd = None, style = 'Mini', width = 2):
        if cmd == None:
            cmd = self.root.destroy
        return ttk.Button(master, text = '✕', style = f'{style}.Accent.TButton', command = cmd, width = width)
            
    def reset_levels(self):
        self.levels = [Level() for _ in range(0, 6)]
        
        self.levels[0]\
            .add_spikes(0, 300, 1000, 50, 'bigspikes')\
            .add_block(640, 390, 350, 50, 'bl', touchdisable = True)\
            .add_trigger(520, 100, 0, 0, 'bigspikes', enabled = True, touchdisable = True, tag = 'trig')\
            .add_block(0, 700, 200, 50)\
            .add_block(400, 900, 200, 50, 'moveblock')\
            .add_movement((4, 0), reps = 20, delay = 30, tag = 'moveblock')\
            .add_spikes(300, 600, 700, 90)\
            .add_ground_spikes()\
            .add_coin(990 - PLAYER_SIZE, 100, 'coin1')\
            .unlock()
        
        self.levels[1].blocks[0].dimensions[2] -= 20
        self.levels[1]\
            .add_block(220, 10, 70, 690)\
            .add_block(85, 350, 125, 50)\
            .add_block(10, 550, 125, 50)\
            .add_spikes(140, 160, 70, 50, 'spikes1')\
            .add_time_toggle('spikes1', 1000)\
            .add_ground_spikes()\
            .add_block(10, 890, 125, 50)\
            .add_flipper(250, 800, 0, 0)\
            .add_coin(560, 285, 'coin1')\
            .add_pad(730, 200, 0, 0, touchdisable = True)\
            .add_block(830, 10, 160, 460)\
            .set_goal(900, 470, 50, 50)\
            .add_spikes(360, 400, 200, 50)
        
        self.levels[2]\
            .add_block(100, 700, 100, 50, 'test')\
            .add_block(220, 0, 70, 500)\
            .add_block(600, 400, 200, 50)\
            .add_block(855, 199, 200, 50, 'block')\
            .add_trigger(180, 10, 0, 0, 'test', color = colors[TRIGGERFLIP])\
            .add_trigger(10, 450, 0, 0, 'pad', color = colors[TRIGGERFLIP])\
            .set_goal(960, 10, 30, 30)\
            .add_pad(400, 830, 50, 50, tag = 'pad', jheight = -35)\
            .add_movement((1, 0), tag = 'test', delay = 40, reps = 30)\
            .add_time_toggle('block', 1000)\
            .add_ground_spikes()\
            .add_coin(600, 100, 'coin1')
        
        self.levels[3].blocks = []
        self.levels[3]\
            .add_spikes(10, 50, 140, 50, tag = 'spikes1')\
            .add_trigger(5, 5, 0, 0, disabletag = 'downblocker', enabled = True)\
            .add_block(10, 160, 740, 75)\
            .add_spikes(430, 10, 50, 140, tag = 'blockspikes')\
            .add_time_toggle('blockspikes', 900)\
            .add_spikes(760, 160, 230, 75, 'downblocker')\
            .add_trigger(650, 5, 0, 0, 'spikes1', enabled = True)\
            .add_flipper(950, 400, 0, 0)\
            .add_spikes(300, 350, 500, 100)\
            .add_flipper(155, 400, 0, 0)\
            .add_block(10, 640, 240, 100)\
            .add_spikes(260, 640, 330, 100)\
            .add_block(600, 640, 190, 100)\
            .add_ground_spikes()\
            .add_block(700, 865, 75, 75)\
            .set_goal(340, 900, 0, 0)
        
        self.levels[4].blocks = []
        self.levels[4]\
            .add_block(10, 160, 140, 100)\
            .add_spikes(160, 160, 300, 40)\
            .add_block(470, 160, 250, 40)\
            .add_spikes(730, 160, 250, 40, 'downblock')\
            .add_time_toggle('downblock', 1200)\
            .add_block(160, 210, 700, 50)\
            .add_block(160, 460, 820, 75)\
            .add_spikes(800, 340, 50, 110)\
            .add_flipper(810, 270, 0, 0, 'one', touchdisable = True, disabledelay = 100)\
            .add_spikes(600, 270, 50, 110)\
            .add_flipper(610, 420, 0, 0, 'two', touchdisable = True, disabledelay = 100)\
            .add_spikes(400, 340, 50, 110)\
            .add_flipper(410, 270, 0, 0, 'thr', touchdisable = True, disabledelay = 100)\
            .add_spikes(200, 270, 50, 110)\
            .add_flipper(210, 420, 0, 0, 'fou', touchdisable = True, disabledelay = 100)\
            .add_ground_spikes()\
            .add_block(10, 865, 200, 75)\
            .add_spikes(220, 700, 75, 240)\
            .add_block(305, 865, 200, 75)\
            .add_spikes(515, 700, 75, 240)\
            .add_block(600, 865, 200, 75)\
            .add_spikes(810, 700, 75, 240)\
            .set_goal(945, 560, 0, 0)\
            .unlock()
            
        self.levels[5]\
            .add_block(160, 160, 50, 630)\
            .add_block(160, 800, 50, 200, 'block')\
            .add_block(460, 10, 50, 830)\
            .add_spikes(220, 220, 110, 50)\
            .add_spikes(340, 370, 110, 50)\
            .add_spikes(220, 620, 110, 50)\
            .add_spikes(430, 940, 50, 50)\
            .add_spikes(750, 880, 240, 110)\
            .add_block(810, 820, 180, 50)\
            .add_spikes(750, 650, 50, 220, 'spikes')\
            .add_time_toggle('spikes', 1000)\
            .add_spikes(810, 650, 50, 50)\
            .add_spikes(940, 650, 50, 50)\
            .add_block(940, 590, 50, 50)\
            .add_pad(650, 470, 0, 0)\
            .add_block(755, 190, 235, 50)\
            .add_trigger(845, 10, 0, 0, 'block', enabled = True)\
            .add_block(0, 0, 0, 0)\
            .add_flipper(10, 990 - PLAYER_SIZE, 0, 0)\
            .add_block(120, 750, 30, 40)\
            .add_block(10, 550, 30, 40)\
            .add_block(120, 350, 30, 40)\
            .add_spikes(10, 750, 30, 40)\
            .add_spikes(120, 550, 30, 40)\
            .add_spikes(10, 350, 30, 40)\
            .set_goal(10, 220, 0, 0)
        
        try:
            unlocked = self.unlocked
        except AttributeError:
            unlocked = 0
            
        self.load_data()
        self.unlocked = max(unlocked, self.unlocked)
        
    def start_circle(self):
        self.canvas.delete('circle')
        
        if not self.settings.jump_circles:
            return
        
        self.circle_size += 1
        x, y = self.last_click
        x = self.proportion(x)
        y = self.proportion(y)
        
        step = max(9 - floor(self.circle_size / 5), 0)
        
        half = self.circle_size / 2
        player_half = PLAYER_SIZE / 2
        
        self.canvas.create_oval(x - half + player_half, y - half, x + half + player_half, y + half, fill = '', outline = fade_to_bg('#ababab', step), tag = 'circle')
        
        if not self.circle_size > 50:
            self.afters['jump-circle'] = self.root.after(10, self.start_circle)
        else:
            self.canvas.delete('circle')
            
    def show_blur(self):
        self.root.update_idletasks()
        
        width, height = self.root.winfo_width(), self.root.winfo_height()
        
        screen_middle = int(self.root.winfo_screenwidth() / 2 - width / 2)
        
        self.root.geometry(f'{width}x{height}+{screen_middle}+10')
        self.root.attributes('-topmost', 1)
        self.root.attributes('-topmost', 0)
        self.root.update()
        
        x, y = self.canvas.winfo_x() + self.root.winfo_rootx(), self.canvas.winfo_y() + self.root.winfo_rooty()
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        
        ss = pyautogui.screenshot(region=(x, y, width, height))
        blurimg = ss.filter(ImageFilter.GaussianBlur(radius = 20))
        self.ss = ImageTk.PhotoImage(image = blurimg)
        self.canvas.create_image(0, 0, image = self.ss, anchor = tk.NW, tag = 'img')
        
        self.canvas.update()
        pyautogui.screenshot(region = (x, y, width, height), imageFilename = 'last.png')
        w, h = width / 20, height / 4
        pyautogui.screenshot(region = (x + w, y + h, width - w, height - h), imageFilename = 'smaller.png')
            
    def die(self):
        def delete():
            self.canvas.delete('all')
            restart_btn.destroy()
            select_btn.destroy()
        
        def restart():
            delete()
            self.playing = True
            self.load_level(self.levels[self.current_level])
            self.start_game()
            
        def show_select():
            delete()
            self.show_select_menu()
        
        self.attempts[self.current_level] += 1
        self.show_blur()
        self.canvas.tag_raise('img')
        self.playing = False
        
        self.clear_afters()
            
        self.canvas.create_text(self.cwidth/2, self.cheight/3, anchor = CENTER, text = 'You Died', tag = 'img', font = self.big_font, fill = 'white')
        
        restart_btn = ttk.Button(self.canvas, text = 'Restart', style = 'Small.Accent.TButton', command = restart, width = 16)
        restart_btn.place(relx = 0.5, rely = 0.5, anchor = CENTER)
        
        select_btn = ttk.Button(self.canvas, text = 'Level Select Menu', style = 'Small.Accent.TButton', command = show_select, width = 16)
        select_btn.place(relx = 0.5, rely = 0.6, anchor = CENTER)
        
    def start_game(self):
        self.player     = [100, 100]
        self.y_speed    = 0
        self.x_speed    = 0
        self.jumps      = 0
        self.grounded   = False
        self.playing    = True
        self.paused     = False
        self.player_col = [10, 80, 80]
        
        self.clear_afters()

        self.afters = {}
        self.pressed = {RIGHT: False, LEFT: False, TOP: False}
        
        self.cwidth, self.cheight = self.canvas.winfo_width(), self.canvas.winfo_height()
        
        self.reset_levels()
        self.physics_loop()
        self.check_keys()
        
        if DEBUG:
            def p(e):
                print((e.x / self.canvas_size)*1000, (e.y / self.canvas_size)*1000)
            self.root.bind('<Button-1>', p)
        
    def test_player(self, element: LevelElement, check_floor = False, player = 'n'):
        if element.tag in self.disabled_tags:
            return False
        
        if player == 'n':
            player = self.player
        
        half = PLAYER_SIZE / 2
        players = [player, 
                   [player[0] + PLAYER_SIZE, player[1]], 
                   [player[0] + PLAYER_SIZE, player[1] + PLAYER_SIZE], 
                   [player[0], player[1] + PLAYER_SIZE], 
                   [player[0] + half, player[1] + half]]
        
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
        
        under_max = self.y_speed > -12
        if self.gravity == 1:
            under_max = self.y_speed < 12
        
        if under_max and not self.grounded:
            self.y_speed += 1 * self.gravity
            
        self.grounded = False
        
        STEPSIZE = 10
        
        def get_id(obj):
            return f'{obj.tag}+{obj.disable_delay}disable{obj.type}'
        
        def get_disable(obj: LevelElement):
            
            steps = obj.disable_delay / STEPSIZE
            id = get_id(obj)
            base_color = self.canvas.itemcget(obj.tag, 'fill')
            gradient = Color(base_color).range_to(fade_to_bg(base_color), int(steps))
            grad_list = [color.get_hex() for color in gradient]
            
            def disable(obj = obj, id = id, grad_list = grad_list, index = 0):
                try:
                    color = grad_list[index]
                except IndexError:
                    del self.afters[id]
                    self.disabled_tags.append(obj.tag)
                else:
                    self.canvas.itemconfig(obj.tag, fill = color, outline = darken(color))
                    self.afters[id] = self.root.after(STEPSIZE, disable, obj, id, grad_list, index + 1)
                    
            return disable
        
        for pad in self.level.pads:
            if self.test_player(pad):
                
                id = get_id(pad)
                if pad.touch_disable and not id in self.afters:
                    self.afters[id] = self.root.after(STEPSIZE, get_disable(pad))
                        
                self.y_speed = pad.jump_height * self.gravity
                self.jumps = 2
                    
        for flipper in self.level.flippers:
            if self.test_player(flipper):
                if time() - flipper.last_trigger > 0.5:
                    
                    id = get_id(flipper)
                    if flipper.touch_disable and not id in self.afters:
                        self.afters[id] = self.root.after(STEPSIZE, get_disable(flipper))
                        
                    self.gravity *= -1
                    flipper.last_trigger = time()
                    
        for coin in self.level.coins:
            if self.test_player(coin):
                self.canvas.itemconfigure(coin.tag, fill = '#ababab')
                self.disabled_tags.append(coin.tag)
                self.coins_collected += 1
        
        if self.y_speed != 0:
            move = self.y_speed / abs(self.y_speed)
            move *= -1
            
            self.player[1] += self.y_speed
            failed = False
            for block in self.level.blocks:
                test = False
                if self.test_player(block):
                    test = True
                while self.test_player(block, True):
                    self.player[1] += move
                    failed = True
                    if self.y_speed * self.gravity >= 0:
                        if move * self.gravity < 0:
                            self.grounded = True
                            self.jumps = 2
                    self.y_speed = self.gravity
                        
                if failed:
                    STEPSIZE = 10
                    id = get_id(block)
                    if block.touch_disable and test and not id in self.afters:
                        self.afters[id] = self.root.after(STEPSIZE, get_disable(block))  
                    break
                
            for spike in self.level.spikes:
                if self.test_player(spike):
                    self.die()
                    return
                
        if self.x_speed != 0:
            self.player[0] += self.x_speed
            move = self.x_speed / abs(self.x_speed)
            move *= -1
            for block in self.level.blocks:
                happened = False
                count = 0
                while self.test_player(block, True):
                            
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
                if time() - trigger.last_trigger > 0.5:
                    trigger.func()
                    trigger.last_trigger = time()
                    
                    id = get_id(trigger)
                    if trigger.touch_disable and not id in self.afters:
                        self.afters[id] = self.root.after(STEPSIZE, get_disable(trigger))
        
        if self.test_player(self.level.goal):
            self.touch_goal()
            return
        
        x, y = copy(self.player)
        x = self.proportion(x, False)
        y = self.proportion(y, False)
        size = self.proportion(PLAYER_SIZE)
        offset = abs(int((self.y_speed) / 2))
        
        hsl = self.player_col
        if self.settings.color_gradient:
            self.player_col[0] = (self.player_col[0] + 1) % 360
        
        rgb = colorsys.hls_to_rgb(hsl[0] / 360, hsl[2] / 100, hsl[1] / 100)
        r = int(rgb[0] * 255)
        g = int(rgb[1] * 255)
        b = int(rgb[2] * 255)
        color = f"#{r:02x}{g:02x}{b:02x}"
        
        self.round_rectangle(x + offset, y - offset, x + size - offset, y + size + offset, fill = color, tag = 'player', radius = 5)
        
        self.last = time()
        
        self.afters['physics'] = self.root.after(11, self.physics_loop)
        
    def clear_afters(self):
        for key in self.afters:
            self.root.after_cancel(key)
        self.afters = {}
        
    def win(self):
        self.clear_afters()
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
        
        def go_next():
            callback()
            self.current_level += 1
            if self.current_level in range(len(self.levels)):
                self.playing = True
                self.load_level(self.levels[self.current_level])
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
            self.load_level(self.levels[self.current_level])
            self.start_game()
            
        record = self.click_records[self.current_level]
        coin_record = self.coin_records[self.current_level]
        
        self.attempts[self.current_level] += 1
        
        if record == None or self.presses < record:
            self.click_records[self.current_level] = self.presses
            
        if self.coins_collected > coin_record:
            self.coin_records[self.current_level] = self.coins_collected
        
        self.show_blur()
        inc = self.cheight / 13
        lbl = lambda x, y, text, font, fill = 'white': self.canvas.create_text(x, y, text = text, font = font, tag = 'img', fill = fill, justify = CENTER)
        
        lbl(self.cwidth / 2, inc, f'You beat level {self.current_level + 1}', self.big_font)
        lbl(self.cwidth / 2, inc * 2, f'You won in {self.presses} clicks', self.small_font)
        lbl(self.cwidth / 2, inc * 3, f'Your record is {self.click_records[self.current_level]} clicks', self.small_font)
        if not len(self.level.coins) == 0:
            lbl(self.cwidth / 2, inc * 4, f'You got {self.coins_collected} out of {len(self.level.coins)} coins', self.small_font)
            lbl(self.cwidth / 2, inc * 5, f'Your record is {self.coin_records[self.current_level]} coins', self.small_font)
        
        lbl(self.cwidth / 2, self.cheight / 1.1, f'Total Attempts: {self.attempts[self.current_level]}', self.small_font)
        nextbtn = ttk.Button(self.canvas, text = 'Next Level', style = 'Small.Accent.TButton', command = go_next, width = 15)
        nextbtn.place(relx = 0.5, rely = 0.5, anchor = CENTER)
        selbtn = ttk.Button(self.canvas, text = 'Level Selection', style = 'Small.Accent.TButton', command = show_select, width = 15)
        selbtn.place(relx = 0.5, rely = 0.6, anchor = CENTER)
        restartbtn = ttk.Button(self.canvas, text = 'Restart', style = 'Small.Accent.TButton', command = restart, width = 15)
        restartbtn.place(relx = 0.5, rely = 0.7, anchor = CENTER)
        
    def pause(self):
        if not self.playing:
            return

        def callback():
            self.canvas.delete('all')
            restartbtn.destroy()
            selbtn.destroy()
            resbtn.destroy()
            
        def show_select():
            callback()
            for index in range(self.unlocked):
                self.levels[index].unlock()
            self.show_select_menu()
            
        def restart():
            for tag in self.afters:
                self.root.after_cancel(self.afters[tag])
            callback()
            self.playing = True
            self.paused = False
            self.load_level(self.levels[self.current_level])
            self.start_game()
            
        def resume():
            self.playing = True
            self.paused = False
            self.physics_loop()
            self.canvas.delete('img')
            restartbtn.destroy()
            selbtn.destroy()
            resbtn.destroy()
        
        self.root.after_cancel(self.afters['physics'])
        self.show_blur()
        self.playing = False
        self.paused = True
        self.canvas.create_text(self.cwidth / 2, self.cheight / 10, text = 'You Won', font = self.big_font, tag = 'img', fill = 'white')
        selbtn = ttk.Button(self.canvas, text = 'Level Selection', style = 'Small.Accent.TButton', command = show_select, width = 15)
        selbtn.place(relx = 0.5, rely = 0.6, anchor = CENTER)
        resbtn = ttk.Button(self.canvas, text = 'Resume', style = 'Small.Accent.TButton', command = resume, width = 15)
        resbtn.place(relx = 0.5, rely = 0.5, anchor = CENTER)
        restartbtn = ttk.Button(self.canvas, text = 'Restart', style = 'Small.Accent.TButton', command = restart, width = 15)
        restartbtn.place(relx = 0.5, rely = 0.7, anchor = CENTER)
        
    def load_level(self, lvl: Level):
        self.afters = {}
        self.disabled_tags = []
        self.canvas.delete('level', 'all')
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
            tag = ['level', coin.tag]
            x, y, width, height = coin.dimensions
            x += width / 2
            y += height / 2
            self.round_rectangle(*positions(coin.dimensions), fill = coin.color, tag = tag, radius = 5)
            self.canvas.create_text(x - 1, y - 1, font = self.mini_font, anchor = CENTER, tag = tag, text = '$', justify = CENTER)
            
        for toggle in draw_lvl.toggles:
            normal_col = self.canvas.itemcget(toggle.tag, 'fill')
            def callback(delay = toggle.delay, tag = toggle.tag, normal_col = normal_col):
                if not (self.playing or self.paused):
                    return
                object = None
                for obj in draw_lvl.blocks:
                    if obj.tag == tag:
                        object = obj
                if tag in self.disabled_tags:
                    self.canvas.itemconfigure(tag, fill = normal_col, outline = darken(normal_col))
                    if tag in self.disabled_tags:
                        self.disabled_tags.remove(tag)
                    if object != None and self.test_player(object):
                        self.die()
                        return
                else:
                    self.disabled_tags.append(tag)
                    color = fade_to_bg(normal_col)
                    self.canvas.itemconfigure(tag, fill = color, outline = darken(color))
                self.afters[f'{delay}.{tag}toggle'] = self.root.after(delay, callback, delay, tag)
            self.afters[f'{toggle.delay}.{toggle.tag}toggle'] = self.root.after(toggle.delay, callback, toggle.delay, toggle.tag, normal_col)
            
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
                if not (self.playing or self.paused):
                    return
                x, y = moves[count % len(moves)]
                
                if x != 0:
                    was_in = self.test_player(obj)
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
                        is_in = self.test_player(obj)
                        if not was_in and is_in:
                            self.player[0] += x
                        if is_in and was_in:
                            self.die()
                            return
                
                if y != 0:
                    was_in = self.test_player(obj)
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
                        is_in = self.test_player(obj)
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
            normal_col = self.canvas.itemcget(trig.disable_tag, 'fill')
            def callbacks(index = index, sprite = sprite, normal_col = normal_col):
                trig = self.level.triggers[index]
                if not (self.playing or self.paused):
                    return
                if trig.enabled:
                    self.level.triggers[index].enabled = False
                    col = trigger.color[0]
                    self.canvas.itemconfigure(sprite, fill = col, outline = darken(col))
                    color = fade_to_bg(normal_col)
                    self.canvas.itemconfigure(trig.disable_tag, fill = color, outline = darken(color))
                    self.disabled_tags.append(trig.disable_tag)
                else:
                    self.level.triggers[index].enabled = True
                    col = trigger.color[1]
                    self.canvas.itemconfigure(sprite, fill = col, outline = darken(col))
                    self.canvas.itemconfigure(trig.disable_tag, fill = normal_col, outline = darken(normal_col))
                    if trig.disable_tag in self.disabled_tags:
                        self.disabled_tags.remove(trig.disable_tag)
                        
            callbacks()
            callbacks()
                    
            trig.func = callbacks
        
        x, y, width, height = draw_lvl.goal.dimensions
        self.goal_img = ImageTk.PhotoImage(Image.open('goalflag.png').resize((width, height), resample = Image.LANCZOS))
        self.canvas.create_image(x, y, image = self.goal_img, tag = ('level', 'goal'), anchor = tk.NW)
        
    #https://stackoverflow.com/questions/44099594/how-to-make-a-tkinter-canvas-rectangle-with-rounded-corners
    def round_rectangle(self, x1, y1, x2, y2, radius = 5, **kwargs):
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
        
        bd = darken(kwargs['fill'])

        return self.canvas.create_polygon(points, **kwargs, smooth=True, outline = bd, width = 2, state = 'normal')
        
    def proportion(self, n, i = True):
        if type(n) is str:
            return n
        n = n/1000 * self.canvas_size
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
    
def fade_to_bg(color, step = 3):
    bg = Color('#1f1f1f')
    gradient = bg.range_to(color, 10)
    
    return next(x for i,x in enumerate(gradient) if i == step)
    
def darken(col, modifier = 0.8):
    color = Color(col)
    color.set_luminance(color.get_luminance() * modifier)
    return color.get_hex()

Game()