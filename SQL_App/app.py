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
        self.setWindowTitle("MBAuto - Detalhes")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Campos
        self.matricula = QLineEdit()
        self.marca = QLineEdit()
        self.isv = QLineEdit()
        self.nRegistoContabilidade = QLineEdit()

        self.dataCompra = QDateEdit()
        self.dataCompra.setDate(QDate.currentDate())
        self.docCompra = QLineEdit()
        self.tipoDocumento = QComboBox()
        self.tipoDocumento.addItems(["Fatura", "Fatura-Recibo", "Fatura Simplificada", "Declaração"])
        self.valorCompra = QLineEdit()

        self.dataVenda = QDateEdit()
        self.dataVenda.setDate(QDate.currentDate())
        self.docVenda = QLineEdit()
        self.valorVenda = QLineEdit()

        # self.regime = QLineEdit()
        self.imposto = QLineEdit()
        self.taxa = QLineEdit()

        # Layouts agrupados
        identificacao_group = QGroupBox("Identificação")
        identificacao_layout = QFormLayout()
        identificacao_layout.addRow("Matrícula:", self.matricula)
        identificacao_layout.addRow("Marca:", self.marca)
        identificacao_layout.addRow("ISV:", self.isv)
        identificacao_layout.addRow("Nº Registo de Contabilidade:", self.nRegistoContabilidade)
        identificacao_group.setLayout(identificacao_layout)

        compras_group = QGroupBox("Compras")
        compras_layout = QFormLayout()
        compras_layout.addRow("Data de Compra:", self.dataCompra)
        compras_layout.addRow("Documento de Compra:", self.docCompra)
        compras_layout.addRow("Tipo de Documento:", self.tipoDocumento)
        compras_layout.addRow("Valor de Compra:", self.valorCompra)
        compras_group.setLayout(compras_layout)

        vendas_group = QGroupBox("Vendas")
        vendas_layout = QFormLayout()
        vendas_layout.addRow("Data de Venda:", self.dataVenda)
        vendas_layout.addRow("Documento de Venda:", self.docVenda)
        vendas_layout.addRow("Valor Venda:", self.valorVenda)
        vendas_group.setLayout(vendas_layout)

        imposto_group = QGroupBox("Imposto")
        imposto_layout = QFormLayout()
        # imposto_layout.addRow("Regime:", self.regime)
        imposto_layout.addRow("Imposto:", self.imposto)
        imposto_layout.addRow("Taxa:", self.taxa)
        imposto_group.setLayout(imposto_layout)

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.addWidget(identificacao_group)
        main_layout.addWidget(compras_group)
        main_layout.addWidget(vendas_group)
        main_layout.addWidget(imposto_group)
        self.dataCompra.setMinimumHeight(30)
        self.dataVenda.setMinimumHeight(30)

        self.add_button = QPushButton("Add/Edit Record")
        self.add_button.clicked.connect(self.add_record)
        main_layout.addWidget(self.add_button)

        self.setLayout(main_layout)

    def apply_styles(self):
        if self.parent_window is not None:
            self.setStyleSheet(self.parent_window.styleSheet())

    def add_record(self):
        global isv_formatado, valor_compra_formatado, valor_venda_formatado
        try:
            try:
                isv_formatado = float(self.isv.text().replace(",", ".")) if self.isv.text() else None
                valor_compra_formatado = float(
                    self.valorCompra.text().replace(",", ".")) if self.valorCompra.text() else None
                valor_venda_formatado = float(self.valorVenda.text().replace(",", ".")) if self.valorVenda.text() else None
            except InvalidOperation:
                QMessageBox.warning(self, "Dados errados", "Decimais inválidos.")

            # Formatar para apresentação
            # isv_str = f"{isv_formatado:.2f} €" if isv_formatado is not None else ""
            # valor_compra_str = f"{valor_compra_formatado:.2f} €" if valor_compra_formatado is not None else ""
            # valor_venda_str = f"{valor_venda_formatado:.2f} €" if valor_venda_formatado is not None else ""

            data_compra_str = self.dataCompra.date().toString("yyyy-MM-dd")
            data_venda_str = self.dataVenda.date().toString("yyyy-MM-dd")

            if add_expense_to_db(self.matricula.text(), self.marca.text(), isv_formatado,
                                 self.nRegistoContabilidade.text(), data_compra_str, self.docCompra.text(),
                                 self.tipoDocumento.currentText(), valor_compra_formatado, data_venda_str,
                                 self.docVenda.text(), valor_venda_formatado, self.imposto.text(), self.taxa.text()):
                self.close()
                self.parent_window.load_table_data()
                QMessageBox.information(self, "Success", "Record added successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to add record")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add record: {e}")
            raise

    def closeEvent(self, event):  # Garante que a opacidade volta ao normal
        if self.parent_window is not None:
            self.parent_window.setGraphicsEffect(None)
        event.accept()


class ExpenseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_table_data()

    def init_ui(self):
        self.setWindowTitle("MBAuto")
        self.setWindowState(Qt.WindowState.WindowMaximized)

        self.add_button = QPushButton("Add Expense")
        self.delete_button = QPushButton("Delete Expense")

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Matrícula", "Marca", "Valor de Compra", "Documento de Venda", "Valor de Venda", "Imposto"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Connect Buttons to Methods
        self.add_button.clicked.connect(self.show_add_expense_dialog)
        self.delete_button.clicked.connect(self.delete_expense)

        # Setup Layouts
        self.setup_layout()

        # Apply Styling
        self.apply_styles()

    def show_add_expense_dialog(self):
        self.add_expense_dialog = AddExpenseDialog(self)  # Passa a janela principal como parent
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.5)  # Define a opacidade
        self.setGraphicsEffect(opacity_effect)  # Aplica o efeito
        self.add_expense_dialog.exec()  # Usamos exec() para modalidade

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
        confirm = QMessageBox.question(self, "Confirm", "Are you sure you want to delete this expense?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if confirm == QMessageBox.StandardButton.Yes and delete_expense_from_db(expense_id):
            self.load_table_data()

    def clear_inputs(self):
        self.date_box.setDate(QDate.currentDate())
        self.dropdown.setCurrentIndex(0)
        self.amount.clear()
        self.description.clear()
