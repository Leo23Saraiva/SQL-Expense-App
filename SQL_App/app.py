from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QComboBox, QDateEdit,
    QTableWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QTableWidgetItem,
    QHeaderView, QDialog, QGraphicsOpacityEffect, QGroupBox, QFormLayout,
    QRadioButton
)
from PyQt6.QtCore import QDate, Qt, QLocale
from decimal import Decimal

from database import fetch_expenses, add_expense_to_db, delete_expense_from_db, update_expense_in_db, \
    fetch_vehicle_by_id


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
        # Alterado: 'imposto' para 'taxa'
        self.taxa.textChanged.connect(self.update_regime_button_states)
        self.taxa.textChanged.connect(self.calculate_regime_fields)


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
        # Usar .get() com um valor padrão para evitar KeyError e TypeError se o valor for None
        self.matricula.setText(self.initial_data.get("matricula", ""))
        self.marca.setText(self.initial_data.get("marca", ""))

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

        data_compra_str = self.initial_data.get("dataCompra")
        if data_compra_str:  # Só tenta converter se a string não for vazia ou None
            self.dataCompra.setDate(QDate.fromString(data_compra_str, "yyyy-MM-dd"))
        else:
            self.dataCompra.setDate(QDate.currentDate())  # Define uma data padrão se não houver data

        self.docCompra.setText(self.initial_data.get("docCompra", ""))
        # Certifique-se de que o item selecionado existe no QComboBox
        tipo_documento_str = self.initial_data.get("tipoDocumento", "")
        index = self.tipoDocumento.findText(tipo_documento_str)
        if index >= 0:
            self.tipoDocumento.setCurrentIndex(index)
        else:
            self.tipoDocumento.setCurrentIndex(0)  # Define o primeiro item como padrão

        self.valorCompra.setText(format_real_for_display(self.initial_data.get("valorCompra")))

        data_venda_str = self.initial_data.get("dataVenda")
        if data_venda_str:  # Só tenta converter se a string não for vazia ou None
            self.dataVenda.setDate(QDate.fromString(data_venda_str, "yyyy-MM-dd"))
        else:
            self.dataVenda.setDate(QDate.currentDate())  # Define uma data padrão se não houver data

        self.docVenda.setText(self.initial_data.get("docVenda", ""))  # Correção: docVenda é texto
        self.valorVenda.setText(format_real_for_display(self.initial_data.get("valorVenda")))

        # Aplicar a função de formatação para imposto, valorBase e taxa
        self.imposto.setText(format_real_for_display(self.initial_data.get("imposto")))
        self.valorBase.setText(format_real_for_display(self.initial_data.get("valorBase")))
        self.taxa.setText(format_real_for_display(self.initial_data.get("taxa"))) # Taxa agora é um input, não um output

        # Carregar o regime fiscal salvo, desabilitando sinais para não disparar handle_regime_selection
        self.regime_geral_radio.blockSignals(True)
        self.regime_lucro_tributavel_radio.blockSignals(True)

        regime_salvo = self.initial_data.get("regime_fiscal", "")
        if regime_salvo == "Regime Normal":
            self.regime_geral_radio.setChecked(True)
        elif regime_salvo == "Margem":
            self.regime_lucro_tributavel_radio.setChecked(True)
        else:
            self.regime_geral_radio.setChecked(False)
            self.regime_lucro_tributavel_radio.setChecked(False)

        self.regime_geral_radio.blockSignals(False)
        self.regime_lucro_tributavel_radio.blockSignals(False)

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

        self.taxa = QLineEdit() # Taxa agora é um input
        self.valorBase = QLineEdit()
        self.imposto = QLineEdit() # Imposto agora é um output

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
        imposto_layout.addRow("Taxa:", self.taxa)
        imposto_layout.addRow("Valor Base:", self.valorBase)
        imposto_layout.addRow("Imposto:", self.imposto)
        imposto_group.setLayout(imposto_layout)

        # Layout principal - Adicionar os grupos de campos aqui
        identificacao_group = QGroupBox("Identificação do Veículo")
        identificacao_layout = QFormLayout()
        identificacao_layout.addRow("Matrícula:", self.matricula)
        identificacao_layout.addRow("Marca:", self.marca)
        identificacao_layout.addRow("ISV:", self.isv)
        identificacao_layout.addRow("Nº Registo Contabilidade:", self.nRegistoContabilidade)
        identificacao_group.setLayout(identificacao_layout)

        compras_group = QGroupBox("Detalhes da Compra")
        compras_layout = QFormLayout()
        compras_layout.addRow("Data da Compra:", self.dataCompra)
        compras_layout.addRow("Doc. Compra:", self.docCompra)
        compras_layout.addRow("Tipo Documento:", self.tipoDocumento)
        compras_layout.addRow("Valor de Compra:", self.valorCompra)
        compras_group.setLayout(compras_layout)

        vendas_group = QGroupBox("Detalhes da Venda")
        vendas_layout = QFormLayout()
        vendas_layout.addRow("Data da Venda:", self.dataVenda)
        vendas_layout.addRow("Doc. Venda:", self.docVenda)
        vendas_layout.addRow("Valor de Venda:", self.valorVenda)
        vendas_group.setLayout(vendas_layout)

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
        border: 1px solid #4caf50; /* Borda verde no hover */
    }
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
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
""")

    # Função auxiliar para lidar com a conversão e arredondamento (reutilizada)
    def get_float_value(self, lineEdit_text):
        if not lineEdit_text:
            return None

        text = str(lineEdit_text)
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
        # Alterado: 'imposto' para 'taxa'
        return (self.get_float_value(self.valorVenda.text()) is not None and
                self.get_float_value(self.taxa.text()) is not None)

    # Validação para o Regime de Margem (Valor de Compra, Valor de Venda e Taxa)
    def are_margin_regime_fields_valid(self):
        """Verifica se os campos necessários para 'Margem' estão preenchidos."""
        # Alterado: 'imposto' para 'taxa'
        return (self.get_float_value(self.valorCompra.text()) is not None and
                self.get_float_value(self.valorVenda.text()) is not None and
                self.get_float_value(self.taxa.text()) is not None)


    def calculate_regime_fields(self):
        """
        Calcula automaticamente os campos 'Valor Base' e 'Imposto' com base no regime fiscal selecionado
        e nos valores de compra, venda e taxa.
        """
        # Desabilitamos sinais dos QLineEdit temporariamente para não disparar recursão
        self.valorBase.blockSignals(True)
        self.imposto.blockSignals(True) # Alterado: 'taxa' para 'imposto'

        # Usar QLocale para formatar os resultados
        locale = QLocale(QLocale.Language.Portuguese, QLocale.Country.Portugal)

        try:
            if self.regime_geral_radio.isChecked() and self.are_normal_regime_fields_valid():
                # Lógica de cálculo para Regime Normal
                valor_venda = self.get_float_value(self.valorVenda.text())
                taxa_percent = self.get_float_value(self.taxa.text()) # Alterado: 'imposto_percent' para 'taxa_percent'

                if valor_venda is not None and taxa_percent is not None:
                    # Cálculo para Regime Normal
                    divisor = (1 + taxa_percent / 100)
                    if divisor != 0:
                        valor_base_calculado = valor_venda / divisor
                        imposto_calculado = valor_base_calculado * (taxa_percent / 100) # Alterado: 'taxa_calculada' para 'imposto_calculado'

                        self.valorBase.setText(locale.toString(valor_base_calculado, 'f', 2))
                        self.imposto.setText(locale.toString(imposto_calculado, 'f', 2)) # Alterado: 'taxa' para 'imposto'

                        print(f"[DEBUG] Valor calculado - valorBase: {valor_base_calculado}")
                        print(f"[DEBUG] Valor calculado - imposto: {imposto_calculado}") # Alterado: 'taxa' para 'imposto'
                        print(f"[DEBUG] Texto aplicado - valorBase: {self.valorBase.text()}")
                        print(f"[DEBUG] Texto aplicado - imposto: {self.imposto.text()}") # Alterado: 'taxa' para 'imposto'
                    else:
                        self.valorBase.setText("Divisão por Zero")
                        self.imposto.setText("Erro") # Alterado: 'taxa' para 'imposto'
                else:
                    self.valorBase.clear()
                    self.imposto.clear() # Alterado: 'taxa' para 'imposto'

            elif self.regime_lucro_tributavel_radio.isChecked() and self.are_margin_regime_fields_valid():
                # Lógica de cálculo para Regime de Margem
                valor_venda = self.get_float_value(self.valorVenda.text())
                valor_compra = self.get_float_value(self.valorCompra.text())
                taxa_percent = self.get_float_value(self.taxa.text()) # Alterado: 'imposto_percent' para 'taxa_percent'

                if valor_venda is not None and valor_compra is not None and taxa_percent is not None:
                    # Cálculo para Regime de Margem
                    divisor = (1 + taxa_percent / 100)
                    if divisor != 0:
                        margem_bruta = valor_venda - valor_compra
                        valor_base_calculado = margem_bruta / divisor
                        imposto_calculado = valor_base_calculado * (taxa_percent / 100) # Alterado: 'taxa_calculada' para 'imposto_calculado'

                        self.valorBase.setText(locale.toString(valor_base_calculado, 'f', 2))
                        self.imposto.setText(locale.toString(imposto_calculado, 'f', 2)) # Alterado: 'taxa' para 'imposto'

                        print(f"[DEBUG] Valor calculado - valorBase: {valor_base_calculado}")
                        print(f"[DEBUG] Valor calculado - imposto: {imposto_calculado}") # Alterado: 'taxa' para 'imposto'
                        print(f"[DEBUG] Texto aplicado - valorBase: {self.valorBase.text()}")
                        print(f"[DEBUG] Texto aplicado - imposto: {self.imposto.text()}") # Alterado: 'taxa' para 'imposto'
                    else:
                        self.valorBase.setText("Divisão por Zero")
                        self.imposto.setText("Erro") # Alterado: 'taxa' para 'imposto'
                else:
                    self.valorBase.clear()
                    self.imposto.clear() # Alterado: 'taxa' para 'imposto'
            else:
                # Se nenhum regime válido estiver selecionado ou os campos não forem válidos, limpar
                self.valorBase.clear()
                self.imposto.clear() # Alterado: 'taxa' para 'imposto'

        except Exception as e:
            print(f"Erro no cálculo de campos: {e}")
            self.valorBase.clear()
            self.imposto.clear() # Alterado: 'taxa' para 'imposto'

        # Reabilitar sinais dos QLineEdit
        self.valorBase.blockSignals(False)
        self.imposto.blockSignals(False) # Alterado: 'taxa' para 'imposto'


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
                self.imposto.clear() # Alterado: 'taxa' para 'imposto'


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
        # Adicione mais validações de campos gerais aqui se necessário

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
            if not self.are_normal_regime_fields_valid():
                QMessageBox.warning(self, "Campos em Falta para Regime Normal",
                                    "Por favor, preencha 'Valor de Venda' e 'Taxa' para o Regime Normal.") # Alterado: 'Imposto' para 'Taxa'
                return False

        elif current_regime_selected == "Margem":
            if not self.are_margin_regime_fields_valid():
                QMessageBox.warning(self, "Campos em Falta para Regime Margem",
                                    "Por favor, preencha 'Valor de Compra', 'Valor de Venda' e 'Taxa' para o Regime Margem.") # Alterado: 'Imposto' para 'Taxa'
                return False

        return True

    def add_record(self):
        self.calculate_regime_fields()
        # Antes de adicionar/atualizar, chamar a validação final
        if not self.validate_all_fields_for_save():
            return  # Se a validação falhar, não prossegue com a gravação

        try:
            isv = self.get_float_value(self.isv.text())
            nRegistoContabilidade = self.nRegistoContabilidade.text()
            valor_compra = self.get_float_value(self.valorCompra.text())
            valor_venda = self.get_float_value(self.valorVenda.text())
            taxa = self.get_float_value(self.taxa.text()) # Taxa agora é lida como input
            # Certifique-se de que valorBase e imposto são lidos dos campos, não recalculados aqui
            valorBase_from_field = self.get_float_value(self.valorBase.text())
            imposto_from_field = self.get_float_value(self.imposto.text()) # Imposto agora é o output
            print(f"[DEBUG] valorBase_from_field: {valorBase_from_field}")
            print(f"[DEBUG] imposto_from_field: {imposto_from_field}") # Alterado: 'taxa' para 'imposto'
            data_compra_str = self.dataCompra.date().toString("yyyy-MM-dd")
            data_venda_str = self.dataVenda.date().toString("yyyy-MM-dd")

            regime_fiscal = ""
            if self.regime_geral_radio.isChecked():
                regime_fiscal = "Regime Normal"
            elif self.regime_lucro_tributavel_radio.isChecked():
                regime_fiscal = "Margem"

            if self.mode == "edit":
                success = update_expense_in_db(self.initial_data["id"], {
                    "matricula": self.matricula.text(),
                    "marca": self.marca.text(),
                    "isv": isv,
                    "nRegistoContabilidade": nRegistoContabilidade,
                    "dataCompra": data_compra_str,
                    "docCompra": self.docCompra.text(),
                    "tipoDocumento": self.tipoDocumento.currentText(),
                    "valorCompra": valor_compra,
                    "dataVenda": data_venda_str,
                    "docVenda": self.docVenda.text(),
                    "valorVenda": valor_venda,
                    "imposto": imposto_from_field, # Usar o valor do campo que agora é o resultado do imposto
                    "valorBase": valorBase_from_field,
                    "taxa": taxa, # Taxa é o input
                    "regime_fiscal": regime_fiscal
                })
            else:
                print("\n--- Argumentos passados para add_expense_to_db ---")
                print(f"matricula: {self.matricula.text()}")
                print(f"marca: {self.marca.text()}")
                print(f"isv: {isv}")
                print(f"nRegistoContabilidade: {nRegistoContabilidade}")
                print(f"dataCompra: {data_compra_str}")
                print(f"docCompra: {self.docCompra.text()}")
                print(f"tipoDocumento: {self.tipoDocumento.currentText()}")
                print(f"valorCompra: {valor_compra}")
                print(f"dataVenda: {data_venda_str}")
                print(f"docVenda: {self.docVenda.text()}")
                print(f"valorVenda: {valor_venda}")
                print(f"imposto: {imposto_from_field}") # Passar o imposto como o output calculado
                print(f"valorBase: {valorBase_from_field}")
                print(f"taxa: {taxa}") # Passar a taxa como input
                print(f"regime_fiscal: {regime_fiscal}")
                print("--- Fim dos Argumentos ---")

                success = add_expense_to_db(
                    self.matricula.text(), self.marca.text(), isv,
                    nRegistoContabilidade,
                    data_compra_str, self.docCompra.text(),
                    self.tipoDocumento.currentText(), valor_compra, data_venda_str,
                    self.docVenda.text(), valor_venda, imposto_from_field, valorBase_from_field, taxa, # Passar valores dos campos, com imposto e taxa invertidos
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
            ["ID", "Matrícula", "Marca", "Valor de Compra", "Documento de Venda", "Valor de Venda", "Imposto"] # Esta label continua a ser 'Imposto' para o que é exibido
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
        border: 1px solid #4caf50; /* Borda verde no hover */
    }
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
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

    def clear_inputs(self):
        # Estes campos não estão definidos nesta classe, verificar se são necessários
        # self.date_box.setDate(QDate.currentDate())
        # self.dropdown.setCurrentIndex(0)
        # self.amount.clear()
        # self.description.clear()
        pass