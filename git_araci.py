# git_araci.py (Tam və Düzəldilmiş Versiya)
import sys
import os
import git
import json
import tempfile
import shutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QInputDialog, QMessageBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QTextEdit, QSystemTrayIcon, QMenu, QLineEdit, QGroupBox
)
from PyQt6.QtGui import QPalette, QColor, QIcon, QFont, QAction, QMouseEvent
from PyQt6.QtCore import Qt, QSize, QTimer, QPoint

if sys.platform == 'win32':
    import winreg

# DİGƏR FAYLLARDAN İMPORTLAR
from settings_window import SettingsWindow
from gite_hazirla import PrepareRepoTab

# Stil kodları (dəyişməyib)
LIGHT_THEME_STYLESHEET = """
    QMainWindow, QWidget, QGroupBox { background-color: #f0f0f0; color: #000000; }
    QGroupBox { border: 1px solid #c4c4c4; margin-top: 10px; }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }
    QTabWidget::pane { border: 1px solid #c4c4c4; }
    QTabBar::tab { background: #e1e1e1; border: 1px solid #c4c4c4; padding: 8px; min-width: 100px; }
    QTabBar::tab:selected { background: #ffffff; margin-bottom: -1px; }
    QTabBar::tab:!selected:hover { background: #dcdcdc; }
    QPushButton { background-color: #e1e1e1; border: 1px solid #c4c4c4; padding: 5px; min-width: 80px; }
    QPushButton:hover { background-color: #dcdcdc; }
    QPushButton:pressed { background-color: #c4c4c4; }
    QTextEdit, QLineEdit, QTableWidget { background-color: #ffffff; color: #000000; border: 1px solid #c4c4c4; }
    QLabel { color: #000000; }
    QHeaderView::section { background-color: #e1e1e1; border: 1px solid #c4c4c4; padding: 4px; }
    QStatusBar { background-color: #e1e1e1; }
"""
DARK_THEME_STYLESHEET = """
    QMainWindow, QWidget, QGroupBox { background-color: #2b2b2b; color: #ffffff; }
    QGroupBox { border: 1px solid #4f4f4f; margin-top: 10px; }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }
    QTabWidget::pane { border: 1px solid #4f4f4f; }
    QTabBar::tab { background: #3c3c3c; border: 1px solid #4f4f4f; padding: 8px; min-width: 100px; color: #ffffff; }
    QTabBar::tab:selected { background: #4f4f4f; margin-bottom: -1px; }
    QTabBar::tab:!selected:hover { background: #454545; }
    QPushButton { background-color: #3c3c3c; border: 1px solid #4f4f4f; padding: 5px; color: #ffffff; }
    QPushButton:hover { background-color: #454545; }
    QPushButton:pressed { background-color: #4f4f4f; }
    QTextEdit, QLineEdit, QTableWidget { background-color: #252525; color: #ffffff; border: 1px solid #4f4f4f; }
    QLabel { color: #ffffff; }
    QHeaderView::section { background-color: #3c3c3c; border: 1px solid #4f4f4f; padding: 4px; color: #ffffff; }
    QStatusBar { background-color: #3c3c3c; color: #ffffff; }
    QTableWidget::item:selected { background-color: #0078d7; color: #ffffff; }
"""
SETTINGS_FILE = 'settings.json'

class IconWidget(QWidget):
    # Bu sinifdə dəyişiklik yoxdur
    def __init__(self, parent_window, initial_pos, on_top=True):
        super().__init__()
        self.parent_window = parent_window
        self.is_waiting_for_second_click = False
        self.drag_pos = None
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.layout = QVBoxLayout(self)
        self.button = QPushButton(self)
        self.button.setIcon(self.parent_window.windowIcon())
        self.button.setIconSize(QSize(48, 48))
        self.button.setFixedSize(QSize(52, 52))
        self.button.setStyleSheet("background: transparent; border: none;")
        self.button.clicked.connect(self.on_icon_click)
        self.layout.addWidget(self.button)
        self.click_timer = QTimer(self)
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self.reset_click_state)
        if initial_pos:
            self.move(initial_pos)

    def on_icon_click(self):
        if self.is_waiting_for_second_click:
            self.click_timer.stop()
            self.button.setStyleSheet("border: 3px solid lightgreen; background-color: rgba(0, 255, 0, 0.3); border-radius: 28px;")
            QTimer.singleShot(150, self.restore_main_window)
        else:
            self.is_waiting_for_second_click = True
            self.button.setStyleSheet("border: 3px solid red; background-color: rgba(255, 0, 0, 0.3); border-radius: 28px;")
            self.click_timer.start(2000)
            
    def restore_main_window(self):
        self.parent_window.settings['icon_position'] = {'x': self.pos().x(), 'y': self.pos().y()}
        self.parent_window.save_settings()
        self.close()
        self.parent_window.show_and_raise()
        
    def reset_click_state(self):
        self.is_waiting_for_second_click = False
        self.button.setStyleSheet("background: transparent; border: none;")
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()
            
    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos is not None:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()


class GitApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = self.load_settings()
        self.setWindowTitle('Git Yönetim Aracı')
        self.setGeometry(300, 300, 800, 600)
        self.setWindowIcon(QIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon)))
        self.repo_path = self.settings.get('last_repo_path', None)
        self.repo = None # Əsas anbar obyekti
        self.history_repo = None # Tarixçə səhifəsi üçün istifadə edilən anbar
        self.temp_clone_dir = None # Müvəqqəti klon üçün qovluq

        self.icon_widget = None
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.setCentralWidget(self.main_widget)
        self.create_top_bar()
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        self.create_push_tab()
        self.create_history_tab()
        self.create_prepare_tab()
        self.statusBar().showMessage('Lütfen bir Git proje klasörü seçin.')
        self.create_tray_icon()
        self.apply_settings()
        if self.repo_path and os.path.exists(self.repo_path):
            self.select_repo_directory(path=self.repo_path)
        self.set_light_theme()
        self.prepare_tab.update_path_display(self.repo_path)
        # Başlanğıcda tarixçə səhifəsindəki yolu da doldur
        self.history_local_path_input.setText(self.repo_path or "")


    def create_top_bar(self):
        # Bu funksiyada dəyişiklik yoxdur
        top_bar_widget = QWidget()
        top_bar_layout = QHBoxLayout(top_bar_widget)
        top_bar_layout.setContentsMargins(0, 5, 0, 5)
        iconify_button = QPushButton()
        iconify_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ArrowDown))
        iconify_button.setToolTip("Pəncərəni masaüstü ikonuna kiçilt")
        iconify_button.clicked.connect(self.iconify_window)
        settings_button = QPushButton()
        settings_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView))
        settings_button.setToolTip("Ayarlar")
        settings_button.clicked.connect(self.open_settings_window)
        light_theme_button = QPushButton("🔆 Açıq Mövzu")
        dark_theme_button = QPushButton("🌙 Tünd Mövzu")
        light_theme_button.clicked.connect(self.set_light_theme)
        dark_theme_button.clicked.connect(self.set_dark_theme)
        top_bar_layout.addWidget(iconify_button)
        top_bar_layout.addWidget(settings_button)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(light_theme_button)
        top_bar_layout.addWidget(dark_theme_button)
        self.main_layout.addWidget(top_bar_widget)

    def create_prepare_tab(self):
        # Bu funksiyada dəyişiklik yoxdur
        self.prepare_tab = PrepareRepoTab(self)
        self.tabs.addTab(self.prepare_tab, "Gite Hazırla")

    def refresh_all_tabs(self):
        # Yalnız əsas pəncərənin tarixçə cədvəlini yeniləyir (əgər lokal seçilidirsə)
        if self.history_repo is self.repo:
            self.show_local_history()

    def iconify_window(self):
        # Bu funksiyada dəyişiklik yoxdur
        self.hide()
        pos_data = self.settings.get('icon_position')
        initial_pos = QPoint(pos_data['x'], pos_data['y']) if pos_data else None
        on_top = self.settings.get('iconify_on_top', True)
        self.icon_widget = IconWidget(self, initial_pos, on_top)
        if not initial_pos:
            main_geo = self.geometry()
            self.icon_widget.move(main_geo.center() - self.icon_widget.rect().center())
        self.icon_widget.show()

    def create_tray_icon(self):
        # Bu funksiyada dəyişiklik yoxdur
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.windowIcon())
        tray_menu = QMenu()
        show_action = QAction("Göstər", self)
        quit_action = QAction("Çıxış", self)
        show_action.triggered.connect(self.show_and_raise)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        # Bu funksiyada dəyişiklik yoxdur
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_and_raise()

    def show_and_raise(self):
        # Bu funksiyada dəyişiklik yoxdur
        if self.icon_widget and self.icon_widget.isVisible():
            self.icon_widget.restore_main_window()
        else:
            self.showNormal()
            self.activateWindow()

    def create_push_tab(self):
        # Bu funksiyada dəyişiklik yoxdur
        self.push_tab = QWidget()
        layout = QVBoxLayout(self.push_tab)
        
        repo_layout = QHBoxLayout()
        self.repo_label = QLabel('Proje Klasörü: Seçilmedi')
        browse_button = QPushButton('Gözat...')
        browse_button.clicked.connect(lambda: self.select_repo_directory(path=None))
        repo_layout.addWidget(self.repo_label)
        repo_layout.addWidget(browse_button)
        layout.addLayout(repo_layout)

        remote_layout = QHBoxLayout()
        remote_layout.addWidget(QLabel("GitHub Depo Linki:"))
        self.remote_url_input = QLineEdit()
        self.remote_url_input.setPlaceholderText("https://github.com/username/repo.git")
        remote_layout.addWidget(self.remote_url_input)
        layout.addLayout(remote_layout)
        
        self.push_button = QPushButton('Değişiklikleri Gite Gönder')
        self.push_button.setEnabled(False) 
        self.push_button.clicked.connect(self.push_changes)
        layout.addWidget(self.push_button)
        
        layout.addWidget(QLabel("Proses Monitoru:"))
        self.log_monitor = QTextEdit()
        self.log_monitor.setReadOnly(True)
        self.log_monitor.setFont(QFont("Consolas, Courier New", 10))
        self.log_monitor.setPlaceholderText("Git əməliyyatlarının nəticələri burada göstəriləcək...")
        layout.addWidget(self.log_monitor)
        
        self.tabs.addTab(self.push_tab, 'Gite Gönder')

    # DƏYİŞİKLİK EDİLMİŞ FUNKSİYA
    def create_history_tab(self):
        self.history_tab = QWidget()
        layout = QVBoxLayout(self.history_tab)
        
        # Lokal Anbar Bölməsi
        local_group = QGroupBox("Lokal Anbar")
        local_layout = QHBoxLayout()
        self.history_local_path_input = QLineEdit()
        self.history_local_path_input.setPlaceholderText("Lokal qovluq yolunu seçin...")
        browse_history_button = QPushButton("Gözat...")
        show_local_history_button = QPushButton("Lokal Tarixçəni Göstər")
        local_layout.addWidget(self.history_local_path_input)
        local_layout.addWidget(browse_history_button)
        local_layout.addWidget(show_local_history_button)
        local_group.setLayout(local_layout)
        layout.addWidget(local_group)
        
        # Uzaq Anbar Bölməsi
        remote_group = QGroupBox("Uzaq Anbar (GitHub)")
        remote_layout = QHBoxLayout()
        self.history_remote_url_input = QLineEdit()
        self.history_remote_url_input.setPlaceholderText("https://github.com/username/repo.git")
        show_remote_history_button = QPushButton("Uzaq Tarixçəni Göstər")
        remote_layout.addWidget(self.history_remote_url_input)
        remote_layout.addWidget(show_remote_history_button)
        remote_group.setLayout(remote_layout)
        layout.addWidget(remote_group)
        
        # Commit cədvəli
        self.commit_table = QTableWidget()
        self.commit_table.setColumnCount(4)
        self.commit_table.setHorizontalHeaderLabels(['Hash', 'Mesaj', 'Yazar', 'Tarih'])
        self.commit_table.verticalHeader().setVisible(False)
        self.commit_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.commit_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.commit_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.commit_table)
        
        # Əməliyyat düymələri
        button_layout = QHBoxLayout()
        self.download_button = QPushButton('Seçileni İndir (ZIP)')
        self.delete_button = QPushButton('Seçili Commiti Sil (Lokal Reset)')
        self.delete_button.setObjectName("DeleteButton")
        button_layout.addStretch()
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)
        
        # Düymələrin funksiyaları
        browse_history_button.clicked.connect(self.browse_for_history_path)
        show_local_history_button.clicked.connect(self.show_local_history)
        show_remote_history_button.clicked.connect(self.show_remote_history)
        self.download_button.clicked.connect(self.download_commit)
        self.delete_button.clicked.connect(self.delete_commit)
        
        self.tabs.addTab(self.history_tab, 'Geçmişi Yönet')

    def browse_for_history_path(self):
        path = QFileDialog.getExistingDirectory(self, "Tarixçə üçün Qovluq Seçin")
        if path:
            self.history_local_path_input.setText(path)

    def show_local_history(self):
        path = self.history_local_path_input.text()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Xəta", "Zəhmət olmasa, düzgün lokal qovluq yolu seçin.")
            return
        
        try:
            repo = git.Repo(path)
            self.history_repo = repo
            self.delete_button.setEnabled(True) # Lokal üçün silmə aktivdir
            self.statusBar().showMessage(f"Lokal anbarın tarixçəsi göstərilir: {path}")
            self.populate_history_table(list(repo.iter_commits('--all', max_count=200)))
        except git.InvalidGitRepositoryError:
            QMessageBox.warning(self, "Xəta", "Seçilmiş qovluq etibarlı bir Git anbarı deyil.")
        except Exception as e:
            QMessageBox.critical(self, "Xəta", f"Lokal tarixçəni göstərərkən xəta baş verdi: {e}")

    def show_remote_history(self):
        url = self.history_remote_url_input.text().strip()
        if not url.startswith("https://") or not url.endswith(".git"):
            QMessageBox.warning(self, "Xəta", "Zəhmət olmasa, düzgün HTTPS Git URL daxil edin.")
            return

        # Köhnə müvəqqəti qovluğu təmizlə
        if self.temp_clone_dir and os.path.exists(self.temp_clone_dir):
            shutil.rmtree(self.temp_clone_dir, ignore_errors=True)
        
        self.temp_clone_dir = tempfile.mkdtemp()
        self.statusBar().showMessage(f"Uzaq depo klonlanır... {url}")
        
        try:
            # Deponu müvəqqəti qovluğa klonla
            cloned_repo = git.Repo.clone_from(url, self.temp_clone_dir, no_checkout=True)
            self.history_repo = cloned_repo
            self.delete_button.setEnabled(False) # Uzaq depo üçün silmə passivdir
            self.statusBar().showMessage("Uzaq depo tarixçəsi göstərilir.")
            self.populate_history_table(list(cloned_repo.iter_commits('--all', max_count=200)))
        except Exception as e:
            self.statusBar().showMessage("Klonlama zamanı xəta.")
            QMessageBox.critical(self, "Xəta", f"Uzaq depo klonlanarkən xəta baş verdi: {e}")

    def populate_history_table(self, commits):
        self.commit_table.setRowCount(0)
        if not commits:
            self.statusBar().showMessage("Göstəriləcək commit tapılmadı.")
            return

        for commit in commits:
            row_position = self.commit_table.rowCount()
            self.commit_table.insertRow(row_position)
            self.commit_table.setItem(row_position, 0, QTableWidgetItem(commit.hexsha[:10]))
            self.commit_table.setItem(row_position, 1, QTableWidgetItem(commit.message.split('\n')[0]))
            self.commit_table.setItem(row_position, 2, QTableWidgetItem(commit.author.name))
            self.commit_table.setItem(row_position, 3, QTableWidgetItem(commit.authored_datetime.strftime('%Y-%m-%d %H:%M')))

    def open_settings_window(self):
        # Bu funksiyada dəyişiklik yoxdur
        dialog = SettingsWindow(self, self.settings)
        dialog.exec()
        
    def apply_and_save_settings(self, new_settings):
        # Bu funksiyada dəyişiklik yoxdur
        self.settings = new_settings
        self.apply_settings()
        self.save_settings()

    def apply_settings(self):
        # Bu funksiyada dəyişiklik yoxdur
        always_on_top = self.settings.get("always_on_top", False)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, always_on_top)
        if sys.platform == 'win32':
            startup_enabled = self.settings.get("start_on_startup", False)
            self.set_startup(startup_enabled)
        self.show()

    def set_startup(self, enable=True):
        # Bu funksiyada dəyişiklik yoxdur
        if not sys.platform == 'win32': return
        app_name = "GitAraci"
        app_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enable:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            else:
                winreg.DeleteValue(key, app_name)
            winreg.CloseKey(key)
        except FileNotFoundError:
            if not enable: pass
        except Exception as e:
            print(f"Windows Registry ilə işləyərkən xəta: {e}")

    def load_settings(self):
        # Bu funksiyada dəyişiklik yoxdur
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f: return json.load(f)
            except (json.JSONDecodeError, IOError): return {}
        return {}

    def save_settings(self):
        # Bu funksiyada dəyişiklik yoxdur
        try:
            with open(SETTINGS_FILE, 'w') as f: json.dump(self.settings, f, indent=4)
        except IOError: self.statusBar().showMessage("Ayarlar yadda saxlanıla bilmədi.")
            
    def closeEvent(self, event):
        # Proqram bağlananda müvəqqəti qovluğu sil
        if self.temp_clone_dir and os.path.exists(self.temp_clone_dir):
            shutil.rmtree(self.temp_clone_dir, ignore_errors=True)
            
        self.save_settings()
        if self.settings.get("minimize_to_tray", False) and self.isVisible():
            event.ignore()
            self.hide()
            self.tray_icon.show()
            self.tray_icon.showMessage("Git Aracı", "Proqram arxa fonda işləyir.", self.windowIcon(), 2000)
        else:
            self.quit_application()

    def quit_application(self):
        # Bu funksiyada dəyişiklik yoxdur
        self.tray_icon.hide()
        QApplication.instance().quit()

    def set_light_theme(self):
        # Bu funksiyada dəyişiklik yoxdur
        self.setStyleSheet(LIGHT_THEME_STYLESHEET + "#DeleteButton { background-color: #ffcccc; color: black; } #DeleteButton:hover { background-color: #ffb8b8; }")

    def set_dark_theme(self):
        # Bu funksiyada dəyişiklik yoxdur
        self.setStyleSheet(DARK_THEME_STYLESHEET + "#DeleteButton { background-color: #8b0000; color: white; } #DeleteButton:hover { background-color: #a10000; }")

    def log_message(self, message, color_name="default"):
        # Bu funksiyada dəyişiklik yoxdur
        current_style = self.styleSheet()
        if "background-color: #2b2b2b" in current_style:
            default_color_name = "#ffffff"
        else:
            default_color_name = "#000000"
        if color_name == "default":
            self.log_monitor.append(f"<p style='color: {default_color_name};'>{message}</p>")
        else:
            self.log_monitor.append(f"<p style='color: {color_name};'>{message}</p>")
        QApplication.processEvents()

    def log_success(self, message):
        # Bu funksiyada dəyişiklik yoxdur
        self.log_message(message, "limegreen")

    def log_error(self, message):
        # Bu funksiyada dəyişiklik yoxdur
        self.log_message(message, "red")

    def select_repo_directory(self, path=None):
        # Bu funksiya əsasən digər səhifələrə təsir edir
        if not path:
            path = QFileDialog.getExistingDirectory(self, "Git Proje Klasörü Seç")
        if path:
            self.repo_path = path
            self.remote_url_input.clear()
            try:
                self.repo = git.Repo(path)
                if 'origin' in self.repo.remotes:
                    origin_url = self.repo.remotes.origin.url
                    self.remote_url_input.setText(origin_url)
            except git.InvalidGitRepositoryError:
                self.repo = None
            
            self.settings['last_repo_path'] = path
            # Əsas pəncərədəki və tarixçə səhifəsindəki yolları yenilə
            self.repo_label.setText(f'Proje Klasörü: {self.repo_path}')
            self.history_local_path_input.setText(self.repo_path)
            
            self.push_button.setEnabled(self.repo is not None)
            
            self.refresh_all_tabs()
            self.prepare_tab.update_path_display(self.repo_path)

    def push_changes(self):
        # Bu funksiyada dəyişiklik yoxdur
        if not self.repo: return
        
        remote_url = self.remote_url_input.text().strip()
        if not remote_url:
            QMessageBox.warning(self, "Xəta", "Zəhmət olmasa, GitHub depo linkini daxil edin.")
            return

        self.log_monitor.clear()
        self.log_message("Dəyişikliklər yoxlanılır...")
        if not self.repo.is_dirty(untracked_files=True):
            self.log_message("Göndəriləcək yeni bir dəyişiklik tapılmadı.")
            QMessageBox.information(self, "Məlumat", "Göndəriləcək yeni dəyişiklik yoxdur.")
            return
            
        commit_message, ok = QInputDialog.getText(self, 'Commit Mesajı', 'Dəyişikliyi təsvir edin:')
        if ok and commit_message:
            try:
                self.log_message(f"Uzaq anbar (remote) '{remote_url}' olaraq tənzimlənir...")
                if 'origin' in self.repo.remotes:
                    origin = self.repo.remotes.origin
                    if origin.url != remote_url:
                        origin.set_url(remote_url)
                        self.log_message("Mövcud 'origin' remote-nun URL-i yeniləndi.")
                else:
                    self.repo.create_remote('origin', remote_url)
                    self.log_message("'origin' adlı yeni remote yaradıldı.")

                self.log_message("Bütün dəyişikliklər Git-ə əlavə edilir (git add .)...")
                self.repo.git.add(A=True)
                self.log_message(f"Commit yaradılır: '{commit_message}'...")
                self.repo.index.commit(commit_message)
                self.log_message("Uzaq depoya (origin) qoşulur...")
                origin = self.repo.remote(name='origin')
                
                refspec = ''
                try:
                    active_branch = self.repo.active_branch
                    branch_name = active_branch.name
                    refspec = f'{branch_name}:{branch_name}'
                    self.log_message(f"'{branch_name}' filialı GitHub-a göndərilir (push)...")
                except TypeError:
                    branch_name = 'main'
                    refspec = f'HEAD:{branch_name}'
                    self.log_message(f"XƏBƏRDARLIQ: Anbar birbaşa bir commit-ə bağlıdır ('detached HEAD'). Dəyişikliklər uzaq depodakı '{branch_name}' filialına göndərilir.", "orange")
                
                push_info = origin.push(refspec=refspec, set_upstream=True)
                
                if push_info[0].flags & git.PushInfo.ERROR:
                    self.log_error(f"XƏTA! Dəyişikliklər göndərilə bilmədi: {push_info[0].summary}")
                    QMessageBox.critical(self, "Xəta", f"Push əməliyyatı zamanı xəta:\n{push_info[0].summary}")
                else:
                    self.log_success("Əməliyyat uğurla tamamlandı! Bütün dəyişikliklər GitHub-a göndərildi.")
                    QMessageBox.information(self, 'Uğurlu', 'Dəyişiklikləriniz uğurla GitHub-a göndərildi.')
                self.refresh_all_tabs()
            except Exception as e:
                self.log_error(f"Gözlənilməz xəta baş verdi: {e}")
                QMessageBox.critical(self, 'Xəta', f'Bir xəta baş verdi:\n{e}')
        else:
            self.log_message("Commit əməliyyatı ləğv edildi.")

    def download_commit(self):
        # Bu funksiya indi 'history_repo' istifadə edir
        if not self.history_repo:
            QMessageBox.warning(self, "Məlumat", "Zəhmət olmasa, əvvəlcə bir tarixçə göstərin.")
            return

        selected_items = self.commit_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'Uyarı', 'Lütfen indirmek için tablodan bir commit seçin.')
            return
        selected_row = selected_items[0].row()
        commit_hash = self.commit_table.item(selected_row, 0).text()
        
        file_path, _ = QFileDialog.getSaveFileName(self, "ZIP Olarak Kaydet", f"versiyon_{commit_hash}.zip", "ZIP Dosyaları (*.zip)")
        if file_path:
            try:
                with open(file_path, 'wb') as fp:
                    self.history_repo.archive(fp, treeish=commit_hash, format='zip')
                self.statusBar().showMessage(f'{commit_hash} versiyonu başarıyla indirildi.')
                QMessageBox.information(self, 'Başarılı', f'Versiyon başarıyla şuraya kaydedildi:\n{file_path}')
            except Exception as e:
                QMessageBox.critical(self, 'Hata', f'İndirme sırasında bir hata oluştu:\n{e}')

    def delete_commit(self):
        # Bu funksiya indi 'history_repo' istifadə edir və yalnız lokalda işləyir
        if not self.history_repo or not self.delete_button.isEnabled():
            QMessageBox.warning(self, "Məlumat", "Bu əməliyyat yalnız lokal tarixçə üçün keçərlidir.")
            return

        selected_items = self.commit_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'Uyarı', 'Lütfen geri dönmek üçün bir commit seçin.')
            return
        selected_row = selected_items[0].row()
        commit_hash = self.commit_table.item(selected_row, 0).text()
        
        reply = QMessageBox.warning(self, 'ÇOX TƏHLÜKƏLİ ƏMƏLİYYAT!',
            f"Seçdiyiniz '{commit_hash}' commitinə geri qayıtmaq üzrəsiniz.\n\n"
            "Bu əməliyyat, bu commitdən sonra edilən bütün dəyişiklikləri **LOKAL ANBARINIZDAN** qalıcı olaraq siləcək.\n"
            "Bu əməliyyat geri alına bilməz və yalnız lokal tarixçənizə təsir edir (GitHub-a yox).\n\n"
            "Davam etməyə əminsinizmi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.history_repo.git.reset('--hard', commit_hash)
                self.statusBar().showMessage(f'Proje {commit_hash} versiyonuna geri alındı. Sonraki commitler lokal olaraq silindi.')
                QMessageBox.information(self, 'İşlem Tamamlandı', 'Proje seçilen versiyona başarıyla sıfırlandı.')
                self.show_local_history() # Siyahını yenilə
            except Exception as e:
                QMessageBox.critical(self, 'Hata', f'Reset işlemi sırasında bir hata oluştu:\n{e}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GitApp()
    window.show()
    sys.exit(app.exec())