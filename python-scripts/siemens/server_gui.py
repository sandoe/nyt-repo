import sys
import ctypes
import logging
import struct # VIGTIG NY IMPORT TIL 8-BYTE FLOATS
import snap7
from snap7.util import get_real, get_int, get_bool
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QFormLayout, QSpinBox, QPushButton, 
                             QLabel, QTabWidget, QTableWidget, QTableWidgetItem, 
                             QComboBox, QMessageBox, QHeaderView, QAbstractItemView)
from PyQt6.QtCore import QTimer, Qt

# Opsætning af logning
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("GUI_PLC")

# --- NY HJÆLPEFUNKTION TIL 8-BYTE LREAL ---
def get_lreal(buffer, byte_index):
    """Læser en 64-bit float (LREAL/Double) fra Siemens hukommelse"""
    try:
        data = bytes(buffer)[byte_index:byte_index+8]
        return struct.unpack('>d', data)[0] # '>d' betyder Big-Endian Double
    except Exception:
        return 0.0

# ==========================================
# 1. Backend: Snap7 Server Indpakning
# ==========================================
class Snap7ServerWrapper:
    def __init__(self):
        self.server = snap7.server.Server()
        self.running = False
        
        self.inputs = None
        self.outputs = None
        self.merkers = None
        self.db = None
        self.db_number = 1

    def start(self, port, io_size, mk_size, db_size, db_number):
        if self.running:
            return False, "Serveren kører allerede."

        try:
            self.db_number = db_number
            # Alloker hukommelse (C-types byte arrays)
            self.inputs = (ctypes.c_ubyte * io_size)()
            self.outputs = (ctypes.c_ubyte * io_size)()
            self.merkers = (ctypes.c_ubyte * mk_size)()
            self.db = (ctypes.c_ubyte * db_size)()

            # Registrer områder (PE=I, PA=Q, MK=M, DB=DataBlock)
            self.server.register_area(snap7.type.SrvArea.PE, 0, self.inputs)
            self.server.register_area(snap7.type.SrvArea.PA, 0, self.outputs)
            self.server.register_area(snap7.type.SrvArea.MK, 0, self.merkers)
            self.server.register_area(snap7.type.SrvArea.DB, self.db_number, self.db)

            self.server.start(tcp_port=port)
            self.running = True
            logger.info(f"Server startet på port {port}. DB{self.db_number} er klar.")
            return True, "Server startet succesfuldt."
        except Exception as e:
            logger.error(f"Kunne ikke starte: {e}")
            return False, str(e)

    def stop(self):
        if self.running:
            self.server.stop()
            self.server.destroy()
            self.running = False
            logger.info("Server stoppet.")

    def get_client_count(self) -> int:
        if not self.running:
            return 0
        try:
            status_data = self.server.get_status()
            if isinstance(status_data, tuple) and len(status_data) >= 3:
                return int(status_data[2])
            return 0
        except Exception:
            return 0

    def read_value(self, area: str, byte_offset: int, data_type: str):
        if not self.running:
            return "Offline"
        try:
            buffer = None
            if area == "I (Inputs)": buffer = self.inputs
            elif area == "Q (Outputs)": buffer = self.outputs
            elif area == "M (Merkers)": buffer = self.merkers
            elif area == "DB": buffer = self.db

            if buffer is None: return "Ugyldigt område"

            # Logik til at håndtere de forskellige datatyper
            if data_type == "REAL (4 Bytes)":
                return f"{get_real(buffer, byte_offset):.4f}"
            elif data_type == "LREAL (8 Bytes)":
                return f"{get_lreal(buffer, byte_offset):.6f}"
            elif data_type == "INT":
                return str(get_int(buffer, byte_offset))
            elif data_type == "BOOL (Bit 0)":
                return str(get_bool(buffer, byte_offset, 0))
            else:
                return "Ukendt type"
        except Exception:
            return "Out of bounds"

# ==========================================
# 2. Frontend: PyQt6 Hovedvindue
# ==========================================
class PLCSimulatorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Snap7 PLC Simulator - Aarhus Maskinmesterskole")
        self.resize(750, 550) 

        self.plc = Snap7ServerWrapper()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.setup_config_tab()
        self.setup_monitor_tab()
        self.setup_statusbar()

        # Timer til live-opdatering af monitor
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_ui)

    def setup_statusbar(self):
        self.statusBar = self.statusBar()
        self.lbl_clients = QLabel("🖥️ Forbundne klienter: 0")
        self.lbl_clients.setStyleSheet("font-weight: bold; color: #1976D2; padding-right: 20px;")
        self.statusBar.addPermanentWidget(self.lbl_clients)

    def setup_config_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.port_input = QSpinBox(); self.port_input.setRange(1, 65535); self.port_input.setValue(102)
        self.io_size_input = QSpinBox(); self.io_size_input.setRange(2, 8192); self.io_size_input.setValue(100)
        self.mk_size_input = QSpinBox(); self.mk_size_input.setRange(2, 8192); self.mk_size_input.setValue(100)
        self.db_size_input = QSpinBox(); self.db_size_input.setRange(2, 8192); self.db_size_input.setValue(100)
        self.db_num_input = QSpinBox(); self.db_num_input.setRange(1, 999); self.db_num_input.setValue(1)

        form_layout.addRow("TCP Port (Standard 102):", self.port_input)
        form_layout.addRow("I/O Størrelse (Bytes):", self.io_size_input)
        form_layout.addRow("Merker Størrelse (Bytes):", self.mk_size_input)
        form_layout.addRow("DB Størrelse (Bytes):", self.db_size_input)
        form_layout.addRow("DB Nummer:", self.db_num_input)

        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start Server")
        self.btn_start.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_start.clicked.connect(self.start_server)

        self.btn_stop = QPushButton("Stop Server")
        self.btn_stop.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 10px;")
        self.btn_stop.clicked.connect(self.stop_server)
        self.btn_stop.setEnabled(False)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)

        self.lbl_status = QLabel("Status: Server er stoppet")
        self.lbl_status.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")

        layout.addLayout(form_layout)
        layout.addLayout(btn_layout)
        layout.addWidget(self.lbl_status)
        layout.addStretch()
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "⚙️ Opsætning")

    def setup_monitor_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        add_layout = QHBoxLayout()
        self.combo_area = QComboBox()
        self.combo_area.addItems(["I (Inputs)", "Q (Outputs)", "M (Merkers)", "DB"])
        
        self.spin_byte = QSpinBox()
        self.spin_byte.setPrefix("Byte ")
        self.spin_byte.setRange(0, 8192)

        self.combo_type = QComboBox()
        self.combo_type.addItems(["REAL (4 Bytes)", "LREAL (8 Bytes)", "INT", "BOOL (Bit 0)"])

        btn_add = QPushButton("Tilføj")
        btn_add.clicked.connect(self.add_tag_to_table)

        btn_delete = QPushButton("Slet Valgte")
        btn_delete.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold;")
        btn_delete.clicked.connect(self.delete_selected_tags)

        add_layout.addWidget(self.combo_area)
        add_layout.addWidget(self.spin_byte)
        add_layout.addWidget(self.combo_type)
        add_layout.addWidget(btn_add)
        add_layout.addWidget(btn_delete) 

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Område", "Byte Offset", "Data Type", "Live Værdi"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        layout.addLayout(add_layout)
        layout.addWidget(self.table)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "👁️ Watch Table (Live)")

    def delete_selected_tags(self):
        """Sletter alle markerede rækker fra tabellen"""
        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        for row in sorted(selected_rows, reverse=True):
            self.table.removeRow(row)

    def keyPressEvent(self, event):
        """Lytter efter Delete-tasten"""
        if self.tabs.currentIndex() == 1 and event.key() == Qt.Key.Key_Delete:
            self.delete_selected_tags()
        else:
            super().keyPressEvent(event)

    def start_server(self):
        port = self.port_input.value()
        io_sz = self.io_size_input.value()
        mk_sz = self.mk_size_input.value()
        db_sz = self.db_size_input.value()
        db_num = self.db_num_input.value()

        success, msg = self.plc.start(port, io_sz, mk_sz, db_sz, db_num)
        if success:
            self.lbl_status.setText(f"Status: Kører på port {port}")
            self.lbl_status.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.update_timer.start(200) 
        else:
            QMessageBox.critical(self, "Fejl", f"Kunne ikke starte serveren:\n{msg}")

    def stop_server(self):
        self.update_timer.stop()
        self.plc.stop()
        self.lbl_status.setText("Status: Server er stoppet")
        self.lbl_status.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_clients.setText("🖥️ Forbundne klienter: 0")
        self.lbl_clients.setStyleSheet("font-weight: bold; color: #1976D2; padding-right: 20px;")

    def add_tag_to_table(self):
        row_pos = self.table.rowCount()
        self.table.insertRow(row_pos)

        area = self.combo_area.currentText()
        byte_offset = str(self.spin_byte.value())
        data_type = self.combo_type.currentText()

        self.table.setItem(row_pos, 0, QTableWidgetItem(area))
        self.table.setItem(row_pos, 1, QTableWidgetItem(byte_offset))
        self.table.setItem(row_pos, 2, QTableWidgetItem(data_type))
        self.table.setItem(row_pos, 3, QTableWidgetItem("N/A"))

    def refresh_ui(self):
        if self.plc.running:
            try:
                clients = self.plc.get_client_count()
            except ValueError:
                clients = 0

            self.lbl_clients.setText(f"🖥️ Forbundne klienter: {clients}")
            
            if clients > 0:
                self.lbl_clients.setStyleSheet("font-weight: bold; color: green; padding-right: 20px;")
            else:
                self.lbl_clients.setStyleSheet("font-weight: bold; color: #1976D2; padding-right: 20px;")

        for row in range(self.table.rowCount()):
            area = self.table.item(row, 0).text()
            byte_offset = int(self.table.item(row, 1).text())
            data_type = self.table.item(row, 2).text()

            value = self.plc.read_value(area, byte_offset, data_type)
            self.table.setItem(row, 3, QTableWidgetItem(value))

    def closeEvent(self, event):
        self.stop_server()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    window = PLCSimulatorGUI()
    window.show()
    sys.exit(app.exec())
    