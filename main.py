from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
import platform

from app.viewmodel.home_viewmodel import HomeViewModel
from app.screens.home_screen import HomeScreen
from app.screens.timer_screen import TimerScreen

# Phone-like window only on desktop (not on Android/iOS)
if platform.system() in ('Windows', 'Darwin', 'Linux'):
    PHONE_W = 390
    PHONE_H = 844
    Window.size = (PHONE_W, PHONE_H)
    Window.resizable = False


class BookTrackerApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = 'Indigo'
        self.theme_cls.theme_style = 'Light'

        self.vm = HomeViewModel()

        sm = ScreenManager()
        sm.add_widget(HomeScreen(viewmodel=self.vm))
        sm.add_widget(TimerScreen())

        return sm


if __name__ == '__main__':
    BookTrackerApp().run()
