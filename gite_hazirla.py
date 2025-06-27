# gite_hazirla.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QApplication,
    QLabel, QTextEdit, QMessageBox, QFileDialog
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import git

class PrepareRepoTab(QWidget):
    def __init__(self, main_app_ref):
        super().__init__()
        self.main_app = main_app_ref
        
        layout = QVBoxLayout(self)
        
        # --- YENİ DİZAYN ---
        # 1. Qovluq seçmə hissəsi
        path_layout = QHBoxLayout()
        self.path_label = QLabel("Qovluq: Hələ seçilməyib")
        self.path_label.setStyleSheet("font-style: italic; color: #888;")
        browse_button = QPushButton("Qovluq Seç...")
        
        path_layout.addWidget(self.path_label)
        path_layout.addStretch()
        path_layout.addWidget(browse_button)
        
        # 2. Əsas əməliyyat düyməsi
        self.prepare_button = QPushButton("Bu Qovluğu Gite Hazırla")
        self.prepare_button.setStyleSheet("padding: 10px; font-weight: bold;")
        self.prepare_button.setEnabled(False) # Başlanğıcda passivdir

        # 3. Əməliyyat monitoru
        self.monitor = QTextEdit()
        self.monitor.setReadOnly(True)
        self.monitor.setFont(QFont("Consolas, Courier New", 10))
        
        # Elementlərin pəncərəyə yerləşdirilməsi
        layout.addLayout(path_layout)
        layout.addWidget(self.prepare_button)
        layout.addWidget(QLabel("Əməliyyat Monitoru:"))
        layout.addWidget(self.monitor)
        
        # Düymələrin funksiyaları
        browse_button.clicked.connect(self.select_folder)
        self.prepare_button.clicked.connect(self.run_full_preparation)

    def select_folder(self):
        """Qovluq seçmək üçün dialoq pəncərəsi açır."""
        path = QFileDialog.getExistingDirectory(self, "Proyekt Qovluğunu Seçin")
        if path:
            # Qovluq seçimi üçün əsas pəncərədəki funksiyanı çağırırıq.
            # Bu, proqramın hər yerində eyni qovluq yolunun istifadə edilməsini təmin edir.
            self.main_app.select_repo_directory(path=path)

    def update_path_display(self, path):
        """Əsas pəncərədən gələn yola görə bu səhifədəki məlumatları yeniləyir."""
        if path:
            self.path_label.setText(f"Qovluq: {path}")
            self.path_label.setStyleSheet("font-style: normal; color: default;")
            self.prepare_button.setEnabled(True)
            self.prepare_button.setToolTip("Seçilmiş qovluqda yeni Git anbarı yaradacaq.")
        else:
            self.path_label.setText("Qovluq: Hələ seçilməyib")
            self.path_label.setStyleSheet("font-style: italic; color: #888;")
            self.prepare_button.setEnabled(False)
            self.prepare_button.setToolTip("Zəhmət olmasa, əvvəlcə bir qovluq seçin.")

    def log_message(self, message, color_name="default"):
        """Monitora rəngli mətn çıxarmaq üçün köməkçi funksiya."""
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

    def run_full_preparation(self):
        """Bir düymə ilə bütün hazırlıq mərhələlərini icra edir."""
        self.monitor.clear()
        path = self.main_app.repo_path
        
        if self.main_app.repo is not None:
             QMessageBox.warning(self, "Məlumat", "Bu qovluq artıq bir Git anbarıdır.")
             self.log_message("MƏLUMAT: Bu qovluq artıq bir Git anbarıdır. Əməliyyat dayandırıldı.", "orange")
             return

        try:
            self.log_message(f"-> '{path}' qovluğunda 'git init' icra edilir...")
            repo = git.Repo.init(path)
            self.main_app.repo = repo
            self.log_message("UĞURLU: Boş Git anbarı yaradıldı.", "limegreen")

            self.log_message("-> Bütün fayllar 'git add .' ilə indeksə əlavə edilir...")
            repo.git.add(A=True)
            self.log_message("UĞURLU: Bütün fayllar əlavə edildi.", "limegreen")
            
            # Əgər əlavə ediləcək fayl varsa, commit et
            if repo.is_dirty(untracked_files=True):
                self.log_message("-> 'İlk commit' mesajı ilə dəyişikliklər təsdiqlənir (commit)...")
                repo.index.commit("İlk commit")
                self.log_message("UĞURLU: 'İlk commit' uğurla yaradıldı.", "limegreen")
            else:
                self.log_message("MƏLUMAT: Təsdiqləmək üçün yeni fayl tapılmadı.", "orange")

            self.log_message("\n🎉 BÜTÜN ƏMƏLİYYATLAR UĞURLA BAŞA ÇATDI!", "limegreen")
            QMessageBox.information(self, "Uğurlu", "Qovluq Git üçün tam hazır vəziyyətə gətirildi.")
            
            self.main_app.refresh_all_tabs()

        except Exception as e:
            self.log_message(f"XƏTA: Əməliyyat zamanı xəta baş verdi: {e}", "red")
            QMessageBox.critical(self, "Xəta", f"Əməliyyat zamanı xəta baş verdi:\n{e}")