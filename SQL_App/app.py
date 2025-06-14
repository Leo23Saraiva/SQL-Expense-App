from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QComboBox, QDateEdit,
    QTableWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QTableWidgetItem,
    QHeaderView, QDialog, QGraphicsOpacityEffect, QGroupBox, QFormLayout,
    QRadioButton
)
from PyQt6.QtCore import QDate, Qt, QLocale
from decimal import Decimal

from database import fetch_expenses, add_expense_to_db, delete_expense_from_db, update_expense_in_db, fetch_vehicle_by_id


class AddExpenseDialog(QDialog):
    def __init__(self, parent=None, mode="add", initial_data=None):
        super().__init__(parent)
        self.parent_window = parent
        self.mode = mode  # "add" ou "edit"
        self.initial_data = initial_data
        self.init_ui()
        self.apply_styles()

        if self.mode == "edit" and self.initial_data:
            self.populate_fields()

    def populate_fields(self):
        # Usar .get() com um valor padrão para evitar KeyError e TypeError se o valor for None
        self.matricula.setText(self.initial_data.get("matricula", ""))
        self.marca.setText(self.initial_data.get("marca", ""))
        # Convertendo para string apenas se não for None, caso contrário usa ""
        self.isv.setText(str(self.initial_data.get("isv", "")) if self.initial_data.get("isv") is not None else "")
        # AQUI ESTÁ A MUDANÇA PRINCIPAL PARA nRegistoContabilidade
        self.nRegistoContabilidade.setText(str(self.initial_data.get("nRegistoContabilidade", "")) if self.initial_data.get("nRegistoContabilidade") is not None else "")


        data_compra_str = self.initial_data.get("dataCompra")
        if data_compra_str: # Só tenta converter se a string não for vazia ou None
            self.dataCompra.setDate(QDate.fromString(data_compra_str, "yyyy-MM-dd"))
        else:
            self.dataCompra.setDate(QDate.currentDate()) # Define uma data padrão se não houver data

        self.docCompra.setText(self.initial_data.get("docCompra", ""))
        # Certifique-se de que o item selecionado existe no QComboBox
        tipo_documento_str = self.initial_data.get("tipoDocumento", "")
        index = self.tipoDocumento.findText(tipo_documento_str)
        if index >= 0:
            self.tipoDocumento.setCurrentIndex(index)
        else:
            self.tipoDocumento.setCurrentIndex(0) # Define o primeiro item como padrão


        self.valorCompra.setText(str(self.initial_data.get("valorCompra", "")) if self.initial_data.get("valorCompra") is not None else "")

        data_venda_str = self.initial_data.get("dataVenda")
        if data_venda_str: # Só tenta converter se a string não for vazia ou None
            self.dataVenda.setDate(QDate.fromString(data_venda_str, "yyyy-MM-dd"))
        else:
            self.dataVenda.setDate(QDate.currentDate()) # Define uma data padrão se não houver data

        self.docVenda.setText(self.initial_data.get("docVenda", ""))
        self.valorVenda.setText(str(self.initial_data.get("valorVenda", "")) if self.initial_data.get("valorVenda") is not None else "")

        self.imposto.setText(str(self.initial_data.get("imposto", "")) if self.initial_data.get("imposto") is not None else "")
        self.taxa.setText(str(self.initial_data.get("taxa", "")) if self.initial_data.get("taxa") is not None else "")

        regime_salvo = self.initial_data.get("regime_fiscal", "")
        if regime_salvo == "Regime Normal":  # <-- Possível problema aqui
            self.regime_geral_radio.setChecked(True)
        elif regime_salvo == "Margem":  # <-- Possível problema aqui
            self.regime_lucro_tributavel_radio.setChecked(True)
        else:
            # Se não houver nada salvo ou for um valor inesperado,
            # você pode decidir qual deve ser o padrão (e.g., nenhum ou um específico)
            self.regime_geral_radio.setChecked(False)
            self.regime_lucro_tributavel_radio.setChecked(False)

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

        self.imposto = QLineEdit()
        self.taxa = QLineEdit()

        # NOVOS CAMPOS: Checkboxes para o Regime Fiscal
        self.regime_geral_radio = QRadioButton("Regime Normal")
        self.regime_lucro_tributavel_radio = QRadioButton("Margem")

        # Layout para as checkboxes
        regime_layout = QHBoxLayout()
        regime_layout.addWidget(self.regime_geral_radio)
        regime_layout.addWidget(self.regime_lucro_tributavel_radio)
        regime_layout.addStretch(1)

        imposto_group = QGroupBox("Imposto")
        imposto_layout = QFormLayout()
        imposto_layout.addRow("Regime Fiscal:", regime_layout)
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

        btn_text = "Atualizar Registo" if self.mode == "edit" else "Adicionar Registo"
        self.add_button = QPushButton(btn_text)
        self.add_button.clicked.connect(self.add_record)
        main_layout.addWidget(self.add_button)

        self.setLayout(main_layout)

    def apply_styles(self):
        if self.parent_window is not None:
            self.setStyleSheet(self.parent_window.styleSheet())

    def add_record(self):
        try:
            isv = float(self.isv.text().replace(",", ".")) if self.isv.text() else None
            valor_compra = float(self.valorCompra.text().replace(",", ".")) if self.valorCompra.text() else None
            valor_venda = float(self.valorVenda.text().replace(",", ".")) if self.valorVenda.text() else None

            data_compra_str = self.dataCompra.date().toString("yyyy-MM-dd")
            data_venda_str = self.dataVenda.date().toString("yyyy-MM-dd")

            regime_fiscal = ""
            if self.regime_geral_radio.isChecked():
                regime_fiscal = "Regime Normal"
            elif self.regime_lucro_tributavel_radio.isChecked():
                regime_fiscal = "Margem"

            imposto = float(self.imposto.text().replace(",", ".")) if self.imposto.text() else None
            taxa = float(self.taxa.text().replace(",", ".")) if self.taxa.text() else None

            if self.mode == "edit":
                success = update_expense_in_db(self.initial_data["id"], {
                    "matricula": self.matricula.text(),
                    "marca": self.marca.text(),
                    "isv": isv,
                    "nRegistoContabilidade": self.nRegistoContabilidade.text(),
                    "dataCompra": data_compra_str,
                    "docCompra": self.docCompra.text(),
                    "tipoDocumento": self.tipoDocumento.currentText(),
                    "valorCompra": valor_compra,
                    "dataVenda": data_venda_str,
                    "docVenda": self.docVenda.text(),
                    "valorVenda": valor_venda,
                    "imposto": imposto,
                    "taxa": taxa,
                    "regime_fiscal": regime_fiscal # Já estava correto aqui
                })
            else:
                print("\n--- Argumentos passados para add_expense_to_db ---")
                print(f"matricula: {self.matricula.text()}")
                print(f"marca: {self.marca.text()}")
                print(f"isv: {isv}")
                print(f"nRegistoContabilidade: {self.nRegistoContabilidade.text()}")
                print(f"dataCompra: {data_compra_str}")
                print(f"docCompra: {self.docCompra.text()}")
                print(f"tipoDocumento: {self.tipoDocumento.currentText()}")
                print(f"valorCompra: {valor_compra}")
                print(f"dataVenda: {data_venda_str}")
                print(f"docVenda: {self.docVenda.text()}")
                print(f"valorVenda: {valor_venda}")
                print(f"imposto: {imposto}")
                print(f"taxa: {taxa}")
                print(f"regime_fiscal: {regime_fiscal}")
                print("--- Fim dos Argumentos ---")

                success = add_expense_to_db(
                    self.matricula.text(), self.marca.text(), isv,
                    self.nRegistoContabilidade.text(), data_compra_str, self.docCompra.text(),
                    self.tipoDocumento.currentText(), valor_compra, data_venda_str,
                    self.docVenda.text(), valor_venda, self.imposto.text(), self.taxa.text(),
                    regime_fiscal  # Esta linha é CRÍTICA
                )

            if success:
                self.close()
                self.parent_window.load_table_data()
                QMessageBox.information(self, "Sucesso", "Registo guardado com sucesso!")
            else:
                QMessageBox.critical(self, "Erro", "Erro ao guardar registo")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro: {e}")
            import traceback
            traceback.print_exc()

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

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Matrícula", "Marca", "Valor de Compra", "Documento de Venda", "Valor de Venda", "Imposto"]
        )
        self.table.setColumnHidden(0, True)  # Hide ID column
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.open_edit_expense_dialog)

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

    def open_edit_expense_dialog(self, row, column):
        vehicle_id = int(self.table.item(row, 0).text())  # Get the ID from the hidden column
        initial_data = fetch_vehicle_by_id(vehicle_id) # Fetch all data

        if initial_data:
            dialog = AddExpenseDialog(self, mode="edit", initial_data=initial_data)
            opacity_effect = QGraphicsOpacityEffect()
            opacity_effect.setOpacity(0.5)
            self.setGraphicsEffect(opacity_effect)
            dialog.exec()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível carregar os dados do veículo.")

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
        font-size: 14px;
        border: 1px solid #cfd9e1;
    }
    QTableWidget::item:selected {
        background-color: #d0d7de; /* Cinzento claro visível */
        color: #000000; /* Texto preto legível */
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

        expense_id = int(self.table.item(selected_row, 0).text())  # Hidden ID column
        confirm = QMessageBox.question(self, "Confirm", "Are you sure you want to delete this expense?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if confirm == QMessageBox.StandardButton.Yes:
            if delete_expense_from_db(expense_id):
                self.load_table_data()
                self.table.clearSelection()  # Deselect after deleting

    def clear_inputs(self):
        self.date_box.setDate(QDate.currentDate())
        self.dropdown.setCurrentIndex(0)
        self.amount.clear()
        self.description.clear()
