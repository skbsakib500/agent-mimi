import sys
from pathlib import Path
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window

from mimi.goals import list_goals
from mimi.tasks import list_tasks

Window.clearcolor = (0.05, 0.08, 0.14, 1)

class MimiLifeOSGUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=20, spacing=15, **kwargs)
        
        # Header Section
        header = Label(
            text="[b]AGENT MIMI[/b] | COMMAND CENTER v12.0",
            markup=True,
            font_size='22sp',
            size_hint_y=None,
            height=50,
            color=(0.2, 0.8, 1, 1)
        )
        self.add_widget(header)

        # Status Board
        self.status_box = GridLayout(cols=2, spacing=10, size_hint_y=None, height=100)
        self.refresh_metrics()
        self.add_widget(self.status_box)

        # Action Buttons
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        btn_refresh = Button(text="Sync Core Matrix", background_color=(0, 0.6, 0.8, 1))
        btn_refresh.bind(on_press=self.refresh_metrics)
        btn_layout.add_widget(btn_refresh)
        self.add_widget(btn_layout)

        # Dynamic Content View
        self.scroll = ScrollView()
        self.content_grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.content_grid.bind(minimum_height=self.content_grid.setter('height'))
        self.scroll.add_widget(self.content_grid)
        self.add_widget(self.scroll)

        self.load_active_data()

    def refresh_metrics(self, *args):
        self.status_box.clear_widgets()
        tasks = list_tasks()
        goals = list_goals()
        
        self.status_box.add_widget(Label(text=f"Active Tasks: [b]{len(tasks)}[/b]", markup=True, font_size='16sp'))
        self.status_box.add_widget(Label(text=f"Active Goals: [b]{len(goals)}[/b]", markup=True, font_size='16sp'))

    def load_active_data(self):
        self.content_grid.clear_widgets()
        tasks = list_tasks()
        
        self.content_grid.add_widget(Label(text="--- ACTIVE TASKS MATRIX ---", font_size='16sp', color=(1, 0.8, 0, 1), size_hint_y=None, height=30))
        
        if not tasks:
            self.content_grid.add_widget(Label(text="No active tasks in database.", size_hint_y=None, height=40))
        else:
            for t in tasks:
                item = Label(
                    text=f"• [{t[2].upper()}] {t[1]} (Status: {t[3]})",
                    size_hint_y=None,
                    height=40,
                    color=(0.9, 0.9, 0.9, 1)
                )
                self.content_grid.add_widget(item)

class AgentMimiApp(App):
    def build(self):
        self.title = "Agent Mimi - Life OS"
        return MimiLifeOSGUI()

if __name__ == "__main__":
    AgentMimiApp().run()
