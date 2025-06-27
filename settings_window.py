# settings_window.py
import sys
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QCheckBox,
    QDialogButtonBox, QLabel, QGroupBox
)
from PyQt6.QtCore import Qt

class SettingsWindow(QDialog):
    def __init__(self, parent, current_settings):
        super().__init__(parent)
        self.setWindowTitle("Ayarlar")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setMinimumWidth(350)
        self.main_app = parent
        self.settings = current_settings.copy()

        layout = QVBoxLayout(self)

        window_group = QGroupBox("Pəncərə Davranışı")
        window_layout = QVBoxLayout()
        
        self.always_on_top_cb = QCheckBox("Əsas pəncərəni həmişə üstdə saxla")
        self.always_on_top_cb.setChecked(self.settings.get("always_on_top", False))
        self.always_on_top_cb.stateChanged.connect(
            lambda state: self.update_setting("always_on_top", state == Qt.CheckState.Checked.value)
        )
        window_layout.addWidget(self.always_on_top_cb)
        
        self.minimize_to_tray_cb = QCheckBox("Bağladıqda 'Tray' ikonuna kiçilt")
        self.minimize_to_tray_cb.setChecked(self.settings.get("minimize_to_tray", False))
        self.minimize_to_tray_cb.stateChanged.connect(
            lambda state: self.update_setting("minimize_to_tray", state == Qt.CheckState.Checked.value)
        )
        window_layout.addWidget(self.minimize_to_tray_cb)
        
        self.iconify_on_top_cb = QCheckBox("Kiçildilmiş ikonu həmişə üstdə saxla")
        self.iconify_on_top_cb.setChecked(self.settings.get("iconify_on_top", True))
        self.iconify_on_top_cb.stateChanged.connect(
            lambda state: self.update_setting("iconify_on_top", state == Qt.CheckState.Checked.value)
        )
        window_layout.addWidget(self.iconify_on_top_cb)
        
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)

        system_group = QGroupBox("Sistem İnteqrasiyası")
        system_layout = QVBoxLayout()
        
        self.startup_cb = QCheckBox("Windows başlayanda proqramı işə sal")
        if sys.platform == 'win32':
            self.startup_cb.setChecked(self.settings.get("start_on_startup", False))
            self.startup_cb.stateChanged.connect(
                lambda state: self.update_setting("start_on_startup", state == Qt.CheckState.Checked.value)
            )
        else:
            self.startup_cb.setChecked(False)
            self.startup_cb.setEnabled(False)
            self.startup_cb.setToolTip("Bu funksiya yalnız Windows sistemlərində işləyir.")
            
        system_layout.addWidget(self.startup_cb)
        system_group.setLayout(system_layout)
        layout.addWidget(system_group)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept_changes)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def update_setting(self, key, value):
        self.settings[key] = value

    def accept_changes(self):
        self.main_app.apply_and_save_settings(self.settings)
        self.accept()