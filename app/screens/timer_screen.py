from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivy.clock import Clock
from kivy.metrics import dp


class TimerScreen(MDScreen):
    STATE_IDLE = 'IDLE'
    STATE_RUNNING = 'RUNNING'
    STATE_PAUSED = 'PAUSED'
    STATE_FINISHED = 'FINISHED'

    def __init__(self, **kwargs):
        super().__init__(name='timer', **kwargs)
        self._state = self.STATE_IDLE
        self._elapsed = 0          # seconds
        self._clock_event = None
        self._book = None
        self._vm = None
        self._build_ui()

    # ------------------------------------------------------------------ build

    def _build_ui(self):
        layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(24),
            padding=dp(32),
        )

        self.book_label = MDLabel(
            text='',
            halign='center',
            font_style='H6',
            size_hint_y=None,
            height=dp(40),
        )

        self.timer_label = MDLabel(
            text='00:00',
            halign='center',
            font_style='H2',
            size_hint_y=0.4,
        )

        btn_row = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(12),
            size_hint_y=None,
            height=dp(56),
        )

        self.start_btn = MDRaisedButton(text='Start', on_release=self._on_start)
        self.pause_btn = MDRaisedButton(text='Pause', on_release=self._on_pause, disabled=True)
        self.end_btn = MDRaisedButton(text='End Session', on_release=self._on_end, disabled=True)
        self.back_btn = MDRaisedButton(text='← Back', on_release=self._on_back)

        btn_row.add_widget(self.start_btn)
        btn_row.add_widget(self.pause_btn)
        btn_row.add_widget(self.end_btn)

        layout.add_widget(self.book_label)
        layout.add_widget(self.timer_label)
        layout.add_widget(btn_row)
        layout.add_widget(self.back_btn)
        self.add_widget(layout)

    # ------------------------------------------------------------------ API

    def set_book(self, book, vm):
        self._book = book
        self._vm = vm
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
        self._elapsed = 0
        self._state = self.STATE_IDLE
        self.timer_label.text = '00:00'
        self.start_btn.text = 'Start'
        self.start_btn.disabled = False
        self.pause_btn.disabled = True
        self.end_btn.disabled = True

    # ------------------------------------------------------------------ button handlers

    def _on_start(self, *args):
        if self._state == self.STATE_IDLE:
            self._state = self.STATE_RUNNING
            self._clock_event = Clock.schedule_interval(self._tick, 1)
            self.start_btn.disabled = True
            self.pause_btn.disabled = False
            self.end_btn.disabled = False

    def _on_pause(self, *args):
        if self._state == self.STATE_RUNNING:
            self._state = self.STATE_PAUSED
            self._clock_event.cancel()
            self.pause_btn.text = 'Resume'
        elif self._state == self.STATE_PAUSED:
            self._state = self.STATE_RUNNING
            self._clock_event = Clock.schedule_interval(self._tick, 1)
            self.pause_btn.text = 'Pause'

    def _on_end(self, *args):
        if self._state in (self.STATE_RUNNING, self.STATE_PAUSED):
            if self._clock_event:
                self._clock_event.cancel()
            self._state = self.STATE_FINISHED
            self._show_end_dialog()

    def _on_back(self, *args):
        self._reset()
        self.manager.current = 'home'

    def _show_end_dialog(self):
        book = self._book
        self.end_page_field = MDTextField(
            hint_text=f'End Page (current: {book.current_page})',
            input_filter='int',
        )
        self.end_error = MDLabel(text='', theme_text_color='Error', size_hint_y=None, height=dp(20))
        content = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(100),
            spacing=dp(8),
        )
        content.add_widget(self.end_page_field)
        content.add_widget(self.end_error)
        self._end_dialog = MDDialog(
            title='Session Complete',
            type='custom',
            content_cls=content,
            buttons=[
                MDRaisedButton(text='Cancel', on_release=lambda *a: self._cancel_end()),
                MDRaisedButton(text='Save', on_release=self._save_session),
            ],
        )
        self._end_dialog.open()

    def _cancel_end(self):
        self._end_dialog.dismiss()
        self._reset()

    def _save_session(self, *args):
        book = self._book
        try:
            ep = int(self.end_page_field.text or 0)
        except ValueError:
            self.end_error.text = 'Please enter a valid number.'
            return
        if ep <= book.current_page:
            self.end_error.text = 'End page must be > current page.'
            return
        if ep > book.total_pages:
            self.end_error.text = f'End page must be ≤ {book.total_pages}.'
            return
        minutes = max(1, self._elapsed // 60)
        try:
            self._vm.update_progress(ep, minutes)
        except ValueError as e:
            self.end_error.text = str(e)
            return
        self._end_dialog.dismiss()
        self._reset()
        self.manager.current = 'home'
