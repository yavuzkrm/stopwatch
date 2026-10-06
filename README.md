# Stopwatch

A desktop stopwatch for focused study sessions, built with Python and PyQt6. I made it for myself: seeing the seconds tick by was distracting, so the timer can be hidden while it keeps running. Each finished session is saved, so you can see how much you studied on each day.

The interface is in Turkish.

## Features

- Start, pause and reset
- **Focus mode**: hide the elapsed time and show "Odaklan" (Focus) until you turn it back on
- **Target duration**: set a goal in minutes (1–600) and the timer stops when you reach it
- **Session history**: "Bitir" (Finish) saves the session to a local SQLite database. The history window shows the total time for each day.
- Custom dark theme and a toggle switch drawn with `QPainter`

## Running it

Requires Python 3.9+.

```bash
git clone https://github.com/yavuzkrm/stopwatch.git
cd stopwatch
pip install -r requirements.txt
python timer.py
```

Sessions are stored in `kronometre.db`, created in the folder you run the app from.

## Tech

- Python, PyQt6 (widgets, `QTimer`, custom-painted `QCheckBox`)
- SQLite (`sqlite3` from the standard library)

## License

This project is licensed under the [MIT License](LICENSE).
