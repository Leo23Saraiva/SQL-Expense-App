from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QComboBox,
    QTableWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QTableWidgetItem,
    QHeaderView, QDialog, QGraphicsOpacityEffect, QGroupBox, QFormLayout,
    QRadioButton, QCalendarWidget
)
from PyQt6.QtCore import QDate, Qt, QLocale, QEvent
from PyQt6.QtGui import QValidator, QColor
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
                print(
                    f"[DEBUG - DateLineEdit] FocusOut: Data '{current_text}' incompleta e inválida. Limpando campo.")
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
                print(f"[DEBUG - DateLineEdit] setText: '{text}' not a valid ISO date. Setting raw text.")
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
        # O setText do DateLineEdit vai agora fazer a conversão de `yyyy-MM-dd` para `dd-MM-yyyy`
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

        self.docVenda.setText(self.initial_data.get("docVenda", ""))  # Este deve ser texto, não real.
        self.valorVenda.setText(format_real_for_display(self.initial_data.get("valorVenda")))

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

    /* A COR DE SELEÇÃO DEVE SER MAIS ESPECÍFICA PARA SOBREPÔR OUTRAS CORES */
    QTableWidget::item:selected {
        background-color: #d0d7de; /* Cor de seleção cinza mais clara */
        color: #000000;
    }

    /* NOVO: Estilo para itens vendidos - será sobreposto por ::item:selected */
    /* Este estilo aplica-se ao item individual, o que pode ser mais robusto */
    QTableWidget::item[sold="true"] { /* Usamos uma propriedade dinâmica 'sold' */
        background-color: #d4edda; /* Verde pastel para vendido */
        color: #333; /* Cor do texto para contraste */
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

    /* Estilo para o botão de Limpar Pesquisa (o "X") */
    QPushButton#clearSearchButton {
        background-color: transparent; /* Fundo transparente */
        border: none; /* Sem borda */
        color: #555555; /* Cor cinza escura para o 'X' */
        padding: 0px 5px; /* Padding ajustado para ser mais compacto */
        border-radius: 5px;
        font-size: 18px; /* Tamanho maior para o 'X' para melhor visibilidade */
        font-weight: bold;
        min-width: 25px; /* Largura mínima menor */
    }
    QPushButton#clearSearchButton:hover {
        background-color: #e0e0e0; /* Um cinza claro no hover */
        border-radius: 5px; /* Manter bordas arredondadas no hover */
    }
    QPushButton#clearSearchButton:pressed {
        background-color: #cccccc; /* Um cinza mais escuro no pressed */
    }

    /* NOVO: Estilo para o botão de Pesquisa (a "Lupa") */
    QPushButton#searchButton {
        background-color: transparent; /* Fundo transparente */
        border: none; /* Sem borda */
        color: #555555; /* Cor cinza escura para a 'Lupa' */
        padding: 0px 5px; /* Padding ajustado para ser mais compacto */
        border-radius: 5px;
        font-size: 18px; /* Tamanho maior para a 'Lupa' */
        font-weight: bold;
        min-width: 25px; /* Largura mínima menor */
    }
    QPushButton#searchButton:hover {
        background-color: #e0e0e0; /* Um cinza claro no hover */
        border-radius: 5px;
    }
    QPushButton#searchButton:pressed {
        background-color: #cccccc; /* Um cinza mais escuro no pressed */
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

    /* Barra de navegação do calendário (onde está o mês e ano) */
    QCalendarWidget QWidget#qt_calendar_navigationbar {
        background-color: #e8ecf4; /* Cor de fundo que você definiu como ideal */
        color: #333; /* Cor do texto para toda a barra - ajustado para o novo fundo */
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        border: none; /* Remover qualquer borda residual */
    }

    /* Estilo dos botões de navegação (setas) e spinbox de ano/mês */
    QCalendarWidget QAbstractSpinBox,
    QCalendarWidget QPushButton {
        background-color: #e8ecf4; /* Mesma cor da barra de navegação */
        color: #4caf50; /* Cor do texto verde */
        border: 1px solid #b0bfc6; /* Borda cinza suave */
        border-radius: 3px;
        font-size: 14px; /* Ajuste para caber melhor */
        padding: 3px 5px; /* Reduzir padding para os botões e spinbox */
    }
    QCalendarWidget QAbstractSpinBox:hover,
    QCalendarWidget QPushButton:hover {
        background-color: #dbe2ea; /* Um tom ligeiramente mais escuro no hover */
    }
    QCalendarWidget QAbstractSpinBox:pressed,
    QCalendarWidget QPushButton:pressed {
        background-color: #c9d0d9; /* Um tom ainda mais escuro no pressed */
    }

    /* Setas dentro do Spinbox */
    QCalendarWidget QSpinBox::up-button,
    QCalendarWidget QSpinBox::down-button {
        subcontrol-origin: border;
        subcontrol-position: right;
        width: 16px;
        border-left: 1px solid #b0bfc6; /* Borda para separar o botão */
        background-color: #e8ecf4; /* Mesma cor da barra */
        border-top-right-radius: 3px;
        border-bottom-right-radius: 3px;
    }
    QCalendarWidget QSpinBox::up-button:hover,
    QCalendarWidget QSpinBox::down-button:hover {
        background-color: #dbe2ea;
    }
    QCalendarWidget QSpinBox::up-arrow,
    QCalendarWidget QSpinBox::down-arrow {
        background-color: transparent;
        color: #4caf50; /* A cor da seta será o verde */
    }

    /* Cabeçalho da grelha do calendário (Dias da Semana - Seg, Ter, Qua, etc.) */
    QCalendarWidget QAbstractItemView {
        background-color: #ffffff; /* Fundo branco para toda a área dos dias */
        selection-background-color: #a0d4a3; /* Fundo mais claro para dias selecionados */
        selection-color: #000000; /* Cor do texto para dias selecionados */
        outline: none; /* Remover a borda de foco */
        border-bottom: 1px solid #e0e0e0; /* Linha de separação para o cabeçalho dos dias da semana */
    }

    QCalendarWidget QAbstractItemView QHeaderView::section {
        background-color: #f0f0f0; /* Fundo cinza claro para a linha dos dias da semana */
        color: #555555; /* Cor do texto para os dias da semana */
        border: none;
        padding: 5px;
    }

    /* Estilo para o dia normal no calendário */
    QCalendarWidget QAbstractItemView:enabled {
        color: #333; /* Cor do texto padrão para os números dos dias */
    }

    QCalendarWidget QAbstractItemView:enabled:hover {
        background-color: #e6ffe6; /* Um verde muito claro no hover */
        border-radius: 3px; /* Bordas arredondadas no hover */
    }

    QCalendarWidget QAbstractItemView:selected {
        background-color: #2a9d8f; /* Cor do fundo do dia selecionado (verde mais escuro) */
        color: white; /* Cor do texto do dia selecionado */
        border-radius: 3px; /* Bordas arredondadas para seleção */
    }

    /* Para o dia de hoje - AGORA COM CIRCULO VERDE MAIS CLARO */
    QCalendarWidget QAbstractItemView:!selected:focus { /* Dia de hoje, se não estiver selecionado */
        background-color: #d4f7d4; /* Um verde pastel */
        color: #000000;
        border: 1px solid #4caf50; /* Borda verde suave */
        border-radius: 50%; /* Faz um círculo */
    }

    /* Para a borda à volta do número do dia */
    QCalendarWidget QCalendarView::item {
        border-radius: 0px; /* Reset para itens normais */
        padding: 4px; /* Padding para espaçar os números */
    }

    /* Dias desabilitados (fora do mês atual) */
    QCalendarWidget QAbstractItemView:disabled {
        color: #cccccc; /* Cor cinza para dias fora do mês */
    }
""")

    def get_form_data(self):
        # Esta função já estava completa e não precisa de alterações relacionadas a "vendido"
        matricula = self.matricula.text().strip()
        marca = self.marca.text().strip()
        numero_quadro = self.numeroQuadro.text().strip()

        # Funções para conversão segura de campos numéricos
        def parse_float(text):
            locale = QLocale(QLocale.Language.Portuguese, QLocale.Country.Portugal)
            try:
                # Remove espaços em branco
                clean_text = text.strip()
                if not clean_text:  # Se for string vazia após strip, retorna None
                    return None
                # Converte para float usando a localidade correta para vírgula/ponto decimal
                return locale.toFloat(clean_text)[0]  # [0] para obter o float do tuple (float, bool)
            except Exception as e:
                print(f"Erro ao converter '{text}' para float: {e}")
                return None

        def parse_int(text):
            try:
                # Remove espaços em branco
                clean_text = text.strip()
                if not clean_text:  # Se for string vazia após strip, retorna None
                    return None
                return int(clean_text)
            except ValueError:
                return None

        isv = parse_float(self.isv.text())
        n_registo_contabilidade = self.nRegistoContabilidade.text().strip()  # Manter como string

        # Obter data da compra do DateLineEdit
        data_compra_qdate = self.dataCompra.date()
        data_compra = data_compra_qdate.toString("yyyy-MM-dd") if data_compra_qdate.isValid() else None

        doc_compra = self.docCompra.text().strip()
        tipo_documento = self.tipoDocumento.currentText()
        valor_compra = parse_float(self.valorCompra.text())

        # Obter data da venda do DateLineEdit
        data_venda_qdate = self.dataVenda.date()
        data_venda = data_venda_qdate.toString("yyyy-MM-dd") if data_venda_qdate.isValid() else None

        doc_venda = self.docVenda.text().strip()  # Manter como string
        valor_venda = parse_float(self.valorVenda.text())

        # Imposto é calculado, não lido diretamente
        imposto = parse_float(self.imposto.text())
        valor_base = parse_float(self.valorBase.text())

        taxa_str = self.taxa.currentText()
        taxa = parse_float(taxa_str) if taxa_str != "N/A" else None

        regime_fiscal = ""
        if self.regime_geral_radio.isChecked():
            regime_fiscal = "Regime Normal"
        elif self.regime_lucro_tributavel_radio.isChecked():
            regime_fiscal = "Margem"

        return {
            "matricula": matricula,
            "marca": marca,
            "numeroQuadro": numero_quadro,
            "isv": isv,
            "nRegistoContabilidade": n_registo_contabilidade,
            "dataCompra": data_compra,
            "docCompra": doc_compra,
            "tipoDocumento": tipo_documento,
            "valorCompra": valor_compra,
            "dataVenda": data_venda,
            "docVenda": doc_venda,
            "valorVenda": valor_venda,
            "imposto": imposto,
            "valorBase": valor_base,
            "taxa": taxa,
            "regime_fiscal": regime_fiscal
        }

    def add_record(self):
        data = self.get_form_data()

        # Validação básica
        if not all([data["matricula"], data["marca"], data["valorCompra"] is not None]):
            QMessageBox.warning(self, "Campos Obrigatórios",
                                "Matrícula, Marca e Valor de Compra são obrigatórios.")
            return

        if self.mode == "add":
            if add_expense_to_db(data["matricula"], data["marca"], data["numeroQuadro"], data["isv"],
                                 data["nRegistoContabilidade"], data["dataCompra"], data["docCompra"],
                                 data["tipoDocumento"], data["valorCompra"], data["dataVenda"],
                                 data["docVenda"], data["valorVenda"], data["imposto"],
                                 data["valorBase"], data["taxa"], data["regime_fiscal"]):
                QMessageBox.information(self, "Sucesso", "Registo adicionado com sucesso!")
                self.parent_window.load_table_data()
                self.accept()
            else:
                QMessageBox.critical(self, "Erro", "Erro ao adicionar registo.")
        elif self.mode == "edit":
            if self.initial_data and self.initial_data.get("id") is not None:
                if update_expense_in_db(self.initial_data["id"], data):
                    QMessageBox.information(self, "Sucesso", "Registo atualizado com sucesso!")
                    self.parent_window.load_table_data()
                    self.accept()
                else:
                    QMessageBox.critical(self, "Erro", "Erro ao atualizar registo.")
            else:
                QMessageBox.critical(self, "Erro", "ID do veículo não encontrado para edição.")

    def update_regime_button_states(self):
        """Atualiza o estado (enabled/disabled) dos radio buttons do regime fiscal
        e reinicia a seleção se as condições não forem cumpridas."""

        valor_compra_text = self.valorCompra.text().strip().replace(',', '.')
        valor_venda_text = self.valorVenda.text().strip().replace(',', '.')
        taxa_selecionada = self.taxa.currentText()

        try:
            valor_compra = float(valor_compra_text) if valor_compra_text else 0.0
            valor_venda = float(valor_venda_text) if valor_venda_text else 0.0
        except ValueError:
            valor_compra = 0.0
            valor_venda = 0.0

        # Condição para habilitar Regime Geral (Normal)
        # Valor de venda preenchido E valor de compra preenchido E taxa selecionada diferente de "N/A"
        enable_regime_geral = (
                valor_compra > 0 and
                valor_venda > 0 and
                taxa_selecionada != "N/A"
        )

        # Condição para habilitar Margem
        # Valor de venda preenchido E valor de compra preenchido E taxa selecionada diferente de "N/A"
        # E (Valor Venda - Valor Compra) > 0
        enable_regime_lucro = (
                enable_regime_geral and
                (valor_venda - valor_compra) > 0
        )

        # Aplicar estados
        self.regime_geral_radio.setEnabled(enable_regime_geral)
        self.regime_lucro_tributavel_radio.setEnabled(enable_regime_lucro)

        # Lógica para redefinir seleção se as condições não forem mais válidas
        # Se um regime estava selecionado e agora está desabilitado, desmarca-o
        if self.regime_geral_radio.isChecked() and not enable_regime_geral:
            self.regime_geral_radio.setChecked(False)
            self.last_valid_regime_radio = None  # Reset do último regime válido
            print("[DEBUG - AddExpenseDialog] Regime Normal desmarcado (condições não cumpridas).")

        if self.regime_lucro_tributavel_radio.isChecked() and not enable_regime_lucro:
            self.regime_lucro_tributavel_radio.setChecked(False)
            self.last_valid_regime_radio = None  # Reset do último regime válido
            print("[DEBUG - AddExpenseDialog] Regime Margem desmarcado (condições não cumpridas).")

        # Se nenhum regime estiver selecionado e um for agora habilitado, e havia um último válido, seleciona-o
        if not self.regime_geral_radio.isChecked() and not self.regime_lucro_tributavel_radio.isChecked():
            if self.last_valid_regime_radio:
                if self.last_valid_regime_radio == self.regime_geral_radio and enable_regime_geral:
                    self.regime_geral_radio.setChecked(True)
                    print("[DEBUG - AddExpenseDialog] Restaurado Regime Normal (último válido).")
                elif self.last_valid_regime_radio == self.regime_lucro_tributavel_radio and enable_regime_lucro:
                    self.regime_lucro_tributavel_radio.setChecked(True)
                    print("[DEBUG - AddExpenseDialog] Restaurado Regime Margem (último válido).")
            # Se não havia um último regime válido, ou ele não pode ser restaurado, não fazemos nada,
            # deixando o utilizador escolher.

        self.calculate_regime_fields()  # Recalcula após mudança de estado/seleção

    def handle_regime_selection(self):
        """Atualiza o 'last_valid_regime_radio' quando o utilizador faz uma seleção."""
        if self.regime_geral_radio.isChecked():
            self.last_valid_regime_radio = self.regime_geral_radio
            print("[DEBUG - AddExpenseDialog] last_valid_regime_radio definido para Regime Normal.")
        elif self.regime_lucro_tributavel_radio.isChecked():
            self.last_valid_regime_radio = self.regime_lucro_tributavel_radio
            print("[DEBUG - AddExpenseDialog] last_valid_regime_radio definido para Margem.")
        else:
            self.last_valid_regime_radio = None
            print("[DEBUG - AddExpenseDialog] Nenhum regime selecionado, last_valid_regime_radio redefinido.")
        self.calculate_regime_fields()  # Recalcula após a seleção do utilizador

    def calculate_regime_fields(self):
        """Calcula o Valor Base e o Imposto com base nas novas regras."""
        valor_compra_text = self.valorCompra.text().strip().replace(',', '.')
        valor_venda_text = self.valorVenda.text().strip().replace(',', '.')
        taxa_str = self.taxa.currentText()

        try:
            valor_compra = Decimal(valor_compra_text) if valor_compra_text else Decimal(0)
            valor_venda = Decimal(valor_venda_text) if valor_venda_text else Decimal(0)
            taxa = Decimal(taxa_str) if taxa_str != "N/A" else Decimal(0)
        except Exception:
            # Se a conversão falhar, limpa os campos de cálculo e sai
            self.valorBase.setText("")
            self.imposto.setText("")
            return

        valor_base = Decimal(0)
        imposto = Decimal(0)

        # NOVO: Esta função agora usa QLocale para formatação localizada (pontos de milhar, vírgula decimal)
        def format_decimal_for_display(value):
            locale = QLocale(QLocale.Language.Portuguese, QLocale.Country.Portugal)
            # Define o comportamento de arredondamento para sempre ter duas casas decimais
            return locale.toString(float(value.quantize(Decimal("0.01"))), 'f', 2)

        if self.regime_geral_radio.isChecked():
            # Regime Normal: valor base = valor venda, imposto = valor venda * (taxa / 100)
            valor_base = valor_venda
            imposto = valor_venda * (taxa / Decimal(100))
            print(f"[DEBUG - Calc] Regime Normal - Venda: {valor_venda}, Taxa: {taxa}, Imposto: {imposto}")
        elif self.regime_lucro_tributavel_radio.isChecked():
            # Regime da Margem: valor base = valor venda - valor compra, imposto = valor base * (taxa / 100)
            margem = valor_venda - valor_compra
            if margem > 0:
                valor_base = margem
                imposto = margem * (taxa / Decimal(100))
            else:
                # Se a margem for <= 0, não há imposto neste regime
                valor_base = Decimal(0)
                imposto = Decimal(0)
            print(
                f"[DEBUG - Calc] Regime Margem - Venda: {valor_venda}, Compra: {valor_compra}, Margem: {margem}, Taxa: {taxa}, Imposto: {imposto}")
        else:
            # Se nenhum regime estiver selecionado, os campos ficam vazios
            self.valorBase.setText("")
            self.imposto.setText("")
            return  # Sai da função, pois não há cálculo a fazer

        # Arredondar para duas casas decimais
        valor_base = valor_base.quantize(Decimal("0.01"))
        imposto = imposto.quantize(Decimal("0.01"))

        self.valorBase.setText(format_decimal_for_display(valor_base))
        self.imposto.setText(format_decimal_for_display(imposto))


class ExpenseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.apply_styles()
        self.load_table_data()
        self.showMaximized()  # Definir para iniciar em tela cheia

    def init_ui(self):
        self.setWindowTitle("MBAuto - Gestão de Despesas de Viaturas")
        # Removido self.setGeometry, pois showMaximized() o substituirá
        # self.setGeometry(100, 100, 1000, 600)  # Maior para acomodar as colunas

        self.table = QTableWidget()
        self.table.setColumnCount(7)  # ID, Matrícula, Marca, Valor Compra, Doc Venda, Valor Venda, Imposto
        self.table.setHorizontalHeaderLabels(
            ["ID", "Matrícula", "Marca", "Valor Compra", "Doc. Venda", "Valor Venda", "Imposto"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Make table non-editable
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)  # Selects entire row

        # --- CONECTAR O SINAL DE DUPLO CLIQUE ---
        self.table.doubleClicked.connect(self.show_edit_dialog)

        # Hide the ID column
        self.table.setColumnHidden(0, True)

        self.add_button = QPushButton("Adicionar Registo")
        self.delete_button = QPushButton("Apagar Registo")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar por Matrícula ou Marca...")

        # Conectar o sinal returnPressed para pesquisar ao pressionar Enter
        self.search_input.returnPressed.connect(self.search_expenses)

        # Botão de limpar pesquisa (X)
        self.clear_search_button = QPushButton("X")
        self.clear_search_button.setObjectName("clearSearchButton")  # Para aplicar estilo CSS específico
        self.clear_search_button.setToolTip("Limpar pesquisa e mostrar todos os registos")
        self.clear_search_button.clicked.connect(self.clear_search)

        # Botão de pesquisa (Lupa)
        self.search_button = QPushButton("🔍")  # Ícone de lupa (Unicode)
        self.search_button.setObjectName("searchButton")  # Para aplicar estilo CSS específico
        self.search_button.setToolTip("Pesquisar registos")
        self.search_button.clicked.connect(self.search_expenses)

        # Layouts
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch(1)  # Push buttons to the left

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.clear_search_button)  # X antes da lupa
        search_layout.addWidget(self.search_button)  # Botão de pesquisa (Lupa)

        self.add_button.clicked.connect(self.show_add_dialog)
        self.delete_button.clicked.connect(self.delete_expense)
        # self.search_button.clicked.connect(self.search_expenses) # Conectado acima

        main_layout = QVBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

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
    QLineEdit, QComboBox {
        background-color: #ffffff;
        font-size: 14px;
        color: #333;
        border: 1px solid #b0bfc6;
        border-radius: 5px;
        padding: 5px;
    }
    QLineEdit:hover, QComboBox:hover {
        border: 1px solid #4caf50;
    }
    QLineEdit:focus, QComboBox:focus {
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

    /* A COR DE SELEÇÃO DEVE SER MAIS ESPECÍFICA PARA SOBREPÔR OUTRAS CORES */
    QTableWidget::item:selected {
        background-color: #d0d7de; /* Cor de seleção cinza mais clara */
        color: #000000;
    }

    /* NOVO: Estilo para itens vendidos - será sobreposto por ::item:selected */
    /* Este estilo aplica-se ao item individual, o que pode ser mais robusto */
    QTableWidget::item[sold="true"] { /* Usamos uma propriedade dinâmica 'sold' */
        background-color: #d4edda; /* Verde pastel para vendido */
        color: #333; /* Cor do texto para contraste */
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

    /* Estilo para o botão de Limpar Pesquisa (o "X") */
    QPushButton#clearSearchButton {
        background-color: transparent;
        border: none;
        color: #555555;
        padding: 0px 5px;
        border-radius: 5px;
        font-size: 18px;
        font-weight: bold;
        min-width: 25px;
    }
    QPushButton#clearSearchButton:hover {
        background-color: #e0e0e0;
        border-radius: 5px;
    }
    QPushButton#clearSearchButton:pressed {
        background-color: #cccccc;
    }

    /* NOVO: Estilo para o botão de Pesquisa (a "Lupa") */
    QPushButton#searchButton {
        background-color: transparent;
        border: none;
        color: #555555;
        padding: 0px 5px;
        border-radius: 5px;
        font-size: 18px;
        font-weight: bold;
        min-width: 25px;
    }
    QPushButton#searchButton:hover {
        background-color: #e0e0e0;
        border-radius: 5px;
    }
    QPushButton#searchButton:pressed {
        background-color: #cccccc;
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
        color: #333;
        padding: 4px 0px;
    }

    QRadioButton::indicator {
        width: 16px;
        height: 16px;
        border-radius: 8px;
        border: 2px solid #555555;
        background-color: #ffffff;
    }

    QRadioButton::indicator:hover {
        border: 2px solid #4caf50;
    }

    QRadioButton::indicator:checked {
        background-color: #4caf50;
        border: 2px solid #2a9d8f;
    }

    /* NOVO ESTILO: QRadioButton quando desabilitado */
    QRadioButton:disabled {
        color: #a0a0a0;
    }

    QRadioButton::indicator:disabled {
        background-color: #e0e0e0;
        border: 2px solid #b0b0b0;
    }

    /* Estilo para QCalendarWidget */
    QCalendarWidget {
        background-color: #ffffff;
        border: 1px solid #cfd9e1;
        border-radius: 5px;
    }

    /* Barra de navegação do calendário (onde está o mês e ano) */
    QCalendarWidget QWidget#qt_calendar_navigationbar {
        background-color: #e8ecf4;
        color: #333;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        border: none;
    }

    /* Estilo dos botões de navegação (setas) e spinbox de ano/mês */
    QCalendarWidget QAbstractSpinBox,
    QCalendarWidget QPushButton {
        background-color: #e8ecf4;
        color: #4caf50;
        border: 1px solid #b0bfc6;
        border-radius: 3px;
        font-size: 14px;
        padding: 3px 5px;
    }
    QCalendarWidget QAbstractSpinBox:hover,
    QCalendarWidget QPushButton:hover {
        background-color: #dbe2ea;
    }
    QCalendarWidget QAbstractSpinBox:pressed,
    QCalendarWidget QPushButton:pressed {
        background-color: #c9d0d9;
    }

    /* Setas dentro do Spinbox */
    QCalendarWidget QSpinBox::up-button,
    QCalendarWidget QSpinBox::down-button {
        subcontrol-origin: border;
        subcontrol-position: right;
        width: 16px;
        border-left: 1px solid #b0bfc6;
        background-color: #e8ecf4;
        border-top-right-radius: 3px;
        border-bottom-right-radius: 3px;
    }
    QCalendarWidget QSpinBox::up-button:hover,
    QCalendarWidget QSpinBox::down-button:hover {
        background-color: #dbe2ea;
    }
    QCalendarWidget QSpinBox::up-arrow,
    QCalendarWidget QSpinBox::down-arrow {
        background-color: transparent;
        color: #4caf50;
    }

    /* Cabeçalho da grelha do calendário (Dias da Semana - Seg, Ter, Qua, etc.) */
    QCalendarWidget QAbstractItemView {
        background-color: #ffffff;
        selection-background-color: #a0d4a3;
        selection-color: #000000;
        outline: none;
        border-bottom: 1px solid #e0e0e0;
    }

    QCalendarWidget QAbstractItemView QHeaderView::section {
        background-color: #f0f0f0;
        color: #555555;
        border: none;
        padding: 5px;
    }

    /* Estilo para o dia normal no calendário */
    QCalendarWidget QAbstractItemView:enabled {
        color: #333;
    }

    QCalendarWidget QAbstractItemView:enabled:hover {
        background-color: #e6ffe6;
        border-radius: 3px;
    }

    QCalendarWidget QAbstractItemView:selected {
        background-color: #2a9d8f;
        color: white;
        border-radius: 3px;
    }

    /* Para o dia de hoje - AGORA COM CIRCULO VERDE MAIS CLARO */
    QCalendarWidget QAbstractItemView:!selected:focus {
        background-color: #d4f7d4;
        color: #000000;
        border: 1px solid #4caf50;
        border-radius: 50%;
    }

    /* Para a borda à volta do número do dia */
    QCalendarWidget QCalendarView::item {
        border-radius: 0px;
        padding: 4px;
    }

    /* Dias desabilitados (fora do mês atual) */
    QCalendarWidget QAbstractItemView:disabled {
        color: #cccccc;
    }
""")

    def load_table_data(self):
        # expense agora inclui dataVenda como o último elemento
        expenses = fetch_expenses()
        self.table.setRowCount(0)

        # Colunas visíveis na tabela: ID, Matrícula, Marca, Valor Compra, Doc Venda, Valor Venda, Imposto
        # total de 7 colunas visíveis + a dataVenda que será a 8ª coluna (índice 7) do `expense`
        # para a lógica do vendido

        for row_idx, expense in enumerate(expenses):
            self.table.insertRow(row_idx)

            # Extrair os campos relevantes para a condição "vendido"
            data_venda = expense[7]  # dataVenda é o último elemento retornado por fetch_expenses
            valor_venda = expense[5]  # valorVenda
            doc_venda = expense[4]  # docVenda

            # Lógica para determinar se o veículo está vendido
            # Consideramos vendido se pelo menos um dos campos de venda estiver preenchido
            is_sold = bool(data_venda) or \
                      (valor_venda is not None and str(valor_venda).strip() != "" and float(valor_venda) > 0) or \
                      (doc_venda is not None and str(doc_venda).strip() != "")

            # Definir a cor de fundo para a linha inteira se o veículo estiver vendido
            # O ideal é aplicar a cor a cada item individualmente para garantir que o estilo de seleção sobrepõe
            sold_background_color = QColor("#d4edda")  # ou QColor("#e0ffe0") para um verde mais suave ainda

            # Iterar apenas sobre as colunas visíveis para definir os itens da tabela
            # As colunas visíveis são de 0 a 6
            for col_idx in range(7):  # 0 a 6 (7 colunas)
                data = expense[col_idx]  # Acessa os dados originais da linha

                # Formata colunas específicas com duas casas decimais se forem numéricas
                # Colunas: 3 (Valor Compra), 5 (Valor Venda), 6 (Imposto)
                if col_idx in [3, 5, 6]:
                    try:
                        # Se o dado for None ou string vazia, exibe string vazia
                        if data is None or (isinstance(data, str) and not str(data).strip()):
                            formatted_data = ""
                        else:
                            # Usa QLocale para formatar números na tabela
                            locale = QLocale(QLocale.Language.Portuguese, QLocale.Country.Portugal)
                            formatted_data = locale.toString(float(data), 'f', 2)
                        item = QTableWidgetItem(formatted_data)
                    except (ValueError, TypeError):
                        # Se não for um número válido, exibe como string
                        item = QTableWidgetItem(str(data))
                else:
                    item = QTableWidgetItem(str(data))

                # Se o veículo estiver vendido, aplicar o background à célula
                if is_sold:
                    item.setBackground(sold_background_color)
                    # Opcional: Para ter a certeza que o texto tem boa visibilidade
                    # item.setForeground(QColor("#333333"))
                    # Definir uma propriedade dinâmica para uso no CSS
                    item.setData(Qt.ItemDataRole.UserRole, True)  # Exemplo de como usar UserRole
                    # Ou de forma mais direta para CSS via propriedade:
                    # item.setData(Qt.ItemDataRole.UserRole + 1, "true") # Para o QTableWidget::item[sold="true"]

                self.table.setItem(row_idx, col_idx, item)

    def show_add_dialog(self):
        dialog = AddExpenseDialog(self, mode="add")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_table_data()

    def show_edit_dialog(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a record to edit.")
            return

        expense_id = int(self.table.item(selected_row, 0).text())
        initial_data = fetch_vehicle_by_id(expense_id)

        if initial_data:
            dialog = AddExpenseDialog(self, mode="edit", initial_data=initial_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_table_data()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível carregar os dados do veículo para edição.")

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
            else:
                QMessageBox.critical(self, "Erro", "Erro ao apagar registo.")

    def search_expenses(self):
        search_text = self.search_input.text().strip().lower()

        # Fetch all data and filter in memory for simplicity
        all_expenses = fetch_expenses()
        self.table.setRowCount(0)

        row_idx = 0
        for expense in all_expenses:
            # Indices: 1 for Matrícula, 2 for Marca
            matricula = str(expense[1]).lower()
            marca = str(expense[2]).lower()

            if search_text in matricula or search_text in marca:
                self.table.insertRow(row_idx)

                # Extrair os campos relevantes para a condição "vendido"
                data_venda = expense[7]  # dataVenda é o último elemento retornado por fetch_expenses
                valor_venda = expense[5]  # valorVenda
                doc_venda = expense[4]  # docVenda

                # Lógica para determinar se o veículo está vendido
                is_sold = bool(data_venda) or \
                          (valor_venda is not None and str(valor_venda).strip() != "" and float(valor_venda) > 0) or \
                          (doc_venda is not None and str(doc_venda).strip() != "")

                sold_background_color = QColor("#d4edda")

                for col_id in range(7):  # Columns 0 to 6 are visible
                    data = expense[col_id]

                    if col_id in [3, 5, 6]:  # Valor Compra, Valor Venda, Imposto
                        try:
                            if data is None or (isinstance(data, str) and not str(data).strip()):
                                formatted_data = ""
                            else:
                                locale = QLocale(QLocale.Language.Portuguese, QLocale.Country.Portugal)
                                formatted_data = locale.toString(float(data), 'f', 2)
                            item = QTableWidgetItem(formatted_data)
                        except (ValueError, TypeError):
                            item = QTableWidgetItem(str(data))
                    else:
                        item = QTableWidgetItem(str(data))

                    if is_sold:
                        item.setBackground(sold_background_color)
                        item.setData(Qt.ItemDataRole.UserRole, True)  # Set custom role data
                    self.table.setItem(row_idx, col_id, item)
                row_idx += 1

    def clear_search(self):
        """Limpa o campo de pesquisa e recarrega todos os dados da tabela."""
        self.search_input.clear()
        self.load_table_data()