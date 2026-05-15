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
from kivy.uix.button import Button


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
        self.bind(pos=self._update, size=self._update)

    def _update(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size


class SmallBookCard(MDCard):
    def __init__(self, book=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(80), dp(110))
        self.radius = [dp(8)]
        self.elevation = 1
        self.padding = dp(6)
        self.orientation = 'vertical'
        cover = MDLabel(text='\U0001f4d6', halign='center', font_style='H5')
        lbl = MDLabel(
            text=(book.title[:12] + '...' if book and len(book.title) > 12 else (book.title if book else '')),
            halign='center', font_style='Caption',
            size_hint_y=None, height=dp(30),
        )
        self.add_widget(cover)
        self.add_widget(lbl)


class ActiveBookCard(MDCard):
    def __init__(self, book, on_select, **kwargs):
        super().__init__(**kwargs)
        self.book = book
        self.size_hint = (None, None)
        self.size = (dp(160), dp(230))
        self.padding = dp(10)
        self.spacing = dp(4)
        self.elevation = 4
        self.radius = [dp(14)]
        self.orientation = 'vertical'
        cover = MDLabel(text='\U0001f4da', halign='center', font_style='H3', size_hint_y=0.6)
        title = MDLabel(text=book.title, halign='center', font_style='Subtitle2', size_hint_y=0.25)
        author = MDLabel(text=book.author, halign='center', font_style='Caption',
                         size_hint_y=0.15, theme_text_color='Secondary')
        self.add_widget(cover)
        self.add_widget(title)
        self.add_widget(author)
        self.bind(on_release=lambda *a: on_select(book.id))


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

class UpdateProgressDialog:
    def __init__(self, current_page, total_pages, on_confirm):
        self.on_confirm = on_confirm
        self.current_page = current_page
        self.total_pages = total_pages
        self.end_page_field = MDTextField(
            hint_text=f'\u041a\u0456\u043d\u0446\u0435\u0432\u0430 \u0441\u0442\u043e\u0440\u0456\u043d\u043a\u0430 (\u0437\u0430\u0440\u0430\u0437: {current_page})',
            input_filter='int',
        )
        self.minutes_field = MDTextField(
            hint_text='\u0425\u0432\u0438\u043b\u0438\u043d \u0432\u0438\u0442\u0440\u0430\u0447\u0435\u043d\u043e',
            input_filter='int',
        )
        self.error_label = MDLabel(text='', theme_text_color='Error', size_hint_y=None, height=dp(20))
        content = MDBoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None, height=dp(160))
        content.add_widget(self.end_page_field)
        content.add_widget(self.minutes_field)
        content.add_widget(self.error_label)
        self.dialog = MDDialog(
            title='\u041e\u043d\u043e\u0432\u0438\u0442\u0438 \u043f\u0440\u043e\u0433\u0440\u0435\u0441',
            type='custom', content_cls=content,
            buttons=[
                MDFlatButton(text='\u0421\u043a\u0430\u0441\u0443\u0432\u0430\u0442\u0438', on_release=lambda *a: self.dialog.dismiss()),
                MDRaisedButton(text='\u0417\u0431\u0435\u0440\u0435\u0433\u0442\u0438', on_release=self._validate),
            ],
        )

    def _validate(self, *args):
        try:
            ep = int(self.end_page_field.text or 0)
            mins = int(self.minutes_field.text or 0)
        except ValueError:
            self.error_label.text = '\u0412\u0432\u0435\u0434\u0456\u0442\u044c \u043a\u043e\u0440\u0435\u043a\u0442\u043d\u0456 \u0447\u0438\u0441\u043b\u0430.'
            return
        if ep <= self.current_page:
            self.error_label.text = '\u0421\u0442\u043e\u0440\u0456\u043d\u043a\u0430 \u043c\u0430\u0454 \u0431\u0443\u0442\u0438 > \u043f\u043e\u0442\u043e\u0447\u043d\u043e\u0457.'
            return
        if ep > self.total_pages:
            self.error_label.text = f'\u041c\u0430\u043a\u0441\u0438\u043c\u0443\u043c {self.total_pages} \u0441\u0442\u043e\u0440.'
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
            multiline=True, max_height=dp(100),
        )
        content = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(120))
        content.add_widget(self.text_field)
        self.dialog = MDDialog(
            title='\u0414\u043e\u0434\u0430\u0442\u0438 \u0446\u0438\u0442\u0430\u0442\u0443',
            type='custom', content_cls=content,
            buttons=[
                MDFlatButton(text='\u0421\u043a\u0430\u0441\u0443\u0432\u0430\u0442\u0438', on_release=lambda *a: self.dialog.dismiss()),
                MDRaisedButton(text='\u0417\u0431\u0435\u0440\u0435\u0433\u0442\u0438', on_release=self._save),
            ],
        )

    def _save(self, *args):
        text = self.text_field.text.strip()
        if text:
            self.dialog.dismiss()
            self.on_confirm(text)

    def open(self):
        self.dialog.open()


# ---------------------------------------------------------------------------
# Calendar Widget
# ---------------------------------------------------------------------------

class ReadingCalendar(BoxLayout):
    DAY_NAMES = ['\u041f', '\u0412', '\u0421', '\u0427', '\u041f', '\u0421', '\u041d']
    MONTH_UA = ['', '\u0421\u0456\u0447\u0435\u043d\u044c', '\u041b\u044e\u0442\u0438\u0439', '\u0411\u0435\u0440\u0435\u0437\u0435\u043d\u044c',
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
        header.add_widget(Label(text='\u041a\u0430\u043b\u0435\u043d\u0434\u0430\u0440 \u0446\u0456\u043b\u0435\u0439',
                                color=(0.2,0.2,0.2,1), font_size=dp(13),
                                halign='left', text_size=(dp(160), None)))
        header.add_widget(Label(text=f'<{self.MONTH_UA[month]}>',
                                color=(0.4,0.4,0.4,1), font_size=dp(12),
                                halign='right', text_size=(dp(100), None)))
        self.add_widget(header)
        days_row = GridLayout(cols=7, size_hint_y=None, height=dp(24))
        for d in self.DAY_NAMES:
            days_row.add_widget(Label(text=d, font_size=dp(11), color=(0.5,0.5,0.5,1)))
        self.add_widget(days_row)
        first_weekday = datetime.date(year, month, 1).weekday()
        import calendar
        days_in_month = calendar.monthrange(year, month)[1]
        grid = GridLayout(cols=7, size_hint_y=None)
        rows = (first_weekday + days_in_month + 6) // 7
        grid.height = rows * dp(30)
        for _ in range(first_weekday):
            grid.add_widget(Label(text=''))
        for day in range(1, days_in_month + 1):
            is_read = day in self.reading_days
            cell = BoxLayout()
            with cell.canvas.before:
                Color(1, 0.7, 0.7, 1) if is_read else Color(0, 0, 0, 0)
                cell._bg = RoundedRectangle(pos=cell.pos, size=cell.size, radius=[dp(6)])
            cell.bind(pos=lambda w,v: setattr(w._bg,'pos',v),
                      size=lambda w,v: setattr(w._bg,'size',v))
            cell.add_widget(Label(text=str(day), font_size=dp(12),
                                  color=(0.6,0.1,0.1,1) if is_read else (0.15,0.15,0.15,1),
                                  bold=is_read))
            grid.add_widget(cell)
        self.add_widget(grid)
        self.height = dp(28) + dp(24) + grid.height + dp(12)

    def update_days(self, reading_days):
        self.reading_days = reading_days
        self._build()


# ---------------------------------------------------------------------------
# Bottom Nav Bar  — займає всю ширину екрану
# ---------------------------------------------------------------------------

class NavButton(BoxLayout):
    """Single nav item: icon + optional label, expands equally."""
    def __init__(self, icon, target, active=False, on_tap=None, **kwargs):
        kwargs.setdefault('orientation', 'vertical')
        kwargs.setdefault('size_hint_x', 1)          # <-- fill equal share
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', dp(56))
        super().__init__(**kwargs)
        self._on_tap = on_tap
        color = (0.27, 0.35, 0.8, 1) if active else (0.45, 0.45, 0.45, 1)
        btn = MDIconButton(
            icon=icon,
            pos_hint={'center_x': 0.5},
            size_hint=(1, 1),
            theme_icon_color='Custom',
            icon_color=color,
            on_release=self._tap,
        )
        self.add_widget(btn)

    def _tap(self, *a):
        if self._on_tap:
            self._on_tap()


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
        kwargs.setdefault('size_hint', (1, None))     # <-- full width
        kwargs.setdefault('height', dp(56))
        kwargs.setdefault('spacing', 0)
        kwargs.setdefault('padding', 0)
        super().__init__(**kwargs)
        self.sm = screen_manager
        with self.canvas.before:
            Color(0.97, 0.97, 0.97, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *a: setattr(self._bg, 'pos', self.pos),
                  size=lambda *a: setattr(self._bg, 'size', self.size))
        self._build()

    def _build(self):
        self.clear_widgets()
        for icon, target in self.ITEMS:
            active = (target == 'home')
            self.add_widget(NavButton(
                icon=icon,
                target=target,
                active=active,
                on_tap=lambda t=target: self._go(t),
            ))

    def _go(self, target):
        if self.sm and self.sm.has_screen(target):
            self.sm.current = target


# ---------------------------------------------------------------------------
# Main HomeScreen
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

        self.toolbar = MDTopAppBar(
            title="Read's diary",
            elevation=0,
            right_action_items=[
                ['magnify', lambda *a: None],
                ['cog-outline', lambda *a: None],
            ],
        )

        scroll = ScrollView()
        self.layout = MDBoxLayout(
            orientation='vertical', spacing=dp(14),
            padding=[dp(16), dp(8), dp(16), dp(16)],
            size_hint_y=None,
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))

        # 1. Carousel
        self.carousel_scroll = ScrollView(
            do_scroll_x=True, do_scroll_y=False,
            size_hint_y=None, height=dp(250),
        )
        self.carousel_box = MDBoxLayout(
            orientation='horizontal', spacing=dp(12),
            size_hint_x=None, padding=[dp(4), 0],
        )
        self.carousel_box.bind(minimum_width=self.carousel_box.setter('width'))
        self.carousel_scroll.add_widget(self.carousel_box)

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
        self.book_title_label = MDLabel(
            text='', font_style='Subtitle1', size_hint_y=None, height=dp(28),
        )
        progress_info_row = MDBoxLayout(
            orientation='horizontal', size_hint_y=None, height=dp(22),
        )
        self.pages_label = MDLabel(text='', font_style='Caption', theme_text_color='Secondary')
        self.pct_label = MDLabel(text='', font_style='Caption', halign='right', theme_text_color='Secondary')
        progress_info_row.add_widget(self.pages_label)
        progress_info_row.add_widget(self.pct_label)
        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(8))

        # 3. Action buttons — уся ширина, рівні части
        action_row = MDBoxLayout(
            orientation='horizontal', spacing=dp(8),
            size_hint=(1, None), height=dp(52),
        )
        self.timer_btn = MDRaisedButton(
            text='\u23f1',
            size_hint_x=1,                           # <-- 1/3 ширини
            on_release=self._start_reading,
        )
        self.update_btn = MDRaisedButton(
            text='\u041e\u043d\u043e\u0432\u0438\u0442\u0438 \u043f\u0440\u043e\u0433\u0440\u0435\u0441',
            size_hint_x=2,                           # <-- 2/3 ширини
            on_release=self._update_progress,
        )
        self.quote_btn = MDRaisedButton(
            text='\u201c\u201d',
            size_hint_x=1,                           # <-- 1/3 ширини
            on_release=self._add_quote,
        )
        action_row.add_widget(self.timer_btn)
        action_row.add_widget(self.update_btn)
        action_row.add_widget(self.quote_btn)

        # 4. Goals row
        self.goals_row = MDBoxLayout(
            orientation='horizontal', spacing=dp(4),
            size_hint_y=None, height=dp(44),
        )
        self.daily_goal_lbl = MDLabel(
            text='\u0429\u043e\u0434\u0435\u043d\u043d\u0430 \u0446\u0456\u043b\u044c\n\u2014 \u0441\u0442',
            font_style='Caption', halign='center',
        )
        self.monthly_goal_lbl = MDLabel(
            text='\u041c\u0435\u0442\u0430 \u043d\u0430 \u043c\u0456\u0441\u044f\u0446\u044c\n0/1 \u043a\u043d\u0438\u0436\u043e\u043a',
            font_style='Caption', halign='center',
        )
        self.yearly_goal_lbl = MDLabel(
            text='\u041c\u0435\u0442\u0430 \u043d\u0430 \u0440\u0456\u043a\n0/12 \u043a\u043d\u0438\u0436\u043e\u043a',
            font_style='Caption', halign='center',
        )
        for lbl in [self.daily_goal_lbl, self.monthly_goal_lbl, self.yearly_goal_lbl]:
            self.goals_row.add_widget(lbl)

        # 5. Calendar
        self.calendar = ReadingCalendar(reading_days=set())

        # 6. Wishlist
        wishlist_header = MDBoxLayout(
            orientation='horizontal', size_hint_y=None, height=dp(28),
        )
        wishlist_header.add_widget(MDLabel(text='\u043f\u0440\u043e\u0447\u0438\u0442\u0430\u0442\u0438', font_style='Subtitle2'))
        self.wishlist_count_lbl = MDLabel(
            text='(0)', font_style='Caption',
            theme_text_color='Secondary', halign='left',
        )
        wishlist_header.add_widget(self.wishlist_count_lbl)
        wishlist_header.add_widget(Widget())
        self.wishlist_scroll = ScrollView(
            do_scroll_x=True, do_scroll_y=False,
            size_hint_y=None, height=dp(120),
        )
        self.wishlist_box = MDBoxLayout(
            orientation='horizontal', spacing=dp(10),
            size_hint_x=None, padding=[dp(4), 0],
        )
        self.wishlist_box.bind(minimum_width=self.wishlist_box.setter('width'))
        self.wishlist_scroll.add_widget(self.wishlist_box)

        # 7. Random button — вся ширина
        random_btn = MDRaisedButton(
            text='\U0001f3b2  \u0412\u0438\u043f\u0430\u0434\u043a\u043e\u0432\u043e',
            size_hint=(1, None), height=dp(48),
            on_release=self._pick_random,
        )

        for w in [
            self.carousel_scroll, self.empty_box,
            self.book_title_label, progress_info_row, self.progress_bar,
            action_row,
            Divider(), self.goals_row,
            Divider(), self.calendar,
            Divider(), wishlist_header, self.wishlist_scroll,
            random_btn,
        ]:
            self.layout.add_widget(w)

        scroll.add_widget(self.layout)

        self.nav_bar = BottomNavBar()

        outer.add_widget(self.toolbar)
        outer.add_widget(scroll)
        outer.add_widget(self.nav_bar)
        self.add_widget(outer)

    # ------------------------------------------------------------------ state

    def _on_state_changed(self):
        books = self.vm.books
        finished = self.vm.finished_count
        goal = self.vm.yearly_goal
        self.yearly_goal_lbl.text = f'\u041c\u0435\u0442\u0430 \u043d\u0430 \u0440\u0456\u043a\n{finished}/{goal} \u043a\u043d\u0438\u0436\u043e\u043a'
        if books:
            self.carousel_scroll.opacity = 1
            self.empty_box.opacity = 0
            self.empty_box.height = 0
            self._rebuild_carousel(books)
            self._update_progress_block()
            for b in [self.timer_btn, self.update_btn, self.quote_btn]:
                b.disabled = False
        else:
            self.carousel_scroll.opacity = 0
            self.carousel_scroll.height = 0
            self.empty_box.opacity = 1
            self.empty_box.height = dp(250)
            self.book_title_label.text = ''
            self.pages_label.text = ''
            self.pct_label.text = ''
            self.progress_bar.value = 0
            for b in [self.timer_btn, self.update_btn, self.quote_btn]:
                b.disabled = True
        self._update_calendar()
        self._rebuild_wishlist()

    def _rebuild_carousel(self, books):
        self.carousel_box.clear_widgets()
        selected = self.vm.selected_book
        for book in books:
            card = ActiveBookCard(book=book, on_select=self._on_book_selected)
            if not (selected and book.id == selected.id):
                card.opacity = 0.75
            self.carousel_box.add_widget(card)

    def _update_progress_block(self):
        book = self.vm.selected_book
        if not book:
            return
        total = book.total_pages or 1
        pct = book.current_page / total
        self.book_title_label.text = book.title
        self.pages_label.text = f'{book.current_page} / {book.total_pages} \u0441\u0442\u043e\u0440.'
        self.pct_label.text = f'{int(pct * 100)}%'
        Animation(value=pct * 100, duration=0.4).start(self.progress_bar)

    def _update_calendar(self):
        try:
            from app.models.book import ReadingSession
            today = datetime.date.today()
            sessions = ReadingSession.select().where(
                ReadingSession.date >= datetime.date(today.year, today.month, 1)
            )
            days = {s.date.day for s in sessions if s.date.month == today.month}
        except Exception:
            days = set()
        self.calendar.update_days(days)

    def _rebuild_wishlist(self):
        self.wishlist_box.clear_widgets()
        try:
            from app.models.book import Book
            wishlist = list(Book.select().where(Book.status == 'WISHLIST').limit(20))
        except Exception:
            wishlist = []
        self.wishlist_count_lbl.text = f'({len(wishlist)})'
        for book in wishlist:
            self.wishlist_box.add_widget(SmallBookCard(book=book))
        if not wishlist:
            self.wishlist_box.add_widget(MDLabel(
                text='\u0421\u043f\u0438\u0441\u043e\u043a \u043f\u043e\u0440\u043e\u0436\u043d\u0456\u0439',
                theme_text_color='Secondary', font_style='Caption',
                size_hint_x=None, width=dp(160),
            ))

    # ------------------------------------------------------------------ actions

    def _on_book_selected(self, book_id):
        self.vm.select_book(book_id)

    def _start_reading(self, *args):
        book = self.vm.selected_book
        if book:
            timer = self.manager.get_screen('timer')
            timer.set_book(book, self.vm)
            self.manager.current = 'timer'

    def _update_progress(self, *args):
        book = self.vm.selected_book
        if book:
            UpdateProgressDialog(
                current_page=book.current_page,
                total_pages=book.total_pages,
                on_confirm=self.vm.update_progress,
            ).open()

    def _add_quote(self, *args):
        AddQuoteDialog(on_confirm=self.vm.add_quote).open()

    def _go_library(self, *args):
        if self.manager.has_screen('library'):
            self.manager.current = 'library'

    def _pick_random(self, *args):
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

    def on_enter(self, *args):
        self.vm.refresh()
        self.nav_bar.sm = self.manager
