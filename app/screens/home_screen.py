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
    """Card used in the wishlist row at the bottom."""
    def __init__(self, book=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(80), dp(110))
        self.radius = [dp(8)]
        self.elevation = 1
        self.padding = dp(6)
        self.orientation = 'vertical'
        lbl = MDLabel(
            text=book.title[:12] + '...' if book and len(book.title) > 12 else (book.title if book else ''),
            halign='center',
            font_style='Caption',
            size_hint_y=None,
            height=dp(30),
        )
        cover = MDLabel(
            text='📖',
            halign='center',
            font_style='H5',
        )
        self.add_widget(cover)
        self.add_widget(lbl)


class ActiveBookCard(MDCard):
    """Large card shown in the main carousel area."""
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

        cover = MDLabel(
            text='📚',
            halign='center',
            font_style='H3',
            size_hint_y=0.6,
        )
        title = MDLabel(
            text=book.title,
            halign='center',
            font_style='Subtitle2',
            size_hint_y=0.25,
        )
        author = MDLabel(
            text=book.author,
            halign='center',
            font_style='Caption',
            size_hint_y=0.15,
            theme_text_color='Secondary',
        )
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
            hint_text=f'Кінцева сторінка (зараз: {current_page})',
            input_filter='int',
        )
        self.minutes_field = MDTextField(
            hint_text='Хвилин витрачено',
            input_filter='int',
        )
        self.error_label = MDLabel(
            text='', theme_text_color='Error',
            size_hint_y=None, height=dp(20),
        )
        content = MDBoxLayout(
            orientation='vertical', spacing=dp(12),
            size_hint_y=None, height=dp(160),
        )
        content.add_widget(self.end_page_field)
        content.add_widget(self.minutes_field)
        content.add_widget(self.error_label)
        self.dialog = MDDialog(
            title='Оновити прогрес',
            type='custom',
            content_cls=content,
            buttons=[
                MDFlatButton(text='Скасувати', on_release=lambda *a: self.dialog.dismiss()),
                MDRaisedButton(text='Зберегти', on_release=self._validate),
            ],
        )

    def _validate(self, *args):
        try:
            ep = int(self.end_page_field.text or 0)
            mins = int(self.minutes_field.text or 0)
        except ValueError:
            self.error_label.text = 'Введіть коректні числа.'
            return
        if ep <= self.current_page:
            self.error_label.text = 'Сторінка має бути > поточної.'
            return
        if ep > self.total_pages:
            self.error_label.text = f'Максимум {self.total_pages} стор.'
            return
        if mins < 1:
            self.error_label.text = 'Мінімум 1 хвилина.'
            return
        self.dialog.dismiss()
        self.on_confirm(ep, mins)

    def open(self):
        self.dialog.open()


class AddQuoteDialog:
    def __init__(self, on_confirm):
        self.on_confirm = on_confirm
        self.text_field = MDTextField(
            hint_text='Введіть цитату...',
            multiline=True,
            max_height=dp(100),
        )
        content = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None, height=dp(120),
        )
        content.add_widget(self.text_field)
        self.dialog = MDDialog(
            title='Додати цитату',
            type='custom',
            content_cls=content,
            buttons=[
                MDFlatButton(text='Скасувати', on_release=lambda *a: self.dialog.dismiss()),
                MDRaisedButton(text='Зберегти', on_release=self._save),
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
    """Simple monthly calendar that highlights days with reading sessions."""

    DAY_NAMES = ['П', 'В', 'С', 'Ч', 'П', 'С', 'Н']
    MONTH_UA = [
        '', 'Січень', 'Лютий', 'Березень', 'Квітень', 'Травень',
        'Червень', 'Липень', 'Серпень', 'Вересень', 'Жовтень',
        'Листопад', 'Грудень',
    ]

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

        # Header row: month name
        header = BoxLayout(size_hint_y=None, height=dp(28))
        header.add_widget(Label(
            text='Календар цілей',
            color=(0.2, 0.2, 0.2, 1),
            font_size=dp(13),
            halign='left', text_size=(dp(160), None),
        ))
        header.add_widget(Label(
            text=f'<{self.MONTH_UA[month]}>',
            color=(0.4, 0.4, 0.4, 1),
            font_size=dp(12),
            halign='right', text_size=(dp(100), None),
        ))
        self.add_widget(header)

        # Day-name row
        days_row = GridLayout(cols=7, size_hint_y=None, height=dp(24))
        for d in self.DAY_NAMES:
            days_row.add_widget(Label(
                text=d, font_size=dp(11),
                color=(0.5, 0.5, 0.5, 1),
            ))
        self.add_widget(days_row)

        # Dates grid
        first_weekday = datetime.date(year, month, 1).weekday()  # 0=Mon
        import calendar
        days_in_month = calendar.monthrange(year, month)[1]

        grid = GridLayout(cols=7, size_hint_y=None)
        total_cells = first_weekday + days_in_month
        rows = (total_cells + 6) // 7
        grid.height = rows * dp(30)

        for _ in range(first_weekday):
            grid.add_widget(Label(text=''))

        for day in range(1, days_in_month + 1):
            is_read = day in self.reading_days
            cell = BoxLayout()
            with cell.canvas.before:
                if is_read:
                    Color(1, 0.7, 0.7, 1)
                else:
                    Color(0, 0, 0, 0)
                cell._bg = RoundedRectangle(pos=cell.pos, size=cell.size, radius=[dp(6)])
            cell.bind(
                pos=lambda w, v: setattr(w._bg, 'pos', v),
                size=lambda w, v: setattr(w._bg, 'size', v),
            )
            lbl = Label(
                text=str(day),
                font_size=dp(12),
                color=(0.15, 0.15, 0.15, 1) if not is_read else (0.6, 0.1, 0.1, 1),
                bold=is_read,
            )
            cell.add_widget(lbl)
            grid.add_widget(cell)

        self.add_widget(grid)
        self.height = dp(28) + dp(24) + grid.height + dp(12)

    def update_days(self, reading_days):
        self.reading_days = reading_days
        self._build()


# ---------------------------------------------------------------------------
# Bottom Nav Bar
# ---------------------------------------------------------------------------

class BottomNavBar(BoxLayout):
    ICONS = [
        ('book-open-variant', 'library'),
        ('chart-bar', 'stats'),
        ('home', 'home'),
        ('notebook', 'notes'),
        ('account', 'profile'),
    ]

    def __init__(self, screen_manager=None, **kwargs):
        kwargs.setdefault('orientation', 'horizontal')
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', dp(56))
        kwargs.setdefault('spacing', 0)
        super().__init__(**kwargs)
        self.sm = screen_manager
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *a: setattr(self._bg, 'pos', self.pos),
                  size=lambda *a: setattr(self._bg, 'size', self.size))
        for icon, target in self.ICONS:
            btn = MDIconButton(
                icon=icon,
                on_release=lambda *a, t=target: self._go(t),
                theme_icon_color='Custom',
                icon_color=(0.3, 0.3, 0.3, 1) if target != 'home' else (0.27, 0.35, 0.8, 1),
            )
            self.add_widget(btn)

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

    # ------------------------------------------------------------------ build

    def _build_ui(self):
        outer = MDBoxLayout(orientation='vertical')

        # ── Top App Bar ──────────────────────────────────────────────────────
        self.toolbar = MDTopAppBar(
            title="Read's diary",
            elevation=0,
            right_action_items=[
                ['magnify', lambda *a: None],
                ['cog-outline', lambda *a: None],
            ],
        )

        # ── Scrollable content ───────────────────────────────────────────────
        scroll = ScrollView()
        self.layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(14),
            padding=[dp(16), dp(8), dp(16), dp(16)],
            size_hint_y=None,
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))

        # 1. Carousel (active book + side books)
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
            text='Немає книг у процесі читання',
            halign='center', font_style='H6',
            theme_text_color='Secondary',
        )
        go_btn = MDRaisedButton(
            text='Перейти до бібліотеки',
            pos_hint={'center_x': 0.5},
            on_release=self._go_library,
        )
        self.empty_box.add_widget(Widget())
        self.empty_box.add_widget(self.empty_label)
        self.empty_box.add_widget(go_btn)
        self.empty_box.add_widget(Widget())

        # 2. Book title + progress info row
        self.book_title_label = MDLabel(
            text='',
            font_style='Subtitle1',
            size_hint_y=None, height=dp(28),
        )
        progress_info_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=dp(22),
        )
        self.pages_label = MDLabel(
            text='',
            font_style='Caption',
            theme_text_color='Secondary',
        )
        self.pct_label = MDLabel(
            text='',
            font_style='Caption',
            halign='right',
            theme_text_color='Secondary',
        )
        progress_info_row.add_widget(self.pages_label)
        progress_info_row.add_widget(self.pct_label)
        self.progress_bar = ProgressBar(
            max=100, value=0,
            size_hint_y=None, height=dp(8),
        )

        # 3. Action buttons row: timer | оновити прогрес | цитата
        action_row = MDBoxLayout(
            orientation='horizontal', spacing=dp(10),
            size_hint_y=None, height=dp(52),
        )
        self.timer_btn = MDIconButton(
            icon='timer-outline',
            on_release=self._start_reading,
            theme_icon_color='Custom',
            icon_color=(0.27, 0.35, 0.8, 1),
        )
        self.update_btn = MDRaisedButton(
            text='Оновити прогрес',
            on_release=self._update_progress,
        )
        self.quote_btn = MDIconButton(
            icon='format-quote-open',
            on_release=self._add_quote,
            theme_icon_color='Custom',
            icon_color=(0.27, 0.35, 0.8, 1),
        )
        action_row.add_widget(self.timer_btn)
        action_row.add_widget(self.update_btn)
        action_row.add_widget(self.quote_btn)

        # 4. Goals block: daily / monthly / yearly
        self.goals_row = MDBoxLayout(
            orientation='horizontal', spacing=dp(4),
            size_hint_y=None, height=dp(44),
        )
        self.daily_goal_lbl = MDLabel(
            text='Щоденна ціль\n— ст', font_style='Caption',
            halign='center',
        )
        self.monthly_goal_lbl = MDLabel(
            text='Мета на місяць\n0/1 книжок', font_style='Caption',
            halign='center',
        )
        self.yearly_goal_lbl = MDLabel(
            text='Мета на рік\n0/12 книжок', font_style='Caption',
            halign='center',
        )
        for lbl in [self.daily_goal_lbl, self.monthly_goal_lbl, self.yearly_goal_lbl]:
            self.goals_row.add_widget(lbl)

        # 5. Calendar
        self.calendar = ReadingCalendar(
            reading_days=set(),
        )

        # 6. Wishlist row
        wishlist_header = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=dp(28),
        )
        wishlist_header.add_widget(MDLabel(
            text='прочитати', font_style='Subtitle2',
        ))
        self.wishlist_count_lbl = MDLabel(
            text='(0)', font_style='Caption',
            theme_text_color='Secondary',
            halign='left',
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

        # 7. Random book button
        random_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=dp(52),
        )
        random_row.add_widget(Widget())
        random_btn = MDRaisedButton(
            text='🎲  Випадково',
            on_release=self._pick_random,
        )
        random_row.add_widget(random_btn)
        random_row.add_widget(Widget())

        # Assemble layout
        for w in [
            self.carousel_scroll,
            self.empty_box,
            self.book_title_label,
            progress_info_row,
            self.progress_bar,
            action_row,
            Divider(),
            self.goals_row,
            Divider(),
            self.calendar,
            Divider(),
            wishlist_header,
            self.wishlist_scroll,
            random_row,
        ]:
            self.layout.add_widget(w)

        scroll.add_widget(self.layout)

        # ── Bottom nav ───────────────────────────────────────────────────────
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

        # Goals row
        self.yearly_goal_lbl.text = f'Мета на рік\n{finished}/{goal} книжок'

        # Carousel
        if books:
            self.carousel_scroll.opacity = 1
            self.empty_box.opacity = 0
            self.empty_box.height = 0
            self._rebuild_carousel(books)
            self._update_progress_block()
            self.timer_btn.disabled = False
            self.update_btn.disabled = False
            self.quote_btn.disabled = False
        else:
            self.carousel_scroll.opacity = 0
            self.carousel_scroll.height = 0
            self.empty_box.opacity = 1
            self.empty_box.height = dp(250)
            self.book_title_label.text = ''
            self.pages_label.text = ''
            self.pct_label.text = ''
            self.progress_bar.value = 0
            self.timer_btn.disabled = True
            self.update_btn.disabled = True
            self.quote_btn.disabled = True

        # Calendar — highlight days that had sessions
        self._update_calendar()

        # Wishlist
        self._rebuild_wishlist()

    def _rebuild_carousel(self, books):
        self.carousel_box.clear_widgets()
        selected = self.vm.selected_book
        for book in books:
            card = ActiveBookCard(book=book, on_select=self._on_book_selected)
            if selected and book.id == selected.id:
                card.elevation = 8
            else:
                card.opacity = 0.75
            self.carousel_box.add_widget(card)

    def _update_progress_block(self):
        book = self.vm.selected_book
        if not book:
            return
        total = book.total_pages or 1
        pct = book.current_page / total
        self.book_title_label.text = book.title
        self.pages_label.text = f'{book.current_page} / {book.total_pages} стор.'
        self.pct_label.text = f'{int(pct * 100)}%'
        Animation(value=pct * 100, duration=0.4).start(self.progress_bar)

    def _update_calendar(self):
        try:
            from app.models.book import ReadingSession
            today = datetime.date.today()
            sessions = ReadingSession.select().where(
                ReadingSession.date.year == today.year,
                ReadingSession.date.month == today.month,
            )
            days = {s.date.day for s in sessions}
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
                text='Список порожній',
                theme_text_color='Secondary',
                font_style='Caption',
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
                Snackbar(text=f'Читай: {book.title}').open()
        except Exception:
            pass

    def on_enter(self, *args):
        """Refresh data every time screen becomes active."""
        self.vm.refresh()
        self.nav_bar.sm = self.manager
