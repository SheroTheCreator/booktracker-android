import datetime
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.uix.label import Label
from kivy.clock import Clock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class Divider(Widget):
    def __init__(self, **kwargs):
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', dp(1))
        super().__init__(**kwargs)
        with self.canvas:
            Color(0.85, 0.85, 0.85, 1)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self._rect.pos  = self.pos
        self._rect.size = self.size


class SmallBookCard(MDCard):
    def __init__(self, book=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size      = (dp(80), dp(110))
        self.radius    = [dp(8)]
        self.elevation = 1
        self.padding   = dp(6)
        self.orientation = 'vertical'
        cover = MDLabel(text='\U0001f4d6', halign='center', font_style='H5')
        title_text = (book.title[:12] + '...' if book and len(book.title) > 12
                      else (book.title if book else ''))
        lbl = MDLabel(text=title_text, halign='center', font_style='Caption',
                      size_hint_y=None, height=dp(28))
        self.add_widget(cover)
        self.add_widget(lbl)


# ---------------------------------------------------------------------------
# Snap Carousel
# ---------------------------------------------------------------------------

class SnapCarousel(ScrollView):
    """
    Horizontal scroll view that snaps to the nearest card
    and scales the active card to 1.0, others to 0.85.
    """
    CARD_W    = dp(160)
    CARD_GAP  = dp(16)
    SCALE_ACT = 1.0
    SCALE_INK = 0.85

    def __init__(self, on_select=None, **kwargs):
        kwargs.setdefault('do_scroll_x', True)
        kwargs.setdefault('do_scroll_y', False)
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', dp(250))
        kwargs.setdefault('bar_width', 0)
        super().__init__(**kwargs)
        self.on_select_cb = on_select
        self._books       = []
        self._selected_idx = 0

        self.inner = BoxLayout(
            orientation='horizontal',
            spacing=self.CARD_GAP,
            size_hint_x=None,
            padding=[dp(100), 0],
        )
        self.inner.bind(minimum_width=self.inner.setter('width'))
        self.add_widget(self.inner)

    def load_books(self, books, selected_id=None):
        self.inner.clear_widgets()
        self._books = books
        self._selected_idx = 0
        for i, book in enumerate(books):
            if selected_id and book.id == selected_id:
                self._selected_idx = i
            card = self._make_card(book, i)
            self.inner.add_widget(card)
        Clock.schedule_once(lambda dt: self._apply_scales(), 0.05)

    def _make_card(self, book, idx):
        card = MDCard(
            size_hint=(None, None),
            size=(self.CARD_W, dp(220)),
            padding=dp(10),
            spacing=dp(4),
            elevation=4,
            radius=[dp(14)],
            orientation='vertical',
        )
        cover  = MDLabel(text='\U0001f4da', halign='center',
                         font_style='H3', size_hint_y=0.6)
        title  = MDLabel(text=book.title,   halign='center',
                         font_style='Subtitle2', size_hint_y=0.25)
        author = MDLabel(text=book.author,  halign='center',
                         font_style='Caption', size_hint_y=0.15,
                         theme_text_color='Secondary')
        card.add_widget(cover)
        card.add_widget(title)
        card.add_widget(author)
        card.bind(on_release=lambda *a, i=idx, b=book: self._tap(i, b))
        return card

    def _tap(self, idx, book):
        self._selected_idx = idx
        self._apply_scales()
        self._scroll_to(idx)
        if self.on_select_cb:
            self.on_select_cb(book.id)

    def _apply_scales(self):
        for i, card in enumerate(self.inner.children[::-1]):
            target = self.SCALE_ACT if i == self._selected_idx else self.SCALE_INK
            Animation(scale=target, duration=0.2).start(card)

    def _scroll_to(self, idx):
        step = self.CARD_W + self.CARD_GAP
        total = step * len(self._books)
        if total <= 0:
            return
        target_x = step * idx
        max_scroll = max(0, total - self.width)
        if max_scroll == 0:
            return
        sx = min(target_x / max_scroll, 1.0)
        Animation(scroll_x=sx, duration=0.25, t='out_quad').start(self)

    def on_scroll_stop(self, touch, check_children=True):
        """Snap to nearest card when user lifts finger."""
        Clock.schedule_once(self._snap, 0.05)
        return super().on_scroll_stop(touch, check_children)

    def _snap(self, dt):
        if not self._books:
            return
        step = self.CARD_W + self.CARD_GAP
        total = step * len(self._books)
        max_scroll = max(0, total - self.width)
        if max_scroll == 0:
            return
        offset = self.scroll_x * max_scroll
        idx = max(0, min(round(offset / step), len(self._books) - 1))
        if idx != self._selected_idx and self._books:
            self._selected_idx = idx
            self._apply_scales()
            self._scroll_to(idx)
            if self.on_select_cb:
                self.on_select_cb(self._books[idx].id)


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

class UpdateProgressDialog:
    def __init__(self, current_page, total_pages, on_confirm):
        self.on_confirm   = on_confirm
        self.current_page = current_page
        self.total_pages  = total_pages
        self.end_page_field = MDTextField(
            hint_text=f'\u041a\u0456\u043d\u0446\u0435\u0432\u0430 \u0441\u0442\u043e\u0440\u0456\u043d\u043a\u0430 (\u0437\u0430\u0440\u0430\u0437: {current_page})',
            input_filter='int',
        )
        self.minutes_field = MDTextField(
            hint_text='\u0425\u0432\u0438\u043b\u0438\u043d \u0432\u0438\u0442\u0440\u0430\u0447\u0435\u043d\u043e',
            input_filter='int',
        )
        self.error_label = MDLabel(
            text='', theme_text_color='Error',
            size_hint_y=None, height=dp(20),
        )
        content = MDBoxLayout(orientation='vertical', spacing=dp(12),
                              size_hint_y=None, height=dp(160))
        content.add_widget(self.end_page_field)
        content.add_widget(self.minutes_field)
        content.add_widget(self.error_label)
        self.dialog = MDDialog(
            title='\u041e\u043d\u043e\u0432\u0438\u0442\u0438 \u043f\u0440\u043e\u0433\u0440\u0435\u0441',
            type='custom', content_cls=content,
            buttons=[
                MDFlatButton(text='\u0421\u043a\u0430\u0441\u0443\u0432\u0430\u0442\u0438',
                             on_release=lambda *a: self.dialog.dismiss()),
                MDRaisedButton(text='\u0417\u0431\u0435\u0440\u0435\u0433\u0442\u0438',
                               on_release=self._validate),
            ],
        )

    def _validate(self, *a):
        try:
            ep   = int(self.end_page_field.text or 0)
            mins = int(self.minutes_field.text  or 0)
        except ValueError:
            self.error_label.text = '\u0412\u0432\u0435\u0434\u0456\u0442\u044c \u043a\u043e\u0440\u0435\u043a\u0442\u043d\u0456 \u0447\u0438\u0441\u043b\u0430.'
            return
        if ep <= self.current_page:
            self.error_label.text = '\u0421\u0442\u043e\u0440\u0456\u043d\u043a\u0430 \u043c\u0430\u0454 \u0431\u0443\u0442\u0438 > \u043f\u043e\u0442\u043e\u0447\u043d\u043e\u0457.'
            return
        if ep > self.total_pages:
            self.error_label.text = f'\u041c\u0430\u043a\u0441 {self.total_pages} \u0441\u0442\u043e\u0440.'
            return
        if mins < 1:
            self.error_label.text = '\u041c\u0456\u043d\u0456\u043c\u0443\u043c 1 \u0445\u0432\u0438\u043b\u0438\u043d\u0430.'
            return
        self.dialog.dismiss()
        self.on_confirm(ep, mins)

    def open(self):
        self.dialog.open()


class AddQuoteDialog:
    def __init__(self, on_confirm):
        self.on_confirm = on_confirm
        self.text_field = MDTextField(
            hint_text='\u0412\u0432\u0435\u0434\u0456\u0442\u044c \u0446\u0438\u0442\u0430\u0442\u0443...',
            multiline=True, max_height=dp(120),
        )
        self.error_label = MDLabel(
            text='', theme_text_color='Error',
            size_hint_y=None, height=dp(20),
        )
        content = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(150))
        content.add_widget(self.text_field)
        content.add_widget(self.error_label)
        self.dialog = MDDialog(
            title='\u0414\u043e\u0434\u0430\u0442\u0438 \u0446\u0438\u0442\u0430\u0442\u0443',
            type='custom', content_cls=content,
            buttons=[
                MDFlatButton(text='\u0421\u043a\u0430\u0441\u0443\u0432\u0430\u0442\u0438',
                             on_release=lambda *a: self.dialog.dismiss()),
                MDRaisedButton(text='\u0417\u0431\u0435\u0440\u0435\u0433\u0442\u0438',
                               on_release=self._save),
            ],
        )

    def _save(self, *a):
        text = self.text_field.text.strip()
        if not text:
            self.error_label.text = '\u0426\u0438\u0442\u0430\u0442\u0430 \u043d\u0435 \u043c\u043e\u0436\u0435 \u0431\u0443\u0442\u0438 \u043f\u043e\u0440\u043e\u0436\u043d\u044c\u043e\u044e.'
            return
        self.dialog.dismiss()
        self.on_confirm(text)

    def open(self):
        self.dialog.open()


class AddBookDialog:
    """Dialog to create a new book (validates totalPages >= 1)."""
    def __init__(self, on_confirm):
        self.on_confirm   = on_confirm
        self.title_field  = MDTextField(hint_text='\u041d\u0430\u0437\u0432\u0430 \u043a\u043d\u0438\u0433\u0438')
        self.author_field = MDTextField(hint_text='\u0410\u0432\u0442\u043e\u0440')
        self.pages_field  = MDTextField(hint_text='\u041a\u0456\u043b\u044c\u043a\u0456\u0441\u0442\u044c \u0441\u0442\u043e\u0440\u0456\u043d\u043e\u043a', input_filter='int')
        self.status_field = MDTextField(
            hint_text='\u0421\u0442\u0430\u0442\u0443\u0441 (WISHLIST / READING / REREADING)',
            text='WISHLIST',
        )
        self.error_label  = MDLabel(
            text='', theme_text_color='Error',
            size_hint_y=None, height=dp(20),
        )
        content = MDBoxLayout(orientation='vertical', spacing=dp(10),
                              size_hint_y=None, height=dp(260))
        for w in [self.title_field, self.author_field,
                  self.pages_field, self.status_field, self.error_label]:
            content.add_widget(w)
        self.dialog = MDDialog(
            title='\u0414\u043e\u0434\u0430\u0442\u0438 \u043a\u043d\u0438\u0433\u0443',
            type='custom', content_cls=content,
            buttons=[
                MDFlatButton(text='\u0421\u043a\u0430\u0441\u0443\u0432\u0430\u0442\u0438',
                             on_release=lambda *a: self.dialog.dismiss()),
                MDRaisedButton(text='\u0414\u043e\u0434\u0430\u0442\u0438',
                               on_release=self._validate),
            ],
        )

    def _validate(self, *a):
        title  = self.title_field.text.strip()
        author = self.author_field.text.strip()
        try:
            pages = int(self.pages_field.text or 0)
        except ValueError:
            self.error_label.text = '\u0412\u0432\u0435\u0434\u0456\u0442\u044c \u0447\u0438\u0441\u043b\u043e \u0441\u0442\u043e\u0440\u0456\u043d\u043e\u043a.'
            return
        status = self.status_field.text.strip().upper()
        if not title:
            self.error_label.text = '\u041d\u0430\u0437\u0432\u0430 \u043e\u0431\u043e\u0432\u2019\u044f\u0437\u043a\u043e\u0432\u0430.'
            return
        if pages < 1:
            self.error_label.text = '\u041a\u043d\u0438\u0433\u0430 \u043f\u043e\u0432\u0438\u043d\u043d\u0430 \u043c\u0430\u0442\u0438 \u0445\u043e\u0447\u0430 \u0431 1 \u0441\u0442\u043e\u0440\u0456\u043d\u043a\u0443.'
            return
        if status not in ('WISHLIST', 'READING', 'REREADING', 'FINISHED'):
            self.error_label.text = '\u041d\u0435\u043a\u043e\u0440\u0435\u043a\u0442\u043d\u0438\u0439 \u0441\u0442\u0430\u0442\u0443\u0441.'
            return
        self.dialog.dismiss()
        self.on_confirm(title, author, pages, status)

    def open(self):
        self.dialog.open()


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------

class ReadingCalendar(BoxLayout):
    DAY_NAMES = ['\u041f', '\u0412', '\u0421', '\u0427', '\u041f', '\u0421', '\u041d']
    MONTH_UA  = ['', '\u0421\u0456\u0447\u0435\u043d\u044c', '\u041b\u044e\u0442\u0438\u0439', '\u0411\u0435\u0440\u0435\u0437\u0435\u043d\u044c',
                 '\u041a\u0432\u0456\u0442\u0435\u043d\u044c', '\u0422\u0440\u0430\u0432\u0435\u043d\u044c', '\u0427\u0435\u0440\u0432\u0435\u043d\u044c',
                 '\u041b\u0438\u043f\u0435\u043d\u044c', '\u0421\u0435\u0440\u043f\u0435\u043d\u044c', '\u0412\u0435\u0440\u0435\u0441\u0435\u043d\u044c',
                 '\u0416\u043e\u0432\u0442\u0435\u043d\u044c', '\u041b\u0438\u0441\u0442\u043e\u043f\u0430\u0434', '\u0413\u0440\u0443\u0434\u0435\u043d\u044c']

    def __init__(self, reading_days=None, **kwargs):
        kwargs.setdefault('orientation', 'vertical')
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('spacing', dp(4))
        super().__init__(**kwargs)
        self.reading_days = reading_days or set()
        self._build()

    def _build(self):
        self.clear_widgets()
        today = datetime.date.today()
        year, month = today.year, today.month

        header = BoxLayout(size_hint_y=None, height=dp(28))
        header.add_widget(Label(
            text='\u041a\u0430\u043b\u0435\u043d\u0434\u0430\u0440 \u0446\u0456\u043b\u0435\u0439',
            color=(0.2, 0.2, 0.2, 1), font_size=dp(13),
            halign='left', text_size=(dp(160), None),
        ))
        header.add_widget(Label(
            text=f'<{self.MONTH_UA[month]}>',
            color=(0.4, 0.4, 0.4, 1), font_size=dp(12),
            halign='right', text_size=(dp(100), None),
        ))
        self.add_widget(header)

        days_row = GridLayout(cols=7, size_hint_y=None, height=dp(24))
        for d in self.DAY_NAMES:
            days_row.add_widget(Label(text=d, font_size=dp(11), color=(0.5, 0.5, 0.5, 1)))
        self.add_widget(days_row)

        import calendar
        first_weekday  = datetime.date(year, month, 1).weekday()
        days_in_month  = calendar.monthrange(year, month)[1]
        rows           = (first_weekday + days_in_month + 6) // 7
        grid           = GridLayout(cols=7, size_hint_y=None, height=rows * dp(30))

        for _ in range(first_weekday):
            grid.add_widget(Label(text=''))

        for day in range(1, days_in_month + 1):
            is_read = day in self.reading_days
            is_today = (day == today.day)
            cell = BoxLayout()
            with cell.canvas.before:
                if is_read:
                    Color(1, 0.6, 0.6, 1)
                elif is_today:
                    Color(0.27, 0.35, 0.8, 0.25)
                else:
                    Color(0, 0, 0, 0)
                cell._bg = RoundedRectangle(pos=cell.pos, size=cell.size, radius=[dp(6)])
            cell.bind(
                pos=lambda w, v: setattr(w._bg, 'pos', v),
                size=lambda w, v: setattr(w._bg, 'size', v),
            )
            cell.add_widget(Label(
                text=str(day), font_size=dp(12),
                color=(0.6, 0.1, 0.1, 1) if is_read else
                      ((0.27, 0.35, 0.8, 1) if is_today else (0.15, 0.15, 0.15, 1)),
                bold=is_read or is_today,
            ))
            grid.add_widget(cell)

        self.add_widget(grid)
        self.height = dp(28) + dp(24) + grid.height + dp(12)

    def update_days(self, reading_days):
        self.reading_days = reading_days
        self._build()


# ---------------------------------------------------------------------------
# Bottom Nav
# ---------------------------------------------------------------------------

class BottomNavBar(BoxLayout):
    ITEMS = [
        ('book-open-variant', 'library'),
        ('chart-bar',         'stats'),
        ('home',              'home'),
        ('notebook',          'notes'),
        ('account',           'profile'),
    ]

    def __init__(self, screen_manager=None, **kwargs):
        kwargs.setdefault('orientation', 'horizontal')
        kwargs.setdefault('size_hint', (1, None))
        kwargs.setdefault('height', dp(56))
        kwargs.setdefault('spacing', 0)
        kwargs.setdefault('padding', 0)
        super().__init__(**kwargs)
        self.sm = screen_manager
        with self.canvas.before:
            Color(0.97, 0.97, 0.97, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos=lambda *a: setattr(self._bg, 'pos', self.pos),
            size=lambda *a: setattr(self._bg, 'size', self.size),
        )
        for icon, target in self.ITEMS:
            active = target == 'home'
            ic = (0.27, 0.35, 0.8, 1) if active else (0.45, 0.45, 0.45, 1)
            self.add_widget(MDIconButton(
                icon=icon, size_hint_x=1, size_hint_y=1,
                theme_icon_color='Custom', icon_color=ic,
                on_release=lambda *a, t=target: self._go(t),
            ))

    def _go(self, target):
        if self.sm and self.sm.has_screen(target):
            self.sm.current = target


# ---------------------------------------------------------------------------
# HomeScreen
# ---------------------------------------------------------------------------

class HomeScreen(MDScreen):
    def __init__(self, viewmodel, **kwargs):
        super().__init__(name='home', **kwargs)
        self.vm = viewmodel
        self.vm.observe(self._on_state_changed)
        self._build_ui()
        self._on_state_changed()

    def _build_ui(self):
        outer = MDBoxLayout(orientation='vertical')

        # Toolbar
        self.toolbar = MDTopAppBar(
            title="Read's diary",
            elevation=0,
            right_action_items=[
                ['plus', lambda *a: self._add_book()],
                ['magnify', lambda *a: None],
            ],
        )

        scroll = ScrollView()
        self.layout = MDBoxLayout(
            orientation='vertical', spacing=dp(14),
            padding=[dp(16), dp(8), dp(16), dp(16)],
            size_hint_y=None,
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))

        # 1. Snap Carousel
        self.carousel = SnapCarousel(on_select=self._on_book_selected)

        # Empty state
        self.empty_box = MDBoxLayout(
            orientation='vertical', size_hint_y=None, height=dp(250), spacing=dp(12),
        )
        self.empty_label = MDLabel(
            text='\u041d\u0435\u043c\u0430\u0454 \u043a\u043d\u0438\u0433 \u0443 \u043f\u0440\u043e\u0446\u0435\u0441\u0456 \u0447\u0438\u0442\u0430\u043d\u043d\u044f',
            halign='center', font_style='H6', theme_text_color='Secondary',
        )
        go_btn = MDRaisedButton(
            text='\u041f\u0435\u0440\u0435\u0439\u0442\u0438 \u0434\u043e \u0431\u0456\u0431\u043b\u0456\u043e\u0442\u0435\u043a\u0438',
            pos_hint={'center_x': 0.5}, on_release=self._go_library,
        )
        self.empty_box.add_widget(Widget())
        self.empty_box.add_widget(self.empty_label)
        self.empty_box.add_widget(go_btn)
        self.empty_box.add_widget(Widget())

        # 2. Progress block
        self.book_title_lbl = MDLabel(
            text='', font_style='Subtitle1', size_hint_y=None, height=dp(28),
        )
        prog_row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(22))
        self.pages_lbl = MDLabel(text='', font_style='Caption', theme_text_color='Secondary')
        self.pct_lbl   = MDLabel(text='', font_style='Caption', halign='right',
                                  theme_text_color='Secondary')
        prog_row.add_widget(self.pages_lbl)
        prog_row.add_widget(self.pct_lbl)
        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(8))

        # 3. Action buttons — full width
        action_row = MDBoxLayout(
            orientation='horizontal', spacing=dp(8),
            size_hint=(1, None), height=dp(52),
        )
        self.timer_btn  = MDRaisedButton(
            text='\u23f1', size_hint_x=1, on_release=self._start_reading,
        )
        self.update_btn = MDRaisedButton(
            text='\u041e\u043d\u043e\u0432\u0438\u0442\u0438 \u043f\u0440\u043e\u0433\u0440\u0435\u0441',
            size_hint_x=2, on_release=self._update_progress,
        )
        self.quote_btn  = MDRaisedButton(
            text='\u201c\u201d', size_hint_x=1, on_release=self._add_quote,
        )
        action_row.add_widget(self.timer_btn)
        action_row.add_widget(self.update_btn)
        action_row.add_widget(self.quote_btn)

        # 4. Goals row
        goals_row = MDBoxLayout(
            orientation='horizontal', spacing=dp(4),
            size_hint_y=None, height=dp(44),
        )
        self.daily_lbl   = MDLabel(text='\u0429\u043e\u0434\u0435\u043d\u043d\u0430\n0 \u0441\u0442\u043e\u0440.',
                                    font_style='Caption', halign='center')
        self.monthly_lbl = MDLabel(text='\u041c\u0456\u0441\u044f\u0446\u044c\n0/0',
                                    font_style='Caption', halign='center')
        self.yearly_lbl  = MDLabel(text='\u0420\u0456\u043a\n0/0',
                                    font_style='Caption', halign='center')
        for lbl in [self.daily_lbl, self.monthly_lbl, self.yearly_lbl]:
            goals_row.add_widget(lbl)

        # 5. Calendar
        self.calendar = ReadingCalendar(reading_days=set())

        # 6. Wishlist
        wl_header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(32))
        wl_header.add_widget(MDLabel(text='\u041f\u0440\u043e\u0447\u0438\u0442\u0430\u0442\u0438', font_style='Subtitle1'))
        self.wl_count_lbl = MDLabel(
            text='(0)', font_style='Caption',
            theme_text_color='Secondary', size_hint_x=None, width=dp(40),
        )
        wl_header.add_widget(self.wl_count_lbl)
        wl_header.add_widget(Widget())

        self.wl_scroll = ScrollView(
            do_scroll_x=True, do_scroll_y=False,
            size_hint_y=None, height=dp(120), bar_width=0,
        )
        self.wl_box = MDBoxLayout(
            orientation='horizontal', spacing=dp(10),
            size_hint_x=None, padding=[dp(2), 0],
        )
        self.wl_box.bind(minimum_width=self.wl_box.setter('width'))
        self.wl_scroll.add_widget(self.wl_box)

        # 7. Random button
        random_btn = MDRaisedButton(
            text='\U0001f3b2  \u0412\u0438\u043f\u0430\u0434\u043a\u043e\u0432\u043e',
            size_hint=(1, None), height=dp(48),
            on_release=self._pick_random,
        )

        for w in [
            self.carousel, self.empty_box,
            self.book_title_lbl, prog_row, self.progress_bar,
            action_row,
            Divider(), goals_row,
            Divider(), self.calendar,
            Divider(), wl_header, self.wl_scroll,
            random_btn,
        ]:
            self.layout.add_widget(w)

        scroll.add_widget(self.layout)
        self.nav_bar = BottomNavBar()
        outer.add_widget(self.toolbar)
        outer.add_widget(scroll)
        outer.add_widget(self.nav_bar)
        self.add_widget(outer)

    # ---------------------------------------------------------------- State

    def _on_state_changed(self):
        books    = self.vm.books
        finished = self.vm.finished_count
        fin_m    = self.vm.finished_month
        goal_y   = self.vm.yearly_goal
        goal_m   = self.vm.monthly_goal
        d_pages  = self.vm.daily_pages

        self.yearly_lbl.text  = f'\u0420\u0456\u043a\n{finished}/{goal_y}'
        self.monthly_lbl.text = f'\u041c\u0456\u0441\u044f\u0446\u044c\n{fin_m}/{goal_m}'
        self.daily_lbl.text   = f'\u0429\u043e\u0434\u0435\u043d\u043d\u0430\n{d_pages} \u0441\u0442\u043e\u0440.'

        if books:
            self.carousel.opacity     = 1
            self.carousel.height      = dp(250)
            self.empty_box.opacity    = 0
            self.empty_box.height     = 0
            selected_id = self.vm.selected_book.id if self.vm.selected_book else None
            self.carousel.load_books(books, selected_id)
            self._update_progress_block()
            for b in [self.timer_btn, self.update_btn, self.quote_btn]:
                b.disabled = False
        else:
            self.carousel.opacity     = 0
            self.carousel.height      = 0
            self.empty_box.opacity    = 1
            self.empty_box.height     = dp(250)
            self.book_title_lbl.text  = ''
            self.pages_lbl.text       = ''
            self.pct_lbl.text         = ''
            self.progress_bar.value   = 0
            for b in [self.timer_btn, self.update_btn, self.quote_btn]:
                b.disabled = True

        self.calendar.update_days(self.vm.reading_days)
        self._rebuild_wishlist()

    def _update_progress_block(self):
        book = self.vm.selected_book
        if not book:
            return
        total = book.total_pages or 1
        pct   = book.current_page / total
        self.book_title_lbl.text = book.title
        self.pages_lbl.text      = f'{book.current_page} / {book.total_pages} \u0441\u0442\u043e\u0440.'
        self.pct_lbl.text        = f'{int(pct * 100)}%'
        Animation(value=pct * 100, duration=0.4).start(self.progress_bar)

    def _rebuild_wishlist(self):
        self.wl_box.clear_widgets()
        try:
            from app.models.book import Book
            wl = list(Book.select().where(Book.status == 'WISHLIST').limit(30))
        except Exception:
            wl = []
        self.wl_count_lbl.text = f'({len(wl)})'
        for book in wl:
            self.wl_box.add_widget(SmallBookCard(book=book))
        if not wl:
            self.wl_box.add_widget(MDLabel(
                text='\u0421\u043f\u0438\u0441\u043e\u043a \u043f\u043e\u0440\u043e\u0436\u043d\u0456\u0439',
                theme_text_color='Secondary', font_style='Caption',
                size_hint_x=None, width=dp(160),
            ))

    # ---------------------------------------------------------------- Actions

    def _on_book_selected(self, book_id):
        self.vm.select_book(book_id)
        self._update_progress_block()

    def _start_reading(self, *a):
        book = self.vm.selected_book
        if book:
            timer = self.manager.get_screen('timer')
            timer.set_book(book, self.vm)
            self.manager.current = 'timer'

    def _update_progress(self, *a):
        book = self.vm.selected_book
        if book:
            UpdateProgressDialog(
                current_page=book.current_page,
                total_pages=book.total_pages,
                on_confirm=self._on_progress_confirmed,
            ).open()

    def _on_progress_confirmed(self, end_page, minutes):
        try:
            self.vm.update_progress(end_page, minutes)
        except ValueError as e:
            pass  # already validated in dialog

    def _add_quote(self, *a):
        AddQuoteDialog(on_confirm=self.vm.add_quote).open()

    def _add_book(self, *a):
        def _save(title, author, pages, status):
            try:
                self.vm.repo.create_book(title, author, pages, status)
                self.vm.refresh()
            except ValueError:
                pass
        AddBookDialog(on_confirm=_save).open()

    def _go_library(self, *a):
        if self.manager.has_screen('library'):
            self.manager.current = 'library'

    def _pick_random(self, *a):
        import random
        try:
            from app.models.book import Book
            books = list(Book.select().where(Book.status == 'WISHLIST'))
            if books:
                book = random.choice(books)
                from kivymd.uix.snackbar import Snackbar
                Snackbar(text=f'\u0427\u0438\u0442\u0430\u0439: {book.title}').open()
        except Exception:
            pass

    def on_enter(self, *a):
        self.vm.refresh()
        self.nav_bar.sm = self.manager
