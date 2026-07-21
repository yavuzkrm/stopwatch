import sqlite3
import sys
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QDialog, QInputDialog, QWidget, QLabel,
                              QPushButton, QVBoxLayout, QHBoxLayout, QCheckBox,
                              QScrollArea)
from PyQt6.QtCore import QSize, QTimer, QTime, Qt
from PyQt6.QtGui import QPainter, QColor

# ── Renk Paleti ──────────────────────────────────────────────────────────────
BG          = "#0D0D0F"
SURFACE     = "#18181C"
SURFACE2    = "#222228"
BORDER      = "#2E2E38"
TEXT_PRI    = "#F0F0F4"
TEXT_SEC    = "#888896"
TEXT_MUTED  = "#555560"
ACCENT      = "#5B8AF0"
ACCENT_DIM  = "#1E2D52"
SUCCESS     = "#3ECF8E"
SUCCESS_DIM = "#0E3828"
DANGER      = "#E5534B"
DANGER_DIM  = "#3D1410"
WHITE       = "#FFFFFF"

DB_PATH = "kronometre.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT,
            record_date TEXT DEFAULT (date('now'))
        )
    """)
    conn.commit()
    conn.close()


def seconds_from_str(t):
    """hh:mm:ss → saniye"""
    h, m, s = map(int, t.split(":"))
    return h * 3600 + m * 60 + s


def seconds_to_str(total):
    """saniye → hh:mm:ss"""
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


# ── Geçmiş Penceresi ─────────────────────────────────────────────────────────
"""Ben yazamadım çok zordu :("""
class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kayıt Geçmişi")
        self.setFixedSize(420, 500)
        self.setStyleSheet(f"""
            QDialog, QWidget {{
                background-color: {BG};
                color: {TEXT_PRI};
                font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
            }}
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {SURFACE};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER};
                border-radius: 3px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("📋  Kayıt Geçmişi")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {TEXT_PRI};")
        layout.addWidget(title)

        # Ayırıcı
        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER};")
        layout.addWidget(sep)

        # Scroll alanı
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.rows_layout = QVBoxLayout(container)
        self.rows_layout.setSpacing(8)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll)

        self.load_records()

    def load_records(self):
        # Önceki satırları temizle (stretch hariç)
        while self.rows_layout.count() > 1:
            item = self.rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT record_date, SUM(
                CAST(SUBSTR(time,1,2) AS INTEGER)*3600 +
                CAST(SUBSTR(time,4,2) AS INTEGER)*60  +
                CAST(SUBSTR(time,7,2) AS INTEGER)
            ) as total_seconds
            FROM records
            GROUP BY record_date
            ORDER BY record_date DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            empty = QLabel("Henüz kayıt yok.")
            empty.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.rows_layout.insertWidget(0, empty)
            return

        for i, (date_str, total_sec) in enumerate(rows):
            # Tarihi Türkçe formatla
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                AYLAR = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran",
                         "Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
                label_date = f"{dt.day} {AYLAR[dt.month-1]} {dt.year}"
            except Exception:
                label_date = date_str

            total_str = seconds_to_str(total_sec or 0)

            row = QWidget()
            row.setStyleSheet(f"""
                QWidget {{
                    background-color: {SURFACE};
                    border: 1px solid {BORDER};
                    border-radius: 10px;
                }}
            """)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(16, 12, 16, 12)

            date_label = QLabel(label_date)
            date_label.setStyleSheet(f"font-size: 14px; color: {TEXT_PRI}; background: transparent; border: none;")

            time_label = QLabel(total_str)
            time_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {ACCENT}; background: transparent; border: none;")
            time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            row_layout.addWidget(date_label)
            row_layout.addStretch()
            row_layout.addWidget(time_label)

            self.rows_layout.insertWidget(i, row)


# ── Toggle Switch ─────────────────────────────────────────────────────────────
class ModernSwitch(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setChecked(True)

    def paintEvent(self, event):
        bg_color = QColor(ACCENT) if self.isChecked() else QColor(SURFACE2)
        circle_color = QColor(WHITE)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        painter.setBrush(bg_color)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2)

        x_pos = (self.width() - self.height() + 3) if self.isChecked() else 3
        painter.setBrush(circle_color)
        painter.drawEllipse(int(x_pos), 3, self.height() - 6, self.height() - 6)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self.isChecked())
            self.update()


# ── Ana Pencere ───────────────────────────────────────────────────────────────
class StopWatch(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(QSize(480, 500))
        self.elapsed_time = QTime(0, 0, 0)

        self.time_label   = QLabel("00:00:00", self)
        self.status_label = QLabel("Hazır", self)

        self.start_button   = QPushButton("▶  Başlat", self)
        self.reset_button   = QPushButton("↺  Sıfırla", self)
        self.target_button  = QPushButton("🎯  Hedef", self)
        self.save_button    = QPushButton("✓  Bitir", self)
        self.history_button = QPushButton("📋  Geçmiş", self)
        self._running = False

        self.timer = QTimer(self)

        self.switch_label  = QLabel("Süreyi göster", self)
        self.toggle_switch = ModernSwitch(self)

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Kronometre")

        outer = QVBoxLayout()
        outer.setContentsMargins(32, 32, 32, 28)
        outer.setSpacing(0)

        # Zaman ekranı
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setObjectName("timeLabel")
        outer.addWidget(self.time_label)

        # Durum satırı
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("statusLabel")
        outer.addWidget(self.status_label)

        outer.addSpacing(20)

        # Switch
        switch_row = QHBoxLayout()
        switch_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        switch_row.setSpacing(10)
        switch_row.addWidget(self.switch_label)
        switch_row.addWidget(self.toggle_switch)
        outer.addLayout(switch_row)

        outer.addSpacing(24)

        # Separator
        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER};")
        outer.addWidget(sep)

        outer.addSpacing(24)

        # Birincil buton
        primary_row = QHBoxLayout()
        primary_row.setSpacing(10)
        primary_row.addWidget(self.start_button)
        outer.addLayout(primary_row)

        outer.addSpacing(10)

        # İkincil butonlar
        secondary_row = QHBoxLayout()
        secondary_row.setSpacing(10)
        secondary_row.addWidget(self.reset_button)
        secondary_row.addWidget(self.target_button)
        secondary_row.addWidget(self.save_button)
        outer.addLayout(secondary_row)

        outer.addSpacing(10)

        # Geçmiş butonu
        history_row = QHBoxLayout()
        history_row.setSpacing(10)
        history_row.addWidget(self.history_button)
        outer.addLayout(history_row)

        self.setLayout(outer)

        # Stil
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG};
                color: {TEXT_PRI};
                font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
            }}

            #timeLabel {{
                font-size: 58px;
                font-weight: 700;
                letter-spacing: 4px;
                color: {TEXT_PRI};
                padding: 8px 0 4px 0;
            }}

            #statusLabel {{
                font-size: 13px;
                color: {TEXT_MUTED};
                letter-spacing: 1px;
                text-transform: uppercase;
                padding-bottom: 4px;
            }}

            QLabel {{
                font-size: 13px;
                color: {TEXT_SEC};
            }}

            QPushButton#startBtn {{
                background-color: {ACCENT};
                color: {WHITE};
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 15px;
                font-weight: 600;
            }}
            QPushButton#startBtn:hover {{ background-color: #7aa3f5; }}
            QPushButton#startBtn:pressed {{ background-color: #4a72c8; }}

            QPushButton#secondaryBtn {{
                background-color: {SURFACE};
                color: {TEXT_SEC};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }}
            QPushButton#secondaryBtn:hover {{
                background-color: {SURFACE2};
                color: {TEXT_PRI};
                border-color: #444450;
            }}
            QPushButton#secondaryBtn:pressed {{ background-color: {SURFACE2}; }}

            QPushButton#saveBtn {{
                background-color: {SUCCESS_DIM};
                color: {SUCCESS};
                border: 1px solid {SUCCESS};
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton#saveBtn:hover {{ background-color: #164030; }}

            QPushButton#historyBtn {{
                background-color: {SURFACE};
                color: {TEXT_SEC};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }}
            QPushButton#historyBtn:hover {{
                background-color: {SURFACE2};
                color: {TEXT_PRI};
                border-color: #444450;
            }}
        """)

        self.start_button.setObjectName("startBtn")
        self.reset_button.setObjectName("secondaryBtn")
        self.target_button.setObjectName("secondaryBtn")
        self.save_button.setObjectName("saveBtn")
        self.history_button.setObjectName("historyBtn")

        self.start_button.setMinimumHeight(46)
        self.reset_button.setMinimumHeight(40)
        self.target_button.setMinimumHeight(40)
        self.save_button.setMinimumHeight(40)
        self.history_button.setMinimumHeight(40)

        self.start_button.clicked.connect(self.toggle_start_stop)
        self.reset_button.clicked.connect(self.reset)
        self.timer.timeout.connect(self.format_time)
        self.toggle_switch.toggled.connect(self.update_time_display)
        self.target_button.clicked.connect(self.get_goal_time)
        self.save_button.clicked.connect(self.save_time)
        self.history_button.clicked.connect(self.show_history)

    def set_status(self, text):
        self.status_label.setText(text)

    def toggle_start_stop(self):
        if self._running:
            self.timer.stop()
            self._running = False
            self.start_button.setText("▶  Başlat")
            self.start_button.setObjectName("startBtn")
            self.start_button.style().unpolish(self.start_button)
            self.start_button.style().polish(self.start_button)
            self.set_status("Duraklatıldı")
        else:
            self.timer.start(1000)
            self._running = True
            self.start_button.setText("⏸  Durdur")
            self.set_status("Çalışıyor")

    def start(self):
        self.timer.start(1000)
        self._running = True

    def stop(self):
        self.timer.stop()
        self._running = False

    def reset(self):
        self.elapsed_time = QTime(0, 0, 0)
        self.timer.stop()
        self._running = False
        self.start_button.setText("▶  Başlat")
        self.set_status("Hazır")
        self.update_time_display()

    def format_time(self):
        self.elapsed_time = self.elapsed_time.addMSecs(1000)
        self.update_time_display()
        self.check_goal_time()

    def update_time_display(self):
        if self.toggle_switch.isChecked():
            self.time_label.setText(self.elapsed_time.toString("hh:mm:ss"))
        else:
            self.time_label.setText("🎯 Odaklan")

    def get_goal_time(self):
        self.goal_time, ok = QInputDialog.getInt(
            self, "Hedef Süre", "Hedef süreyi dakika cinsinden girin:", 60, 1, 600, 1)
        if not ok:
            if hasattr(self, 'goal_time'):
                del self.goal_time
        else:
            self.set_status(f"Hedef: {self.goal_time} dk")

    def check_goal_time(self):
        if hasattr(self, 'goal_time'):
            elapsed_seconds = self.elapsed_time.msecsSinceStartOfDay() // 1000
            goal_seconds = self.goal_time * 60
            if elapsed_seconds >= goal_seconds:
                self.timer.stop()
                self._running = False
                self.start_button.setText("▶  Başlat")
                self.time_label.setText("🎯 Hedefe Ulaşıldı!")
                self.set_status("Tamamlandı")

    def save_time(self):
        self.timer.stop()
        time_str = self.elapsed_time.toString("hh:mm:ss")
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO records (time, record_date) VALUES (?, ?)",
                (time_str, today)
            )
            conn.commit()
            conn.close()
            self.time_label.setText("Kaydedildi")
            self.set_status(f"Süre: {time_str}")
        except sqlite3.Error as err:
            print("Veritabanı hatası:", err)
            self.set_status("Kayıt başarısız")
        finally:
            self.reset()

    def show_history(self):
        dlg = HistoryDialog(self)
        dlg.exec()


if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    stopwatch = StopWatch()
    stopwatch.show()
    sys.exit(app.exec())