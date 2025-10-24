"""
VM list table widget with real-time updates
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor

from backend.libvirt_manager import LibvirtManager
from backend.vm_controller import VMController, VMState
from models.vm_model import VMModel
from utils.logger import logger


class VMListWidget(QWidget):
    """Widget displaying list of VMs with controls"""
    
    vm_selected = Signal(str)  # Emits VM UUID
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize backend
        self.manager = LibvirtManager()
        self.controller = VMController(self.manager)
        
        # Setup UI
        self._setup_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_vm_list)
        self.refresh_timer.start(3000)  # Refresh every 3 seconds
        
        # Initial load
        self.refresh_vm_list()
    
    def _setup_ui(self):
        """Setup widget UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.clicked.connect(self._on_start_vm)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self._on_stop_vm)
        
        self.reboot_btn = QPushButton("🔄 Reboot")
        self.reboot_btn.clicked.connect(self._on_reboot_vm)
        
        self.delete_btn = QPushButton("🗑 Delete")
        self.delete_btn.clicked.connect(self._on_delete_vm)
        self.delete_btn.setStyleSheet("background-color: #C62828; color: white;")
        
        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.clicked.connect(self.refresh_vm_list)

        self.gpu_activate_btn = QPushButton("🎮 Activate GPU")
        self.gpu_activate_btn.clicked.connect(self._on_activate_gpu)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.reboot_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.gpu_activate_btn)
        button_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(button_layout)
        
        # VM table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Name", "State", "vCPUs", "Memory (GB)", "Autostart", "UUID"
        ])
        
        # Table styling
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Resize columns
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        layout.addWidget(self.table)
        
        # Apply dark theme to table
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2B2B2B;
                color: #FFFFFF;
                gridline-color: #3E3E3E;
                border: 1px solid #3E3E3E;
            }
            QTableWidget::item:selected {
                background-color: #0D7377;
            }
            QHeaderView::section {
                background-color: #1E1E1E;
                color: #FFFFFF;
                padding: 5px;
                border: 1px solid #3E3E3E;
            }
        """)
    
    def refresh_vm_list(self):
        """Refresh VM list from libvirt"""
        try:
            domains = self.manager.list_all_vms()
            
            # Clear table
            self.table.setRowCount(0)
            
            # Populate table
            for domain in domains:
                info = self.controller.get_vm_info(domain)
                if not info:
                    continue
                
                vm = VMModel.from_libvirt_info(info)
                self._add_vm_to_table(vm)
            
            logger.debug(f"Refreshed VM list: {len(domains)} VMs")
            
        except Exception as e:
            logger.error(f"Failed to refresh VM list: {e}")
    
    def _add_vm_to_table(self, vm: VMModel):
        """Add VM to table"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Name
        self.table.setItem(row, 0, QTableWidgetItem(vm.name))
        
        # State (with color coding)
        state_item = QTableWidgetItem(vm.state_name)
        if vm.is_active:
            state_item.setForeground(QColor("#4CAF50"))  # Green
        else:
            state_item.setForeground(QColor("#9E9E9E"))  # Gray
        self.table.setItem(row, 1, state_item)
        
        # vCPUs
        self.table.setItem(row, 2, QTableWidgetItem(str(vm.vcpus)))
        
        # Memory
        self.table.setItem(row, 3, QTableWidgetItem(f"{vm.memory_gb:.1f}"))
        
        # Autostart
        autostart = "Yes" if vm.autostart else "No"
        self.table.setItem(row, 4, QTableWidgetItem(autostart))
        
        # UUID
        self.table.setItem(row, 5, QTableWidgetItem(vm.uuid))
    
    def _get_selected_vm(self):
        """Get currently selected VM domain"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a VM first")
            return None
        
        row = selected[0].row()
        vm_name = self.table.item(row, 0).text()
        
        domain = self.manager.get_vm_by_name(vm_name)
        if not domain:
            QMessageBox.critical(self, "Error", f"VM '{vm_name}' not found")
        
        return domain
    
    def _on_start_vm(self):
        """Handle start VM button"""
        domain = self._get_selected_vm()
        if not domain:
            return
        
        try:
            vm_name = domain.name()
            logger.info(f"Starting VM '{vm_name}'...")
            
            # Start VM
            domain.create()
            logger.info(f"VM '{vm_name}' started successfully")
            
            # Launch viewer after short delay
            from PySide6.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self._launch_viewer(vm_name))
            
            # Refresh list
            self.refresh_vm_list()
            
        except Exception as e:
            logger.exception(f"Failed to start VM: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to start VM:\n{str(e)}")

    def _launch_viewer(self, vm_name: str):
        """Launch virt-viewer for VM"""
        try:
            import subprocess
            subprocess.Popen([
                'virt-viewer',
                '--connect', 'qemu:///system',
                '--wait',
                vm_name
            ])
            logger.info(f"Launched viewer for '{vm_name}'")
        except Exception as e:
            logger.error(f"Failed to launch viewer: {e}")


    def _on_stop_vm(self):
        """Handle stop VM button"""
        domain = self._get_selected_vm()
        if domain:
            reply = QMessageBox.question(
                self, "Confirm Stop",
                f"Shutdown VM '{domain.name()}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.controller.stop_vm_and_close_viewer(domain)
                self.refresh_vm_list()
    
    def _on_reboot_vm(self):
        """Handle reboot VM button"""
        domain = self._get_selected_vm()
        if domain and self.controller.reboot_vm(domain):
            self.refresh_vm_list()
    
    def _on_delete_vm(self):
        """Handle delete VM button"""
        domain = self._get_selected_vm()
        if not domain:
            return
        
        reply = QMessageBox.warning(
            self, "Confirm Deletion",
            f"Permanently delete VM '{domain.name()}' and its storage?\n\n"
            "This action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.manager.delete_vm(domain, remove_storage=True):
                QMessageBox.information(self, "Success", "VM deleted successfully")
                self.refresh_vm_list()
    
    def _on_selection_changed(self):
        """Handle table selection change"""
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            uuid = self.table.item(row, 5).text()
            self.vm_selected.emit(uuid)

    def _on_activate_gpu(self):
        """Handle GPU activation button"""
        domain = self._get_selected_vm()
        if not domain:
            return

        from ui.gpu_activation_dialog import GPUActivationDialog
        from backend.gpu_detector import GPUDetector

        detector = GPUDetector()
        passthrough_gpus = detector.get_passthrough_gpus()

        if not passthrough_gpus:
            QMessageBox.warning(
                self,
                "No GPU Available",
                "No GPUs available for passthrough"
            )
            return

        gpu = passthrough_gpus[0]

        dialog = GPUActivationDialog(domain.name(), gpu, self)
        dialog.exec()
        self.refresh_vm_list()
