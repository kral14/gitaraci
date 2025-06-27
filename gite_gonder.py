# gite_gonder.py
import git
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog, QMessageBox
from PyQt6.QtCore import pyqtSignal

class GiteGonderTab(QWidget):
    path_changed = pyqtSignal(str)
    # DƏYİŞİKLİK: URL dəyişəndə siqnal göndərmək üçün
    remote_url_changed = pyqtSignal(str)
    
    def __init__(self, initial_path='', settings=None, initial_remote_url=''):
        super().__init__()
        self.repo_path = initial_path
        self.settings = settings if settings is not None else {}
        
        layout = QVBoxLayout(self)
        
        local_path_layout = QHBoxLayout()
        self.local_path_label = QLabel(f"Lokal Qovluq: {self.repo_path or 'Seçilməyib'}")
        browse_local_button = QPushButton("Qovluq Seç...")
        local_path_layout.addWidget(self.local_path_label)
        local_path_layout.addStretch()
        local_path_layout.addWidget(browse_local_button)
        layout.addLayout(local_path_layout)
        
        remote_path_layout = QHBoxLayout()
        # DƏYİŞİKLİK: URL xanasını yadda saxlanılan məlumatla doldururuq
        self.remote_url_input = QLineEdit(initial_remote_url)
        self.remote_url_input.setPlaceholderText("https://github.com/istifadeci/proyekt.git")
        # URL dəyişdikdə siqnal göndərir
        self.remote_url_input.textChanged.connect(self.remote_url_changed.emit)
        remote_path_layout.addWidget(QLabel("Uzaq Anbar (Remote) URL:"))
        remote_path_layout.addWidget(self.remote_url_input)
        layout.addLayout(remote_path_layout)
        
        self.commit_message_input = QLineEdit()
        self.commit_message_input.setPlaceholderText("Dəyişiklik üçün bir mesaj yazın (məs: 'İlk commit')")
        layout.addWidget(self.commit_message_input)
        
        send_button = QPushButton("Gite Göndər (Commit & Push)")
        layout.addWidget(send_button)
        
        self.monitor = QTextEdit()
        self.monitor.setReadOnly(True)
        self.monitor.setPlaceholderText("Əməliyyatların nəticəsi burada görünəcək...")
        layout.addWidget(self.monitor)
        
        browse_local_button.clicked.connect(self.select_folder)
        send_button.clicked.connect(self.commit_and_push)
        
    def update_repo_path(self, path):
        self.repo_path = path
        self.local_path_label.setText(f"Lokal Qovluq: {self.repo_path}")

    def select_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Lokal Git Anbarını Seçin")
        if path:
            self.repo_path = path
            self.local_path_label.setText(f"Lokal Qovluq: {self.repo_path}")
            self.monitor.append(f"✅ Lokal qovluq seçildi: {path}")
            self.path_changed.emit(self.repo_path)

    def commit_and_push(self):
        if not self.repo_path:
            return QMessageBox.warning(self, "Xəta", "Lokal qovluq seçilməyib.")
        remote_url = self.remote_url_input.text().strip()
        if not remote_url:
            return QMessageBox.warning(self, "Xəta", "Uzaq anbar URL-i daxil edilməyib.")
        commit_message = self.commit_message_input.text().strip()
        
        # Boş commit mesajına icazə vermirik
        if not commit_message:
            return QMessageBox.warning(self, "Xəta", "Commit mesajı boş ola bilməz.")

        username = self.settings.get("username")
        email = self.settings.get("email")
        if not username or not email:
            return QMessageBox.warning(self, "Müəllif Məlumatı Yoxdur", "Zəhmət olmasa, menyudan 'Fayl -> Parametrlər' bölməsinə daxil olub istifadəçi adınızı və e-poçtunuzu təyin edin.")
        
        try:
            repo = git.Repo(self.repo_path)
            
            with repo.config_writer() as config:
                config.set_value("user", "name", username)
                config.set_value("user", "email", email)
            self.monitor.append(f"-> Müəllif təyin edildi: {username} <{email}>")
            
            if 'origin' in [remote.name for remote in repo.remotes]:
                origin = repo.remotes.origin
                if origin.url != remote_url:
                    origin.set_url(remote_url)
            else:
                repo.create_remote('origin', remote_url)
            
            self.monitor.append("-> Dəyişikliklər əlavə edilir (git add .)...")
            repo.git.add(A=True)
            self.monitor.append("✅ Dəyişikliklər əlavə edildi.")

            if repo.is_dirty(untracked_files=True):
                self.monitor.append(f"-> '{commit_message}' mesajı ilə commit edilir...")
                repo.git.commit('-m', commit_message)
                self.monitor.append("✅ Uğurla commit edildi.")
            else:
                self.monitor.append("-> Commit üçün yeni dəyişiklik yoxdur, davam edilir...")

            active_branch = repo.active_branch.name
            self.monitor.append(f"-> Aktiv filial tapıldı: '{active_branch}'")
            
            self.monitor.append(f"-> GitHub-dakı yeniliklər yoxlanılır (git pull)...")
            repo.git.pull('origin', active_branch, '--rebase')
            self.monitor.append("✅ Uzaq anbarla sinxronizasiya edildi.")

            self.monitor.append(f"-> '{active_branch}' filialı uzaq anbara göndərilir (push)...")
            repo.git.push('--set-upstream', 'origin', active_branch)
            self.monitor.append("🎉 TAMAMLANDI: Bütün əməliyyatlar uğurla başa çatdı!")
            
        except Exception as e:
            self.monitor.append(f"❌ XƏTA: {e}")