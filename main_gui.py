import os
import sqlite3
from pathlib import Path

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.core.window import Window

from mimi.goals import list_goals
from mimi.tasks import list_tasks

# AMOLED Pure Black Theme Matrix
COLOR_BG = (0, 0, 0, 1)
COLOR_CARD = (0.05, 0.07, 0.12, 1)
COLOR_CYAN = (0.0, 0.94, 1.0, 1)
COLOR_PURPLE = (0.58, 0.2, 1.0, 1)
COLOR_GREEN = (0.0, 1.0, 0.5, 1)
COLOR_TEXT = (0.9, 0.95, 1.0, 1)
COLOR_MUTED = (0.4, 0.5, 0.6, 1)

Window.clearcolor = COLOR_BG

class AmoledCard(BoxLayout):
    """Custom Glassmorphism Card with Neon Borders"""
    def __init__(self, bg_color=COLOR_CARD, border_color=(0.0, 0.94, 1.0, 0.25), radius=[14], **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.border_color = border_color
        self.radius = radius
        self.bind(pos=self._render, size=self._render)

    def _render(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)
            Color(*self.border_color)
            Line(rounded_rectangle=(self.pos[0], self.pos[1], self.size[0], self.size[1], self.radius[0]), width=1.1)

class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name='dashboard', **kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=15)
        
        # System Metric Cards
        metrics = GridLayout(cols=2, spacing=12, size_hint_y=None, height=140)
        
        card1 = AmoledCard(orientation='vertical', padding=10)
        card1.add_widget(Label(text="ACTIVE TASKS", font_size='12sp', color=COLOR_MUTED))
        self.lbl_tasks = Label(text="0", font_size='26sp', bold=True, color=COLOR_CYAN)
        card1.add_widget(self.lbl_tasks)
        
        card2 = AmoledCard(orientation='vertical', padding=10)
        card2.add_widget(Label(text="ACTIVE GOALS", font_size='12sp', color=COLOR_MUTED))
        self.lbl_goals = Label(text="0", font_size='26sp', bold=True, color=COLOR_PURPLE)
        card2.add_widget(self.lbl_goals)

        metrics.add_widget(card1)
        metrics.add_widget(card2)
        layout.add_widget(metrics)

        # Core Engine Status
        status_card = AmoledCard(orientation='vertical', padding=15, size_hint_y=None, height=130)
        status_card.add_widget(Label(text="MIMI AGENT CORE STATUS", font_size='13sp', bold=True, color=COLOR_GREEN))
        status_card.add_widget(Label(text="● Neural Logic Matrix: ACTIVE\n● Database Bridge: CONNECTED\n● Auto-Trigger System: ONLINE", 
                                     font_size='12sp', color=COLOR_TEXT, halign='left'))
        layout.add_widget(status_card)
        
        layout.add_widget(Widget()) # Spacer
        self.add_widget(layout)

    def refresh(self):
        self.lbl_tasks.text = str(len(list_tasks()))
        self.lbl_goals.text = str(len(list_goals()))

class TasksScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name='tasks', **kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        layout.add_widget(Label(text="TASKS MATRIX", font_size='16sp', bold=True, color=COLOR_CYAN, size_hint_y=None, height=30))
        
        scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)
        
        layout.add_widget(scroll)
        self.add_widget(layout)

    def refresh(self):
        self.grid.clear_widgets()
        tasks = list_tasks()
        if not tasks:
            self.grid.add_widget(Label(text="No active tasks in database", color=COLOR_MUTED, size_hint_y=None, height=40))
        for t in tasks:
            card = AmoledCard(orientation='horizontal', padding=12, size_hint_y=None, height=55)
            card.add_widget(Label(text=f"[{t[2].upper()}] {t[1]}", color=COLOR_TEXT, halign='left'))
            card.add_widget(Label(text=t[3].upper(), color=COLOR_GREEN if t[3]=='active' else COLOR_MUTED, size_hint_x=0.3))
            self.grid.add_widget(card)

class AutomationsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name='automations', **kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="AUTOMATION & TRIGGERS", font_size='16sp', bold=True, color=COLOR_PURPLE, size_hint_y=None, height=30))
        
        triggers = [
            ("Auto-Sync Local DB", "Runs every 15 mins"),
            ("Audit Guardian Shield", "Monitors invalid modules"),
            ("Task Auto-Prioritizer", "Analyzes deadlines")
        ]
        
        for name, desc in triggers:
            card = AmoledCard(orientation='vertical', padding=12, size_hint_y=None, height=65)
            card.add_widget(Label(text=name, bold=True, color=COLOR_CYAN, font_size='14sp'))
            card.add_widget(Label(text=desc, color=COLOR_MUTED, font_size='11sp'))
            layout.add_widget(card)
            
        layout.add_widget(Widget())
        self.add_widget(layout)

class LifeOSMain(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        
        # Header Bar
        header = AmoledCard(orientation='horizontal', padding=[15, 5], size_hint_y=None, height=55, radius=[0,0,12,12])
        header.add_widget(Label(text="[b]AGENT MIMI[/b]  |  LIFE OS 2090", markup=True, font_size='16sp', color=COLOR_CYAN))
        self.add_widget(header)

        # Screen Navigation Manager
        self.sm = ScreenManager(transition=FadeTransition(duration=0.15))
        self.sc_dash = DashboardScreen()
        self.sc_tasks = TasksScreen()
        self.sc_auto = AutomationsScreen()

        self.sm.add_widget(self.sc_dash)
        self.sm.add_widget(self.sc_tasks)
        self.sm.add_widget(self.sc_auto)
        
        self.add_widget(self.sm)

        # Bottom AMOLED Navigation Bar
        nav = AmoledCard(orientation='horizontal', padding=5, spacing=5, size_hint_y=None, height=60, radius=[14,14,0,0])
        
        btn_dash = Button(text="Dashboard", background_color=(0,0,0,0), color=COLOR_CYAN)
        btn_dash.bind(on_press=lambda x: self.switch_tab('dashboard'))
        
        btn_tasks = Button(text="Tasks", background_color=(0,0,0,0), color=COLOR_MUTED)
        btn_tasks.bind(on_press=lambda x: self.switch_tab('tasks'))
        
        btn_auto = Button(text="Triggers", background_color=(0,0,0,0), color=COLOR_MUTED)
        btn_auto.bind(on_press=lambda x: self.switch_tab('automations'))

        self.nav_btns = {'dashboard': btn_dash, 'tasks': btn_tasks, 'automations': btn_auto}

        for b in self.nav_btns.values():
            nav.add_widget(b)

        self.add_widget(nav)
        self.switch_tab('dashboard')

    def switch_tab(self, name):
        self.sm.current = name
        for k, btn in self.nav_btns.items():
            btn.color = COLOR_CYAN if k == name else COLOR_MUTED
            
        if name == 'dashboard':
            self.sc_dash.refresh()
        elif name == 'tasks':
            self.sc_tasks.refresh()

class AgentMimiApp(App):
    def build(self):
        self.title = "Agent Mimi - Life OS 2090"
        return LifeOSMain()

if __name__ == "__main__":
    AgentMimiApp().run()
