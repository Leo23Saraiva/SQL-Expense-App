from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QComboBox,
    QTableWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QTableWidgetItem,
    QHeaderView, QDialog, QGraphicsOpacityEffect, QGroupBox, QFormLayout,
    QRadioButton, QCalendarWidget
)
from PyQt6.QtCore import QDate, Qt, QLocale, QEvent
from PyQt6.QtGui import QValidator
from decimal import Decimal

from database import fetch_expenses, add_expense_to_db, delete_expense_from_db, update_expense_in_db, \
    fetch_vehicle_by_id


# --- NOVA CLASSE AUXILIAR PARA O CAMPO DE DATA PERSONALIZADO ---
class DateValidator(QValidator):
    def validate(self, input_str, pos):
        # Remove a máscara e tenta parsear
        cleaned_input = input_str.replace('-', '').strip()

        if not cleaned_input:
            # Se a string estiver vazia, é aceitável.
            return QValidator.State.Acceptable, input_str, pos

        # Se a string não for vazia, mas tiver menos de 8 dígitos (DDMMAAAA), é intermediária
        if len(cleaned_input) < 8:
            return QValidator.State.Intermediate, input_str, pos

        if len(cleaned_input) > 8:
            # Se tiver mais de 8 dígitos numéricos, é inválida
            return QValidator.State.Invalid, input_str, pos

        try:
            day = int(cleaned_input[0:2])
            month = int(cleaned_input[2:4])
            year = int(cleaned_input[4:8])
            qdate = QDate(year, month, day)

            if qdate.isValid():
                return QValidator.State.Acceptable, input_str, pos
            else:
                # Se os números não formam uma data válida (ex: 32-01-2023)
                return QValidator.State.Invalid, input_str, pos
        except ValueError:
            # Se a conversão para int falhar (não são dígitos)
            return QValidator.State.Invalid, input_str, pos


class CalendarDialog(QDialog):
    def __init__(self, parent=None, initial_date=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Data")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setFixedSize(320, 270)  # Aumentado o tamanho fixo para o diálogo do calendário

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked[QDate].connect(self.accept_date)

        # Configurar a data inicial do calendário
        if initial_date and initial_date.isValid():
            self.calendar.setSelectedDate(initial_date)
            # Garantir que o calendário mostra a página do mês/ano da data inicial
            self.calendar.setCurrentPage(initial_date.year(), initial_date.month())
        else:
            # Se a data inicial for inválida ou None, usar a data atual
            self.calendar.setSelectedDate(QDate.currentDate())
            self.calendar.setCurrentPage(QDate.currentDate().year(), QDate.currentDate().month())

        v_layout = QVBoxLayout()
        v_layout.addWidget(self.calendar)
        self.setLayout(v_layout)

        self.selected_date = None

    def accept_date(self, date):
        self.selected_date = date
        self.accept()  # Fecha o diálogo com QDialog.Accepted


class DateLineEdit(QHBoxLayout):
    def __init__(self, parent=None):
        super().__init__()
        self.parent_dialog = parent  # Referência ao AddExpenseDialog

        self.date_input = QLineEdit(parent)
        self.date_input.setPlaceholderText("DD-MM-AAAA")  # Placeholder para ajudar o utilizador
        # REMOVIDO: self.date_input.setInputMask("99-99-9999") # Máscara removida para depuração e flexibilidade
        self.date_input.setMinimumHeight(30)
        self.date_input.setValidator(DateValidator())  # Aplicar o validador
        self.date_input.textChanged.connect(self._format_date_on_input)  # Adicionar conexão para formatar

        # Event filter para capturar focus in/out
        self.date_input.installEventFilter(self)

        # Estilo específico para o QLineEdit interno
        self.date_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                font-size: 14px;
                color: #333;
                border: 1px solid #b0bfc6;
                border-radius: 5px;
                padding: 5px;
            }
            QLineEdit:hover {
                border: 1px solid #4caf50;
            }
            QLineEdit:focus {
                border: 1px solid #2a9d8f;
                background-color: #f5f9fc;
            }
            QLineEdit:invalid {
                border: 1px solid #ff6347; /* Vermelho/laranja escuro para inválido */
            }
            /* O estado intermediate agora tem a mesma borda que o estado normal/default */
            QLineEdit:intermediate {
                border: 1px solid #b0bfc6;
            }
        """)

        self.calendar_button = QPushButton("📅", parent)  # Ícone de calendário (Unicode)
        self.calendar_button.setFixedSize(30, 30)  # Tamanho fixo para o botão para que o ícone fique bem
        self.calendar_button.clicked.connect(self.show_calendar_dialog)
        # Estilo específico para o QPushButton do calendário para anular o estilo global
        self.calendar_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50; /* Um verde forte */
                color: white;
                border: 1px solid #3d8b40; /* Uma borda ligeiramente mais escura que o fundo */
                border-radius: 5px;
                font-size: 16px; /* Tamanho do ícone */
                padding: 0px; /* Remover padding extra */
            }
            QPushButton:hover {
                background-color: #45a049; /* Verde mais escuro no hover */
                border: 1px solid #367c39;
            }
            QPushButton:pressed {
                background-color: #3d8b40; /* Verde ainda mais escuro no pressed */
                border: 1px solid #2f6932;
            }
        """)

        self.addWidget(self.date_input)
        self.addWidget(self.calendar_button)
        self.setStretch(0, 1)  # Permite que o campo de texto ocupe a maior parte do espaço

    def eventFilter(self, obj, event):
        if obj == self.date_input:
            if event.type() == QEvent.Type.FocusOut:
                self._handle_focus_out()
            elif event.type() == QEvent.Type.FocusIn:
                self._handle_focus_in()
        return super().eventFilter(obj, event)

    def _handle_focus_in(self):
        # Quando o campo ganha foco, se estiver vazio, não faz nada (placeholder já está visível)
        pass

    def _handle_focus_out(self):
        current_text = self.date_input.text().strip()
        validator_state, _, _ = self.date_input.validator().validate(current_text, 0)

        if validator_state == QValidator.State.Invalid:
            print(f"[DEBUG - DateLineEdit] FocusOut: Data '{current_text}' inválida. Limpando campo.")
            self.date_input.clear()  # Limpa completamente se a data for inválida
        elif validator_state == QValidator.State.Intermediate:
            # Se for incompleta, tenta parsear para ver se é algo razoável
            qdate = self.date()
            if not qdate.isValid():
                print(f"[DEBUG - DateLineEdit] FocusOut: Data '{current_text}' incompleta e inválida. Limpando campo.")
                self.date_input.clear()  # Limpa se for incompleta e não puder ser uma data válida
            else:
                print(
                    f"[DEBUG - DateLineEdit] FocusOut: Data '{current_text}' incompleta mas válida para QDate. Mantendo.")
        else:
            print(f"[DEBUG - DateLineEdit] FocusOut: Data '{current_text}' aceitável. Mantendo.")

    def _format_date_on_input(self, text):
        cleaned_text = text.replace('-', '').strip()
        formatted_text = ""

        # Limita a entrada a 8 dígitos para evitar datas muito longas
        if len(cleaned_text) > 8:
            cleaned_text = cleaned_text[:8]

        if len(cleaned_text) > 0:
            if len(cleaned_text) <= 2:
                formatted_text = cleaned_text
            elif len(cleaned_text) <= 4:
                formatted_text = f"{cleaned_text[0:2]}-{cleaned_text[2:4]}"
            elif len(cleaned_text) <= 8:
                formatted_text = f"{cleaned_text[0:2]}-{cleaned_text[2:4]}-{cleaned_text[4:8]}"

            # Evita loops infinitos ao definir o texto
            if self.date_input.text() != formatted_text:
                self.date_input.blockSignals(True)
                self.date_input.setText(formatted_text)
                self.date_input.blockSignals(False)
                # Garante que o cursor permanece no final ou na posição correta
                self.date_input.setCursorPosition(len(formatted_text))

    def show_calendar_dialog(self):
        # Tenta obter a data atual do QLineEdit
        current_date_qdate = self.date()  # Usa o método .date() que retorna QDate ou QDate() inválida
        print(
            f"[DEBUG - DateLineEdit] Abrindo calendário. Data atual do campo: '{self.date_input.text()}' -> QDate: {current_date_qdate.toString(Qt.DateFormat.ISODate)} (isValid: {current_date_qdate.isValid()})")

        # Cria o diálogo do calendário com a data inicial
        # Se current_date_qdate for inválida (campo vazio ou data mal formatada), o CalendarDialog usará currentDate()
        dialog = CalendarDialog(self.parent_dialog, current_date_qdate)

        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_date:
            # Formata a data selecionada para "DD-MM-AAAA" e define no QLineEdit
            self.date_input.setText(dialog.selected_date.toString("dd-MM-yyyy"))
            print(f"[DEBUG - DateLineEdit] Calendar Selected: Set LineEdit to '{self.date_input.text()}'")
        else:
            # Se o diálogo for cancelado, a data existente no campo não é alterada.
            # O validador lidará com o estado se a data for inválida ou incompleta.
            print("[DEBUG - DateLineEdit] Calendar Cancelled or No Date Selected.")
            pass

    def text(self):
        """Retorna o texto do QLineEdit interno."""
        return self.date_input.text()

    def setText(self, text):
        """Define o texto do QLineEdit interno.
        Esta função também deve ser responsável por formatar o texto corretamente.
        """
        print(f"[DEBUG - DateLineEdit] setText called with raw text: '{text}'")
        if not text:
            self.date_input.clear()
            print("[DEBUG - DateLineEdit] setText: Cleared field because text was empty.")
        else:
            # Tenta converter o texto para QDate para ver se é um formato válido
            # Assumimos que o texto de entrada do DB é "yyyy-MM-dd"
            qdate = QDate.fromString(text, "yyyy-MM-dd")
            if qdate.isValid():
                # Se for válido, formata para DD-MM-AAAA e define
                formatted_text = qdate.toString("dd-MM-yyyy")
                print(
                    f"[DEBUG - DateLineEdit] setText: Converted '{text}' (yyyy-MM-dd) to '{formatted_text}' (dd-MM-yyyy).")
                self.date_input.blockSignals(True)
                self.date_input.setText(formatted_text)
                self.date_input.blockSignals(False)
            else:
                # Se não for um QDate válido do formato esperado, apenas define o texto bruto
                # e deixa o validador/formatador lidar com isso no textChanged
                print(f"[DEBUG - DateLineEdit] setText: '{text}' not a valid yyyy-MM-dd. Setting raw text.")
                self.date_input.blockSignals(True)
                self.date_input.setText(text)
                self.date_input.blockSignals(False)
        # O textChanged do QLineEdit interno vai chamar _format_date_on_input
        # que fará a formatação final e posicionamento do cursor.

    def date(self):
        """Retorna um objeto QDate do texto do QLineEdit interno (espera DD-MM-AAAA)."""
        date_str = self.date_input.text().replace('-', '').strip()
        if len(date_str) == 8:
            try:
                day = int(date_str[0:2])
                month = int(date_str[2:4])
                year = int(date_str[4:8])
                qdate = QDate(year, month, day)
                if qdate.isValid():
                    return qdate
            except ValueError:
                pass
        return QDate()  # Retorna uma data inválida se não puder ser parseada

    def setDate(self, qdate):
        """Define a data no QLineEdit interno a partir de um objeto QDate.
        Este método é usado para carregar a data programaticamente.
        """
        if qdate and qdate.isValid():  # Garante que qdate não é None e é válida
            formatted_date_str = qdate.toString("dd-MM-yyyy")
            print(
                f"[DEBUG - DateLineEdit] setDate called with QDate: {qdate.toString(Qt.DateFormat.ISODate)} (isValid: {qdate.isValid()}). Setting text to '{formatted_date_str}'.")
            self.date_input.blockSignals(
                True)  # Bloca sinais para evitar _format_date_on_input ser chamado prematuramente
            self.date_input.setText(formatted_date_str)
            self.date_input.blockSignals(False)
            # A função _format_date_on_input já lida com o posicionamento do cursor
        else:
            print(f"[DEBUG - DateLineEdit] setDate called with invalid QDate or None. Clearing field.")
            self.date_input.clear()


class AddExpenseDialog(QDialog):
    def __init__(self, parent=None, mode="add", initial_data=None):
        super().__init__(parent)
        self.parent_window = parent
        self.mode = mode  # "add" ou "edit"
        self.initial_data = initial_data
        self.init_ui()
        self.apply_styles()

        # Desabilitar os radio buttons por defeito
        self.regime_geral_radio.setEnabled(False)
        self.regime_lucro_tributavel_radio.setEnabled(False)

        # Conectar os sinais textChanged dos campos relevantes para atualizar estados e CÁLCULOS
        self.valorCompra.textChanged.connect(self.update_regime_button_states)
        self.valorCompra.textChanged.connect(self.calculate_regime_fields)
        self.valorVenda.textChanged.connect(self.update_regime_button_states)
        self.valorVenda.textChanged.connect(self.calculate_regime_fields)

        # Conectar o sinal currentIndexChanged do QComboBox da taxa
        self.taxa.currentIndexChanged.connect(self.update_regime_button_states)
        self.taxa.currentIndexChanged.connect(self.calculate_regime_fields)

        # Conectar o sinal clicked dos radio buttons (para capturar a seleção real e disparar cálculo)
        self.regime_geral_radio.clicked.connect(self.handle_regime_selection)
        self.regime_geral_radio.clicked.connect(self.calculate_regime_fields)
        self.regime_lucro_tributavel_radio.clicked.connect(self.handle_regime_selection)
        self.regime_lucro_tributavel_radio.clicked.connect(self.calculate_regime_fields)

        # Variável para armazenar o QRadioButton que estava selecionado por último de forma válida
        # Será None se nenhum estiver selecionado ou se a validação falhar
        self.last_valid_regime_radio = None

        if self.mode == "edit" and self.initial_data:
            self.populate_fields()
            # Após popular os campos, atualiza o estado dos radio buttons e, se aplicável, recalcula
            self.update_regime_button_states()
            self.calculate_regime_fields()
            # Define o last_valid_regime_radio com base no que foi carregado
            if self.regime_geral_radio.isChecked():
                self.last_valid_regime_radio = self.regime_geral_radio
            elif self.regime_lucro_tributavel_radio.isChecked():
                self.last_valid_regime_radio = self.regime_lucro_tributavel_radio

    def populate_fields(self):
        print("[DEBUG - AddExpenseDialog] Populating fields...")
        # Usar .get() com um valor padrão para evitar KeyError e TypeError se o valor for None
        self.matricula.setText(self.initial_data.get("matricula", ""))
        self.marca.setText(self.initial_data.get("marca", ""))
        self.numeroQuadro.setText(self.initial_data.get("numeroQuadro", ""))

        # --- FUNÇÃO AUXILIAR PARA FORMATAR NÚMEROS REAIS (Vazio para None/Vazio) ---
        # NOVO: Esta função agora usa QLocale para formatação localizada (pontos de milhar, vírgula decimal)
        def format_real_for_display(value):
            locale = QLocale(QLocale.Language.Portuguese, QLocale.Country.Portugal)
            try:
                if value is None or (isinstance(value, str) and not value.strip()):
                    return ""
                else:
                    numeric_value = float(value)
                    # Formata como moeda, mas sem o símbolo da moeda, com 2 casas decimais
                    return locale.toString(numeric_value, 'f', 2)
            except (ValueError, TypeError):
                return ""

        # --- FIM DA FUNÇÃO AUXILIAR ---

        self.isv.setText(format_real_for_display(self.initial_data.get("isv")))

        # Mantendo nRegistoContabilidade como TEXT no populate_fields conforme a sua decisão anterior
        self.nRegistoContabilidade.setText(
            str(self.initial_data.get("nRegistoContabilidade", "")) if self.initial_data.get(
                "nRegistoContabilidade") is not None else "")

        data_compra_str = self.initial_data.get("dataCompra", "")
        print(f"[DEBUG - AddExpenseDialog] dataCompra_str from DB: '{data_compra_str}'")
        # Usar o setter do DateLineEdit que lida com QDate ou string vazia
        # O setText do DateLineEdit vai agora fazer a conversão de yyyy-MM-dd para dd-MM-yyyy
        self.dataCompra.setText(data_compra_str)
        print(f"[DEBUG - AddExpenseDialog] After dataCompra.setText, field content: '{self.dataCompra.text()}'")

        self.docCompra.setText(self.initial_data.get("docCompra", ""))
        # Certifique-se de que o item selecionado existe no QComboBox
        tipo_documento_str = self.initial_data.get("tipoDocumento", "")
        index = self.tipoDocumento.findText(tipo_documento_str)
        if index >= 0:
            self.tipoDocumento.setCurrentIndex(index)
        else:
            self.tipoDocumento.setCurrentIndex(0)  # Define o primeiro item como padrão

        self.valorCompra.setText(format_real_for_display(self.initial_data.get("valorCompra")))

        data_venda_str = self.initial_data.get("dataVenda", "")
        print(f"[DEBUG - AddExpenseDialog] dataVenda_str from DB: '{data_venda_str}'")
        # Usar o setter do DateLineEdit que lida com QDate ou string vazia
        self.dataVenda.setText(data_venda_str)
        print(f"[DEBUG - AddExpenseDialog] After dataVenda.setText, field content: '{self.dataVenda.text()}'")

        self.docVenda.setText(
            format_real_for_display(self.initial_data.get("docVenda")))  # Este deve ser texto, não real.
        self.valorVenda.setText(format_real_for_display(self.initial_data.get("valorVenda")))

        # Aplicar a função de formatação para imposto, valorBase
        self.imposto.setText(format_real_for_display(self.initial_data.get("imposto")))
        self.valorBase.setText(format_real_for_display(self.initial_data.get("valorBase")))

        # Popula o QComboBox da taxa
        taxa_value = self.initial_data.get("taxa")
        # Correção: Se taxa_value for None ou vazio, define para "N/A"
        if taxa_value is None or (isinstance(taxa_value, str) and not taxa_value.strip()):
            self.taxa.setCurrentText("N/A")
        else:
            # Converte para string para encontrar o item na combobox (ex: 6.0 -> "6")
            # Usa str(int(taxa_value)) apenas se for um número inteiro, para evitar ".0"
            try:
                numeric_taxa = float(taxa_value)
                if numeric_taxa.is_integer():
                    taxa_str = str(int(numeric_taxa))
                else:
                    taxa_str = str(
                        numeric_taxa)  # Para o caso de ter casas decimais (embora não esperado para 6, 13, 23)
            except (ValueError, TypeError):
                taxa_str = ""  # Em caso de erro na conversão, trata como vazio

            index = self.taxa.findText(taxa_str)
            if index >= 0:
                self.taxa.setCurrentIndex(index)
            else:
                self.taxa.setCurrentText("N/A")  # Fallback se o valor não estiver na lista ou for inválido

        # Carregar o regime fiscal salvo, desabilitando sinais para não disparar handle_regime_selection
        self.regime_geral_radio.blockSignals(True)
        self.regime_lucro_tributavel_radio.blockSignals(True)

        regime_salvo = self.initial_data.get("regime_fiscal", "")
        print(f"[DEBUG - AddExpenseDialog] Regime fiscal from DB: '{regime_salvo}'")
        if regime_salvo == "Regime Normal":
            self.regime_geral_radio.setChecked(True)
        elif regime_salvo == "Margem":
            self.regime_lucro_tributavel_radio.setChecked(True)
        else:
            self.regime_geral_radio.setChecked(False)
            self.regime_lucro_tributavel_radio.setChecked(False)

        self.regime_geral_radio.blockSignals(False)
        self.regime_lucro_tributavel_radio.blockSignals(False)
        print("[DEBUG - AddExpenseDialog] Populating fields finished.")

    def init_ui(self):
        self.setWindowTitle("MBAuto - Detalhes")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Campos
        self.matricula = QLineEdit()
        self.marca = QLineEdit()
        self.numeroQuadro = QLineEdit()
        self.isv = QLineEdit()
        self.nRegistoContabilidade = QLineEdit()

        # Substituir QDateEdit por DateLineEdit personalizado
        self.dataCompra = DateLineEdit(self)  # Passar self para a referência parent_dialog
        self.docCompra = QLineEdit()
        self.tipoDocumento = QComboBox()
        self.tipoDocumento.addItems(["Fatura", "Fatura-Recibo", "Fatura Simplificada", "Declaração"])
        self.valorCompra = QLineEdit()

        # Substituir QDateEdit por DateLineEdit personalizado
        self.dataVenda = DateLineEdit(self)  # Passar self para a referência parent_dialog
        self.docVenda = QLineEdit()
        self.valorVenda = QLineEdit()

        # Taxa agora é um QComboBox
        self.taxa = QComboBox()
        self.taxa.addItems(["N/A", "6", "13", "23"])  # Valores da dropdown

        self.valorBase = QLineEdit()
        self.imposto = QLineEdit()  # Imposto agora é um output

        # NOVOS CAMPOS: Radio Buttons para o Regime Fiscal
        self.regime_geral_radio = QRadioButton("Regime Normal")
        self.regime_lucro_tributavel_radio = QRadioButton("Margem")

        # Layout para os radio buttons
        regime_layout = QHBoxLayout()
        regime_layout.addWidget(self.regime_geral_radio)
        regime_layout.addWidget(self.regime_lucro_tributavel_radio)
        regime_layout.addStretch(1)

        imposto_group = QGroupBox("Imposto")
        imposto_layout = QFormLayout()
        imposto_layout.addRow("Regime Fiscal:", regime_layout)
        imposto_layout.addRow("Taxa:", self.taxa)  # Taxa agora é um QComboBox
        imposto_layout.addRow("Valor Base:", self.valorBase)
        imposto_layout.addRow("Imposto:", self.imposto)
        imposto_group.setLayout(imposto_layout)

        # Layout principal - Adicionar os grupos de campos aqui
        identificacao_group = QGroupBox("Identificação do Veículo")
        identificacao_layout = QFormLayout()
        identificacao_layout.addRow("Matrícula:", self.matricula)
        identificacao_layout.addRow("Marca:", self.marca)
        identificacao_layout.addRow("Número de Quadro:", self.numeroQuadro)
        identificacao_layout.addRow("ISV:", self.isv)
        identificacao_layout.addRow("Nº Registo Contabilidade:", self.nRegistoContabilidade)
        identificacao_group.setLayout(identificacao_layout)

        compras_group = QGroupBox("Detalhes da Compra")
        compras_layout = QFormLayout()
        # Adiciona o DateLineEdit ao layout usando addLayout
        compras_layout.addRow("Data da Compra:", self.dataCompra)
        compras_layout.addRow("Doc. Compra:", self.docCompra)
        compras_layout.addRow("Tipo Documento:", self.tipoDocumento)
        compras_layout.addRow("Valor de Compra:", self.valorCompra)
        compras_group.setLayout(compras_layout)

        vendas_group = QGroupBox("Detalhes da Venda")
        vendas_layout = QFormLayout()
        # Adiciona o DateLineEdit ao layout usando addLayout
        vendas_layout.addRow("Data da Venda:", self.dataVenda)
        vendas_layout.addRow("Doc. Venda:", self.docVenda)
        vendas_layout.addRow("Valor de Venda:", self.valorVenda)
        vendas_group.setLayout(vendas_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(identificacao_group)
        main_layout.addWidget(compras_group)
        main_layout.addWidget(vendas_group)
        main_layout.addWidget(imposto_group)

        # Não é necessário definir minimum height aqui para DateLineEdit, ele já tem no construtor
        # self.dataCompra.setMinimumHeight(30)
        # self.dataVenda.setMinimumHeight(30)

        btn_text = "Atualizar Registo" if self.mode == "edit" else "Adicionar Registo"
        self.add_button = QPushButton(btn_text)
        self.add_button.clicked.connect(self.add_record)
        main_layout.addWidget(self.add_button)

        self.setLayout(main_layout)

    def apply_styles(self):
        # Apenas um ajuste para o estilo do QLineEdit na classe principal,
        # pois o DateLineEdit tem seu próprio estilo para o QLineEdit interno.
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
    QLineEdit, QComboBox { /* Apply this to regular QLineEdit and QComboBox */
        background-color: #ffffff;
        font-size: 14px;
        color: #333;
        border: 1px solid #b0bfc6;
        border-radius: 5px;
        padding: 5px;
    }
    QLineEdit:hover, QComboBox:hover {
        border: 1px solid #4caf50; /* Borda verde no hover */
    }
    QLineEdit:focus, QComboBox:focus {
        border: 1px solid #2a9d8f; /* Borda verde mais escura no focus */
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
        background-color: #d0d7de;
        color: #000000;
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
    /* Este estilo geral para QPushButton é apenas para botões fora do DateLineEdit */
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

    /* ESTILO PARA QRadioButton */
    QRadioButton {
        color: #333; /* Cor do texto mais escura para melhor legibilidade */
        padding: 4px 0px; /* Mantém o padding */
    }

    QRadioButton::indicator {
        width: 16px;
        height: 16px;
        border-radius: 8px; /* Mantém o indicador redondo */
        border: 2px solid #555555; /* Borda mais escura para o indicador (normal) */
        background-color: #ffffff; /* Fundo branco para o indicador (normal) */
    }

    QRadioButton::indicator:hover {
        border: 2px solid #4caf50; /* Borda verde mais escura no hover */
    }

    QRadioButton::indicator:checked {
        background-color: #4caf50; /* Preenchimento verde quando selecionado */
        border: 2px solid #2a9d8f; /* Borda verde mais escura quando selecionado */
    }

    /* NOVO ESTILO: QRadioButton quando desabilitado */
    QRadioButton:disabled {
        color: #a0a0a0; /* Cor do texto cinzento */
    }

    QRadioButton::indicator:disabled {
        background-color: #e0e0e0; /* Fundo cinzento claro para o indicador */
        border: 2px solid #b0b0b0; /* Borda cinzenta mais escura */
    }

    /* Estilo para QCalendarWidget */
    QCalendarWidget {
        background-color: #ffffff;
        border: 1px solid #cfd9e1;
        border-radius: 5px;
    }

    QCalendarWidget QWidget#qt_calendar_navigationbar { /* Barra de navegação */
        background-color: #e8ecf4; 
        color: white; /* Cor do texto para toda a barra */
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
    }
    /* Estilo dos botões de navegação e ano/mês */
    QCalendarWidget QWidget#qt_calendar_navigationbar QPushButton {
        background-color: #4caf50; /* Verde */
        color: white;
        border: 1px solid #3d8b40;
        border-radius: 3px;
        font-size: 16px;
        padding: 5px;
    }
    QCalendarWidget QWidget#qt_calendar_navigationbar QPushButton:hover {
        background-color: #45a049;
    }
    QCalendarWidget QWidget#qt_calendar_navigationbar QPushButton:pressed {
        background-color: #3d8b40;
    }
    /* Spinbox de ano e mês no calendário */
    QCalendarWidget QSpinBox {
        border: 1px solid #b0bfc6;
        border-radius: 3px;
        padding-right: 15px; /* Espaço para o botão de seta */
        color: white; /* Cor do texto do spinbox */
        background-color: #4caf50; /* Fundo verde para o spinbox */
    }
    QCalendarWidget QSpinBox::up-button, QCalendarWidget QSpinBox::down-button {
        width: 16px;
        border: 1px solid #b0bfc6;
        border-radius: 3px;
        background-color: #f0f0f0;
    }
    QCalendarWidget QSpinBox::up-arrow, QCalendarWidget QSpinBox::down-arrow {
        width: 10px;
        height: 10px;
    }
    QCalendarWidget QSpinBox::up-button:hover, QCalendarWidget QSpinBox::down-button:hover {
        background-color: #e0e0e0;
    }

    QCalendarWidget QAbstractItemView { /* Grid do calendário */
        selection-background-color: #d0d7de; /* Cor de fundo da seleção ao passar o rato */
        selection-color: #000000; /* Cor do texto da seleção ao passar o rato */
        outline: none; /* Remover a borda de foco */
    }
    /* Estilo para o dia normal no calendário */
    QCalendarWidget QAbstractItemView:enabled {
        color: #333; /* Cor do texto padrão para dias */
    }

    QCalendarWidget QAbstractItemView:enabled:hover {
        background-color: #f2f7fb; /* Cor de fundo ao passar o mouse */
    }

    QCalendarWidget QAbstractItemView:selected {
        background-color: #2a9d8f; /* Cor do fundo do dia selecionado (verde mais escuro) */
        color: white; /* Cor do texto do dia selecionado */
    }

    /* Para o dia de hoje - agora será um círculo cinza suave com borda verde */
    QCalendarWidget QAbstractItemView:!selected:focus { /* Dia de hoje, se não estiver selecionado */
        background-color: #e0e0e0; /* Cinza suave para o dia de hoje */
        color: #000000;
        border: 1px solid #4caf50; /* Borda verde suave */
        border-radius: 50%; /* Faz um círculo */
    }
    /* Para a borda à volta do número do dia */
    QCalendarWidget QCalendarView::item {
        border-radius: 0px; /* Reset para itens normais */
    }
""")

    # Função auxiliar para lidar com a conversão e arredondamento
    def get_float_value(self, input_widget):
        if isinstance(input_widget, QLineEdit):
            text = input_widget.text()
        elif isinstance(input_widget, QComboBox):
            text = input_widget.currentText()
            if text == "N/A" or not text.strip():  # Considerar "N/A" ou string vazia como None
                return None
        else:
            return None  # Tipo de widget não suportado

        # Primeiro remover todos os tipos de espaço
        text = text.replace("\u202f", "").replace(" ", "").replace("\xa0", "").strip()
        # Agora substituir a vírgula decimal por ponto
        text = text.replace(",", ".")

        try:
            return round(float(text), 2)
        except ValueError:
            print(f"[DEBUG] Erro ao converter valor para float: {text}")
            return None

    # Validação para o Regime Normal (Valor de Venda e Taxa)
    def are_normal_regime_fields_valid(self):
        """Verifica se os campos necessários para 'Regime Normal' estão preenchidos."""
        # Agora verifica o valor do QComboBox da taxa
        return (self.get_float_value(self.valorVenda) is not None and
                self.get_float_value(self.taxa) is not None)

    # Validação para o Regime de Margem (Valor de Compra, Valor de Venda e Taxa)
    def are_margin_regime_fields_valid(self):
        """Verifica se os campos necessários para 'Margem' estão preenchidos."""
        # Agora verifica o valor do QComboBox da taxa
        return (self.get_float_value(self.valorCompra) is not None and
                self.get_float_value(self.valorVenda) is not None and
                self.get_float_value(self.taxa) is not None)

    def calculate_regime_fields(self):
        """
        Calcula automaticamente os campos 'Valor Base' e 'Imposto' com base no regime fiscal selecionado
        e nos valores de compra, venda e taxa.
        """
        # Desabilitamos sinais dos QLineEdit temporariamente para não disparar recursão
        self.valorBase.blockSignals(True)
        self.imposto.blockSignals(True)

        # Usar QLocale para formatar os resultados
        locale = QLocale(QLocale.Language.Portuguese, QLocale.Country.Portugal)

        try:
            if self.regime_geral_radio.isChecked() and self.are_normal_regime_fields_valid():
                # Lógica de cálculo para Regime Normal
                valor_venda = self.get_float_value(self.valorVenda)
                taxa_percent = self.get_float_value(self.taxa)  # Obter valor do QComboBox

                if valor_venda is not None and taxa_percent is not None:
                    divisor = (1 + taxa_percent / 100)
                    if divisor != 0:
                        valor_base_calculado = valor_venda / divisor
                        imposto_calculado = valor_base_calculado * (taxa_percent / 100)

                        self.valorBase.setText(locale.toString(valor_base_calculado, 'f', 2))
                        self.imposto.setText(locale.toString(imposto_calculado, 'f', 2))

                        print(f"[DEBUG] Valor calculado - valorBase (Regime Normal): {valor_base_calculado}")
                        print(f"[DEBUG] Valor calculado - imposto (Regime Normal): {imposto_calculado}")
                    else:
                        self.valorBase.setText("Divisão por Zero")
                        self.imposto.setText("Erro")
                else:
                    self.valorBase.clear()
                    self.imposto.clear()

            elif self.regime_lucro_tributavel_radio.isChecked() and self.are_margin_regime_fields_valid():
                # Lógica de cálculo para Regime de Margem
                valor_venda = self.get_float_value(self.valorVenda)
                valor_compra = self.get_float_value(self.valorCompra)
                taxa_percent = self.get_float_value(self.taxa)  # Obter valor do QComboBox

                if valor_venda is not None and valor_compra is not None and taxa_percent is not None:
                    margem_bruta = valor_venda - valor_compra
                    divisor = (1 + taxa_percent / 100)
                    if divisor != 0:
                        valor_base_calculado = margem_bruta / divisor
                        imposto_calculado = valor_base_calculado * (taxa_percent / 100)

                        self.valorBase.setText(locale.toString(valor_base_calculado, 'f', 2))
                        self.imposto.setText(locale.toString(imposto_calculado, 'f', 2))

                        print(f"[DEBUG] Valor calculado - valorBase (Margem): {valor_base_calculado}")
                        print(f"[DEBUG] Valor calculado - imposto (Margem): {imposto_calculado}")
                    else:
                        self.valorBase.setText("Divisão por Zero")
                        self.imposto.setText("Erro")
                else:
                    self.valorBase.clear()
                    self.imposto.clear()
            else:
                # Se nenhum regime válido estiver selecionado ou os campos não forem válidos, limpar
                self.valorBase.clear()
                self.imposto.clear()

        except Exception as e:
            print(f"Erro no cálculo de campos: {e}")
            self.valorBase.clear()
            self.imposto.clear()

        # Reabilitar sinais dos QLineEdit
        self.valorBase.blockSignals(False)
        self.imposto.blockSignals(False)

    def update_regime_button_states(self):
        """Habilita/desabilita os radio buttons com base na validação dos campos."""

        # Desabilitamos os sinais dos radio buttons para evitar loops ou seleção automática indesejada
        self.regime_geral_radio.blockSignals(True)
        self.regime_lucro_tributavel_radio.blockSignals(True)

        can_select_normal = self.are_normal_regime_fields_valid()
        can_select_margin = self.are_margin_regime_fields_valid()

        self.regime_geral_radio.setEnabled(can_select_normal)
        self.regime_lucro_tributavel_radio.setEnabled(can_select_margin)

        # Se o regime atualmente selecionado (last_valid_regime_radio)
        # se tornar inválido, desmarca-o.
        if self.regime_geral_radio.isChecked() and not can_select_normal:
            self.regime_geral_radio.setChecked(False)
            self.last_valid_regime_radio = None

        if self.regime_lucro_tributavel_radio.isChecked() and not can_select_margin:
            self.regime_lucro_tributavel_radio.setChecked(False)
            self.last_valid_regime_radio = None

        # Re-marcar o último regime válido se ele ainda for válido
        if self.last_valid_regime_radio == self.regime_geral_radio and can_select_normal:
            self.regime_geral_radio.setChecked(True)
        elif self.last_valid_regime_radio == self.regime_lucro_tributavel_radio and can_select_margin:
            self.regime_lucro_tributavel_radio.setChecked(True)
        else:
            # Se o último regime válido não puder ser re-marcado (tornou-se inválido),
            # ou se não havia last_valid_regime_radio e nenhum está marcado,
            # garante que nenhum radio está marcado e que o cálculo é limpo.
            if not self.regime_geral_radio.isChecked() and not self.regime_lucro_tributavel_radio.isChecked():
                self.valorBase.clear()
                self.imposto.clear()

        self.regime_geral_radio.blockSignals(False)
        self.regime_lucro_tributavel_radio.blockSignals(False)

        # Após atualizar os estados dos botões (e possivelmente desmarcar um radio),
        # Dispara o cálculo novamente para garantir que os campos de imposto são atualizados.
        self.calculate_regime_fields()

    def handle_regime_selection(self):
        """
        Lida com a seleção de um regime fiscal, atualizando last_valid_regime_radio.
        A validação de campos obrigatórios é feita no update_regime_button_states
        e na validação final antes de salvar.
        """
        sender_radio = self.sender()
        if sender_radio.isChecked():
            # Se um radio button foi clicado e está marcado, ele é o novo last_valid_regime_radio.
            # A validade dos campos já foi verificada pelo update_regime_button_states que habilitou o botão.
            self.last_valid_regime_radio = sender_radio
            print(f"Regime selecionado: {sender_radio.text()}")
        else:
            # Se um radio button foi desmarcado (o que só acontece se o outro for marcado)
            # e não temos um last_valid_regime_radio atual, então limpamos.
            # Isso é mais uma salvaguarda, pois last_valid_regime_radio deve sempre apontar para o marcado.
            if self.last_valid_regime_radio == sender_radio:
                self.last_valid_regime_radio = None

        # Dispara o cálculo assim que um regime é selecionado
        self.calculate_regime_fields()

    def validate_all_fields_for_save(self):
        missing_fields = []

        # Validações de campos gerais (matrícula, marca, etc.)
        if not self.matricula.text().strip():
            missing_fields.append("Matrícula")
        if not self.marca.text().strip():
            missing_fields.append("Marca")

        # Validação das datas usando o método .date() do DateLineEdit
        # Apenas se a data não estiver vazia, verifica se é válida.
        # Se estiver vazia, o validador já a marca como Acceptable.
        if self.dataCompra.text().strip() and not self.dataCompra.date().isValid():
            QMessageBox.warning(self, "Data Inválida",
                                "Por favor, insira uma 'Data da Compra' válida (DD-MM-AAAA) ou deixe o campo vazio.")
            return False
        if self.dataVenda.text().strip() and not self.dataVenda.date().isValid():
            QMessageBox.warning(self, "Data Inválida",
                                "Por favor, insira uma 'Data da Venda' válida (DD-MM-AAAA) ou deixe o campo vazio.")
            return False

        if missing_fields:
            QMessageBox.warning(self, "Campos Obrigatórios em Falta",
                                f"Por favor, preencha os seguintes campos obrigatórios:\n\n- " +
                                "\n- ".join(missing_fields))
            return False

        # Valida os campos específicos do regime selecionado APENAS SE FOR SELECIONADO
        current_regime_selected = None
        if self.regime_geral_radio.isChecked():
            current_regime_selected = "Regime Normal"
        elif self.regime_lucro_tributavel_radio.isChecked():
            current_regime_selected = "Margem"

        if current_regime_selected == "Regime Normal":
            # Aqui, taxa é um QComboBox, então passamos o widget diretamente
            if not self.are_normal_regime_fields_valid():
                QMessageBox.warning(self, "Campos em Falta para Regime Normal",
                                    "Por favor, preencha 'Valor de Venda' e selecione uma 'Taxa' para o Regime Normal.")
                return False

        elif current_regime_selected == "Margem":
            # Aqui, taxa é um QComboBox, então passamos o widget diretamente
            if not self.are_margin_regime_fields_valid():
                QMessageBox.warning(self, "Campos em Falta para Regime Margem",
                                    "Por favor, preencha 'Valor de Compra', 'Valor de Venda' e selecione uma 'Taxa' para o Regime Margem.")
                return False

        return True

    def add_record(self):
        self.calculate_regime_fields()
        # Antes de adicionar/atualizar, chamar a validação final
        if not self.validate_all_fields_for_save():
            return  # Se a validação falhar, não prossegue com a gravação

        try:
            isv = self.get_float_value(self.isv)  # Ajustado para passar o widget
            nRegistoContabilidade = self.nRegistoContabilidade.text()
            numero_quadro = self.numeroQuadro.text()

            valor_compra = self.get_float_value(self.valorCompra)  # Ajustado para passar o widget
            valor_venda = self.get_float_value(self.valorVenda)  # Ajustado para passar o widget
            taxa = self.get_float_value(self.taxa)  # Obter valor do QComboBox usando get_float_value

            valorBase_from_field = self.get_float_value(self.valorBase)  # Ajustado para passar o widget
            imposto_from_field = self.get_float_value(self.imposto)  # Ajustado para passar o widget

            print(f"[DEBUG - AddExpenseDialog] Saving - valorBase: {valorBase_from_field}")
            print(f"[DEBUG - AddExpenseDialog] Saving - imposto: {imposto_from_field}")
            print(f"[DEBUG - AddExpenseDialog] Saving - taxa: {taxa}")

            # Obter a string da data do DateLineEdit (já formatada para DD-MM-AAAA ou vazia)
            data_compra_ddmmyyyy = self.dataCompra.text()
            data_venda_ddmmyyyy = self.dataVenda.text()

            # Converter para yyyy-MM-dd para armazenar no DB
            data_compra_db = ""
            if data_compra_ddmmyyyy:
                qdate_compra = QDate.fromString(data_compra_ddmmyyyy, "dd-MM-yyyy")
                if qdate_compra.isValid():
                    data_compra_db = qdate_compra.toString("yyyy-MM-dd")
            print(
                f"[DEBUG - AddExpenseDialog] dataCompra_ddmmyyyy: '{data_compra_ddmmyyyy}' -> dataCompra_db: '{data_compra_db}'")

            data_venda_db = ""
            if data_venda_ddmmyyyy:
                qdate_venda = QDate.fromString(data_venda_ddmmyyyy, "dd-MM-yyyy")
                if qdate_venda.isValid():
                    data_venda_db = qdate_venda.toString("yyyy-MM-dd")
            print(
                f"[DEBUG - AddExpenseDialog] dataVenda_ddmmyyyy: '{data_venda_ddmmyyyy}' -> dataVenda_db: '{data_venda_db}'")

            regime_fiscal = ""
            if self.regime_geral_radio.isChecked():
                regime_fiscal = "Regime Normal"
            elif self.regime_lucro_tributavel_radio.isChecked():
                regime_fiscal = "Margem"

            if self.mode == "edit":
                success = update_expense_in_db(self.initial_data["id"], {
                    "matricula": self.matricula.text(),
                    "marca": self.marca.text(),
                    "numeroQuadro": numero_quadro,
                    "isv": isv,
                    "nRegistoContabilidade": nRegistoContabilidade,
                    "dataCompra": data_compra_db,  # Salvar no DB como yyyy-MM-dd
                    "docCompra": self.docCompra.text(),
                    "tipoDocumento": self.tipoDocumento.currentText(),
                    "valorCompra": valor_compra,
                    "dataVenda": data_venda_db,  # Salvar no DB como yyyy-MM-dd
                    "docVenda": self.docVenda.text(),
                    "valorVenda": valor_venda,
                    "imposto": imposto_from_field,
                    "valorBase": valorBase_from_field,
                    "taxa": taxa,
                    "regime_fiscal": regime_fiscal
                })
            else:
                print("\n--- Argumentos passados para add_expense_to_db ---")
                print(f"matricula: {self.matricula.text()}")
                print(f"marca: {self.marca.text()}")
                print(f"numeroQuadro: {numero_quadro}")
                print(f"isv: {isv}")
                print(f"nRegistoContabilidade: {nRegistoContabilidade}")
                print(f"dataCompra: {data_compra_db}")
                print(f"docCompra: {self.docCompra.text()}")
                print(f"tipoDocumento: {self.tipoDocumento.currentText()}")
                print(f"valorCompra: {valor_compra}")
                print(f"dataVenda: {data_venda_db}")
                print(f"docVenda: {self.docVenda.text()}")
                print(f"valorVenda: {valor_venda}")
                print(f"imposto: {imposto_from_field}")
                print(f"valorBase: {valorBase_from_field}")
                print(f"taxa: {taxa}")
                print(f"regime_fiscal: {regime_fiscal}")
                print("--- Fim dos Argumentos ---")

                success = add_expense_to_db(
                    self.matricula.text(), self.marca.text(), numero_quadro, isv,
                    nRegistoContabilidade,
                    data_compra_db, self.docCompra.text(),  # Salvar no DB como yyyy-MM-dd
                    self.tipoDocumento.currentText(), valor_compra, data_venda_db,  # Salvar no DB como yyyy-MM-dd
                    self.docVenda.text(), valor_venda, imposto_from_field, valorBase_from_field, taxa,
                    regime_fiscal
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

    def closeEvent(self, event):
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

        # Mantemos as 7 colunas visíveis na tabela principal
        # As colunas da tabela principal são: ID, Matrícula, Marca, Valor de Compra, Documento de Venda, Valor de Venda, Imposto
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Matrícula", "Marca", "Valor de Compra", "Documento de Venda", "Valor de Venda", "Imposto"]
            # Esta label continua a ser 'Imposto' para o que é exibido
        )
        self.table.setColumnHidden(0, True)  # Oculta a coluna ID
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.open_edit_expense_dialog)

        self.add_button.clicked.connect(self.show_add_expense_dialog)
        self.delete_button.clicked.connect(self.delete_expense)

        self.setup_layout()

        self.apply_styles()

    def show_add_expense_dialog(self):
        self.add_expense_dialog = AddExpenseDialog(self)
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.5)
        self.setGraphicsEffect(opacity_effect)
        self.add_expense_dialog.exec()

    def open_edit_expense_dialog(self, row, column):
        vehicle_id = int(self.table.item(row, 0).text())
        initial_data = fetch_vehicle_by_id(vehicle_id)
        print(f"[DEBUG - ExpenseApp] Fetched initial_data for ID {vehicle_id}: {initial_data}")

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

        row1.addWidget(self.add_button)
        row1.addWidget(self.delete_button)

        layout.addLayout(row1)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def apply_styles(self):
        # Apenas um ajuste para o estilo do QLineEdit na classe principal,
        # pois o DateLineEdit tem seu próprio estilo para o QLineEdit interno.
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
    QLineEdit, QComboBox { /* Apply this to regular QLineEdit and QComboBox */
        background-color: #ffffff;
        font-size: 14px;
        color: #333;
        border: 1px solid #b0bfc6;
        border-radius: 5px;
        padding: 5px;
    }
    QLineEdit:hover, QComboBox:hover {
        border: 1px solid #4caf50; /* Borda verde no hover */
    }
    QLineEdit:focus, QComboBox:focus {
        border: 1px solid #2a9d8f; /* Borda verde mais escura no focus */
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
        background-color: #d0d7de;
        color: #000000;
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
    /* Este estilo geral para QPushButton é apenas para botões fora do DateLineEdit */
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

    /* ESTILO PARA QRadioButton */
    QRadioButton {
        color: #333; /* Cor do texto mais escura para melhor legibilidade */
        padding: 4px 0px; /* Mantém o padding */
    }

    QRadioButton::indicator {
        width: 16px;
        height: 16px;
        border-radius: 8px; /* Mantém o indicador redondo */
        border: 2px solid #555555; /* Borda mais escura para o indicador (normal) */
        background-color: #ffffff; /* Fundo branco para o indicador (normal) */
    }

    QRadioButton::indicator:hover {
        border: 2px solid #4caf50; /* Borda verde mais escura no hover */
    }

    QRadioButton::indicator:checked {
        background-color: #4caf50; /* Preenchimento verde quando selecionado */
        border: 2px solid #2a9d8f; /* Borda verde mais escura quando selecionado */
    }

    /* NOVO ESTILO: QRadioButton quando desabilitado */
    QRadioButton:disabled {
        color: #a0a0a0; /* Cor do texto cinzento */
    }

    QRadioButton::indicator:disabled {
        background-color: #e0e0e0; /* Fundo cinzento claro para o indicador */
        border: 2px solid #b0b0b0; /* Borda cinzenta mais escura */
    }

    /* Estilo para QCalendarWidget */
    QCalendarWidget {
        background-color: #ffffff;
        border: 1px solid #cfd9e1;
        border-radius: 5px;
    }

    QCalendarWidget QWidget#qt_calendar_navigationbar { /* Barra de navegação */
        background-color: #4caf50; /* Verde principal para a barra inteira */
        color: white; /* Cor do texto para toda a barra */
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
    }
    /* Estilo dos botões de navegação e ano/mês */
    QCalendarWidget QWidget#qt_calendar_navigationbar QPushButton {
        background-color: #4caf50; /* Verde */
        color: white;
        border: 1px solid #3d8b40;
        border-radius: 3px;
        font-size: 16px;
        padding: 5px;
    }
    QCalendarWidget QWidget#qt_calendar_navigationbar QPushButton:hover {
        background-color: #45a049;
    }
    QCalendarWidget QWidget#qt_calendar_navigationbar QPushButton:pressed {
        background-color: #3d8b40;
    }
    /* Spinbox de ano e mês no calendário */
    QCalendarWidget QSpinBox {
        border: 1px solid #b0bfc6;
        border-radius: 3px;
        padding-right: 15px; /* Espaço para o botão de seta */
        color: white; /* Cor do texto do spinbox */
        background-color: #4caf50; /* Fundo verde para o spinbox */
    }
    QCalendarWidget QSpinBox::up-button, QCalendarWidget QSpinBox::down-button {
        width: 16px;
        border: 1px solid #b0bfc6;
        border-radius: 3px;
        background-color: #f0f0f0;
    }
    QCalendarWidget QSpinBox::up-arrow, QCalendarWidget QSpinBox::down-arrow {
        width: 10px;
        height: 10px;
    }
    QCalendarWidget QSpinBox::up-button:hover, QCalendarWidget QSpinBox::down-button:hover {
        background-color: #e0e0e0;
    }

    QCalendarWidget QAbstractItemView { /* Grid do calendário */
        selection-background-color: #d0d7de; /* Cor de fundo da seleção ao passar o rato */
        selection-color: #000000; /* Cor do texto da seleção ao passar o rato */
        outline: none; /* Remover a borda de foco */
    }
    /* Estilo para o dia normal no calendário */
    QCalendarWidget QAbstractItemView:enabled {
        color: #333; /* Cor do texto padrão para dias */
    }

    QCalendarWidget QAbstractItemView:enabled:hover {
        background-color: #f2f7fb; /* Cor de fundo ao passar o mouse */
    }

    QCalendarWidget QAbstractItemView:selected {
        background-color: #2a9d8f; /* Cor do fundo do dia selecionado (verde mais escuro) */
        color: white; /* Cor do texto do dia selecionado */
    }

    /* Para o dia de hoje - agora será um círculo cinza suave com borda verde */
    QCalendarWidget QAbstractItemView:!selected:focus { /* Dia de hoje, se não estiver selecionado */
        background-color: #e0e0e0; /* Cinza suave para o dia de hoje */
        color: #000000;
        border: 1px solid #4caf50; /* Borda verde suave */
        border-radius: 50%; /* Faz um círculo */
    }
    /* Para a borda à volta do número do dia */
    QCalendarWidget QCalendarView::item {
        border-radius: 0px; /* Reset para itens normais */
    }
""")

    def load_table_data(self):
        expenses = fetch_expenses()
        self.table.setRowCount(0)
        for row_idx, expense in enumerate(expenses):
            self.table.insertRow(row_idx)
            for col_idx, data in enumerate(expense):
                # Formata colunas específicas com duas casas decimais se forem numéricas
                # Colunas: 3 (Valor Compra), 5 (Valor Venda), 6 (Imposto)
                if col_idx in [3, 5, 6]:
                    try:
                        # Se o dado for None ou string vazia, exibe string vazia
                        if data is None or (isinstance(data, str) and not str(data).strip()):
                            formatted_data = ""
                        else:
                            # NOVO: Usa QLocale para formatar números na tabela
                            locale = QLocale(QLocale.Language.Portuguese, QLocale.Country.Portugal)
                            formatted_data = locale.toString(float(data), 'f', 2)
                        self.table.setItem(row_idx, col_idx, QTableWidgetItem(formatted_data))
                    except (ValueError, TypeError):
                        # Se não for um número válido, exibe como string
                        self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
                else:
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
                self.table.clearSelection()  # Deselects the row after deletion