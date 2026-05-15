# 📚 BookTracker Android

Android book tracking app built with **Python + Kivy/KivyMD**.

## Features (MVP v1.0 — Home Screen)
- 📖 Carousel of currently-reading books
- ⏱️ Reading session timer
- 📊 Per-book progress tracking
- 💬 Quote capture
- 🎯 Yearly reading goal
- ✅ Auto-finish book when last page reached

## Tech Stack
| Layer | Technology |
|---|---|
| UI | KivyMD (Material Design) |
| State | Python reactive ViewModel pattern |
| Database | SQLite via sqlite3 / peewee |
| Packaging | Buildozer (APK) |

## Project Structure
```
booktracker-android/
├── main.py                  # App entry point
├── buildozer.spec           # Android build config
├── requirements.txt
├── app/
│   ├── models/
│   │   ├── book.py          # Book, ReadingSession, Quote models
│   │   └── user_stats.py    # UserStats model
│   ├── repository/
│   │   └── repository.py    # DB operations
│   ├── viewmodel/
│   │   └── home_viewmodel.py
│   └── screens/
│       ├── home_screen.py
│       └── timer_screen.py
└── assets/
    └── placeholder_cover.png
```

## Run locally (desktop)
```bash
pip install -r requirements.txt
python main.py
```

## Build APK
```bash
pip install buildozer
buildozer android debug
```
