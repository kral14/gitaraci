# gite_hazirla.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QApplication,
    QLabel, QTextEdit, QLineEdit
)
from PyQt6.QtGui import QFont, QColor
import git

class PrepareRepoTab(QWidget):
    def __init__(self, main_app_ref):
        super().__init__()
        self.main_app = main_app_ref
        
        layout = QVBoxLayout(self)
        
        self.init_button = QPushButton("1. Proyekt Yarat (git init)")
        self.remote_label = QLabel("GitHub URL-i:")
        self.remote_url_input = QLineEdit()
        self.remote_url_input.setPlaceholderText("https://github.com/istifadeci/proyekt.git")
        self.remote_add_button = QPushButton("2. Uzaqdan İdarəetməni Əlavə Et")
        self.status_button = QPushButton("Vəziyyəti Yoxla (git status)")
        
        self.monitor = QTextEdit()
        self.monitor.setReadOnly(True)
        self.monitor.setFont(QFont("Consolas, Courier New", 10))
        
        remote_layout = QHBoxLayout()
        remote_layout.addWidget(self.remote_label)
        remote_layout.addWidget(self.remote_url_input)
        remote_layout.addWidget(self.remote_add_button)

        layout.addWidget(self.init_button)
        layout.addLayout(remote_layout)
        layout.addWidget(self.status_button)
        layout.addWidget(QLabel("Əməliyyat Monitoru:"))
        layout.addWidget(self.monitor)
        
        self.init_button.clicked.connect(self.run_git_init)
        self.remote_add_button.clicked.connect(self.run_git_remote_add)
        self.status_button.clicked.connect(self.run_git_status)

        self.update_button_states()

    def log_message(self, message, color_name="default"):
        current_style = self.main_app.styleSheet()
        if "background-color: #2b2b2b" in current_style:
            default_color_name = "#ffffff"
        else:
            default_color_name = "#000000"

        if color_name == "default":
            self.monitor.append(f"<p style='color: {default_color_name};'>{message}</p>")
        else:
            self.monitor.append(f"<p style='color: {color_name};'>{message}</p>")
        QApplication.instance().processEvents()

    def update_button_states(self):
        repo_exists = self.main_app.repo is not None
        path_selected = self.main_app.repo_path is not None

        self.init_button.setEnabled(path_selected and not repo_exists)
        self.remote_add_button.setEnabled(repo_exists)
        self.status_button.setEnabled(repo_exists)

        if repo_exists:
            self.init_button.setToolTip("Bu qovluq artıq bir Git proyektidir.")
        else:
            self.init_button.setToolTip("Seçilmiş qovluqda yeni Git proyektinə başlayır.")

    def run_git_init(self):
        self.monitor.clear()
        path = self.main_app.repo_path
        if not path:
            self.log_message("Xəta: Zəhmət olmasa, əvvəlcə bir qovluq seçin.", "red")
            return
        
        try:
            self.log_message(f"'{path}' qovluğunda 'git init' icra edilir...")
            repo = git.Repo.init(path)
            self.log_message("Uğurlu: Boş Git anbarı yaradıldı.", "limegreen")
            self.main_app.repo = repo
            self.main_app.refresh_all_tabs()
        except Exception as e:
            self.log_message(f"Xəta: {e}", "red")

    def run_git_remote_add(self):
        self.monitor.clear()
        if not self.main_app.repo:
            self.log_message("Xəta: Əvvəlcə bir Git anbarı seçilməli və ya yaradılmalıdır.", "red")
            return
        
        url = self.remote_url_input.text().strip()
        if not (url.startswith("https://") and url.endswith(".git")):
            self.log_message("Xəta: Zəhmət olmasa, düzgün bir HTTPS Git URL-i daxil edin.", "red")
            return
            
        try:
            self.log_message(f"'origin' adlı remote '{url}' ünvanı ilə yaradılır...")
            if 'origin' in self.main_app.repo.remotes:
                self.log_message("Məlumat: 'origin' adlı remote artıq mövcuddur. Mövcud olan silinir və yenisi yaradılır.")
                self.main_app.repo.delete_remote('origin')
            
            self.main_app.repo.create_remote('origin', url)
            self.log_message("Uğurlu: 'origin' remote-u uğurla əlavə edildi.", "limegreen")
        except Exception as e:
            self.log_message(f"Xəta: {e}", "red")
            
    def run_git_status(self):
        self.monitor.clear()
        if not self.main_app.repo:
            self.log_message("Xəta: Vəziyyəti yoxlamaq üçün bir Git anbarı olmalıdır.", "red")
            return
            
        try:
            self.log_message("'git status' nəticəsi:")
            status_result = self.main_app.repo.git.status()
            self.monitor.append(status_result)
        except Exception as e:
            self.log_message(f"Xəta: {e}", "red")