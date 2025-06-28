import sys
import os
import requests
import git
import shutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QAbstractItemView, QGroupBox, QFileDialog, QInputDialog, QTabWidget
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize

class CombinedGitTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.github_token = None
        self.headers = {}
        self.repos_data = []  # GitHub-dan gələn repo məlumatları
        self.local_repo = None # Aktiv lokal depo obyekti (git.Repo)
        self.temp_dir_for_remote_view = None # Yalnız uzaqdan baxmaq üçün müvəqqəti qovluq

        self.init_ui()
        self.setWindowTitle("Birləşdirilmiş Git Aləti (Test)")
        self.resize(1200, 800)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # 1. GİRİŞ BÖLMƏSİ
        login_group = QGroupBox("1. GitHub Hesabına Giriş (Token ilə)")
        login_layout = QHBoxLayout()
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setPlaceholderText("GitHub Personal Access Token...")
        self.login_button = QPushButton("Hesaba Bağlan və Depoları Göstər")
        login_layout.addWidget(QLabel("Access Token:"))
        login_layout.addWidget(self.token_input)
        login_layout.addWidget(self.login_button)
        login_group.setLayout(login_layout)
        main_layout.addWidget(login_group)

        # 2. DEPO SEÇİMİ VƏ COMMIT CƏDVƏLİ
        content_layout = QHBoxLayout()
        
        # SOL PANEL: DEPO SEÇİMİ (TABLI GÖRÜNÜŞ)
        selection_group = QGroupBox("2. Depo Seçimi")
        selection_layout = QVBoxLayout()
        self.selection_tabs = QTabWidget()

        # Onlayn Depo Seçimi Tabı
        github_repos_widget = QWidget()
        github_repos_layout = QVBoxLayout(github_repos_widget)
        github_repos_layout.addWidget(QLabel("Hesabınızdakı depolar:"))
        self.repo_list_widget = QListWidget()
        github_repos_layout.addWidget(self.repo_list_widget)
        self.selection_tabs.addTab(github_repos_widget, "GitHub Depolarım")

        # Lokal Depo Seçimi Tabı
        local_repo_widget = QWidget()
        local_repo_layout = QVBoxLayout(local_repo_widget)
        local_repo_layout.addStretch()
        local_repo_layout.addWidget(QLabel("Və ya kompüterinizdən bir qovluq seçin:"))
        browse_button = QPushButton("Lokal Qovluq Seç...")
        local_repo_layout.addWidget(browse_button)
        local_repo_layout.addStretch()
        self.selection_tabs.addTab(local_repo_widget, "Lokal Anbar")
        
        selection_layout.addWidget(self.selection_tabs)
        selection_group.setLayout(selection_layout)

        # SAĞ PANEL: COMMIT CƏDVƏLİ VƏ ƏMƏLİYYATLAR
        right_panel_layout = QVBoxLayout()
        commit_group = QGroupBox("Commit Tarixçəsi")
        commit_layout = QVBoxLayout()
        self.commit_table = QTableWidget(0, 4)
        self.commit_table.setHorizontalHeaderLabels(['Hash', 'Mesaj', 'Yazar', 'Tarix'])
        self.commit_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.commit_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        commit_layout.addWidget(self.commit_table)
        commit_group.setLayout(commit_layout)
        right_panel_layout.addWidget(commit_group)
        
        # Əməliyyatlar Paneli
        actions_group = QGroupBox("3. Əməliyyatlar")
        actions_layout = QVBoxLayout()
        self.local_path_label = QLineEdit("Hazırda heç bir lokal anbar aktiv deyil.")
        self.local_path_label.setReadOnly(True)
        self.commit_input = QLineEdit()
        self.commit_input.setPlaceholderText("Commit mesajı...")
        self.commit_button = QPushButton("Commit et və Göndər (Push)")
        self.download_button = QPushButton("Seçili Commiti Yüklə (ZIP)")

        actions_layout.addWidget(QLabel("Aktiv Lokal Anbarın Yolu:"))
        actions_layout.addWidget(self.local_path_label)
        
        commit_layout_h = QHBoxLayout()
        commit_layout_h.addWidget(self.commit_input)
        commit_layout_h.addWidget(self.commit_button)
        actions_layout.addLayout(commit_layout_h)
        actions_layout.addWidget(self.download_button)
        actions_group.setLayout(actions_layout)
        right_panel_layout.addWidget(actions_group)

        content_layout.addWidget(selection_group, 2)
        content_layout.addLayout(right_panel_layout, 5)
        main_layout.addLayout(content_layout)

        # Siqnallar
        self.login_button.clicked.connect(self.fetch_github_repos)
        browse_button.clicked.connect(self.select_local_repo)
        self.repo_list_widget.itemDoubleClicked.connect(self.clone_selected_repo)
        self.commit_button.clicked.connect(self.commit_and_push)
        self.download_button.clicked.connect(self.download_commit)
        
        self.update_ui_state()

    def update_ui_state(self):
        """Proqramın vəziyyətinə görə düymələri aktiv/deaktiv edir."""
        is_local_repo_active = self.local_repo is not None
        self.commit_input.setEnabled(is_local_repo_active)
        self.commit_button.setEnabled(is_local_repo_active)
        self.download_button.setEnabled(is_local_repo_active)
        
        if is_local_repo_active:
            self.local_path_label.setText(self.local_repo.working_dir)
        else:
            self.local_path_label.setText("Hazırda heç bir lokal anbar aktiv deyil.")

    def fetch_github_repos(self):
        """Token ilə GitHub-dan depoları gətirir."""
        self.github_token = self.token_input.text().strip()
        if not self.github_token: return self.show_error("Token daxil edilməyib.")

        self.headers = {"Authorization": f"token {self.github_token}"}
        try:
            user_info = requests.get("https://api.github.com/user", headers=self.headers).json()
            repos_url = user_info['repos_url'] + '?per_page=100'
            self.repos_data = requests.get(repos_url, headers=self.headers).json()
            
            self.repo_list_widget.clear()
            for repo in self.repos_data:
                self.repo_list_widget.addItem(repo['name'])
            
            self.statusBar().showMessage(f"'{user_info['login']}' hesabındakı {len(self.repos_data)} depo tapıldı. Üzərində işləmək üçün depoya iki dəfə klikləyin.", 10000)

        except Exception as e:
            self.show_error(f"GitHub ilə əlaqə xətası: {e}")

    def select_local_repo(self):
        """Lokal qovluq seçməyə imkan verir."""
        path = QFileDialog.getExistingDirectory(self, "Lokal Git Anbarını Seçin")
        if not path: return
        
        try:
            self.local_repo = git.Repo(path)
            self.populate_commit_table_from_local()
            self.update_ui_state()
            self.statusBar().showMessage(f"Lokal depo açıldı: {path}", 5000)
        except git.InvalidGitRepositoryError:
            self.show_error(f"'{path}' etibarlı bir Git anbarı deyil.")
        except Exception as e:
            self.show_error(f"Lokal depo açılarkən xəta: {e}")
            
    def clone_selected_repo(self, item):
        """Siyahıdan seçilmiş deponu klonlayır."""
        repo_name = item.text()
        repo_data = next((repo for repo in self.repos_data if repo['name'] == repo_name), None)
        if not repo_data: return
        
        path = QFileDialog.getExistingDirectory(self, f"'{repo_name}' deposunu klonlamaq üçün yer seçin")
        if not path: return
        
        clone_path = os.path.join(path, repo_name)
        auth_repo_url = repo_data['clone_url'].replace('https://', f'https://{self.github_token}@')
        
        try:
            if os.path.exists(clone_path):
                self.local_repo = git.Repo(clone_path)
                QMessageBox.information(self, "Məlumat", "Depo artıq mövcuddur. Həmin qovluq açılır.")
            else:
                self.statusBar().showMessage(f"'{repo_name}' klonlanır...", 30000)
                QApplication.processEvents()
                self.local_repo = git.Repo.clone_from(auth_repo_url, clone_path)
                self.statusBar().showMessage("Depo uğurla klonlandı!", 5000)

            self.populate_commit_table_from_local()
            self.update_ui_state()
            self.selection_tabs.setCurrentIndex(1) # Lokal Anbar tabına keç
            
        except Exception as e:
            self.show_error(f"Klonlama xətası: {e}")

    def populate_commit_table_from_local(self):
        """Aktiv lokal deponun commitlərini cədvələ doldurur."""
        self.commit_table.setRowCount(0)
        if not self.local_repo: return
        
        try:
            commits = list(self.local_repo.iter_commits(max_count=200))
            for commit in commits:
                row = self.commit_table.rowCount()
                self.commit_table.insertRow(row)
                self.commit_table.setItem(row, 0, QTableWidgetItem(commit.hexsha[:8]))
                self.commit_table.setItem(row, 1, QTableWidgetItem(commit.summary))
                self.commit_table.setItem(row, 2, QTableWidgetItem(commit.author.name))
                self.commit_table.setItem(row, 3, QTableWidgetItem(commit.authored_datetime.strftime('%Y-%m-%d %H:%M')))
        except Exception as e:
            self.show_error(f"Lokal tarixçəni göstərərkən xəta: {e}")

    def commit_and_push(self):
        if not self.local_repo: return self.show_error("Heç bir lokal anbar aktiv deyil.")
        
        commit_message = self.commit_input.text().strip()
        if not commit_message: return self.show_error("Commit mesajı boş ola bilməz.")
        
        try:
            if not self.local_repo.is_dirty(untracked_files=True):
                return QMessageBox.information(self, "Məlumat", "Commit üçün yeni dəyişiklik tapılmadı.")

            self.statusBar().showMessage("Dəyişikliklər göndərilir...", 30000)
            self.local_repo.git.add(A=True)
            self.local_repo.index.commit(commit_message)
            origin = self.local_repo.remote(name='origin')
            origin.push()
            
            QMessageBox.information(self, "Uğurlu", "Dəyişikliklər uğurla GitHub-a göndərildi!")
            self.commit_input.clear()
            self.populate_commit_table_from_local() # Cədvəli yenilə

        except Exception as e:
            self.show_error(f"Commit/Push xətası: {e}")

    def download_commit(self):
        if not self.local_repo: return self.show_error("Əvvəlcə bir depo açın və ya klonlayın.")
        
        selected = self.commit_table.selectedItems()
        if not selected: return self.show_error("Cədvəldən bir commit seçin.")
        
        commit_hash = self.commit_table.item(selected[0].row(), 0).text()
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Commiti ZIP olaraq saxla", f"{commit_hash}.zip", "ZIP Files (*.zip)")
        if not save_path: return
        
        try:
            with open(save_path, 'wb') as fp:
                self.local_repo.archive(fp, treeish=commit_hash, format='zip')
            QMessageBox.information(self, "Uğurlu", f"Arxiv uğurla yadda saxlandı.")
        except Exception as e:
            self.show_error(f"Yükləmə xətası: {e}")
            
    def show_error(self, message):
        QMessageBox.warning(self, "Xəta", message)
        self.statusBar().showMessage(f"Xəta: {message}", 5000)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CombinedGitTool()
    window.show()
    sys.exit(app.exec())