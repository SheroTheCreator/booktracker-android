from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle


class TimerScreen(MDScreen):
    STATE_IDLE     = 'IDLE'
    STATE_RUNNING  = 'RUNNING'
    STATE_PAUSED   = 'PAUSED'
    STATE_FINISHED = 'FINISHED'

    def __init__(self, **kwargs):
        super().__init__(name='timer', **kwargs)
        self._state        = self.STATE_IDLE
        self._elapsed      = 0
        self._clock_event  = None
        self._book         = None
        self._vm           = None
        self._end_dialog   = None
        self._build_ui()

    # ------------------------------------------------------------------ build

    def _build_ui(self):
        root = MDBoxLayout(orientation='vertical')

        # Toolbar-like header
        header = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=dp(56),
            padding=[dp(8), 0],
        )
        back_btn = MDRaisedButton(
            text='\u2190',
            size_hint=(None, None),
            size=(dp(48), dp(40)),
            on_release=self._on_back,
        )
        self.book_label = MDLabel(
            text='',
            halign='center',
            font_style='H6',
        )
        header.add_widget(back_btn)
        header.add_widget(self.book_label)
        header.add_widget(Widget(size_hint_x=None, width=dp(48)))

        # Timer display
        timer_box = MDBoxLayout(
            orientation='vertical',
            size_hint_y=0.5,
            padding=[0, dp(24)],
        )
        self.state_label = MDLabel(
            text='\u0413\u043e\u0442\u043e\u0432\u0438\u0439',
            halign='center',
            font_style='Subtitle1',
            theme_text_color='Secondary',
            size_hint_y=None, height=dp(28),
        )
        self.timer_label = MDLabel(
            text='00:00',
            halign='center',
            font_style='H1',
        )
        timer_box.add_widget(self.state_label)
        timer_box.add_widget(self.timer_label)

        # Buttons
        btn_box = MDBoxLayout(
            orientation='vertical',
            spacing=dp(12),
            padding=[dp(24), 0],
            size_hint_y=None,
            height=dp(180),
        )

        self.start_btn  = MDRaisedButton(
            text='\u25b6  \u0420\u043e\u0437\u043f\u043e\u0447\u0430\u0442\u0438',
            size_hint=(1, None), height=dp(48),
            on_release=self._on_start,
        )
        self.pause_btn  = MDRaisedButton(
            text='\u23f8  \u041f\u0430\u0443\u0437\u0430',
            size_hint=(1, None), height=dp(48),
            on_release=self._on_pause,
            disabled=True,
        )
        self.end_btn    = MDRaisedButton(
            text='\u23f9  \u0417\u0430\u0432\u0435\u0440\u0448\u0438\u0442\u0438 \u0441\u0435\u0441\u0456\u044e',
            size_hint=(1, None), height=dp(48),
            on_release=self._on_end,
            disabled=True,
            md_bg_color=(0.8, 0.2, 0.2, 1),
        )

        btn_box.add_widget(self.start_btn)
        btn_box.add_widget(self.pause_btn)
        btn_box.add_widget(self.end_btn)

        root.add_widget(header)
        root.add_widget(timer_box)
        root.add_widget(btn_box)
        root.add_widget(Widget())
        self.add_widget(root)

    # ------------------------------------------------------------------ API

    def set_book(self, book, vm):
        self._book = book
        self._vm   = vm
        self._reset()
        self.book_label.text = book.title

    # ------------------------------------------------------------------ timer

    def _tick(self, dt):
        self._elapsed += 1
        m, s = divmod(self._elapsed, 60)
        self.timer_label.text = f'{m:02d}:{s:02d}'

    def _reset(self):
        if self._clock_event:
            self._clock_event.cancel()
            self._clock_event = None
        self._elapsed           = 0
        self._state             = self.STATE_IDLE
        self.timer_label.text   = '00:00'
        self.state_label.text   = '\u0413\u043e\u0442\u043e\u0432\u0438\u0439'
        self.start_btn.text     = '\u25b6  \u0420\u043e\u0437\u043f\u043e\u0447\u0430\u0442\u0438'
        self.start_btn.disabled = False
        self.pause_btn.disabled = True
        self.pause_btn.text     = '\u23f8  \u041f\u0430\u0443\u0437\u0430'
        self.end_btn.disabled   = True

    # ------------------------------------------------------------------ handlers

    def _on_start(self, *a):
        if self._state == self.STATE_IDLE:
            self._state             = self.STATE_RUNNING
            self._clock_event       = Clock.schedule_interval(self._tick, 1)
            self.start_btn.disabled = True
            self.pause_btn.disabled = False
            self.end_btn.disabled   = False
            self.state_label.text   = '\u0427\u0438\u0442\u0430\u044e...'

    def _on_pause(self, *a):
        if self._state == self.STATE_RUNNING:
            self._state           = self.STATE_PAUSED
            self._clock_event.cancel()
            self.pause_btn.text   = '\u25b6  \u041f\u0440\u043e\u0434\u043e\u0432\u0436\u0438\u0442\u0438'
            self.state_label.text = '\u041f\u0430\u0443\u0437\u0430'
        elif self._state == self.STATE_PAUSED:
            self._state           = self.STATE_RUNNING
            self._clock_event     = Clock.schedule_interval(self._tick, 1)
            self.pause_btn.text   = '\u23f8  \u041f\u0430\u0443\u0437\u0430'
            self.state_label.text = '\u0427\u0438\u0442\u0430\u044e...'

    def _on_end(self, *a):
        if self._state in (self.STATE_RUNNING, self.STATE_PAUSED):
            if self._clock_event:
                self._clock_event.cancel()
                self._clock_event = None
            self._state           = self.STATE_FINISHED
            self.state_label.text = '\u0417\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u043e'
            self._show_end_dialog()

    def _on_back(self, *a):
        """Exit without saving — reset state (edge case from spec §9.3)."""
        if self._end_dialog:
            try:
                self._end_dialog.dismiss()
            except Exception:
                pass
        self._reset()
        self.manager.current = 'home'

    # ------------------------------------------------------------------ end dialog

    def _show_end_dialog(self):
        book = self._book
        self.end_page_field = MDTextField(
            hint_text=f'\u041a\u0456\u043d\u0446\u0435\u0432\u0430 \u0441\u0442\u043e\u0440\u0456\u043d\u043a\u0430 (\u0437\u0430\u0440\u0430\u0437: {book.current_page}, \u043c\u0430\u043a\u0441: {book.total_pages})',
            input_filter='int',
        )
        self.end_error = MDLabel(
            text='', theme_text_color='Error',
            size_hint_y=None, height=dp(20),
        )
        elapsed_min = max(1, self._elapsed // 60)
        time_info = MDLabel(
            text=f'\u0427\u0430\u0441 \u0441\u0435\u0441\u0456\u0457: {elapsed_min} \u0445\u0432.',
            font_style='Caption', theme_text_color='Secondary',
            size_hint_y=None, height=dp(20),
        )
        content = MDBoxLayout(
            orientation='vertical', spacing=dp(8),
            size_hint_y=None, height=dp(120),
        )
        content.add_widget(time_info)
        content.add_widget(self.end_page_field)
        content.add_widget(self.end_error)

        self._end_dialog = MDDialog(
            title='\u0421\u0435\u0441\u0456\u044f \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0430',
            type='custom', content_cls=content,
            buttons=[
                MDFlatButton(
                    text='\u0421\u043a\u0430\u0441\u0443\u0432\u0430\u0442\u0438',
                    on_release=lambda *a: self._cancel_end(),
                ),
                MDRaisedButton(
                    text='\u0417\u0431\u0435\u0440\u0435\u0433\u0442\u0438',
                    on_release=self._save_session,
                ),
            ],
        )
        self._end_dialog.open()

    def _cancel_end(self):
        """Cancel end dialog — reset timer (user stays on timer screen)."""
        self._end_dialog.dismiss()
        self._reset()

    def _save_session(self, *a):
        book = self._book
        try:
            ep = int(self.end_page_field.text or 0)
        except ValueError:
            self.end_error.text = '\u0412\u0432\u0435\u0434\u0456\u0442\u044c \u043a\u043e\u0440\u0435\u043a\u0442\u043d\u0435 \u0447\u0438\u0441\u043b\u043e.'
            return
        if ep <= book.current_page:
            self.end_error.text = '\u0421\u0442\u043e\u0440\u0456\u043d\u043a\u0430 \u043c\u0430\u0454 \u0431\u0443\u0442\u0438 > \u043f\u043e\u0442\u043e\u0447\u043d\u043e\u0457.'
            return
        if ep > book.total_pages:
            self.end_error.text = f'\u041c\u0430\u043a\u0441\u0438\u043c\u0443\u043c {book.total_pages}.'
            return
        minutes = max(1, self._elapsed // 60)
        try:
            self._vm.update_progress(ep, minutes)
        except ValueError as e:
            self.end_error.text = str(e)
            return
        self._end_dialog.dismiss()
        self._end_dialog = None
        self._reset()
        self.manager.current = 'home'
