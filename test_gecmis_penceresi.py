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
from PyQt6.QtCore import Qt

class CombinedGitTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.github_token = None
        self.headers = {}
        self.repos_data = []
        self.local_repo = None
        
        self.init_ui()
        self.setWindowTitle("Birləşdirilmiş Git Aləti v4 (Stabil)")
        self.resize(1200, 800)

    def center(self):
        screen_geometry = self.screen().availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())

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
        repo_header_layout = QHBoxLayout()
        repo_header_layout.addWidget(QLabel("Hesabınızdakı depolar (baxmaq üçün tək, klonlamaq üçün cüt klik):"))
        repo_header_layout.addStretch()
        self.refresh_repos_button = QPushButton("🔄 Yenilə")
        self.refresh_repos_button.setToolTip("Depo siyahısını yenilə")
        self.refresh_repos_button.setFixedWidth(100)
        repo_header_layout.addWidget(self.refresh_repos_button)
        github_repos_layout.addLayout(repo_header_layout)
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
        self.refresh_repos_button.clicked.connect(self.fetch_github_repos)
        browse_button.clicked.connect(self.activate_local_repo)
        self.repo_list_widget.itemClicked.connect(self.display_remote_commits)
        self.repo_list_widget.itemDoubleClicked.connect(self.clone_selected_repo)
        self.commit_button.clicked.connect(self.commit_and_push)
        self.download_button.clicked.connect(self.download_commit)
        
        self.update_ui_state()

    def update_ui_state(self):
        is_local_repo_active = self.local_repo is not None
        self.commit_input.setEnabled(is_local_repo_active)
        self.commit_button.setEnabled(is_local_repo_active)
        self.download_button.setEnabled(self.commit_table.rowCount() > 0)
        
        if is_local_repo_active:
            self.local_path_label.setText(self.local_repo.working_dir)
        else:
            self.local_path_label.setText("Lokal anbarla işləmək üçün bir depo klonlayın və ya lokal qovluq seçin.")

    def fetch_github_repos(self):
        if not self.github_token:
            self.github_token = self.token_input.text().strip()
            if not self.github_token: return self.show_error("Token daxil edilməyib.")

        self.statusBar().showMessage("Depolar GitHub-dan yüklənir...")
        QApplication.processEvents()
        
        self.headers = {"Authorization": f"token {self.github_token}"}
        try:
            user_info = requests.get("https://api.github.com/user", headers=self.headers).json()
            repos_url = user_info.get('repos_url', '') + '?per_page=200'
            response = requests.get(repos_url, headers=self.headers)
            response.raise_for_status()
            
            self.repos_data = response.json()
            
            self.repo_list_widget.clear()
            self.commit_table.setRowCount(0)
            for repo in self.repos_data:
                self.repo_list_widget.addItem(repo['name'])
            
            self.refresh_repos_button.setEnabled(True)
            self.statusBar().showMessage(f"'{user_info.get('login')}' hesabındakı {len(self.repos_data)} depo tapıldı.", 10000)

        except requests.exceptions.HTTPError as e:
            self.show_error(f"GitHub API Xətası (Status {e.response.status_code}): Tokeninizi yoxlayın.")
            self.github_token = None
        except Exception as e:
            self.show_error(f"GitHub ilə əlaqə xətası: {e}")
            self.github_token = None
            
    def display_remote_commits(self, item):
        repo_name = item.text()
        repo_data = next((repo for repo in self.repos_data if repo['name'] == repo_name), None)
        if not repo_data: return

        self.statusBar().showMessage(f"'{repo_name}' üçün uzaqdan commitlər yüklənir...")
        QApplication.processEvents()
        
        self.local_repo = None 
        self.update_ui_state()

        try:
            commits_url = repo_data['commits_url'].replace('{/sha}', '') + '?per_page=100'
            response = requests.get(commits_url, headers=self.headers)
            response.raise_for_status()
            commits = response.json()
            
            self.populate_commit_table_from_remote(commits)
            self.statusBar().showMessage(f"'{repo_name}' üçün commitlər göstərilir. Klonlamaq üçün iki dəfə klikləyin.", 5000)

        except Exception as e:
            self.show_error(f"Uzaqdan commitlər yüklənərkən xəta: {e}")

    def activate_local_repo(self):
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
            self.selection_tabs.setCurrentIndex(1)
            
        except Exception as e:
            self.show_error(f"Klonlama xətası: {e}")
    
    def populate_commit_table_from_remote(self, commits):
        self.commit_table.setRowCount(0)
        for commit_data in commits:
            row = self.commit_table.rowCount()
            self.commit_table.insertRow(row)
            commit_info = commit_data.get('commit', {})
            author_info = commit_info.get('author', {})
            self.commit_table.setItem(row, 0, QTableWidgetItem(commit_data.get('sha', '')[:8]))
            self.commit_table.setItem(row, 1, QTableWidgetItem(commit_info.get('message', '').split('\n')[0]))
            self.commit_table.setItem(row, 2, QTableWidgetItem(author_info.get('name', 'N/A')))
            self.commit_table.setItem(row, 3, QTableWidgetItem(author_info.get('date', '').replace('T', ' ').replace('Z', '')))
        self.update_ui_state()

    def populate_commit_table_from_local(self):
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
            self.update_ui_state()
        except Exception as e:
            self.show_error(f"Lokal tarixçəni göstərərkən xəta: {e}")

    # --- DÜZƏLİŞ: 'fatal: You are not currently on a branch' xətası üçün düzəliş ---
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
            
            # Aktiv filialı yoxlayaq və ya əsas filiala göndərək
            try:
                # Əgər aktiv filial varsa, ona push et
                active_branch = self.local_repo.active_branch
                push_info = origin.push(active_branch.name)
            except TypeError:
                # Aktiv filial yoxdursa (detached HEAD), əsas filiala (main/master) push et
                self.show_error("Aktiv filial tapılmadı (Detached HEAD). 'main' filialına göndərilir...")
                push_info = origin.push('HEAD:main')

            # Push nəticəsini yoxlayaq
            if any(p.flags & git.PushInfo.ERROR for p in push_info):
                error_summary = "\n".join(p.summary for p in push_info if p.flags & git.PushInfo.ERROR)
                raise Exception(f"Push əməliyyatı zamanı xəta baş verdi:\n{error_summary}")
            
            QMessageBox.information(self, "Uğurlu", "Bütün dəyişikliklər uğurla GitHub-a göndərildi!")
            self.commit_input.clear()
            self.populate_commit_table_from_local()

        except Exception as e:
            self.show_error(f"Commit/Push xətası: {e}")

    # --- DÜZƏLİŞ: 'KeyError: '/ref'' xətası üçün düzəliş ---
    def download_commit(self):
        selected = self.commit_table.selectedItems()
        if not selected: return self.show_error("Cədvəldən bir commit seçin.")
        
        commit_hash = self.commit_table.item(selected[0].row(), 0).text()
        
        if self.local_repo:
            save_path, _ = QFileDialog.getSaveFileName(self, "Commiti ZIP olaraq saxla", f"{commit_hash}.zip", "ZIP Files (*.zip)")
            if not save_path: return
            try:
                with open(save_path, 'wb') as fp:
                    self.local_repo.archive(fp, treeish=commit_hash, format='zip')
                QMessageBox.information(self, "Uğurlu", "Arxiv uğurla yadda saxlandı.")
            except Exception as e:
                self.show_error(f"Yükləmə xətası: {e}")
        else:
            repo_name_item = self.repo_list_widget.currentItem()
            if not repo_name_item: return self.show_error("Yükləmə üçün depo seçilməyib.")
            repo_name = repo_name_item.text()
            repo_data = next((repo for repo in self.repos_data if repo['name'] == repo_name), None)
            if not repo_data: return

            # URL-i düzgün formatlayırıq
            archive_url = repo_data['archive_url'].replace('{archive_format}{/ref}', f'zipball/{commit_hash}')
            
            save_path, _ = QFileDialog.getSaveFileName(self, "Arxivi Yadda Saxla", f"{repo_name}-{commit_hash}.zip", "ZIP Files (*.zip)")
            if not save_path: return
            
            try:
                with requests.get(archive_url, headers=self.headers, stream=True) as r:
                    r.raise_for_status()
                    with open(save_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
                QMessageBox.information(self, "Uğurlu", "Arxiv uğurla yadda saxlandı.")
            except Exception as e:
                self.show_error(f"Yükləmə zamanı xəta: {e}")
            
    def show_error(self, message):
        QMessageBox.warning(self, "Xəta", message)
        self.statusBar().showMessage(f"Xəta: {message}", 5000)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CombinedGitTool()
    window.show()
    window.center() 
    sys.exit(app.exec())