# main_penceresi.py
import sys
import os
import json
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox
from PyQt6.QtGui import QIcon, QAction

# Təb-lərin siniflərini import edirik
from gite_hazirla import GiteHazirlaTab
from gite_gonder import GiteGonderTab
from git_tarixcesi import GitTarixcesiTab

class MainPenceresi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Yeni Git Aracı')
        self.setGeometry(100, 100, 900, 700)
        try:
            self.setWindowIcon(QIcon('icon.png'))
        except:
            print("icon.png tapılmadı.")

        self.settings = self.load_settings()
        
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Təb-ləri yaradırıq
        self.create_tabs()
        
        # --- DÜZƏLİŞ BURADADIR ---
        # Menyu zolağını yaratmaq üçün bu funksiyanı çağırırıq
        self.create_menu()
        
        # Stili tətbiq edirik
        self.apply_styles()

    def create_tabs(self):
        # Hər təb üçün öz sinfindən bir obyekt yaradırıq
        last_path = self.settings.get('last_repo_path', '')
        
        self.gite_hazirla_tab = GiteHazirlaTab(last_path)
        # settings-i GiteGonderTab-a ötürürük
        self.gite_gonder_tab = GiteGonderTab(last_path, self.settings) 
        self.git_tarixcesi_tab = GitTarixcesiTab()

        self.tab_widget.addTab(self.gite_hazirla_tab, "Gite Hazırla")
        self.tab_widget.addTab(self.gite_gonder_tab, "Gite Göndər")
        self.tab_widget.addTab(self.git_tarixcesi_tab, "Tarixçə İdarə Et")
        
        # Təb-lər arasında qovluq yolu sinxronizasiyası
        self.gite_hazirla_tab.path_changed.connect(self.gite_gonder_tab.update_repo_path)
        self.gite_gonder_tab.path_changed.connect(self.gite_hazirla_tab.update_repo_path)

    # --- YENİ ƏLAVƏ EDİLMİŞ FUNKSİYA ---
    def create_menu(self):
        """Pəncərənin yuxarısında 'Fayl' menyusunu yaradır."""
        # Menyu zolağını əldə edirik
        menubar = self.menuBar()
        
        # "Fayl" menyusunu yaradırıq
        file_menu = menubar.addMenu('Fayl')
        
        # "Parametrlər" seçimini yaradırıq
        settings_action = QAction('Parametrlər', self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)

        # "Çıxış" seçimini yaradırıq
        exit_action = QAction('Çıxış', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def open_settings(self):
        """Parametrlər pəncərəsini açır."""
        # settings_window.py faylını import etməliyik
        from settings_window import SettingsWindow
        dialog = SettingsWindow(self.settings)
        # Pəncərə "Yadda Saxla" ilə bağlanarsa...
        if dialog.exec():
            # ...dəyişiklikləri settings faylına yazırıq
            self.save_settings()
            print("Parametrlər uğurla yeniləndi.")

    def load_settings(self):
        """Proqram açıldıqda yadda saxlanılan yolu oxuyur."""
        if os.path.exists('settings.json'):
            try:
                with open('settings.json', 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {} # Fayl boş və ya səhv formatdadırsa
        return {}

    def save_settings(self):
        """Proqram bağlananda aktiv yolu və parametrləri yaddaşa yazır."""
        self.settings['last_repo_path'] = self.gite_hazirla_tab.repo_path
        with open('settings.json', 'w') as f:
            json.dump(self.settings, f, indent=4)
        print("Parametrlər yadda saxlanıldı.")

    def closeEvent(self, event):
        """Pəncərə bağlanarkən çağırılır."""
        self.save_settings()
        super().closeEvent(event)
        
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2E2E2E;
                color: #FFFFFF;
                font-size: 14px;
            }
            QMenuBar {
                background-color: #3C3C3C;
                color: #FFFFFF;
            }
            QMenuBar::item:selected {
                background-color: #007ACC;
            }
            QMenu {
                background-color: #3C3C3C;
                border: 1px solid #4F4F4F;
            }
            QMenu::item:selected {
                background-color: #007ACC;
            }
            QTabWidget::pane {
                border-top: 2px solid #4F4F4F;
            }
            QTabBar::tab {
                background: #4F4F4F;
                color: #FFFFFF;
                padding: 10px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #2E2E2E;
                border-top: 2px solid #007ACC;
            }
            QPushButton {
                background-color: #007ACC;
                border: none;
                padding: 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #008AE6;
            }
            QLineEdit, QTextEdit {
                background-color: #3C3C3C;
                border: 1px solid #4F4F4F;
                padding: 5px;
                border-radius: 4px;
            }
            QTableWidget {
                background-color: #3C3C3C;
                gridline-color: #4F4F4F;
            }
            QHeaderView::section {
                background-color: #4F4F4F;
                padding: 4px;
                border: 1px solid #2E2E2E;
            }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainPenceresi()
    window.show()
    sys.exit(app.exec())