from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QComboBox, QDateEdit,
    QTableWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QTableWidgetItem,
    QHeaderView, QDialog, QGraphicsOpacityEffect, QGroupBox, QFormLayout
)
from PyQt6.QtCore import QDate, Qt, QLocale
from decimal import Decimal

from database import fetch_expenses, add_expense_to_db, delete_expense_from_db


class AddExpenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        self.setWindowTitle("Add/Edit Record")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Campos
        self.reg_num = QLineEdit()
        self.comp_doc = QLineEdit()
        self.comp_val = QLineEdit()
        self.vend_comp_doc = QLineEdit()
        self.vend_vend_doc = QLineEdit()
        self.vend_liq_val = QLineEdit()
        self.apur_pv = QLineEdit()
        self.apur_taxa = QLineEdit()
        self.apur_imp = QLineEdit()
        self.rep_doc = QLineEdit()
        self.rep_liq_val = QLineEdit()
        self.regime_iva = QLineEdit()
        self.obs_imp_auto = QLineEdit()
        self.obs_matricula = QLineEdit()
        self.obs_mat_estrangeira = QLineEdit()
        self.obs_marca = QLineEdit()
        self.data_venda = QDateEdit()
        self.data_venda.setDate(QDate.currentDate())


        # Layouts agrupados
        compras_group = QGroupBox("Compras")
        compras_layout = QFormLayout()
        compras_layout.addRow("Documento:", self.comp_doc)
        compras_layout.addRow("Valor Total:", self.comp_val)
        compras_group.setLayout(compras_layout)

        vendas_group = QGroupBox("Vendas")
        vendas_layout = QFormLayout()
        vendas_layout.addRow("Documento de Compra:", self.vend_comp_doc)
        vendas_layout.addRow("Documento de Venda:", self.vend_vend_doc)
        vendas_layout.addRow("Valor Líquido:", self.vend_liq_val)
        vendas_group.setLayout(vendas_layout)

        apuramento_group = QGroupBox("Apuramento do Imposto")
        apuramento_layout = QFormLayout()
        apuramento_layout.addRow("Preço Venda - Preço Compra:", self.apur_pv)
        apuramento_layout.addRow("Taxa (%):", self.apur_taxa)
        apuramento_layout.addRow("Imposto:", self.apur_imp)
        apuramento_group.setLayout(apuramento_layout)

        reparacoes_group = QGroupBox("Reparações")
        reparacoes_layout = QFormLayout()
        reparacoes_layout.addRow("Documento:", self.rep_doc)
        reparacoes_layout.addRow("Valor Total Líquido:", self.rep_liq_val)
        reparacoes_group.setLayout(reparacoes_layout)

        observacoes_group = QGroupBox("Observações")
        observacoes_layout = QFormLayout()
        observacoes_layout.addRow("Imposto Sobre Automóveis:", self.obs_imp_auto)
        observacoes_layout.addRow("Matrícula:", self.obs_matricula)
        observacoes_layout.addRow("Matrícula Estrangeira:", self.obs_mat_estrangeira)
        observacoes_layout.addRow("Marca:", self.obs_marca)
        observacoes_group.setLayout(observacoes_layout)

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.addWidget(QLabel("Número de ordem do registo (contabilidade):"))
        main_layout.addWidget(self.reg_num)
        main_layout.addWidget(compras_group)
        main_layout.addWidget(vendas_group)
        main_layout.addWidget(apuramento_group)
        main_layout.addWidget(reparacoes_group)
        main_layout.addWidget(QLabel("Regime IVA:"))
        main_layout.addWidget(self.regime_iva)
        main_layout.addWidget(observacoes_group)
        main_layout.addWidget(QLabel("Data de Venda:"))
        main_layout.addWidget(self.data_venda)
        self.data_venda.setMinimumHeight(30)

        self.add_button = QPushButton("Add/Edit Record")
        self.add_button.clicked.connect(self.add_record) # Renomeado para add_record
        main_layout.addWidget(self.add_button)

        self.setLayout(main_layout)

    def apply_styles(self):
        if self.parent_window is not None:
            self.setStyleSheet(self.parent_window.styleSheet())

    def add_record(self): # Renomeado para add_record
        # Aqui vais validar e formatar os dados antes de os passar para a BD
        try:
            comp_val = Decimal(self.comp_val.text().replace(",", ".")) if self.comp_val.text() else None
            vend_liq_val = Decimal(self.vend_liq_val.text().replace(",", ".")) if self.vend_liq_val.text() else None
            apur_pv = Decimal(self.apur_pv.text().replace(",", ".")) if self.apur_pv.text() else None
            apur_taxa = int(self.apur_taxa.text().replace("%", "")) if self.apur_taxa.text() else None
            apur_imp = Decimal(self.apur_imp.text().replace(",", ".")) if self.apur_imp.text() else None
            rep_liq_val = Decimal(self.rep_liq_val.text().replace(",", ".")) if self.rep_liq_val.text() else None
            obs_imp_auto = Decimal(self.obs_imp_auto.text().replace(",", ".")) if self.obs_imp_auto.text() else None

            # Formatar para apresentação (exemplo)
            comp_val_str = f"{comp_val:.2f} €" if comp_val is not None else ""
            vend_liq_val_str = f"{vend_liq_val:.2f} €" if vend_liq_val is not None else ""
            apur_pv_str = f"{apur_pv:.2f} €" if apur_pv is not None else ""
            apur_taxa_str = f"{apur_taxa}%" if apur_taxa is not None else ""
            apur_imp_str = f"{apur_imp:.2f} €" if apur_imp is not None else ""
            rep_liq_val_str = f"{rep_liq_val:.2f} €" if rep_liq_val is not None else ""
            obs_imp_auto_str = f"{obs_imp_auto:.2f} €" if obs_imp_auto is not None else ""
            data_venda = self.data_venda.date().toString("yyyy-MM-dd")
            # ... (Resto da lógica para adicionar à BD, usando os valores convertidos)
            if add_expense_to_db(self.reg_num.text(), self.comp_doc.text(), comp_val, self.vend_comp_doc.text(), self.vend_vend_doc.text(), vend_liq_val, apur_pv, apur_taxa, apur_imp, self.rep_doc.text(), rep_liq_val, self.regime_iva.text(), obs_imp_auto, self.obs_matricula.text(), self.obs_mat_estrangeira.text(), self.obs_marca.text(), data_venda):
                self.close()
                self.parent_window.load_table_data()
                QMessageBox.information(self, "Success", "Record added successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to add record")
        except: ValueError

    def closeEvent(self, event): # Garante que a opacidade volta ao normal
        if self.parent_window is not None:
            self.parent_window.setGraphicsEffect(None)
        event.accept()
    
    def populate_dropdown(self):
        categories = ["Food", "Transportation", "Rent", "Shopping", "Entertainment", "Bills", "Other"]
        self.dropdown.addItems(categories)

class ExpenseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_table_data()

    def init_ui(self):
        self.setWindowTitle("Expense Tracker 2.0")
        self.setWindowState(Qt.WindowState.WindowMaximized)

        self.add_button = QPushButton("Add Expense")
        self.delete_button = QPushButton("Delete Expense")

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Id", "Date", "Category", "Amount", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Connect Buttons to Methods
        self.add_button.clicked.connect(self.show_add_expense_dialog)
        self.delete_button.clicked.connect(self.delete_expense)

        # Setup Layouts
        self.setup_layout()

        # Apply Styling
        self.apply_styles()

    def show_add_expense_dialog(self):
        self.add_expense_dialog = AddExpenseDialog(self) # Passa a janela principal como parent
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.5) # Define a opacidade
        self.setGraphicsEffect(opacity_effect) # Aplica o efeito
        self.add_expense_dialog.exec() # Usamos exec() para modalidade

    def setup_layout(self):
        layout = QVBoxLayout()
        row1 = QHBoxLayout()

        # Row 3 (Buttons)
        row1.addWidget(self.add_button)
        row1.addWidget(self.delete_button)

        # Add rows to main layout
        layout.addLayout(row1)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def apply_styles(self):
        self.setStyleSheet("""
    /* Base styling */
    QWidget {
        background-color: #e3e9f2;
        font-family: Arial, sans-serif;
        font-size: 14px;
        color: #333;
    }

    /* Headings for labels */
    QLabel {
        font-size: 16px;
        color: #2c3e50;
        font-weight: bold;
        padding: 5px;
    }

    /* Styling for input fields */
    QLineEdit, QComboBox, QDateEdit {
        background-color: #ffffff;
        font-size: 14px;
        color: #333;
        border: 1px solid #b0bfc6;
        border-radius: 5px;
        padding: 5px;
    }
    QLineEdit:hover, QComboBox:hover, QDateEdit:hover {
        border: 1px solid #4caf50;
    }
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
        border: 1px solid #2a9d8f;
        background-color: #f5f9fc;
    }

    /* Table styling */
    QTableWidget {
        background-color: #ffffff;
        alternate-background-color: #f2f7fb;
        gridline-color: #c0c9d0;
        selection-background-color: #4caf50;
        selection-color: white;
        font-size: 14px;
        border: 1px solid #cfd9e1;
    }
    QHeaderView::section {
        background-color: #4caf50;
        color: white;
        font-weight: bold;
        padding: 4px;
        border: 1px solid #cfd9e1;
    }

    /* Scroll bar styling */
    QScrollBar:vertical {
        width: 12px;
        background-color: #f0f0f0;
        border: none;
    }
    QScrollBar::handle:vertical {
        background-color: #4caf50;
        min-height: 20px;
        border-radius: 5px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        background: none;
    }

    /* Buttons */
    QPushButton {
        background-color: #4caf50;
        color: white;
        padding: 10px 15px;
        border-radius: 5px;
        font-size: 14px;
        font-weight: bold;
        transition: background-color 0.3s;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
    QPushButton:pressed {
        background-color: #3d8b40;
    }
    QPushButton:disabled {
        background-color: #c8c8c8;
        color: #6e6e6e;
    }

    /* Tooltip styling */
    QToolTip {
        background-color: #2c3e50;
        color: #ffffff;
        border: 1px solid #333;
        font-size: 12px;
        padding: 5px;
        border-radius: 4px;
    }
""")


    def load_table_data(self):
        expenses = fetch_expenses()
        self.table.setRowCount(0)
        for row_idx, expense in enumerate(expenses):
            self.table.insertRow(row_idx)
            for col_idx, data in enumerate(expense):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

    def delete_expense(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select an expense to delete.")
            return

        expense_id = int(self.table.item(selected_row, 0).text())
        confirm = QMessageBox.question(self, "Confirm", "Are you sure you want to delete this expense?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes and delete_expense_from_db(expense_id):
            self.load_table_data()

    def clear_inputs(self):
        self.date_box.setDate(QDate.currentDate())
        self.dropdown.setCurrentIndex(0)
        self.amount.clear()
        self.description.clear()
