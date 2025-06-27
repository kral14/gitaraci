# git_tarixcesi.py
import os
import git
import tempfile
import shutil
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QLineEdit, QTableWidget, QHeaderView, QAbstractItemView, 
                             QTableWidgetItem, QMessageBox, QFileDialog)

class GitTarixcesiTab(QWidget):
    def __init__(self):
        super().__init__()
        self.repo = None
        self.temp_dir = tempfile.mkdtemp() # Tarixçəyə baxmaq üçün müvəqqəti qovluq
        
        layout = QVBoxLayout(self)
        
        # URL daxil etmə hissəsi
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://github.com/istifadeci/proyekt.git")
        show_history_button = QPushButton("Tarixçəni Göstər")
        url_layout.addWidget(QLabel("Depo Linki:"))
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(show_history_button)
        layout.addLayout(url_layout)
        
        # Commit cədvəli
        self.commit_table = QTableWidget()
        self.commit_table.setColumnCount(4)
        self.commit_table.setHorizontalHeaderLabels(['Heş', 'Mesaj', 'Müəllif', 'Tarix'])
        self.commit_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.commit_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.commit_table)
        
        # Düymələr
        buttons_layout = QHBoxLayout()
        download_button = QPushButton("Seçilmişi Yüklə (ZIP)")
        delete_button = QPushButton("Seçilmişi Sil (Lokal)")
        buttons_layout.addStretch()
        buttons_layout.addWidget(download_button)
        buttons_layout.addWidget(delete_button)
        layout.addLayout(buttons_layout)
        
        # Funksiyalar
        show_history_button.clicked.connect(self.load_history)
        download_button.clicked.connect(self.download_commit)
        delete_button.clicked.connect(self.delete_commit_locally)

    def load_history(self):
        url = self.url_input.text().strip()
        if not url:
            return QMessageBox.warning(self, "Xəta", "Zəhmət olmasa, depo linkini daxil edin.")
        
        repo_name = url.split('/')[-1].replace('.git', '')
        clone_path = os.path.join(self.temp_dir, repo_name)
        
        try:
            if os.path.exists(clone_path):
                self.repo = git.Repo(clone_path)
                self.repo.remotes.origin.pull()
            else:
                self.repo = git.Repo.clone_from(url, clone_path)
            
            self.populate_table()
            
        except Exception as e:
            QMessageBox.critical(self, "Xəta", f"Tarixçə yüklənərkən xəta baş verdi:\n{e}")

    def populate_table(self):
        self.commit_table.setRowCount(0)
        if not self.repo: return
        
        commits = list(self.repo.iter_commits('master', max_count=100))
        self.commit_table.setRowCount(len(commits))
        
        for row, commit in enumerate(commits):
            self.commit_table.setItem(row, 0, QTableWidgetItem(commit.hexsha[:8]))
            self.commit_table.setItem(row, 1, QTableWidgetItem(commit.summary))
            self.commit_table.setItem(row, 2, QTableWidgetItem(commit.author.name))
            self.commit_table.setItem(row, 3, QTableWidgetItem(commit.authored_datetime.strftime('%d-%m-%Y %H:%M')))

    def get_selected_commit(self):
        selected_rows = self.commit_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Xəta", "Zəhmət olmasa, cədvəldən bir commit seçin.")
            return None
        
        sha = self.commit_table.item(selected_rows[0].row(), 0).text()
        return self.repo.commit(sha)

    def download_commit(self):
        commit = self.get_selected_commit()
        if not commit: return
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Commit-i ZIP olaraq saxla", f"{commit.hexsha[:8]}.zip", "ZIP Files (*.zip)")
        if file_path:
            with open(file_path, 'wb') as fp:
                self.repo.archive(fp, treeish=commit.hexsha, format='zip')
            QMessageBox.information(self, "Uğurlu", "Commit uğurla ZIP formatında yadda saxlanıldı.")

    def delete_commit_locally(self):
        commit_to_delete = self.get_selected_commit()
        if not commit_to_delete: return

        if commit_to_delete != self.repo.head.commit:
            return QMessageBox.warning(self, "Xəta", "Yalnız ən son commit-i silə bilərsiniz.")

        reply = QMessageBox.question(self, "Təsdiq", "Əminsinizmi? Bu əməliyyat lokal anbarınızdakı son commit-i siləcək və geri qaytarıla bilməz.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.repo.git.reset('--hard', 'HEAD~1')
                self.populate_table()
                QMessageBox.information(self, "Uğurlu", "Son commit lokal olaraq silindi.")
            except Exception as e:
                QMessageBox.critical(self, "Xəta", f"Commit silinərkən xəta: {e}")

    def __del__(self):
        # Proqram bağlananda müvəqqəti qovluğu silir
        shutil.rmtree(self.temp_dir, ignore_errors=True)