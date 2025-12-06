"""
Interface Gráfica do Sistema Financeiro
Desenvolvida com PyQt6, inspirada no design do Bling
"""

import sys
import os
import requests
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit,
    QComboBox, QDateEdit, QDialog, QFormLayout, QTextEdit, QHeaderView,
    QFrame, QScrollArea, QMessageBox, QSpinBox, QDoubleSpinBox, QSplitter,
    QTabWidget, QListWidget, QSizePolicy, QFileDialog, QScrollBar, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, QSize
from PyQt6.QtGui import QFont, QIcon, QColor

import statistics
from decimal import Decimal
import database
from models import TipoLancamento, StatusLancamento, ContaBancaria, Lancamento, Categoria, Lancamento, Categoria

# Matplotlib para gráficos
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class UpperCaseLineEdit(QLineEdit):
    """QLineEdit que converte automaticamente para maiúsculas"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textChanged.connect(self._to_upper)
    
    def _to_upper(self):
        cursor_pos = self.cursorPosition()
        self.blockSignals(True)
        self.setText(self.text().upper())
        self.blockSignals(False)
        self.setCursorPosition(cursor_pos)


class UpperCaseTextEdit(QTextEdit):
    """QTextEdit que converte automaticamente para maiúsculas"""
    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        cursor = self.textCursor()
        pos = cursor.position()
        self.blockSignals(True)
        self.setPlainText(self.toPlainText().upper())
        self.blockSignals(False)
        cursor.setPosition(pos)
        self.setTextCursor(cursor)


class SidebarButton(QPushButton):
    """Botão customizado para o menu lateral"""
    def __init__(self, text, icon_text="", scale_factor=1.0):
        super().__init__(f"{icon_text}  {text}")
        self.setCheckable(True)
        self.setMinimumHeight(int(45 * scale_factor))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class CustomCheckBox(QCheckBox):
    """Checkbox customizado com checkmark preto dentro do quadrado branco"""
    def paintEvent(self, a0):
        """Desenha o checkbox com checkmark customizado"""
        from PyQt6.QtGui import QPainter, QPen
        
        super().paintEvent(a0)
        
        if self.isChecked():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Definir cor e espessura do checkmark
            pen = QPen(QColor("black"))
            pen.setWidth(3)
            painter.setPen(pen)
            
            # Desenhar o checkmark (✓) dentro do indicador
            # Coordenadas relativas ao tamanho do checkbox
            x_offset = 4
            y_offset = 10
            painter.drawLine(x_offset + 2, y_offset, x_offset + 6, y_offset + 4)
            painter.drawLine(x_offset + 6, y_offset + 4, x_offset + 14, y_offset - 4)
            
            painter.end()

class MainWindow(QMainWindow):
    """Janela principal do sistema"""
    
    def __init__(self):
        super().__init__()
        # Inicializar banco de dados SQLite
        database.criar_tabelas()
        # Helpers para compatibilidade
        self._clientes_cache = None
        self._fornecedores_cache = None
        self.sidebar_visible = True
        
        # Calcular escala baseada na resolução da tela
        screen = QApplication.primaryScreen()
        if screen:
            screen_width = screen.geometry().width()
            # Escala baseada em 1920px como referência (monitores Full HD)
            # Para 1366px (15"): escala ~0.71
            # Para 1920px (24"): escala 1.0
            # Para 2560px (27"): escala ~1.33
            # Para 3840px (32" 4K): escala 2.0
            self.scale_factor = screen_width / 1920.0
            # Limitar escala entre 0.7 e 2.0
            self.scale_factor = max(0.7, min(2.0, self.scale_factor))
        else:
            self.scale_factor = 1.0
        
        self.init_ui()
    
    def scale_size(self, base_size):
        """Retorna tamanho escalado baseado na resolução"""
        return int(base_size * self.scale_factor)
    
    def formatar_moeda(self, valor):
        """Formata valor monetário com vírgula nas casas decimais"""
        # Formata com ponto como separador de milhar e vírgula como decimal
        valor_formatado = f"{valor:,.2f}"
        # Substitui vírgula por um placeholder temporário
        valor_formatado = valor_formatado.replace(",", "TEMP")
        # Substitui ponto por vírgula (decimal)
        valor_formatado = valor_formatado.replace(".", ",")
        # Substitui placeholder por ponto (milhar)
        valor_formatado = valor_formatado.replace("TEMP", ".")
        return f"R$ {valor_formatado}"
        
    def init_ui(self):
        """Inicializa a interface"""
        self.setWindowTitle("Sistema Financeiro - Gestao Empresarial")
        
        # Obter informações da tela
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
            
            # Calcular tamanho mínimo baseado na resolução (80% da tela)
            min_width = int(screen_width * 0.8)
            min_height = int(screen_height * 0.8)
            
            # Definir tamanho mínimo adaptativo
            self.setMinimumSize(min_width, min_height)
        else:
            # Fallback para tamanhos fixos se não conseguir detectar a tela
            self.setMinimumSize(1200, 700)
        
        self.showMaximized()
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Criar sidebar e área de conteúdo
        self.create_sidebar()
        self.create_content_area()
        
        # Adicionar ao layout principal
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area)
        
        # Criar barra de status
        status_bar = self.statusBar()
        if status_bar:
            status_bar.setStyleSheet("""
                QStatusBar {
                    background-color: #f8f9fa;
                    color: #666;
                    border-top: 1px solid #ddd;
                    padding: 5px;
                }
            """)
            status_bar.showMessage("✓ Sistema pronto. Dados salvos automaticamente.", 5000)
        
        # Mostrar contas bancárias por padrão
        self.show_contas_bancarias()
        
        # Aplicar estilos
        self.apply_styles()
        
    def create_sidebar(self):
        """Cria o menu lateral"""
        self.sidebar = QFrame()
        
        # Largura adaptativa da sidebar (15% da largura da tela, mín 200px, máx 300px)
        screen = QApplication.primaryScreen()
        if screen:
            screen_width = screen.geometry().width()
            sidebar_width = max(200, min(300, int(screen_width * 0.15)))
            self.sidebar.setFixedWidth(sidebar_width)
        else:
            self.sidebar.setFixedWidth(250)
        
        self.sidebar.setObjectName("sidebar")
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Logo/Título
        header = QLabel("Sistema Financeiro")
        header.setObjectName("sidebarHeader")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setMinimumHeight(self.scale_size(70))
        header.setFont(QFont("Segoe UI", self.scale_size(12), QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Botões do menu
        self.btn_contas = SidebarButton("Contas Bancarias", "🏦", self.scale_factor)
        self.btn_receber = SidebarButton("Contas a Receber", "💰", self.scale_factor)
        self.btn_pagar = SidebarButton("Contas a Pagar", "💳", self.scale_factor)
        self.btn_fluxo = SidebarButton("Fluxo de Caixa", "📈", self.scale_factor)
        self.btn_cadastros = SidebarButton("Cadastros", "📋", self.scale_factor)
        self.btn_relatorios = SidebarButton("Relatorios", "📑", self.scale_factor)
        
        # Container para submenu de cadastros
        self.cadastros_container = QWidget()
        self.cadastros_layout = QVBoxLayout(self.cadastros_container)
        self.cadastros_layout.setContentsMargins(0, 0, 0, 0)
        self.cadastros_layout.setSpacing(0)
        
        # Adicionar botão principal de cadastros
        self.cadastros_layout.addWidget(self.btn_cadastros)
        
        # Submenu de cadastros (inicialmente oculto)
        self.submenu_cadastros = QWidget()
        self.submenu_cadastros.setObjectName("submenuCadastros")
        submenu_layout = QVBoxLayout(self.submenu_cadastros)
        submenu_layout.setContentsMargins(20, 0, 0, 0)
        submenu_layout.setSpacing(0)
        
        self.btn_categorias = SidebarButton("Categorias", "🏷️", self.scale_factor)
        self.btn_clientes = SidebarButton("Clientes", "👥", self.scale_factor)
        self.btn_fornecedores = SidebarButton("Fornecedores", "🏢", self.scale_factor)
        
        submenu_layout.addWidget(self.btn_categorias)
        submenu_layout.addWidget(self.btn_clientes)
        submenu_layout.addWidget(self.btn_fornecedores)
        
        self.cadastros_layout.addWidget(self.submenu_cadastros)
        self.submenu_cadastros.setVisible(False)
        
        # Container para submenu de relatórios
        self.relatorios_container = QWidget()
        self.relatorios_layout = QVBoxLayout(self.relatorios_container)
        self.relatorios_layout.setContentsMargins(0, 0, 0, 0)
        self.relatorios_layout.setSpacing(0)
        
        # Adicionar botão principal de relatórios
        self.relatorios_layout.addWidget(self.btn_relatorios)
        
        # Submenu de relatórios (inicialmente oculto)
        self.submenu_relatorios = QWidget()
        self.submenu_relatorios.setObjectName("submenuRelatorios")
        submenu_relatorios_layout = QVBoxLayout(self.submenu_relatorios)
        submenu_relatorios_layout.setContentsMargins(20, 0, 0, 0)
        submenu_relatorios_layout.setSpacing(0)
        
        self.btn_fluxo_projetado = SidebarButton("Fluxo de Caixa Projetado", "🔮", self.scale_factor)
        self.btn_analise_contas = SidebarButton("Análise de Contas", "📊", self.scale_factor)
        self.btn_resumo_parceiros = SidebarButton("Resumo por Cliente/Fornecedor", "📇", self.scale_factor)
        self.btn_analise_categorias = SidebarButton("Análise de Categorias", "📁", self.scale_factor)
        self.btn_comparativo_periodos = SidebarButton("Comparativo de Períodos", "📉", self.scale_factor)
        self.btn_indicadores = SidebarButton("Indicadores Financeiros", "🎯", self.scale_factor)
        self.btn_inadimplencia = SidebarButton("Inadimplência", "⚠️", self.scale_factor)
        self.btn_evolucao_patrimonial = SidebarButton("Evolução Patrimonial", "📈", self.scale_factor)
        
        submenu_relatorios_layout.addWidget(self.btn_fluxo_projetado)
        submenu_relatorios_layout.addWidget(self.btn_analise_contas)
        submenu_relatorios_layout.addWidget(self.btn_resumo_parceiros)
        submenu_relatorios_layout.addWidget(self.btn_analise_categorias)
        submenu_relatorios_layout.addWidget(self.btn_comparativo_periodos)
        submenu_relatorios_layout.addWidget(self.btn_indicadores)
        submenu_relatorios_layout.addWidget(self.btn_inadimplencia)
        submenu_relatorios_layout.addWidget(self.btn_evolucao_patrimonial)
        
        self.relatorios_layout.addWidget(self.submenu_relatorios)
        self.submenu_relatorios.setVisible(False)
        
        # Adicionar botões
        self.menu_buttons = [
            self.btn_contas,
            self.btn_receber, self.btn_pagar, self.btn_fluxo,
            self.btn_cadastros, self.btn_relatorios
        ]
        
        layout.addWidget(self.btn_contas)
        layout.addWidget(self.btn_receber)
        layout.addWidget(self.btn_pagar)
        layout.addWidget(self.btn_fluxo)
        layout.addWidget(self.cadastros_container)
        layout.addWidget(self.relatorios_container)
        
        # Conectar eventos
        self.btn_contas.clicked.connect(self.handle_menu_click)
        self.btn_receber.clicked.connect(self.handle_menu_click)
        self.btn_pagar.clicked.connect(self.handle_menu_click)
        self.btn_fluxo.clicked.connect(self.handle_menu_click)
        self.btn_cadastros.clicked.connect(self.toggle_cadastros_menu)
        self.btn_relatorios.clicked.connect(self.toggle_relatorios_menu)
        
        self.btn_categorias.clicked.connect(lambda: self.show_cadastros(0))
        self.btn_clientes.clicked.connect(self.show_clientes)
        self.btn_fornecedores.clicked.connect(self.show_fornecedores)
        
        self.btn_fluxo_projetado.clicked.connect(self.show_fluxo_projetado)
        self.btn_analise_contas.clicked.connect(self.show_analise_contas)
        self.btn_resumo_parceiros.clicked.connect(self.show_resumo_parceiros)
        self.btn_analise_categorias.clicked.connect(self.show_analise_categorias)
        self.btn_comparativo_periodos.clicked.connect(self.show_comparativo_periodos)
        self.btn_indicadores.clicked.connect(self.show_indicadores)
        self.btn_inadimplencia.clicked.connect(self.show_inadimplencia)
        self.btn_evolucao_patrimonial.clicked.connect(self.show_evolucao_patrimonial)
        
        layout.addStretch()
        
        # Botão Calculadora
        btn_calculadora = QPushButton("🔢  Calculadora")
        btn_calculadora.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                padding: 10px 15px;
                text-align: left;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        btn_calculadora.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_calculadora.clicked.connect(self.abrir_calculadora)
        layout.addWidget(btn_calculadora)
        
        # Rodapé com informações
        footer = QLabel("v1.0.0")
        footer.setObjectName("sidebarFooter")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setMinimumHeight(self.scale_size(40))
        layout.addWidget(footer)
        
    def toggle_sidebar(self):
        """Alterna a visibilidade da sidebar"""
        self.sidebar_visible = not self.sidebar_visible
        self.sidebar.setVisible(self.sidebar_visible)
        
        # Atualizar ícone do botão
        if self.sidebar_visible:
            self.btn_toggle_sidebar.setText("◀")
            self.btn_toggle_sidebar.setToolTip("Ocultar menu")
        else:
            self.btn_toggle_sidebar.setText("▶")
            self.btn_toggle_sidebar.setToolTip("Mostrar menu")
    
    def create_content_area(self):
        """Cria a área de conteúdo principal"""
        self.content_area = QFrame()
        self.content_area.setObjectName("contentArea")
        
        main_content_layout = QVBoxLayout(self.content_area)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(0)
        
        # Botão para ocultar/mostrar sidebar
        toggle_bar = QWidget()
        toggle_bar.setStyleSheet("background-color: #2c3e50;")
        toggle_bar.setFixedHeight(40)
        toggle_layout = QHBoxLayout(toggle_bar)
        toggle_layout.setContentsMargins(10, 5, 10, 5)
        
        self.btn_toggle_sidebar = QPushButton("◀")
        self.btn_toggle_sidebar.setToolTip("Ocultar menu")
        self.btn_toggle_sidebar.setFixedSize(30, 30)
        self.btn_toggle_sidebar.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)
        self.btn_toggle_sidebar.clicked.connect(self.toggle_sidebar)
        toggle_layout.addWidget(self.btn_toggle_sidebar)
        toggle_layout.addStretch()
        
        main_content_layout.addWidget(toggle_bar)
        
        # Área de conteúdo scrollável
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(15)
        
        main_content_layout.addWidget(content_widget)
        
    def handle_menu_click(self):
        """Trata cliques nos botões do menu"""
        sender = self.sender()
        
        # Desmarcar outros botões
        for btn in self.menu_buttons:
            btn.setChecked(btn == sender)
        
        # Navegar para a tela correspondente
        if sender == self.btn_contas:
            self.show_contas_bancarias()
        elif sender == self.btn_receber:
            self.show_contas_receber()
        elif sender == self.btn_pagar:
            self.show_contas_pagar()
        elif sender == self.btn_fluxo:
            self.show_fluxo_caixa()
        elif sender == self.btn_cadastros:
            self.show_cadastros()
        elif sender == self.btn_relatorios:
            self.show_relatorios()
    
    def clear_content(self):
        """Limpa a área de conteúdo"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child is not None:
                widget = child.widget()
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()
                else:
                    # Se for um layout, limpar recursivamente
                    layout = child.layout()
                    if layout is not None:
                        self.clear_layout(layout)
                        # Deletar o layout após limpar
                        layout.deleteLater()
        
        # Forçar atualização visual
        self.content_area.update()
    
    def clear_layout(self, layout):
        """Limpa um layout recursivamente"""
        if layout is None:
            return
        while layout.count():
            child = layout.takeAt(0)
            if child is not None:
                widget = child.widget()
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()
                else:
                    sublayout = child.layout()
                    if sublayout is not None:
                        self.clear_layout(sublayout)
                        # Deletar o sublayout após limpar
                        sublayout.deleteLater()
    

    
    def create_card(self, titulo, valor, cor):
        """Cria um card de informação"""
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(self.scale_size(120))
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(titulo)
        title_label.setObjectName("cardTitle")
        title_label.setFont(QFont("Segoe UI", self.scale_size(9)))
        layout.addWidget(title_label)
        
        value_label = QLabel(valor)
        value_label.setObjectName("cardValue")
        value_label.setFont(QFont("Segoe UI", self.scale_size(20), QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {cor};")
        layout.addWidget(value_label)
        
        return card
    
    def create_proximos_vencimentos(self):
        """Cria tabela com próximos vencimentos"""
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        
        title = QLabel("Proximos Vencimentos (7 dias)")
        title.setObjectName("cardTitle")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(title)
        
        hoje = datetime.now()
        fim = hoje + timedelta(days=7)
        lancamentos = [l for l in database.listar_lancamentos() if hoje <= l.data_vencimento <= fim]
        lancamentos = [l for l in lancamentos if l.status == StatusLancamento.PENDENTE]
        lancamentos.sort(key=lambda x: x.data_vencimento)
        
        if lancamentos:
            table = QTableWidget()
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["Tipo", "Descrição", "Valor", "Vencimento", "Pessoa"])
            table.setRowCount(len(lancamentos[:10]))  # Máximo 10
            
            for i, lanc in enumerate(lancamentos[:10]):
                tipo_icon = "REC" if lanc.tipo == TipoLancamento.RECEITA else "DESP"
                table.setItem(i, 0, QTableWidgetItem(tipo_icon))
                table.setItem(i, 1, QTableWidgetItem(lanc.descricao))
                table.setItem(i, 2, QTableWidgetItem(self.formatar_moeda(lanc.valor)))
                table.setItem(i, 3, QTableWidgetItem(lanc.data_vencimento.strftime("%d/%m/%Y")))
                table.setItem(i, 4, QTableWidgetItem(lanc.pessoa or "-"))
            
            vheader = table.verticalHeader()
            if vheader:
                vheader.setVisible(False)
            
            header = table.horizontalHeader()
            if header:
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            layout.addWidget(table)
        else:
            label_vazio = QLabel("Nenhum vencimento proximo")
            label_vazio.setFont(QFont("Segoe UI", 9))
            layout.addWidget(label_vazio)
        
        return frame
    
    def show_contas_bancarias(self):
        """Exibe tela de contas bancárias"""
        self.clear_content()
        
        # Desmarcar todos os botões
        for btn in self.menu_buttons:
            btn.setChecked(False)
        self.btn_contas.setChecked(True)
        
        # Cabeçalho
        header = QHBoxLayout()
        title = QLabel("Contas Bancarias")
        title.setObjectName("pageTitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        
        btn_nova = QPushButton("+ Nova Conta")
        btn_nova.setObjectName("primaryButton")
        btn_nova.clicked.connect(self.dialog_nova_conta)
        header.addWidget(btn_nova)
        
        btn_recalcular = QPushButton("🔄 Recalcular Saldos")
        btn_recalcular.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        btn_recalcular.setToolTip("Recalcula os saldos das contas baseado nos lançamentos")
        btn_recalcular.clicked.connect(self.recalcular_saldos)
        header.addWidget(btn_recalcular)
        
        self.content_layout.addLayout(header)
        
        # Dashboard Expandido com Resumo Financeiro
        contas = database.listar_contas()
        saldo_total = sum(conta.saldo_atual for conta in contas)
        
        dashboard_frame = QFrame()
        dashboard_frame.setObjectName("summaryFrame")
        dashboard_frame.setMaximumWidth(1200)
        dashboard_layout = QHBoxLayout(dashboard_frame)
        
        # Card de Saldo Total (expandido)
        card_saldo_total = QFrame()
        card_saldo_total.setStyleSheet(f"""
            QFrame {{
                background-color: {'#d4edda' if saldo_total >= 0 else '#f8d7da'};
                border-left: 5px solid {'#28a745' if saldo_total >= 0 else '#dc3545'};
                border-radius: 5px;
                padding: 10px;
            }}
        """)
        card_saldo_layout = QVBoxLayout(card_saldo_total)
        card_saldo_layout.setSpacing(5)
        
        titulo_saldo = QLabel("💰 Saldo Total")
        titulo_saldo.setStyleSheet("font-size: 12px; color: #666; font-weight: bold;")
        card_saldo_layout.addWidget(titulo_saldo)
        
        valor_saldo = QLabel(self.formatar_moeda(saldo_total))
        valor_saldo.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {'#28a745' if saldo_total >= 0 else '#dc3545'};")
        card_saldo_layout.addWidget(valor_saldo)
        
        # Informação adicional: maior e menor saldo
        if contas:
            maior_saldo = max([c.saldo_atual for c in contas])
            menor_saldo = min([c.saldo_atual for c in contas])
            info_saldo = QLabel(f"<small>Maior: {self.formatar_moeda(maior_saldo)}<br>Menor: {self.formatar_moeda(menor_saldo)}</small>")
            info_saldo.setStyleSheet("color: #666;")
            card_saldo_layout.addWidget(info_saldo)
        
        dashboard_layout.addWidget(card_saldo_total)
        
        # Card de Quantidade de Contas (expandido)
        card_qtd = QFrame()
        card_qtd.setStyleSheet("""
            QFrame {
                background-color: #d1ecf1;
                border-left: 5px solid #17a2b8;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        card_qtd_layout = QVBoxLayout(card_qtd)
        card_qtd_layout.setSpacing(5)
        
        titulo_qtd = QLabel("🏦 Total de Contas")
        titulo_qtd.setStyleSheet("font-size: 12px; color: #666; font-weight: bold;")
        card_qtd_layout.addWidget(titulo_qtd)
        
        valor_qtd = QLabel(str(len(contas)))
        valor_qtd.setStyleSheet("font-size: 24px; font-weight: bold; color: #17a2b8;")
        card_qtd_layout.addWidget(valor_qtd)
        
        # Informação adicional: contas ativas
        if contas:
            contas_ativas = len([c for c in contas if c.saldo_atual > 0])
            info_qtd = QLabel(f"<small>Com Saldo: {contas_ativas}<br>Zeradas: {len(contas) - contas_ativas}</small>")
            info_qtd.setStyleSheet("color: #666;")
            card_qtd_layout.addWidget(info_qtd)
        
        dashboard_layout.addWidget(card_qtd)
        
        # Card de Saldo Médio (NOVO)
        card_medio = QFrame()
        card_medio.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border-left: 5px solid #ffc107;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        card_medio_layout = QVBoxLayout(card_medio)
        card_medio_layout.setSpacing(5)
        
        titulo_medio = QLabel("📊 Saldo Médio")
        titulo_medio.setStyleSheet("font-size: 12px; color: #666; font-weight: bold;")
        card_medio_layout.addWidget(titulo_medio)
        
        saldo_medio = saldo_total / len(contas) if contas else 0
        valor_medio = QLabel(self.formatar_moeda(saldo_medio))
        valor_medio.setStyleSheet("font-size: 24px; font-weight: bold; color: #f0ad4e;")
        card_medio_layout.addWidget(valor_medio)
        
        # Informação adicional: distribuição
        if contas and len(contas) > 1:
            saldos = [c.saldo_atual for c in contas]
            try:
                desvio = statistics.stdev(saldos)
                info_medio = QLabel(f"<small>Desvio Padrão:<br>{self.formatar_moeda(desvio)}</small>")
            except statistics.StatisticsError:
                # Desvio padrão requer ao menos 2 valores
                info_medio = QLabel("<small>Distribuição uniforme</small>")
            info_medio.setStyleSheet("color: #666;")
            card_medio_layout.addWidget(info_medio)
        
        dashboard_layout.addWidget(card_medio)
        
        # Card de Variação Mensal (NOVO)
        card_variacao = QFrame()
        card_variacao_layout = QVBoxLayout(card_variacao)
        card_variacao_layout.setSpacing(5)
        
        titulo_variacao = QLabel("📈 Variação Mensal")
        titulo_variacao.setStyleSheet("font-size: 12px; color: #666; font-weight: bold;")
        card_variacao_layout.addWidget(titulo_variacao)
        
        # Calcular variação do mês atual
        from datetime import datetime
        hoje = datetime.now().date()
        inicio_mes = datetime(hoje.year, hoje.month, 1).date()
        
        lancamentos = database.listar_lancamentos()
        receitas_mes = sum([l.valor for l in lancamentos 
                           if l.tipo == TipoLancamento.RECEITA and 
                           l.status == StatusLancamento.PAGO and
                           l.data_pagamento and
                           l.data_pagamento.date() >= inicio_mes])
        
        despesas_mes = sum([l.valor for l in lancamentos 
                           if l.tipo == TipoLancamento.DESPESA and 
                           l.status == StatusLancamento.PAGO and
                           l.data_pagamento and
                           l.data_pagamento.date() >= inicio_mes])
        
        variacao = receitas_mes - despesas_mes
        valor_variacao = QLabel(self.formatar_moeda(abs(variacao)))
        valor_variacao.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {'#28a745' if variacao >= 0 else '#dc3545'};")
        card_variacao_layout.addWidget(valor_variacao)
        
        if variacao >= 0:
            card_variacao.setStyleSheet("""
                QFrame {
                    background-color: #d4edda;
                    border-left: 5px solid #28a745;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)
            info_variacao = QLabel("<small>Crescimento este mês</small>")
        else:
            card_variacao.setStyleSheet("""
                QFrame {
                    background-color: #f8d7da;
                    border-left: 5px solid #dc3545;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)
            info_variacao = QLabel("<small>Redução este mês</small>")
        
        info_variacao.setStyleSheet("color: #666;")
        card_variacao_layout.addWidget(info_variacao)
        
        dashboard_layout.addWidget(card_variacao)
        
        dashboard_layout.addStretch()
        self.content_layout.addWidget(dashboard_frame)
        
        # Tabela de contas
        table = QTableWidget()
        table.setObjectName("dataTable")
        contas = database.listar_contas()
        
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Banco", "Agência", "Conta", "Saldo Inicial", "Saldo Atual", "Ações"])
        table.setRowCount(len(contas))
        
        for i, conta in enumerate(contas):
            banco_item = QTableWidgetItem(conta.banco)
            banco_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            banco_item.setForeground(QColor("#000000"))
            banco_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            table.setItem(i, 0, banco_item)
            
            agencia_item = QTableWidgetItem(conta.agencia)
            agencia_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            agencia_item.setForeground(QColor("#000000"))
            agencia_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            table.setItem(i, 1, agencia_item)
            
            conta_item = QTableWidgetItem(conta.conta)
            conta_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            conta_item.setForeground(QColor("#000000"))
            conta_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            table.setItem(i, 2, conta_item)
            
            saldo_inicial_item = QTableWidgetItem(self.formatar_moeda(conta.saldo_inicial))
            saldo_inicial_item.setForeground(QColor("#000000"))
            saldo_inicial_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            saldo_inicial_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(i, 3, saldo_inicial_item)
            
            saldo_item = QTableWidgetItem(self.formatar_moeda(conta.saldo_atual))
            cor = QColor("#4CAF50") if conta.saldo_atual >= 0 else QColor("#F44336")
            saldo_item.setForeground(cor)
            saldo_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            saldo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(i, 4, saldo_item)
            
            # Widget de ações com botões de editar e excluir
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            actions_layout.setSpacing(5)
            
            btn_editar = QPushButton("✏️")
            btn_editar.setToolTip("Editar conta")
            btn_editar.setMaximumWidth(35)
            btn_editar.setStyleSheet("QPushButton { background-color: transparent; border: 1px solid #ddd; border-radius: 3px; padding: 5px; font-size: 18px; } QPushButton:hover { background-color: #f0f0f0; }")
            btn_editar.clicked.connect(lambda checked=False, c=conta, idx=i: self.dialog_editar_conta(c, idx))
            actions_layout.addWidget(btn_editar)
            
            btn_excluir = QPushButton("✖")
            btn_excluir.setToolTip("Excluir conta")
            btn_excluir.setMaximumWidth(35)
            btn_excluir.setStyleSheet("QPushButton { background-color: transparent; border: 1px solid #ddd; border-radius: 3px; padding: 5px; font-size: 18px; color: #dc3545; font-weight: bold; } QPushButton:hover { background-color: #fee; }")
            btn_excluir.clicked.connect(lambda checked=False, nome=conta.nome: self.excluir_conta(nome))
            actions_layout.addWidget(btn_excluir)
            
            table.setCellWidget(i, 5, actions_widget)
        
        header = table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        table.setShowGrid(False)
        
        # Configurar altura das linhas ajustável
        
        v_header = table.verticalHeader()
        if v_header:
            v_header.setVisible(False)
            v_header.setDefaultSectionSize(40)
            v_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setMaximumWidth(1200)
        
        self.content_layout.addWidget(table)
        self.content_layout.addStretch()
    
    def show_contas_pagar(self):
        """Exibe tela de contas a pagar"""
        self.clear_content()
        
        # Desmarcar todos os botões
        for btn in self.menu_buttons:
            btn.setChecked(False)
        self.btn_pagar.setChecked(True)
        
        # Header com título e botões
        header = QHBoxLayout()
        title = QLabel("Contas a Pagar")
        title.setObjectName("pageTitle")
        title.setFont(QFont("Segoe UI", self.scale_size(24), QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        
        # Botões de exportação no header
        btn_exportar_pdf = QPushButton("📄 Exportar PDF")
        btn_exportar_pdf.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 70px;
                height: 28px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        btn_exportar_pdf.clicked.connect(self.exportar_pagar_pdf)
        header.addWidget(btn_exportar_pdf)
        
        btn_exportar_excel = QPushButton("📊 Exportar Excel")
        btn_exportar_excel.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 70px;
                height: 28px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        btn_exportar_excel.clicked.connect(self.exportar_pagar_excel)
        header.addWidget(btn_exportar_excel)
        
        btn_atualizar = QPushButton("🔄 Atualizar")
        btn_atualizar.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 70px;
                height: 28px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        btn_atualizar.clicked.connect(self.atualizar_contas_pagar)
        header.addWidget(btn_atualizar)
        
        self.content_layout.addLayout(header)
        
        # Filtros Rápidos com ComboBox
        filtros_rapidos_frame = QFrame()
        filtros_rapidos_frame.setObjectName("quickFilterFrame")
        filtros_rapidos_layout = QHBoxLayout(filtros_rapidos_frame)
        filtros_rapidos_layout.setSpacing(15)
        
        # Label
        label_rapido = QLabel("Filtro Rápido:")
        label_rapido.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        filtros_rapidos_layout.addWidget(label_rapido)
        
        # ComboBox de filtro rápido
        self.combo_filtro_rapido_pagar = QComboBox()
        self.combo_filtro_rapido_pagar.addItems([
            "Todas",
            "Pendentes",
            "Vencidas",
            "Pagas",
            "Vence Hoje",
            "Próximos 7 dias",
            "Próximos 30 dias"
        ])
        self.combo_filtro_rapido_pagar.setCurrentText("Todas")
        self.combo_filtro_rapido_pagar.currentTextChanged.connect(self.aplicar_filtro_rapido_pagar_combo)
        self.combo_filtro_rapido_pagar.setStyleSheet("QComboBox { background-color: white; color: black; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        filtros_rapidos_layout.addWidget(self.combo_filtro_rapido_pagar)
        
        filtros_rapidos_layout.addStretch()
        self.content_layout.addWidget(filtros_rapidos_frame)
        
        # Filtros detalhados
        filtros_frame = QFrame()
        filtros_frame.setObjectName("filterFrame")
        filtros_layout = QHBoxLayout(filtros_frame)
        filtros_layout.setSpacing(10)
        
        # Filtro de status (oculto, controlado pelos botões rápidos)
        self.combo_status_pagar = QComboBox()
        self.combo_status_pagar.addItems(["Todos", "Pendentes", "Vencidas", "Pagas"])
        self.combo_status_pagar.currentTextChanged.connect(self.atualizar_contas_pagar)
        self.combo_status_pagar.setVisible(False)
        
        # Filtro de período
        filtros_layout.addWidget(QLabel("De:"))
        self.data_inicio_pagar = QDateEdit()
        self.data_inicio_pagar.setDate(QDate.currentDate().addMonths(-1))
        self.data_inicio_pagar.setCalendarPopup(True)
        filtros_layout.addWidget(self.data_inicio_pagar)
        
        filtros_layout.addWidget(QLabel("Até:"))
        self.data_fim_pagar = QDateEdit()
        self.data_fim_pagar.setDate(QDate.currentDate().addMonths(1))
        self.data_fim_pagar.setCalendarPopup(True)
        filtros_layout.addWidget(self.data_fim_pagar)
        
        # Botão de pesquisa por data
        btn_filtrar_data_pagar = QPushButton("🔍")
        btn_filtrar_data_pagar.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ddd;
                padding: 8px 12px;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-color: #999;
            }
        """)
        btn_filtrar_data_pagar.setToolTip("Filtrar por período")
        btn_filtrar_data_pagar.clicked.connect(self.atualizar_contas_pagar)
        filtros_layout.addWidget(btn_filtrar_data_pagar)
        
        # Busca com botão de lupa
        search_container = QWidget()
        search_container_layout = QHBoxLayout(search_container)
        search_container_layout.setContentsMargins(0, 0, 0, 0)
        search_container_layout.setSpacing(0)
        
        self.search_pagar = UpperCaseLineEdit()
        self.search_pagar.setPlaceholderText("Buscar por descricao ou fornecedor...")
        self.search_pagar.textChanged.connect(self.atualizar_contas_pagar)
        self.search_pagar.setStyleSheet("""
            QLineEdit {
                padding-right: 30px;
                background-color: white;
            }
        """)
        search_container_layout.addWidget(self.search_pagar)
        
        # Botão de lupa dentro do campo de texto
        btn_search_fornecedores = QPushButton("🔍")
        btn_search_fornecedores.setFixedSize(25, 25)
        btn_search_fornecedores.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search_fornecedores.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
                margin-right: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-radius: 3px;
            }
        """)
        btn_search_fornecedores.clicked.connect(self.dialog_selecionar_fornecedor)
        btn_search_fornecedores.setToolTip("Selecionar fornecedor cadastrado")
        
        # Posicionar botão sobre o campo de texto
        search_container_layout.addWidget(btn_search_fornecedores)
        search_container_layout.setAlignment(btn_search_fornecedores, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        btn_search_fornecedores.move(self.search_pagar.width() - 30, 2)
        
        filtros_layout.addWidget(search_container)
        
        filtros_layout.addStretch()
        
        self.content_layout.addWidget(filtros_frame)
        
        # Filtros detalhados adicionais
        filtros_detalhados_frame = QFrame()
        filtros_detalhados_frame.setObjectName("filterFrame")
        filtros_detalhados_frame.setStyleSheet("QFrame#filterFrame { background-color: white; }")
        filtros_detalhados_layout = QHBoxLayout(filtros_detalhados_frame)
        filtros_detalhados_layout.setSpacing(10)
        
        # Filtro por categoria
        filtros_detalhados_layout.addWidget(QLabel("Categoria:"))
        self.combo_categoria_pagar = QComboBox()
        self.combo_categoria_pagar.addItem("Todas")
        categorias_despesa = [cat.nome for cat in database.listar_categorias() if cat.tipo == TipoLancamento.DESPESA]
        self.combo_categoria_pagar.addItems(categorias_despesa)
        self.combo_categoria_pagar.currentTextChanged.connect(self.atualizar_contas_pagar)
        self.combo_categoria_pagar.setStyleSheet("QComboBox { background-color: white; color: black; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        filtros_detalhados_layout.addWidget(self.combo_categoria_pagar)
        
        # Filtro por fornecedor
        filtros_detalhados_layout.addWidget(QLabel("Fornecedor:"))
        self.combo_fornecedor_pagar = QComboBox()
        self.combo_fornecedor_pagar.addItem("Todos")
        fornecedores = list(set([d.pessoa for d in [l for l in database.listar_lancamentos() if l.tipo == TipoLancamento.DESPESA] if d.pessoa]))
        self.combo_fornecedor_pagar.addItems(sorted(fornecedores))
        self.combo_fornecedor_pagar.currentTextChanged.connect(self.atualizar_contas_pagar)
        self.combo_fornecedor_pagar.setMinimumWidth(200)
        self.combo_fornecedor_pagar.setStyleSheet("QComboBox { background-color: white; color: black; min-width: 200px; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        filtros_detalhados_layout.addWidget(self.combo_fornecedor_pagar)
        
        # Filtro por mês
        filtros_detalhados_layout.addWidget(QLabel("Mês:"))
        self.combo_mes_pagar = QComboBox()
        self.combo_mes_pagar.addItem("Todos")
        meses = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        for i, mes in enumerate(meses, 1):
            self.combo_mes_pagar.addItem(f"{mes}")
        self.combo_mes_pagar.currentTextChanged.connect(self.atualizar_contas_pagar)
        self.combo_mes_pagar.setStyleSheet("QComboBox { background-color: white; color: black; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        filtros_detalhados_layout.addWidget(self.combo_mes_pagar)
        
        # Filtro por número de documento
        filtros_detalhados_layout.addWidget(QLabel("Nº Documento:"))
        self.search_doc_pagar = UpperCaseLineEdit()
        self.search_doc_pagar.setPlaceholderText("Buscar por número do documento...")
        self.search_doc_pagar.textChanged.connect(self.atualizar_contas_pagar)
        filtros_detalhados_layout.addWidget(self.search_doc_pagar)
        
        # Botão limpar filtros
        btn_limpar_pagar = QPushButton("Limpar Filtros")
        btn_limpar_pagar.clicked.connect(lambda: self.limpar_filtros_pagar())
        filtros_detalhados_layout.addWidget(btn_limpar_pagar)
        
        filtros_detalhados_layout.addStretch()
        
        self.content_layout.addWidget(filtros_detalhados_frame)
        
        # Saldo de Contas Bancárias
        saldo_frame = QFrame()
        saldo_frame.setObjectName("saldoFrame")
        saldo_frame.setStyleSheet("QFrame#saldoFrame { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 10px; }")
        saldo_layout = QHBoxLayout(saldo_frame)
        saldo_layout.setSpacing(15)
        
        # Saldo Total
        saldo_total_label = QLabel("Saldo Total:")
        saldo_total_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        saldo_layout.addWidget(saldo_total_label)
        
        self.label_saldo_total_pagar = QLabel("R$ 0,00")
        self.label_saldo_total_pagar.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.label_saldo_total_pagar.setStyleSheet("color: #28a745;")
        saldo_layout.addWidget(self.label_saldo_total_pagar)
        
        saldo_layout.addSpacing(30)
        
        # Filtro por Banco
        saldo_layout.addWidget(QLabel("Banco:"))
        self.combo_banco_pagar = QComboBox()
        self.combo_banco_pagar.addItem("Todos")
        bancos = list(set([conta.banco for conta in database.listar_contas()]))
        self.combo_banco_pagar.addItems(sorted(bancos))
        self.combo_banco_pagar.currentTextChanged.connect(self.atualizar_saldo_banco_pagar)
        self.combo_banco_pagar.setMinimumWidth(150)
        self.combo_banco_pagar.setStyleSheet("QComboBox { background-color: white; color: black; min-width: 150px; padding: 5px; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        saldo_layout.addWidget(self.combo_banco_pagar)
        
        # Saldo do Banco Selecionado
        self.label_saldo_banco_pagar = QLabel("")
        self.label_saldo_banco_pagar.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.label_saldo_banco_pagar.setStyleSheet("color: #007bff;")
        saldo_layout.addWidget(self.label_saldo_banco_pagar)
        
        saldo_layout.addStretch()
        
        # Botão Nova Despesa na extrema direita
        btn_nova_despesa = QPushButton("+ Nova Despesa")
        btn_nova_despesa.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 100px;
                height: 28px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        btn_nova_despesa.clicked.connect(lambda: self.dialog_novo_lancamento(TipoLancamento.DESPESA))
        saldo_layout.addWidget(btn_nova_despesa)
        
        self.content_layout.addWidget(saldo_frame)
        
        # Atualizar saldos inicialmente
        self.atualizar_saldo_banco_pagar()
        
        # Botões de ação em lote
        acoes_lote_frame = QFrame()
        acoes_lote_layout = QHBoxLayout(acoes_lote_frame)
        acoes_lote_layout.setContentsMargins(0, 10, 0, 10)
        
        btn_selecionar_todos_pagar = QPushButton("☑ Selecionar Todos")
        btn_selecionar_todos_pagar.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #4a90e2, stop:1 #357abd);
                color: white;
                border: 1px solid #2e5f8f;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10pt;
                min-width: 140px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #5ba3ff, stop:1 #4a90e2);
                border: 1px solid #4a90e2;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #357abd, stop:1 #2e5f8f);
                padding-top: 9px;
                padding-bottom: 7px;
            }
        """)
        btn_selecionar_todos_pagar.clicked.connect(self.selecionar_todos_pagar)
        acoes_lote_layout.addWidget(btn_selecionar_todos_pagar)
        
        btn_desselecionar_todos_pagar = QPushButton("☐ Desselecionar Todos")
        btn_desselecionar_todos_pagar.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #95a5a6, stop:1 #7f8c8d);
                color: white;
                border: 1px solid #6c7a7b;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10pt;
                min-width: 140px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #a6b6b7, stop:1 #95a5a6);
                border: 1px solid #7f8c8d;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #7f8c8d, stop:1 #6c7a7b);
                padding-top: 9px;
                padding-bottom: 7px;
            }
        """)
        btn_desselecionar_todos_pagar.clicked.connect(self.desselecionar_todos_pagar)
        acoes_lote_layout.addWidget(btn_desselecionar_todos_pagar)
        
        acoes_lote_layout.addStretch()
        
        btn_liquidar_selecionados_pagar = QPushButton("💰 Liquidar Selecionados")
        btn_liquidar_selecionados_pagar.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        btn_liquidar_selecionados_pagar.clicked.connect(self.liquidar_selecionados_pagar)
        acoes_lote_layout.addWidget(btn_liquidar_selecionados_pagar)
        
        btn_excluir_selecionados_pagar = QPushButton("🗑 Excluir Selecionados")
        btn_excluir_selecionados_pagar.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        btn_excluir_selecionados_pagar.clicked.connect(self.excluir_selecionados_pagar)
        acoes_lote_layout.addWidget(btn_excluir_selecionados_pagar)
        
        self.content_layout.addWidget(acoes_lote_frame)
        
        # Criar tabela de despesas
        self.table_pagar = QTableWidget()
        self.table_pagar.setObjectName("dataTable")
        self.table_pagar.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.table_pagar.setAlternatingRowColors(True)
        font_size = self.scale_size(11)
        self.table_pagar.setStyleSheet(f"""
            QTableWidget {{ 
                background-color: white;
                font-size: {font_size}px;
                alternate-background-color: #d0d0d0;
            }} 
            QHeaderView::section {{ 
                background-color: #f0f0f0;
                font-size: {font_size}px;
            }}
            QCheckBox {{
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: #f0f0f0;
                width: 10px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #2196F3;
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #1976D2;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: #f0f0f0;
            }}
        """)
        
        self.table_pagar.setColumnCount(12)
        self.table_pagar.setHorizontalHeaderLabels([
            "☐", "Fornecedor", "Categoria", "Subcategoria", "Nº Doc", "Descrição", "Valor", "Vencimento", "Competência", "Dt. Liquidação", "Status", "Ações"
        ])
        vheader = self.table_pagar.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        self.table_pagar.setShowGrid(False)
        self.table_pagar.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_pagar.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Configurar e ocultar o cabeçalho vertical (coluna com números)
        row_height = self.scale_size(45)
        header_height = self.scale_size(40)
        v_header = self.table_pagar.verticalHeader()
        if v_header is not None:
            v_header.hide()
            v_header.setDefaultSectionSize(row_height)
        
        # Definir altura mínima para exibir 13 linhas (adaptativo)
        self.table_pagar.setMinimumHeight(row_height * 13 + header_height)
        
        self.table_pagar.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.content_layout.addWidget(self.table_pagar)
        
        # Atualizar tabela com os dados
        self.atualizar_contas_pagar()
        
        self.content_layout.addStretch()
    
    def atualizar_contas_pagar(self):
        """Atualiza a tabela de contas a pagar com todos os filtros"""
        despesas = [l for l in database.listar_lancamentos() if l.tipo == TipoLancamento.DESPESA]
        
        # Filtrar por status
        if hasattr(self, 'combo_status_pagar'):
            status_selecionado = self.combo_status_pagar.currentText()
            if status_selecionado == "Pendentes":
                despesas = [d for d in despesas if d.status == StatusLancamento.PENDENTE]
            elif status_selecionado == "Vencidas":
                despesas = [d for d in despesas if d.status == StatusLancamento.VENCIDO]
            elif status_selecionado == "Pagas":
                despesas = [d for d in despesas if d.status == StatusLancamento.PAGO]
        
        # Filtrar por busca
        try:
            if hasattr(self, 'search_pagar') and self.search_pagar.text():
                termo = self.search_pagar.text().lower()
                despesas = [d for d in despesas if termo in d.descricao.lower() or termo in (d.pessoa or "").lower()]
        except RuntimeError as e:
            # Widget pode ter sido destruído durante atualização
            print(f"Aviso: Erro ao filtrar por pesquisa: {e}")
        
        # Filtrar por categoria
        try:
            if hasattr(self, 'combo_categoria_pagar') and self.combo_categoria_pagar.currentText() != "Todas":
                categoria = self.combo_categoria_pagar.currentText()
                despesas = [d for d in despesas if d.categoria == categoria]
        except RuntimeError as e:
            # Widget pode ter sido destruído durante atualização
            print(f"Aviso: Erro ao filtrar por categoria: {e}")
        
        # Filtrar por fornecedor
        try:
            if hasattr(self, 'combo_fornecedor_pagar') and self.combo_fornecedor_pagar.currentText() != "Todos":
                fornecedor = self.combo_fornecedor_pagar.currentText()
                despesas = [d for d in despesas if d.pessoa == fornecedor]
        except RuntimeError as e:
            # Widget pode ter sido destruído durante atualização
            print(f"Aviso: Erro ao filtrar por fornecedor: {e}")
        
        # Filtrar por mês
        try:
            if hasattr(self, 'combo_mes_pagar') and self.combo_mes_pagar.currentText() != "Todos":
                mes_nome = self.combo_mes_pagar.currentText()
                meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
                mes_num = meses.index(mes_nome) + 1
                despesas = [d for d in despesas if d.data_vencimento.month == mes_num]
        except (RuntimeError, ValueError) as e:
            # Widget destruído ou mês inválido
            print(f"Aviso: Erro ao filtrar por mês: {e}")
        
        # Filtrar por número de documento
        try:
            if hasattr(self, 'search_doc_pagar') and self.search_doc_pagar.text():
                termo_doc = self.search_doc_pagar.text().lower()
                despesas = [d for d in despesas if d.num_documento and termo_doc in d.num_documento.lower()]
        except RuntimeError as e:
            # Widget pode ter sido destruído durante atualização
            print(f"Aviso: Erro ao filtrar por documento: {e}")
        
        # Ordenar sempre por vencimento
        despesas.sort(key=lambda d: d.data_vencimento)
        
        # Usar função de preenchimento ao invés de preencher inline
        self._preencher_tabela_pagar(despesas)
        return
        
        # Configurar tabela (este código não será executado mais)
        self.table_pagar.setColumnCount(11)
        self.table_pagar.setHorizontalHeaderLabels([
            "Fornecedor", "Categoria", "Subcategoria", "Nº Doc", "Descrição", "Valor", "Vencimento", "Competência", "Dt. Liquidação", "Status", "Ações"
        ])
        self.table_pagar.setShowGrid(False)
        self.table_pagar.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_pagar.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table_pagar.setRowCount(len(despesas))
        
        # Configurar altura das linhas
        row_height = self.scale_size(45)
        header_height = self.scale_size(40)
        v_header = self.table_pagar.verticalHeader()
        if v_header:
            v_header.hide()
            v_header.setDefaultSectionSize(row_height)
        
        # Definir altura mínima para exibir 13 linhas (adaptativo)
        self.table_pagar.setMinimumHeight(row_height * 13 + header_height)
        
        for i, desp in enumerate(despesas):
            # Nova ordem: Fornecedor, Categoria, Subcategoria, Nº Doc, Descrição, Valor, Vencimento
            fornecedor_item = QTableWidgetItem(desp.pessoa or "-")
            fornecedor_item.setForeground(QColor("#000000"))
            self.table_pagar.setItem(i, 0, fornecedor_item)
            
            categoria_item = QTableWidgetItem(desp.categoria)
            categoria_item.setForeground(QColor("#000000"))
            self.table_pagar.setItem(i, 1, categoria_item)
            
            subcat_item = QTableWidgetItem("-")
            subcat_item.setForeground(QColor("#000000"))
            self.table_pagar.setItem(i, 2, subcat_item)
            
            doc_item = QTableWidgetItem(desp.num_documento or "-")
            doc_item.setForeground(QColor("#000000"))
            self.table_pagar.setItem(i, 3, doc_item)
            
            desc_item = QTableWidgetItem(desp.descricao)
            desc_item.setForeground(QColor("#000000"))
            self.table_pagar.setItem(i, 4, desc_item)
            
            # Valor formatado e alinhado à direita
            valor_item = QTableWidgetItem(self.formatar_moeda(desp.valor))
            valor_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            valor_item.setForeground(QColor("#000000"))
            font = valor_item.font()
            font.setBold(True)
            valor_item.setFont(font)
            self.table_pagar.setItem(i, 5, valor_item)
            
            venc_item = QTableWidgetItem(desp.data_vencimento.strftime("%d/%m/%Y"))
            venc_item.setForeground(QColor("#000000"))
            self.table_pagar.setItem(i, 6, venc_item)
            
            comp_item = QTableWidgetItem("-")
            comp_item.setForeground(QColor("#000000"))
            self.table_pagar.setItem(i, 7, comp_item)
            
            liq_item = QTableWidgetItem("-")
            liq_item.setForeground(QColor("#000000"))
            self.table_pagar.setItem(i, 8, liq_item)
            
            # Status com cores baseado na data de vencimento
            hoje = datetime.now().date()
            data_venc = desp.data_vencimento.date()
            
            status_item = QTableWidgetItem()
            
            if desp.status == StatusLancamento.PAGO:
                # Pago - fundo verde
                status_item.setText("PAGO")
                status_item.setBackground(QColor("#28a745"))
                status_item.setForeground(QColor("#000000"))
            elif data_venc > hoje:
                # No prazo - fundo marrom
                status_item.setText("NO PRAZO")
                status_item.setBackground(QColor("#8B4513"))
                status_item.setForeground(QColor("#000000"))
            elif data_venc == hoje:
                # Vence hoje - fundo amarelo
                status_item.setText("VENCE HOJE")
                status_item.setBackground(QColor("#ffc107"))
                status_item.setForeground(QColor("#000000"))
            else:
                # Vencido - fundo vermelho
                status_item.setText("VENCIDO")
                status_item.setBackground(QColor("#dc3545"))
                status_item.setForeground(QColor("#000000"))
            
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_pagar.setItem(i, 9, status_item)
            
            # Botões de ação com ícones
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(6)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            actions_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            # Tamanhos adaptativos para botões
            btn_size = self.scale_size(25)
            font_size = self.scale_size(14)
            
            # Botão Liquidar - apenas para contas pendentes ou vencidas
            if desp.status == StatusLancamento.PENDENTE or desp.status == StatusLancamento.VENCIDO:
                btn_liquidar = QPushButton("✓")
                btn_liquidar.setToolTip("Liquidar conta")
                btn_liquidar.setFixedSize(btn_size, btn_size)
                btn_liquidar.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #28a745;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        font-size: {font_size}px;
                    }}
                    QPushButton:hover {{
                        background-color: #218838;
                        border: 1px solid #1e7e34;
                    }}
                    QPushButton:pressed {{
                        background-color: #1e7e34;
                    }}
                """)
                lancamento_id = desp.id
                btn_liquidar.clicked.connect(lambda checked=False, lid=lancamento_id: self.dialog_pagar_lancamento(lid))
                actions_layout.addWidget(btn_liquidar)
            
            # Botão Duplicar
            btn_duplicar = QPushButton("⧉")
            btn_duplicar.setToolTip("Duplicar conta")
            btn_duplicar.setFixedSize(btn_size, btn_size)
            btn_duplicar.setStyleSheet(f"""
                QPushButton {{
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: {font_size}px;
                }}
                QPushButton:hover {{
                    background-color: #5a6268;
                    border: 2px solid #545b62;
                }}
                QPushButton:pressed {{
                    background-color: #545b62;
                }}
            """)
            btn_duplicar.clicked.connect(lambda checked=False, r=desp: self.duplicar_lancamento(r))
            actions_layout.addWidget(btn_duplicar)
            
            # Botão Editar
            btn_editar = QPushButton("✎")
            btn_editar.setToolTip("Editar conta")
            btn_editar.setFixedSize(btn_size, btn_size)
            btn_editar.setStyleSheet(f"""
                QPushButton {{
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: {font_size}px;
                }}
                QPushButton:hover {{
                    background-color: #0056b3;
                    border: 2px solid #004085;
                }}
                QPushButton:pressed {{
                    background-color: #004085;
                }}
            """)
            btn_editar.clicked.connect(lambda checked=False, d=desp: self.dialog_editar_lancamento(d))
            actions_layout.addWidget(btn_editar)
            
            # Botão Excluir
            btn_excluir = QPushButton("✖")
            btn_excluir.setToolTip("Excluir conta")
            btn_excluir.setFixedSize(btn_size, btn_size)
            btn_excluir.setStyleSheet(f"""
                QPushButton {{
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: {font_size}px;
                }}
                QPushButton:hover {{
                    background-color: #c82333;
                    border: 2px solid #bd2130;
                }}
                QPushButton:pressed {{
                    background-color: #bd2130;
                }}
            """)
            lancamento_id = desp.id
            btn_excluir.clicked.connect(lambda checked=False, lid=lancamento_id: self.excluir_lancamento(lid))
            actions_layout.addWidget(btn_excluir)
            
            self.table_pagar.setCellWidget(i, 10, actions_widget)
        
        header = self.table_pagar.horizontalHeader()
        if header:
            # Modo responsivo: colunas se ajustam ao espaço disponível
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            # Colunas com largura automática baseada no conteúdo
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Categoria
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Nº Doc
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Valor
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Vencimento
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Competência
            header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Dt. Liquidação
            header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Status
            header.setSectionResizeMode(10, QHeaderView.ResizeMode.Fixed)  # Ações
            header.resizeSection(10, 190)  # Largura fixa para Ações (ajustada para incluir botão duplicar)
        
        self.table_pagar.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Filtros inferiores
        filtros_inf_frame = QFrame()
        filtros_inf_frame.setObjectName("filterFrame")
        filtros_inf_layout = QVBoxLayout(filtros_inf_frame)
        
        # Primeira linha de filtros
        linha1 = QHBoxLayout()
        
        # Filtros rápidos por data
        linha1.addWidget(QLabel("Filtros Rápidos:"))
        
        btn_vence_hoje = QPushButton("Vence Hoje")
        btn_vence_hoje.setObjectName("successButton")
        btn_vence_hoje.clicked.connect(lambda: self.filtrar_pagar_vence_hoje())
        linha1.addWidget(btn_vence_hoje)
        
        btn_vencidos = QPushButton("Vencidos")
        btn_vencidos.setObjectName("dangerButton")
        btn_vencidos.clicked.connect(lambda: self.filtrar_pagar_vencidos())
        linha1.addWidget(btn_vencidos)
        
        btn_7dias = QPushButton("Próximos 7 Dias")
        btn_7dias.clicked.connect(lambda: self.filtrar_pagar_proximos_7dias())
        linha1.addWidget(btn_7dias)
        
        btn_mes = QPushButton("Este Mês")
        btn_mes.clicked.connect(lambda: self.filtrar_pagar_este_mes())
        linha1.addWidget(btn_mes)
        
        btn_limpar = QPushButton("Limpar Filtros")
        btn_limpar.clicked.connect(lambda: self.limpar_filtros_pagar())
        linha1.addWidget(btn_limpar)
        
        linha1.addStretch()
        filtros_inf_layout.addLayout(linha1)
        
        # Segunda linha de filtros
        linha2 = QHBoxLayout()
        
        # Filtro por categoria
        linha2.addWidget(QLabel("Categoria:"))
        self.combo_categoria_pagar = QComboBox()
        self.combo_categoria_pagar.addItem("Todas")
        categorias_despesa = [cat.nome for cat in database.listar_categorias() if cat.tipo == TipoLancamento.DESPESA]
        self.combo_categoria_pagar.addItems(categorias_despesa)
        self.combo_categoria_pagar.currentTextChanged.connect(self.atualizar_contas_pagar)
        self.combo_categoria_pagar.setStyleSheet("QComboBox { background-color: white; color: black; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        linha2.addWidget(self.combo_categoria_pagar)
        
        # Filtro por fornecedor
        linha2.addWidget(QLabel("Fornecedor:"))
        self.combo_fornecedor_pagar = QComboBox()
        self.combo_fornecedor_pagar.addItem("Todos")
        fornecedores = list(set([d.pessoa for d in [l for l in database.listar_lancamentos() if l.tipo == TipoLancamento.DESPESA] if d.pessoa]))
        self.combo_fornecedor_pagar.addItems(sorted(fornecedores))
        self.combo_fornecedor_pagar.currentTextChanged.connect(self.atualizar_contas_pagar)
        self.combo_fornecedor_pagar.setStyleSheet("QComboBox { background-color: white; color: black; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        linha2.addWidget(self.combo_fornecedor_pagar)
        
        # Filtro por valor
        linha2.addWidget(QLabel("Valor Mín:"))
        self.valor_min_pagar = QDoubleSpinBox()
        self.valor_min_pagar.setPrefix("R$ ")
        self.valor_min_pagar.setMaximum(999999999.99)
        self.valor_min_pagar.setValue(0)
        self.valor_min_pagar.valueChanged.connect(self.atualizar_contas_pagar)
        linha2.addWidget(self.valor_min_pagar)
        
        linha2.addWidget(QLabel("Valor Máx:"))
        self.valor_max_pagar = QDoubleSpinBox()
        self.valor_max_pagar.setPrefix("R$ ")
        self.valor_max_pagar.setMaximum(999999999.99)
        self.valor_max_pagar.setValue(999999999.99)
        self.valor_max_pagar.valueChanged.connect(self.atualizar_contas_pagar)
        linha2.addWidget(self.valor_max_pagar)
        
        linha2.addStretch()
        filtros_inf_layout.addLayout(linha2)
        
        self.content_layout.addWidget(filtros_inf_frame)
    
    def atualizar_contas_receber(self):
        """Atualiza a tabela de contas a receber"""
        receitas = [l for l in database.listar_lancamentos() if l.tipo == TipoLancamento.RECEITA]
        
        # Filtrar por status
        try:
            if hasattr(self, 'combo_status_receber'):
                status_selecionado = self.combo_status_receber.currentText()
                if status_selecionado == "Pendentes":
                    receitas = [r for r in receitas if r.status == StatusLancamento.PENDENTE]
                elif status_selecionado == "Vencidas":
                    receitas = [r for r in receitas if r.status == StatusLancamento.VENCIDO]
                elif status_selecionado == "Pagas":
                    receitas = [r for r in receitas if r.status == StatusLancamento.PAGO]
        except RuntimeError as e:
            # Widget pode ter sido destruído durante atualização
            print(f"Aviso: Erro ao filtrar por status: {e}")
        
        # Filtrar por busca
        try:
            if hasattr(self, 'search_receber') and self.search_receber.text():
                termo = self.search_receber.text().lower()
                receitas = [r for r in receitas if termo in r.descricao.lower() or termo in (r.pessoa or "").lower() or termo in (r.num_documento or "").lower()]
        except RuntimeError as e:
            # Widget pode ter sido destruído durante atualização
            print(f"Aviso: Erro ao filtrar por busca: {e}")
        
        # Filtrar por categoria
        try:
            if hasattr(self, 'combo_categoria_receber'):
                categoria_selecionada = self.combo_categoria_receber.currentText()
                if categoria_selecionada != "Todas":
                    receitas = [r for r in receitas if r.categoria == categoria_selecionada]
        except RuntimeError as e:
            # Widget pode ter sido destruído durante atualização
            print(f"Aviso: Erro ao filtrar por categoria: {e}")
        
        # Filtrar por cliente
        try:
            if hasattr(self, 'combo_cliente_receber'):
                cliente_selecionado = self.combo_cliente_receber.currentText()
                if cliente_selecionado != "Todos":
                    receitas = [r for r in receitas if r.pessoa == cliente_selecionado]
        except RuntimeError as e:
            # Widget pode ter sido destruído durante atualização
            print(f"Aviso: Erro ao filtrar por cliente: {e}")
        
        # Filtrar por número de documento
        try:
            if hasattr(self, 'search_doc_receber') and self.search_doc_receber.text():
                termo_doc = self.search_doc_receber.text().lower()
                receitas = [r for r in receitas if r.num_documento and termo_doc in r.num_documento.lower()]
        except RuntimeError as e:
            # Widget pode ter sido destruído durante atualização
            print(f"Aviso: Erro ao filtrar por documento: {e}")
        
        # Filtrar por mês
        try:
            if hasattr(self, 'combo_mes_receber'):
                mes_selecionado = self.combo_mes_receber.currentText()
                if mes_selecionado != "Todos":
                    meses = [
                        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
                    ]
                    mes_num = meses.index(mes_selecionado) + 1
                    receitas = [r for r in receitas if r.data_vencimento.month == mes_num]
        except (RuntimeError, ValueError) as e:
            # Widget destruído ou mês inválido
            print(f"Aviso: Erro ao filtrar por mês: {e}")
        
        # Ordenar sempre por vencimento
        receitas.sort(key=lambda r: r.data_vencimento)
        
        self._preencher_tabela_receber(receitas)
    
    def aplicar_filtro_rapido_pagar_combo(self, filtro):
        """Aplica filtro rápido através do ComboBox em Contas a Pagar"""
        if filtro == "Todas":
            self.combo_status_pagar.setCurrentText("Todos")
        elif filtro == "Pendentes":
            self.combo_status_pagar.setCurrentText("Pendentes")
        elif filtro == "Vencidas":
            self.combo_status_pagar.setCurrentText("Vencidas")
        elif filtro == "Pagas":
            self.combo_status_pagar.setCurrentText("Pagas")
        elif filtro == "Vence Hoje":
            self.filtrar_vence_hoje_pagar()
            return
        elif filtro == "Próximos 7 dias":
            self.filtrar_proximos_dias_pagar(7)
            return
        elif filtro == "Próximos 30 dias":
            self.filtrar_proximos_dias_pagar(30)
            return
        
        self.atualizar_contas_pagar()
    
    def filtrar_vence_hoje_pagar(self):
        """Filtra apenas contas que vencem hoje em Contas a Pagar"""
        despesas = [l for l in database.listar_lancamentos() if l.tipo == TipoLancamento.DESPESA]
        hoje = datetime.now().date()
        
        # Filtrar apenas as que vencem hoje e não estão pagas
        despesas = [d for d in despesas 
                   if d.data_vencimento.date() == hoje 
                   and d.status != StatusLancamento.PAGO]
        
        self._preencher_tabela_pagar(despesas)
    
    def filtrar_proximos_dias_pagar(self, dias):
        """Filtra contas que vencem nos próximos N dias em Contas a Pagar"""
        despesas = [l for l in database.listar_lancamentos() if l.tipo == TipoLancamento.DESPESA]
        hoje = datetime.now().date()
        data_limite = hoje + timedelta(days=dias)
        
        # Filtrar apenas as pendentes que vencem nos próximos N dias
        despesas = [d for d in despesas 
                   if d.status != StatusLancamento.PAGO
                   and hoje <= d.data_vencimento.date() <= data_limite]
        
        self._preencher_tabela_pagar(despesas)
    
    def atualizar_saldo_banco_pagar(self):
        """Atualiza o saldo exibido conforme banco selecionado em Contas a Pagar"""
        # Calcular saldo total
        saldo_total = sum([c.saldo_inicial for c in database.listar_contas()])
        self.label_saldo_total_pagar.setText(self.formatar_moeda(saldo_total))
        
        # Filtrar por banco se selecionado
        banco_selecionado = self.combo_banco_pagar.currentText()
        if banco_selecionado == "Todos":
            self.label_saldo_banco_pagar.setText("")
        else:
            contas_banco = [c for c in database.listar_contas() if c.banco == banco_selecionado]
            saldo_banco = sum(c.saldo_atual for c in contas_banco)
            self.label_saldo_banco_pagar.setText(f"Saldo {banco_selecionado}: {self.formatar_moeda(saldo_banco)}")
    
    def dialog_selecionar_fornecedor(self):
        """Abre diálogo para selecionar fornecedor cadastrado"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Selecionar Fornecedor")
        dialog.resize(1400, 700)
        dialog.setStyleSheet("""
            QDialog { background-color: white; }
            QTableWidget {
                background-color: #2d2d2d;
                color: white;
                gridline-color: #404040;
                selection-background-color: #0d47a1;
                selection-color: white;
            }
            QHeaderView::section {
                background-color: #1e1e1e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title = QLabel("Selecione um Fornecedor")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)
        
        # Campo de busca
        search_box = QLineEdit()
        search_box.setPlaceholderText("Buscar fornecedor...")
        search_box.setStyleSheet("QLineEdit { background-color: white; color: black; padding: 8px; border: 1px solid #ccc; border-radius: 4px; }")
        layout.addWidget(search_box)
        
        # Tabela
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Nome", "CNPJ", "Contato", "Email"])
        h_header = table.horizontalHeader()
        if h_header is not None:
            h_header.setStretchLastSection(True)
        v_header = table.verticalHeader()
        if v_header is not None:
            v_header.setVisible(True)
            v_header.setDefaultSectionSize(40)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #d0d0d0;
                background-color: #ffffff;
            }
        """)
        
        # Preencher com fornecedores únicos
        fornecedores = set()
        
        # Adicionar fornecedores dos lançamentos
        for lancamento in [l for l in database.listar_lancamentos() if l.tipo == TipoLancamento.DESPESA]:
            if lancamento.pessoa:
                fornecedores.add(lancamento.pessoa)
        
        # Converter para lista e ordenar
        fornecedores = sorted(list(fornecedores))
        
        table.setRowCount(len(fornecedores))
        for i, fornecedor in enumerate(fornecedores):
            table.setItem(i, 0, QTableWidgetItem(fornecedor))
            table.setItem(i, 1, QTableWidgetItem("-"))
            table.setItem(i, 2, QTableWidgetItem("-"))
            table.setItem(i, 3, QTableWidgetItem("-"))
        
        # Função de filtro
        def filtrar_table():
            termo = search_box.text().lower()
            for row in range(table.rowCount()):
                item = table.item(row, 0)
                if item:
                    match = termo in item.text().lower()
                    table.setRowHidden(row, not match)
        
        search_box.textChanged.connect(filtrar_table)
        
        layout.addWidget(table)
        
        # Botões
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        btn_selecionar = QPushButton("Selecionar")
        btn_selecionar.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
                min-width: 100px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        btn_selecionar.clicked.connect(lambda: self.selecionar_fornecedor_da_tabela(table, dialog))
        buttons_layout.addWidget(btn_selecionar)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #424242;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
                min-width: 100px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        btn_cancelar.clicked.connect(dialog.reject)
        buttons_layout.addWidget(btn_cancelar)
        
        layout.addLayout(buttons_layout)
        
        # Duplo clique para selecionar
        table.doubleClicked.connect(lambda: self.selecionar_fornecedor_da_tabela(table, dialog))
        
        dialog.exec()
    
    def selecionar_fornecedor_da_tabela(self, table, dialog):
        """Seleciona fornecedor da tabela e preenche o campo de busca"""
        current_row = table.currentRow()
        if current_row >= 0:
            nome_fornecedor = table.item(current_row, 0).text()
            if hasattr(self, 'search_pagar'):
                self.search_pagar.setText(nome_fornecedor)
            dialog.accept()
    
    def exportar_pagar_pdf(self):
        """Exporta tabela de contas a pagar para PDF"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            
            # Coletar dados da tabela
            dados = []
            
            # Cabeçalho
            headers = []
            for col in range(self.table_pagar.columnCount() - 1):  # Excluir coluna Ações
                header_item = self.table_pagar.horizontalHeaderItem(col)
                headers.append(header_item.text() if header_item else f"Col {col}")
            dados.append(headers)
            
            # Dados
            for row in range(self.table_pagar.rowCount()):
                linha = []
                for col in range(self.table_pagar.columnCount() - 1):  # Excluir coluna Ações
                    item = self.table_pagar.item(row, col)
                    linha.append(item.text() if item else "")
                dados.append(linha)
            
            if len(dados) <= 1:  # Apenas cabeçalho
                QMessageBox.information(self, "Exportar", "Não há dados para exportar.")
                return
            
            # Diálogo para escolher onde salvar
            nome_arquivo = f"contas_pagar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            caminho_completo, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Arquivo PDF",
                os.path.join(os.path.expanduser("~"), "Downloads", nome_arquivo),
                "Arquivos PDF (*.pdf)"
            )
            
            if not caminho_completo:
                return
            
            doc = SimpleDocTemplate(caminho_completo, pagesize=landscape(A4))
            elementos = []
            
            # Título
            styles = getSampleStyleSheet()
            titulo_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=30,
                alignment=1  # Centralizado
            )
            titulo = Paragraph("Contas a Pagar", titulo_style)
            elementos.append(titulo)
            elementos.append(Spacer(1, 0.5*cm))
            
            # Criar tabela
            tabela = Table(dados)
            
            # Estilo da tabela
            estilo = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2c3e50'))
            ])
            tabela.setStyle(estilo)
            
            elementos.append(tabela)
            
            # Construir PDF
            doc.build(elementos)
            
            QMessageBox.information(
                self,
                "Exportação Concluída",
                f"Arquivo PDF exportado com sucesso!\n\nLocal: {caminho_completo}"
            )
            
        except ImportError:
            QMessageBox.warning(
                self,
                "Biblioteca Não Encontrada",
                "Para exportar para PDF, instale a biblioteca:\npip install reportlab"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {str(e)}")
    
    def exportar_pagar_excel(self):
        """Exporta tabela de contas a pagar para Excel"""
        try:
            import pandas as pd
            
            # Coletar dados da tabela
            dados = []
            for row in range(self.table_pagar.rowCount()):
                linha = {}
                for col in range(self.table_pagar.columnCount() - 1):  # Excluir coluna Ações
                    header_item = self.table_pagar.horizontalHeaderItem(col)
                    header = header_item.text() if header_item else f"Coluna {col}"
                    item = self.table_pagar.item(row, col)
                    linha[header] = item.text() if item else ""
                dados.append(linha)
            
            if not dados:
                QMessageBox.information(self, "Exportar", "Não há dados para exportar.")
                return
            
            # Criar DataFrame
            df = pd.DataFrame(dados)
            
            # Diálogo para escolher onde salvar
            nome_arquivo = f"contas_pagar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            caminho_completo, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Arquivo Excel",
                os.path.join(os.path.expanduser("~"), "Downloads", nome_arquivo),
                "Arquivos Excel (*.xlsx)"
            )
            
            if not caminho_completo:
                return
            
            df.to_excel(caminho_completo, index=False, engine='openpyxl')
            
            QMessageBox.information(
                self,
                "Exportação Concluída",
                f"Arquivo exportado com sucesso!\n\nLocal: {caminho_completo}"
            )
            
        except ImportError:
            QMessageBox.warning(
                self,
                "Biblioteca Não Encontrada",
                "Para exportar para Excel, instale as bibliotecas:\npip install pandas openpyxl"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar: {str(e)}")
    
    def _preencher_tabela_pagar(self, despesas):
        """Preenche a tabela com a lista de despesas fornecida"""
        hoje = datetime.now().date()
        
        # Limpar tabela
        self.table_pagar.setRowCount(0)
        self.table_pagar.setRowCount(len(despesas))
        
        for i, desp in enumerate(despesas):
            # Checkbox na primeira coluna
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            checkbox = CustomCheckBox()
            checkbox.setStyleSheet("""
                QCheckBox::indicator {
                    border: 2px solid #000000;
                    width: 20px;
                    height: 20px;
                    border-radius: 4px;
                    background-color: white;
                }
                QCheckBox::indicator:hover {
                    background-color: #f0f0f0;
                    border-color: #000000;
                }
                QCheckBox::indicator:checked {
                    background-color: white;
                    border-color: #000000;
                }
                QCheckBox::indicator:checked:hover {
                    background-color: #f0f0f0;
                    border-color: #000000;
                }
            """)
            checkbox.setProperty("lancamento_id", desp.id)
            checkbox.setFixedSize(22, 22)
            checkbox_layout.addWidget(checkbox)
            
            self.table_pagar.setCellWidget(i, 0, checkbox_widget)
            
            # Colunas: Checkbox, Fornecedor, Categoria, Subcategoria, Nº Doc, Descrição, Valor, Vencimento, Competência, Dt. Liquidação, Status, Ações
            fornecedor_item = QTableWidgetItem(desp.pessoa or "-")
            fornecedor_item.setForeground(QColor("#000000"))
            self.table_pagar.setItem(i, 1, fornecedor_item)
            
            categoria_item = QTableWidgetItem(desp.categoria)
            categoria_item.setForeground(QColor("#000000"))
            self.table_pagar.setItem(i, 2, categoria_item)
            
            subcat_item = QTableWidgetItem(desp.subcategoria if desp.subcategoria else "-")
            subcat_item.setForeground(QColor("#000000"))
            self.table_pagar.setItem(i, 3, subcat_item)
            
            doc_item = QTableWidgetItem(desp.num_documento or "-")
            doc_item.setForeground(QColor("#000000"))
            self.table_pagar.setItem(i, 4, doc_item)
            
            desc_item = QTableWidgetItem(desp.descricao)
            desc_item.setForeground(QColor("#000000"))
            self.table_pagar.setItem(i, 5, desc_item)
            
            # Valor formatado
            valor_item = QTableWidgetItem(self.formatar_moeda(desp.valor))
            valor_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            valor_item.setForeground(QColor("#000000"))
            font = valor_item.font()
            font.setBold(True)
            valor_item.setFont(font)
            self.table_pagar.setItem(i, 6, valor_item)
            
            venc_item = QTableWidgetItem(desp.data_vencimento.strftime("%d/%m/%Y"))
            venc_item.setForeground(QColor("#000000"))
            self.table_pagar.setItem(i, 7, venc_item)
            
            comp_item = QTableWidgetItem("-")
            comp_item.setForeground(QColor("#000000"))
            self.table_pagar.setItem(i, 8, comp_item)
            
            liq_item = QTableWidgetItem("-")
            liq_item.setForeground(QColor("#000000"))
            self.table_pagar.setItem(i, 9, liq_item)
            
            # Status com cores baseado na data de vencimento
            hoje = datetime.now().date()
            data_venc = desp.data_vencimento.date()
            
            status_item = QTableWidgetItem()
            
            if desp.status == StatusLancamento.PAGO:
                # Pago - fundo verde
                status_item.setText("PAGO")
                status_item.setBackground(QColor("#28a745"))
                status_item.setForeground(QColor("#000000"))
            elif data_venc > hoje:
                # No prazo - fundo marrom
                status_item.setText("NO PRAZO")
                status_item.setBackground(QColor("#8B4513"))
                status_item.setForeground(QColor("#000000"))
            elif data_venc == hoje:
                # Vence hoje - fundo amarelo
                status_item.setText("VENCE HOJE")
                status_item.setBackground(QColor("#ffc107"))
                status_item.setForeground(QColor("#000000"))
            else:
                # Vencido - fundo vermelho
                status_item.setText("VENCIDO")
                status_item.setBackground(QColor("#dc3545"))
                status_item.setForeground(QColor("#000000"))
            
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_pagar.setItem(i, 10, status_item)
            
            # Ações com ícones (ajustado para ícones totalmente visíveis)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(6)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            actions_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            # Tamanhos adaptativos para botões
            btn_size = self.scale_size(25)
            font_size = self.scale_size(14)
            
            # Botão Liquidar - apenas para contas pendentes ou vencidas
            if desp.status == StatusLancamento.PENDENTE or desp.status == StatusLancamento.VENCIDO:
                btn_liquidar = QPushButton("✓")
                btn_liquidar.setToolTip("Liquidar conta")
                btn_liquidar.setFixedSize(btn_size, btn_size)
                btn_liquidar.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #28a745;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        font-size: {font_size}px;
                    }}
                    QPushButton:hover {{
                        background-color: #218838;
                        border: 1px solid #1e7e34;
                    }}
                    QPushButton:pressed {{
                        background-color: #1e7e34;
                    }}
                """)
                lancamento_id = desp.id
                btn_liquidar.clicked.connect(lambda checked=False, lid=lancamento_id: self.dialog_pagar_lancamento(lid))
                actions_layout.addWidget(btn_liquidar)
            
            # Botão Duplicar
            btn_duplicar = QPushButton("⧉")
            btn_duplicar.setToolTip("Duplicar conta")
            btn_duplicar.setFixedSize(btn_size, btn_size)
            btn_duplicar.setStyleSheet(f"""
                QPushButton {{
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: {font_size}px;
                }}
                QPushButton:hover {{
                    background-color: #5a6268;
                    border: 2px solid #545b62;
                }}
                QPushButton:pressed {{
                    background-color: #545b62;
                }}
            """)
            btn_duplicar.clicked.connect(lambda checked=False, r=desp: self.duplicar_lancamento(r))
            actions_layout.addWidget(btn_duplicar)
            
            # Botão Editar
            btn_editar = QPushButton("✎")
            btn_editar.setToolTip("Editar conta")
            btn_editar.setFixedSize(btn_size, btn_size)
            btn_editar.setStyleSheet(f"""
                QPushButton {{
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: {font_size}px;
                }}
                QPushButton:hover {{
                    background-color: #0056b3;
                    border: 2px solid #004085;
                }}
                QPushButton:pressed {{
                    background-color: #004085;
                }}
            """)
            btn_editar.clicked.connect(lambda checked=False, d=desp: self.dialog_editar_lancamento(d))
            actions_layout.addWidget(btn_editar)
            
            # Botão Excluir
            btn_excluir = QPushButton("✖")
            btn_excluir.setToolTip("Excluir conta")
            btn_excluir.setFixedSize(btn_size, btn_size)
            btn_excluir.setStyleSheet(f"""
                QPushButton {{
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: {font_size}px;
                }}
                QPushButton:hover {{
                    background-color: #c82333;
                    border: 2px solid #bd2130;
                }}
                QPushButton:pressed {{
                    background-color: #bd2130;
                }}
            """)
            lancamento_id = desp.id
            btn_excluir.clicked.connect(lambda checked=False, lid=lancamento_id: self.excluir_lancamento(lid))
            actions_layout.addWidget(btn_excluir)
            
            self.table_pagar.setCellWidget(i, 11, actions_widget)
        
        header = self.table_pagar.horizontalHeader()
        if header:
            # Modo responsivo: colunas se ajustam ao espaço disponível
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            # Checkbox - largura fixa
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(0, 40)
            # Colunas com largura automática baseada no conteúdo
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Categoria
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Nº Doc
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Valor
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Vencimento
            header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Competência
            header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Dt. Liquidação
            header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)  # Status
            header.setSectionResizeMode(11, QHeaderView.ResizeMode.Fixed)  # Ações
            header.resizeSection(11, 190)  # Largura fixa para Ações (ajustada para incluir botão duplicar)
    
    def selecionar_todos_pagar(self):
        """Seleciona todos os checkboxes da tabela de contas a pagar"""
        for row in range(self.table_pagar.rowCount()):
            widget = self.table_pagar.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(True)
    
    def desselecionar_todos_pagar(self):
        """Desseleciona todos os checkboxes da tabela de contas a pagar"""
        for row in range(self.table_pagar.rowCount()):
            widget = self.table_pagar.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)
    
    def liquidar_selecionados_pagar(self):
        """Liquid

a os lançamentos selecionados"""
        ids_selecionados = []
        for row in range(self.table_pagar.rowCount()):
            widget = self.table_pagar.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    lancamento_id = checkbox.property("lancamento_id")
                    if lancamento_id:
                        ids_selecionados.append(lancamento_id)
        
        if not ids_selecionados:
            QMessageBox.warning(self, "Aviso", "Nenhum lançamento selecionado!")
            return
        
        # Perguntar confirmação
        reply = QMessageBox.question(
            self, "Confirmar Liquidação",
            f"Deseja liquidar {len(ids_selecionados)} lançamento(s) selecionado(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Liquidar cada lançamento
            for lancamento_id in ids_selecionados:
                self.dialog_pagar_lancamento(lancamento_id)
            
            self.atualizar_contas_pagar()
    
    def excluir_selecionados_pagar(self):
        """Exclui os lançamentos selecionados"""
        ids_selecionados = []
        for row in range(self.table_pagar.rowCount()):
            widget = self.table_pagar.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    lancamento_id = checkbox.property("lancamento_id")
                    if lancamento_id:
                        ids_selecionados.append(lancamento_id)
        
        if not ids_selecionados:
            QMessageBox.warning(self, "Aviso", "Nenhum lançamento selecionado!")
            return
        
        # Perguntar confirmação
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja realmente excluir {len(ids_selecionados)} lançamento(s) selecionado(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Excluir cada lançamento
            for lancamento_id in ids_selecionados:
                self.excluir_lancamento(lancamento_id)
            
            self.atualizar_contas_pagar()
    
    def selecionar_todos_receber(self):
        """Marca todos os checkboxes da tabela de receber"""
        for row in range(self.table_receber.rowCount()):
            widget = self.table_receber.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(True)
    
    def desselecionar_todos_receber(self):
        """Desmarca todos os checkboxes da tabela de receber"""
        for row in range(self.table_receber.rowCount()):
            widget = self.table_receber.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)
    
    def liquidar_selecionados_receber(self):
        """Liquida os lançamentos selecionados"""
        ids_selecionados = []
        for row in range(self.table_receber.rowCount()):
            widget = self.table_receber.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    lancamento_id = checkbox.property("lancamento_id")
                    if lancamento_id:
                        ids_selecionados.append(lancamento_id)
        
        if not ids_selecionados:
            QMessageBox.warning(self, "Aviso", "Nenhum lançamento selecionado!")
            return
        
        # Perguntar confirmação
        reply = QMessageBox.question(
            self, "Confirmar Liquidação",
            f"Deseja realmente liquidar {len(ids_selecionados)} lançamento(s) selecionado(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Liquidar cada lançamento
            for lancamento_id in ids_selecionados:
                self.dialog_pagar_lancamento(lancamento_id)
            
            self.atualizar_contas_receber()
    
    def excluir_selecionados_receber(self):
        """Exclui os lançamentos selecionados"""
        ids_selecionados = []
        for row in range(self.table_receber.rowCount()):
            widget = self.table_receber.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    lancamento_id = checkbox.property("lancamento_id")
                    if lancamento_id:
                        ids_selecionados.append(lancamento_id)
        
        if not ids_selecionados:
            QMessageBox.warning(self, "Aviso", "Nenhum lançamento selecionado!")
            return
        
        # Perguntar confirmação
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja realmente excluir {len(ids_selecionados)} lançamento(s) selecionado(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Excluir cada lançamento
            for lancamento_id in ids_selecionados:
                self.excluir_lancamento(lancamento_id)
            
            self.atualizar_contas_receber()
    
    def _preencher_tabela_receber(self, receitas):
        """Preenche a tabela com a lista de receitas fornecida"""
        hoje = datetime.now().date()
        
        # Limpar tabela
        self.table_receber.setRowCount(0)
        self.table_receber.setRowCount(len(receitas))
        
        for i, rec in enumerate(receitas):
            # Adicionar checkbox na primeira coluna
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox = CustomCheckBox()
            checkbox.setStyleSheet("""
                QCheckBox::indicator {
                    border: 2px solid #000000;
                    width: 20px;
                    height: 20px;
                    border-radius: 4px;
                    background-color: white;
                }
                QCheckBox::indicator:hover {
                    background-color: #f0f0f0;
                    border-color: #000000;
                }
                QCheckBox::indicator:checked {
                    background-color: white;
                    border-color: #000000;
                }
                QCheckBox::indicator:checked:hover {
                    background-color: #f0f0f0;
                    border-color: #000000;
                }
            """)
            checkbox.setProperty("lancamento_id", rec.id)
            checkbox.setFixedSize(22, 22)
            checkbox_layout.addWidget(checkbox)
            self.table_receber.setCellWidget(i, 0, checkbox_widget)
            
            # Nova ordem: Cliente, Categoria, Nº Doc, Descrição, Valor, Vencimento, Dias, Competência, Dt. Liquidação, Status, Urgência
            cliente_item = QTableWidgetItem(rec.pessoa or "-")
            cliente_item.setForeground(QColor("#000000"))
            self.table_receber.setItem(i, 1, cliente_item)
            
            categoria_item = QTableWidgetItem(rec.categoria)
            categoria_item.setForeground(QColor("#000000"))
            self.table_receber.setItem(i, 2, categoria_item)
            
            subcat_item = QTableWidgetItem(rec.subcategoria if rec.subcategoria else "-")
            subcat_item.setForeground(QColor("#000000"))
            self.table_receber.setItem(i, 3, subcat_item)
            
            doc_item = QTableWidgetItem(rec.num_documento or "-")
            doc_item.setForeground(QColor("#000000"))
            self.table_receber.setItem(i, 4, doc_item)
            
            desc_item = QTableWidgetItem(rec.descricao)
            desc_item.setForeground(QColor("#000000"))
            self.table_receber.setItem(i, 5, desc_item)
            
            # Valor formatado
            valor_item = QTableWidgetItem(self.formatar_moeda(rec.valor))
            valor_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            valor_item.setForeground(QColor("#000000"))
            font = valor_item.font()
            font.setBold(True)
            valor_item.setFont(font)
            self.table_receber.setItem(i, 6, valor_item)
            
            venc_item = QTableWidgetItem(rec.data_vencimento.strftime("%d/%m/%Y"))
            venc_item.setForeground(QColor("#000000"))
            self.table_receber.setItem(i, 7, venc_item)
            
            comp_item = QTableWidgetItem("-")
            comp_item.setForeground(QColor("#000000"))
            self.table_receber.setItem(i, 8, comp_item)
            
            liq_item = QTableWidgetItem("-")
            liq_item.setForeground(QColor("#000000"))
            self.table_receber.setItem(i, 9, liq_item)
            
            # Status com cores baseado na data de vencimento
            hoje = datetime.now().date()
            data_venc = rec.data_vencimento.date()
            
            status_item = QTableWidgetItem()
            
            if rec.status == StatusLancamento.PAGO:
                # Pago - fundo verde
                status_item.setText("PAGO")
                status_item.setBackground(QColor("#28a745"))
                status_item.setForeground(QColor("#000000"))
            elif data_venc > hoje:
                # No prazo - fundo marrom
                status_item.setText("NO PRAZO")
                status_item.setBackground(QColor("#8B4513"))
                status_item.setForeground(QColor("#000000"))
            elif data_venc == hoje:
                # Vence hoje - fundo amarelo
                status_item.setText("VENCE HOJE")
                status_item.setBackground(QColor("#ffc107"))
                status_item.setForeground(QColor("#000000"))
            else:
                # Vencido - fundo vermelho
                status_item.setText("VENCIDO")
                status_item.setBackground(QColor("#dc3545"))
                status_item.setForeground(QColor("#000000"))
            
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_receber.setItem(i, 10, status_item)
            
            # Ações com ícones (ajustado para ícones totalmente visíveis)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(6)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            actions_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            # Tamanhos adaptativos para botões
            btn_size = self.scale_size(25)
            font_size = self.scale_size(14)
            
            # Botão Liquidar - apenas para contas pendentes ou vencidas
            if rec.status == StatusLancamento.PENDENTE or rec.status == StatusLancamento.VENCIDO:
                btn_liquidar = QPushButton("✓")
                btn_liquidar.setToolTip("Liquidar conta")
                btn_liquidar.setFixedSize(btn_size, btn_size)
                btn_liquidar.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #28a745;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        font-size: {font_size}px;
                    }}
                    QPushButton:hover {{
                        background-color: #218838;
                        border: 1px solid #1e7e34;
                    }}
                    QPushButton:pressed {{
                        background-color: #1e7e34;
                    }}
                """)
                lancamento_id = rec.id
                btn_liquidar.clicked.connect(lambda checked=False, lid=lancamento_id: self.dialog_pagar_lancamento(lid))
                actions_layout.addWidget(btn_liquidar)
            
            # Botão Duplicar
            btn_duplicar = QPushButton("⧉")
            btn_duplicar.setToolTip("Duplicar conta")
            btn_duplicar.setFixedSize(btn_size, btn_size)
            btn_duplicar.setStyleSheet(f"""
                QPushButton {{
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: {font_size}px;
                }}
                QPushButton:hover {{
                    background-color: #5a6268;
                    border: 2px solid #545b62;
                }}
                QPushButton:pressed {{
                    background-color: #545b62;
                }}
            """)
            btn_duplicar.clicked.connect(lambda checked=False, r=rec: self.duplicar_lancamento(r))
            actions_layout.addWidget(btn_duplicar)
            
            # Botão Editar
            btn_editar = QPushButton("✎")
            btn_editar.setToolTip("Editar conta")
            btn_editar.setFixedSize(btn_size, btn_size)
            btn_editar.setStyleSheet(f"""
                QPushButton {{
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: {font_size}px;
                }}
                QPushButton:hover {{
                    background-color: #0056b3;
                    border: 2px solid #004085;
                }}
                QPushButton:pressed {{
                    background-color: #004085;
                }}
            """)
            btn_editar.clicked.connect(lambda checked=False, r=rec: self.dialog_editar_lancamento(r))
            actions_layout.addWidget(btn_editar)
            
            # Botão Excluir
            btn_excluir = QPushButton("✖")
            btn_excluir.setToolTip("Excluir conta")
            btn_excluir.setFixedSize(btn_size, btn_size)
            btn_excluir.setStyleSheet(f"""
                QPushButton {{
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: {font_size}px;
                }}
                QPushButton:hover {{
                    background-color: #c82333;
                    border: 2px solid #bd2130;
                }}
                QPushButton:pressed {{
                    background-color: #bd2130;
                }}
            """)
            lancamento_id = rec.id
            btn_excluir.clicked.connect(lambda checked=False, lid=lancamento_id: self.excluir_lancamento(lid))
            actions_layout.addWidget(btn_excluir)
            
            self.table_receber.setCellWidget(i, 11, actions_widget)
        
        header = self.table_receber.horizontalHeader()
        if header:
            # Modo responsivo: colunas se ajustam ao espaço disponível
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            # Coluna checkbox com largura fixa
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(0, 40)
            # Colunas com largura automática baseada no conteúdo
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Categoria
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Nº Doc
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Valor
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Vencimento
            header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Competência
            header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Dt. Liquidação
            header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)  # Status
            header.setSectionResizeMode(11, QHeaderView.ResizeMode.Fixed)  # Ações
            header.resizeSection(11, 190)  # Largura fixa para Ações (ajustada para incluir botão duplicar)
    
    def criar_kpi_card(self, titulo, valor_principal, valor_secundario, cor):
        """Cria um card de KPI estilizado"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-left: 4px solid {cor};
                border-radius: 6px;
                padding: 15px;
                min-width: 180px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(5)
        
        # Título
        label_titulo = QLabel(titulo)
        label_titulo.setFont(QFont("Segoe UI", 9))
        label_titulo.setStyleSheet("color: #6c757d;")
        layout.addWidget(label_titulo)
        
        # Valor principal
        label_valor = QLabel(valor_principal)
        label_valor.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        label_valor.setStyleSheet(f"color: {cor};")
        layout.addWidget(label_valor)
        
        # Valor secundário
        label_secundario = QLabel(valor_secundario)
        label_secundario.setFont(QFont("Segoe UI", 8))
        label_secundario.setStyleSheet("color: #adb5bd;")
        layout.addWidget(label_secundario)
        
        return card
    
    def aplicar_filtro_rapido_receber_combo(self, filtro):
        """Aplica filtro rápido através do ComboBox"""
        if filtro == "Todas":
            self.combo_status_receber.setCurrentText("Todos")
        elif filtro == "Pendentes":
            self.combo_status_receber.setCurrentText("Pendentes")
        elif filtro == "Vencidas":
            self.combo_status_receber.setCurrentText("Vencidas")
        elif filtro == "Pagas":
            self.combo_status_receber.setCurrentText("Pagas")
        elif filtro == "Vence Hoje":
            self.filtrar_vence_hoje_receber()
            return
        elif filtro == "Próximos 7 dias":
            self.filtrar_proximos_dias_receber(7)
            return
        elif filtro == "Próximos 30 dias":
            self.filtrar_proximos_dias_receber(30)
            return
        
        self.atualizar_contas_receber()
    
    def filtrar_proximos_dias_receber(self, dias):
        """Filtra contas que vencem nos próximos N dias"""
        receitas = [l for l in database.listar_lancamentos() if l.tipo == TipoLancamento.RECEITA]
        hoje = datetime.now().date()
        data_limite = hoje + timedelta(days=dias)
        
        # Filtrar apenas as pendentes que vencem nos próximos N dias
        receitas = [r for r in receitas 
                   if r.status != StatusLancamento.PAGO
                   and hoje <= r.data_vencimento.date() <= data_limite]
        
        self._preencher_tabela_receber(receitas)
    
    def exportar_receber_excel(self):
        """Exporta tabela de contas a receber para Excel"""
        try:
            import pandas as pd
            
            # Coletar dados da tabela
            dados = []
            for row in range(self.table_receber.rowCount()):
                linha = {}
                for col in range(self.table_receber.columnCount() - 1):  # Excluir coluna Ações
                    header_item = self.table_receber.horizontalHeaderItem(col)
                    header = header_item.text() if header_item else f"Coluna {col}"
                    item = self.table_receber.item(row, col)
                    linha[header] = item.text() if item else ""
                dados.append(linha)
            
            if not dados:
                QMessageBox.information(self, "Exportar", "Não há dados para exportar.")
                return
            
            # Criar DataFrame
            df = pd.DataFrame(dados)
            
            # Diálogo para escolher onde salvar
            nome_arquivo = f"contas_receber_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            caminho_completo, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Arquivo Excel",
                os.path.join(os.path.expanduser("~"), "Downloads", nome_arquivo),
                "Arquivos Excel (*.xlsx)"
            )
            
            if not caminho_completo:
                return
            
            df.to_excel(caminho_completo, index=False, engine='openpyxl')
            
            QMessageBox.information(
                self,
                "Exportação Concluída",
                f"Arquivo exportado com sucesso!\n\nLocal: {caminho_completo}"
            )
            
        except ImportError:
            QMessageBox.warning(
                self,
                "Biblioteca Não Encontrada",
                "Para exportar para Excel, instale as bibliotecas:\npip install pandas openpyxl"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar: {str(e)}")
    
    def exportar_receber_pdf(self):
        """Exporta tabela de contas a receber para PDF"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            
            # Coletar dados da tabela
            dados = []
            
            # Cabeçalho
            headers = []
            for col in range(self.table_receber.columnCount() - 1):  # Excluir coluna Ações
                header_item = self.table_receber.horizontalHeaderItem(col)
                headers.append(header_item.text() if header_item else f"Col {col}")
            dados.append(headers)
            
            # Dados
            for row in range(self.table_receber.rowCount()):
                linha = []
                for col in range(self.table_receber.columnCount() - 1):  # Excluir coluna Ações
                    item = self.table_receber.item(row, col)
                    linha.append(item.text() if item else "")
                dados.append(linha)
            
            if len(dados) <= 1:  # Apenas cabeçalho
                QMessageBox.information(self, "Exportar", "Não há dados para exportar.")
                return
            
            # Diálogo para escolher onde salvar
            nome_arquivo = f"contas_receber_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            caminho_completo, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Arquivo PDF",
                os.path.join(os.path.expanduser("~"), "Downloads", nome_arquivo),
                "Arquivos PDF (*.pdf)"
            )
            
            if not caminho_completo:
                return
            
            doc = SimpleDocTemplate(caminho_completo, pagesize=landscape(A4))
            elementos = []
            
            # Título
            styles = getSampleStyleSheet()
            titulo_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=30,
                alignment=1  # Centralizado
            )
            titulo = Paragraph("Contas a Receber", titulo_style)
            elementos.append(titulo)
            elementos.append(Spacer(1, 0.5*cm))
            
            # Criar tabela
            tabela = Table(dados)
            
            # Estilo da tabela
            estilo = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2c3e50'))
            ])
            tabela.setStyle(estilo)
            
            elementos.append(tabela)
            
            # Construir PDF
            doc.build(elementos)
            
            QMessageBox.information(
                self,
                "Exportação Concluída",
                f"Arquivo PDF exportado com sucesso!\n\nLocal: {caminho_completo}"
            )
            
        except ImportError:
            QMessageBox.warning(
                self,
                "Biblioteca Não Encontrada",
                "Para exportar para PDF, instale a biblioteca:\npip install reportlab"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {str(e)}")
    
    def importar_pdf_receber(self):
        """Importa receitas de um arquivo PDF"""
        arquivo, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo PDF",
            "",
            "Arquivos PDF (*.pdf)"
        )
        
        if not arquivo:
            return
        
        try:
            # Placeholder para funcionalidade de importação de PDF
            # Aqui você pode adicionar a lógica de extração de dados do PDF
            QMessageBox.information(
                self,
                "Importar PDF",
                f"Funcionalidade de importação de PDF em desenvolvimento.\n\nArquivo selecionado: {arquivo}\n\nEm breve será possível extrair dados automaticamente do PDF."
            )
            
            # Exemplo de como implementar:
            # import PyPDF2 ou pdfplumber
            # Extrair dados do PDF
            # Criar lançamentos automaticamente
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao importar PDF: {str(e)}")
    
    def filtrar_vence_hoje_receber(self):
        """Filtra apenas contas que vencem hoje"""
        receitas = [l for l in database.listar_lancamentos() if l.tipo == TipoLancamento.RECEITA]
        hoje = datetime.now().date()
        
        # Filtrar apenas as que vencem hoje e não estão pagas
        receitas = [r for r in receitas 
                   if r.data_vencimento.date() == hoje 
                   and r.status != StatusLancamento.PAGO]
        
        # Limpar tabela
        self.table_receber.setRowCount(0)
        self.table_receber.setRowCount(len(receitas))
        
        for i, rec in enumerate(receitas):
            cliente_item = QTableWidgetItem(rec.pessoa or "-")
            cliente_item.setForeground(QColor("#000000"))
            self.table_receber.setItem(i, 0, cliente_item)
            
            categoria_item = QTableWidgetItem(rec.categoria)
            categoria_item.setForeground(QColor("#000000"))
            self.table_receber.setItem(i, 1, categoria_item)
            
            subcat_item = QTableWidgetItem("-")
            subcat_item.setForeground(QColor("#000000"))
            self.table_receber.setItem(i, 2, subcat_item)
            
            doc_item = QTableWidgetItem(rec.num_documento or "-")
            doc_item.setForeground(QColor("#000000"))
            self.table_receber.setItem(i, 3, doc_item)
            
            desc_item = QTableWidgetItem(rec.descricao)
            desc_item.setForeground(QColor("#000000"))
            self.table_receber.setItem(i, 4, desc_item)
            
            valor_item = QTableWidgetItem(self.formatar_moeda(rec.valor))
            valor_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            valor_item.setForeground(QColor("#000000"))
            font = valor_item.font()
            font.setBold(True)
            valor_item.setFont(font)
            self.table_receber.setItem(i, 5, valor_item)
            
            venc_item = QTableWidgetItem(rec.data_vencimento.strftime("%d/%m/%Y"))
            venc_item.setForeground(QColor("#000000"))
            self.table_receber.setItem(i, 6, venc_item)
            
            comp_item = QTableWidgetItem("-")
            comp_item.setForeground(QColor("#000000"))
            self.table_receber.setItem(i, 7, comp_item)
            
            liq_item = QTableWidgetItem("-")
            liq_item.setForeground(QColor("#000000"))
            self.table_receber.setItem(i, 8, liq_item)
            
            status_item = QTableWidgetItem("VENCE HOJE")
            status_item.setBackground(QColor("#ffc107"))
            status_item.setForeground(QColor("#000000"))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_receber.setItem(i, 9, status_item)
            
            # Ações com ícones (ajustado para ícones totalmente visíveis)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(6)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            actions_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            # Tamanhos adaptativos para botões
            btn_size = self.scale_size(25)
            font_size = self.scale_size(14)
            
            btn_liquidar = QPushButton("✓")
            btn_liquidar.setToolTip("Liquidar conta")
            btn_liquidar.setFixedSize(btn_size, btn_size)
            btn_liquidar.setStyleSheet(f"""
                QPushButton {{
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-size: {font_size}px;
                }}
                QPushButton:hover {{
                    background-color: #218838;
                    border: 1px solid #1e7e34;
                }}
                QPushButton:pressed {{
                    background-color: #1e7e34;
                }}
            """)
            lancamento_id = rec.id
            btn_liquidar.clicked.connect(lambda checked=False, lid=lancamento_id: self.dialog_pagar_lancamento(lid))
            actions_layout.addWidget(btn_liquidar)
            
            btn_editar = QPushButton("✎")
            btn_editar.setToolTip("Editar conta")
            btn_editar.setFixedSize(btn_size, btn_size)
            btn_editar.setStyleSheet(f"""
                QPushButton {{
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-size: {font_size}px;
                }}
                QPushButton:hover {{
                    background-color: #0056b3;
                    border: 1px solid #004085;
                }}
                QPushButton:pressed {{
                    background-color: #004085;
                }}
            """)
            btn_editar.clicked.connect(lambda checked=False, r=rec: self.dialog_editar_lancamento(r))
            actions_layout.addWidget(btn_editar)
            
            btn_excluir = QPushButton("✖")
            btn_excluir.setToolTip("Excluir conta")
            btn_excluir.setFixedSize(btn_size, btn_size)
            btn_excluir.setStyleSheet(f"""
                QPushButton {{
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-size: {font_size}px;
                }}
                QPushButton:hover {{
                    background-color: #c82333;
                    border: 1px solid #bd2130;
                }}
                QPushButton:pressed {{
                    background-color: #bd2130;
                }}
            """)
            lancamento_id = rec.id
            btn_excluir.clicked.connect(lambda checked=False, lid=lancamento_id: self.excluir_lancamento(lid))
            actions_layout.addWidget(btn_excluir)
            
            self.table_receber.setCellWidget(i, 10, actions_widget)
        
        header = self.table_receber.horizontalHeader()
        if header:
            # Modo responsivo: colunas se ajustam ao espaço disponível
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            # Colunas com largura automática baseada no conteúdo
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Categoria
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Nº Doc
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Valor
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Vencimento
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Competência
            header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Dt. Liquidação
            header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Status
            header.setSectionResizeMode(10, QHeaderView.ResizeMode.Fixed)  # Ações
            header.resizeSection(10, 160)  # Largura fixa para Ações (ajustada para novos tamanhos)
    
    def limpar_filtros_receber(self):
        """Limpa todos os filtros de contas a receber"""
        self.combo_status_receber.setCurrentText("Todos")
        self.search_receber.clear()
        self.combo_categoria_receber.setCurrentText("Todas")
        self.combo_cliente_receber.setCurrentText("Todos")
        if hasattr(self, 'combo_mes_receber'):
            self.combo_mes_receber.setCurrentText("Todos")
        if hasattr(self, 'search_doc_receber'):
            self.search_doc_receber.clear()
        if hasattr(self, 'combo_filtro_rapido_receber'):
            self.combo_filtro_rapido_receber.setCurrentText("Todas")
        self.atualizar_contas_receber()
    
    def atualizar_saldo_banco_receber(self):
        """Atualiza o saldo exibido conforme banco selecionado"""
        # Calcular saldo total
        saldo_total = sum([c.saldo_inicial for c in database.listar_contas()])
        self.label_saldo_total.setText(self.formatar_moeda(saldo_total))
        
        # Filtrar por banco se selecionado
        banco_selecionado = self.combo_banco_receber.currentText()
        if banco_selecionado == "Todos":
            self.label_saldo_banco.setText("")
        else:
            contas_banco = [c for c in database.listar_contas() if c.banco == banco_selecionado]
            saldo_banco = sum(c.saldo_atual for c in contas_banco)
            self.label_saldo_banco.setText(f"Saldo {banco_selecionado}: {self.formatar_moeda(saldo_banco)}")
    
    def show_contas_receber(self):
        """Exibe tela de contas a receber"""
        self.clear_content()
        
        # Desmarcar todos os botões
        for btn in self.menu_buttons:
            btn.setChecked(False)
        self.btn_receber.setChecked(True)
        
        # Header com título e botões
        header = QHBoxLayout()
        title = QLabel("Contas a Receber")
        title.setObjectName("pageTitle")
        title.setFont(QFont("Segoe UI", self.scale_size(24), QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        
        # Botões de exportação no header
        btn_exportar_pdf = QPushButton("📄 Exportar PDF")
        btn_exportar_pdf.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 70px;
                height: 28px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        btn_exportar_pdf.clicked.connect(self.exportar_receber_pdf)
        header.addWidget(btn_exportar_pdf)
        
        btn_exportar_excel = QPushButton("📊 Exportar Excel")
        btn_exportar_excel.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 70px;
                height: 28px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        btn_exportar_excel.clicked.connect(self.exportar_receber_excel)
        header.addWidget(btn_exportar_excel)
        
        btn_atualizar = QPushButton("🔄 Atualizar")
        btn_atualizar.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 70px;
                height: 28px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        btn_atualizar.clicked.connect(self.atualizar_contas_receber)
        header.addWidget(btn_atualizar)
        
        self.content_layout.addLayout(header)
        
        # Filtros Rápidos com ComboBox
        filtros_rapidos_frame = QFrame()
        filtros_rapidos_frame.setObjectName("quickFilterFrame")
        filtros_rapidos_layout = QHBoxLayout(filtros_rapidos_frame)
        filtros_rapidos_layout.setSpacing(15)
        
        # Label
        label_rapido = QLabel("Filtro Rápido:")
        label_rapido.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        filtros_rapidos_layout.addWidget(label_rapido)
        
        # ComboBox de filtro rápido
        self.combo_filtro_rapido_receber = QComboBox()
        self.combo_filtro_rapido_receber.addItems([
            "Todas",
            "Pendentes",
            "Vencidas",
            "Pagas",
            "Vence Hoje",
            "Próximos 7 dias",
            "Próximos 30 dias"
        ])
        self.combo_filtro_rapido_receber.setCurrentText("Todas")
        self.combo_filtro_rapido_receber.currentTextChanged.connect(self.aplicar_filtro_rapido_receber_combo)
        self.combo_filtro_rapido_receber.setStyleSheet("QComboBox { background-color: white; color: black; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        filtros_rapidos_layout.addWidget(self.combo_filtro_rapido_receber)
        
        filtros_rapidos_layout.addStretch()
        self.content_layout.addWidget(filtros_rapidos_frame)
        
        # Filtros detalhados
        filtros_frame = QFrame()
        filtros_frame.setObjectName("filterFrame")
        filtros_layout = QHBoxLayout(filtros_frame)
        filtros_layout.setSpacing(10)
        
        # Filtro de status (oculto, controlado pelos botões rápidos)
        self.combo_status_receber = QComboBox()
        self.combo_status_receber.addItems(["Todos", "Pendentes", "Vencidas", "Pagas"])
        self.combo_status_receber.currentTextChanged.connect(self.atualizar_contas_receber)
        self.combo_status_receber.setVisible(False)
        
        # Filtro de período
        filtros_layout.addWidget(QLabel("De:"))
        self.data_inicio_receber = QDateEdit()
        self.data_inicio_receber.setDate(QDate.currentDate().addMonths(-1))
        self.data_inicio_receber.setCalendarPopup(True)
        filtros_layout.addWidget(self.data_inicio_receber)
        
        filtros_layout.addWidget(QLabel("Até:"))
        self.data_fim_receber = QDateEdit()
        self.data_fim_receber.setDate(QDate.currentDate().addMonths(1))
        self.data_fim_receber.setCalendarPopup(True)
        filtros_layout.addWidget(self.data_fim_receber)
        
        # Botão de pesquisa por data
        btn_filtrar_data_receber = QPushButton("🔍")
        btn_filtrar_data_receber.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ddd;
                padding: 8px 12px;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-color: #999;
            }
        """)
        btn_filtrar_data_receber.setToolTip("Filtrar por período")
        btn_filtrar_data_receber.clicked.connect(self.atualizar_contas_receber)
        filtros_layout.addWidget(btn_filtrar_data_receber)
        
        # Busca com botão de lupa
        search_container = QWidget()
        search_container_layout = QHBoxLayout(search_container)
        search_container_layout.setContentsMargins(0, 0, 0, 0)
        search_container_layout.setSpacing(0)
        
        self.search_receber = UpperCaseLineEdit()
        self.search_receber.setPlaceholderText("Buscar por descricao ou cliente...")
        self.search_receber.textChanged.connect(self.atualizar_contas_receber)
        self.search_receber.setStyleSheet("""
            QLineEdit {
                padding-right: 30px;
                background-color: white;
            }
        """)
        search_container_layout.addWidget(self.search_receber)
        
        # Botão de lupa dentro do campo de texto
        btn_search_clientes = QPushButton("🔍")
        btn_search_clientes.setFixedSize(25, 25)
        btn_search_clientes.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search_clientes.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
                margin-right: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-radius: 3px;
            }
        """)
        btn_search_clientes.clicked.connect(self.dialog_selecionar_cliente)
        btn_search_clientes.setToolTip("Selecionar cliente cadastrado")
        
        # Posicionar botão sobre o campo de texto
        search_container_layout.addWidget(btn_search_clientes)
        search_container_layout.setAlignment(btn_search_clientes, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        btn_search_clientes.move(self.search_receber.width() - 30, 2)
        
        filtros_layout.addWidget(search_container)
        
        filtros_layout.addStretch()
        
        self.content_layout.addWidget(filtros_frame)
        
        # Filtros detalhados adicionais
        filtros_detalhados_frame = QFrame()
        filtros_detalhados_frame.setObjectName("filterFrame")
        filtros_detalhados_frame.setStyleSheet("QFrame#filterFrame { background-color: white; }")
        filtros_detalhados_layout = QHBoxLayout(filtros_detalhados_frame)
        filtros_detalhados_layout.setSpacing(10)
        
        # Filtro por categoria
        filtros_detalhados_layout.addWidget(QLabel("Categoria:"))
        self.combo_categoria_receber = QComboBox()
        self.combo_categoria_receber.addItem("Todas")
        categorias_receita = [cat.nome for cat in database.listar_categorias() if cat.tipo == TipoLancamento.RECEITA]
        self.combo_categoria_receber.addItems(categorias_receita)
        self.combo_categoria_receber.currentTextChanged.connect(self.atualizar_contas_receber)
        self.combo_categoria_receber.setStyleSheet("QComboBox { background-color: white; color: black; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        filtros_detalhados_layout.addWidget(self.combo_categoria_receber)
        
        # Filtro por cliente
        filtros_detalhados_layout.addWidget(QLabel("Cliente:"))
        self.combo_cliente_receber = QComboBox()
        self.combo_cliente_receber.addItem("Todos")
        clientes = list(set([r.pessoa for r in [l for l in database.listar_lancamentos() if l.tipo == TipoLancamento.RECEITA] if r.pessoa]))
        self.combo_cliente_receber.addItems(sorted(clientes))
        self.combo_cliente_receber.currentTextChanged.connect(self.atualizar_contas_receber)
        self.combo_cliente_receber.setStyleSheet("QComboBox { background-color: white; color: black; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        filtros_detalhados_layout.addWidget(self.combo_cliente_receber)
        
        # Filtro por mês
        filtros_detalhados_layout.addWidget(QLabel("Mês:"))
        self.combo_mes_receber = QComboBox()
        self.combo_mes_receber.addItem("Todos")
        meses = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        for i, mes in enumerate(meses, 1):
            self.combo_mes_receber.addItem(f"{mes}")
        self.combo_mes_receber.currentTextChanged.connect(self.atualizar_contas_receber)
        self.combo_mes_receber.setStyleSheet("QComboBox { background-color: white; color: black; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        filtros_detalhados_layout.addWidget(self.combo_mes_receber)
        
        # Filtro por número de documento
        filtros_detalhados_layout.addWidget(QLabel("Nº Documento:"))
        self.search_doc_receber = UpperCaseLineEdit()
        self.search_doc_receber.setPlaceholderText("Buscar por número do documento...")
        self.search_doc_receber.textChanged.connect(self.atualizar_contas_receber)
        filtros_detalhados_layout.addWidget(self.search_doc_receber)
        
        # Botão limpar filtros
        btn_limpar_receber = QPushButton("Limpar Filtros")
        btn_limpar_receber.clicked.connect(lambda: self.limpar_filtros_receber())
        filtros_detalhados_layout.addWidget(btn_limpar_receber)
        
        filtros_detalhados_layout.addStretch()
        
        self.content_layout.addWidget(filtros_detalhados_frame)
        
        # Saldo de Contas Bancárias
        saldo_frame = QFrame()
        saldo_frame.setObjectName("saldoFrame")
        saldo_frame.setStyleSheet("QFrame#saldoFrame { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 10px; }")
        saldo_layout = QHBoxLayout(saldo_frame)
        saldo_layout.setSpacing(15)
        
        # Saldo Total
        saldo_total_label = QLabel("Saldo Total:")
        saldo_total_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        saldo_layout.addWidget(saldo_total_label)
        
        self.label_saldo_total = QLabel("R$ 0,00")
        self.label_saldo_total.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.label_saldo_total.setStyleSheet("color: #28a745;")
        saldo_layout.addWidget(self.label_saldo_total)
        
        saldo_layout.addSpacing(30)
        
        # Filtro por Banco
        saldo_layout.addWidget(QLabel("Banco:"))
        self.combo_banco_receber = QComboBox()
        self.combo_banco_receber.addItem("Todos")
        bancos = list(set([conta.banco for conta in database.listar_contas()]))
        self.combo_banco_receber.addItems(sorted(bancos))
        self.combo_banco_receber.currentTextChanged.connect(self.atualizar_saldo_banco_receber)
        self.combo_banco_receber.setMinimumWidth(150)
        self.combo_banco_receber.setStyleSheet("QComboBox { background-color: white; color: black; min-width: 150px; padding: 5px; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        saldo_layout.addWidget(self.combo_banco_receber)
        
        # Saldo do Banco Selecionado
        self.label_saldo_banco = QLabel("")
        self.label_saldo_banco.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.label_saldo_banco.setStyleSheet("color: #007bff;")
        saldo_layout.addWidget(self.label_saldo_banco)
        
        saldo_layout.addStretch()
        
        # Botão Nova Receita na extrema direita
        btn_nova_receita = QPushButton("+ Nova Receita")
        btn_nova_receita.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 100px;
                height: 28px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        btn_nova_receita.clicked.connect(lambda: self.dialog_novo_lancamento(TipoLancamento.RECEITA))
        saldo_layout.addWidget(btn_nova_receita)
        
        self.content_layout.addWidget(saldo_frame)
        
        # Atualizar saldos inicialmente
        self.atualizar_saldo_banco_receber()
        
        # Botões de ação em lote
        acoes_lote_frame = QFrame()
        acoes_lote_layout = QHBoxLayout(acoes_lote_frame)
        acoes_lote_layout.setContentsMargins(0, 10, 0, 10)
        
        btn_selecionar_todos_receber = QPushButton("☑ Selecionar Todos")
        btn_selecionar_todos_receber.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #4a90e2, stop:1 #357abd);
                color: white;
                border: 1px solid #2e5f8f;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10pt;
                min-width: 140px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #5ba3ff, stop:1 #4a90e2);
                border: 1px solid #4a90e2;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #357abd, stop:1 #2e5f8f);
                padding-top: 9px;
                padding-bottom: 7px;
            }
        """)
        btn_selecionar_todos_receber.clicked.connect(self.selecionar_todos_receber)
        acoes_lote_layout.addWidget(btn_selecionar_todos_receber)
        
        btn_desselecionar_todos_receber = QPushButton("☐ Desselecionar Todos")
        btn_desselecionar_todos_receber.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #95a5a6, stop:1 #7f8c8d);
                color: white;
                border: 1px solid #6c7a7b;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10pt;
                min-width: 140px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #a6b6b7, stop:1 #95a5a6);
                border: 1px solid #7f8c8d;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #7f8c8d, stop:1 #6c7a7b);
                padding-top: 9px;
                padding-bottom: 7px;
            }
        """)
        btn_desselecionar_todos_receber.clicked.connect(self.desselecionar_todos_receber)
        acoes_lote_layout.addWidget(btn_desselecionar_todos_receber)
        
        acoes_lote_layout.addStretch()
        
        btn_liquidar_selecionados_receber = QPushButton("💰 Liquidar Selecionados")
        btn_liquidar_selecionados_receber.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        btn_liquidar_selecionados_receber.clicked.connect(self.liquidar_selecionados_receber)
        acoes_lote_layout.addWidget(btn_liquidar_selecionados_receber)
        
        btn_excluir_selecionados_receber = QPushButton("🗑 Excluir Selecionados")
        btn_excluir_selecionados_receber.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        btn_excluir_selecionados_receber.clicked.connect(self.excluir_selecionados_receber)
        acoes_lote_layout.addWidget(btn_excluir_selecionados_receber)
        
        self.content_layout.addWidget(acoes_lote_frame)
        
        # Criar tabela de receitas
        self.table_receber = QTableWidget()
        self.table_receber.setObjectName("dataTable")
        self.table_receber.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.table_receber.setAlternatingRowColors(True)
        font_size = self.scale_size(11)
        self.table_receber.setStyleSheet(f"""
            QTableWidget {{ 
                background-color: white;
                font-size: {font_size}px;
                alternate-background-color: #d0d0d0;
            }} 
            QHeaderView::section {{ 
                background-color: #f0f0f0;
                font-size: {font_size}px;
            }}
            QCheckBox {{
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: #f0f0f0;
                width: 10px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #2196F3;
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #1976D2;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: #f0f0f0;
            }}
        """)
        
        self.table_receber.setColumnCount(12)
        self.table_receber.setHorizontalHeaderLabels([
            "☐", "Cliente", "Categoria", "Subcategoria", "Nº Doc", "Descrição", "Valor", "Vencimento", "Competência", "Dt. Liquidação", "Status", "Ações"
        ])
        self.table_receber.setShowGrid(False)
        self.table_receber.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_receber.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Configurar e ocultar o cabeçalho vertical (coluna com números)
        row_height = self.scale_size(45)
        header_height = self.scale_size(40)
        v_header = self.table_receber.verticalHeader()
        if v_header is not None:
            v_header.hide()
            v_header.setDefaultSectionSize(row_height)
        
        # Definir altura mínima para exibir 13 linhas (adaptativo)
        self.table_receber.setMinimumHeight(row_height * 13 + header_height)
        
        self.table_receber.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.content_layout.addWidget(self.table_receber)
        
        # Atualizar tabela com os dados
        self.atualizar_contas_receber()
        
        self.content_layout.addStretch()
    
    def toggle_cadastros_menu(self):
        """Alterna a visibilidade do submenu de cadastros"""
        is_visible = self.submenu_cadastros.isVisible()
        self.submenu_cadastros.setVisible(not is_visible)
        
        # Atualizar ícone do botão mantendo o emoji
        if is_visible:
            self.btn_cadastros.setText("📋  Cadastros                    ▼")
        else:
            self.btn_cadastros.setText("📋  Cadastros                    ▲")
    
    def toggle_relatorios_menu(self):
        """Alterna a visibilidade do submenu de relatórios"""
        is_visible = self.submenu_relatorios.isVisible()
        self.submenu_relatorios.setVisible(not is_visible)
        
        # Atualizar ícone do botão mantendo o emoji
        if is_visible:
            self.btn_relatorios.setText("📑  Relatorios                   ▼")
        else:
            self.btn_relatorios.setText("📑  Relatorios                   ▲")
    
    def show_cadastros(self, tab_index=0):
        """Exibe tela de cadastros com sub-abas"""
        self.clear_content()
        
        # Desmarcar todos os botões
        for btn in self.menu_buttons:
            btn.setChecked(False)
        self.btn_cadastros.setChecked(True)
        
        # Garantir que o submenu está visível
        if not self.submenu_cadastros.isVisible():
            self.submenu_cadastros.setVisible(True)
            self.btn_cadastros.setText("Cadastros                    ▲")
        
        # Título
        title = QLabel("Cadastros")
        title.setObjectName("pageTitle")
        title.setFont(QFont("Segoe UI", self.scale_size(24), QFont.Weight.Bold))
        self.content_layout.addWidget(title)
        
        # Criar abas
        tabs = QTabWidget()
        tabs.setObjectName("cadastroTabs")
        
        # Aba 1: Categorias de Receitas
        tab_receitas = self.create_tab_categorias_receitas()
        tabs.addTab(tab_receitas, "Categorias de Receitas")
        
        # Aba 2: Categorias de Despesas
        tab_despesas = self.create_tab_categorias_despesas()
        tabs.addTab(tab_despesas, "Categorias de Despesas")
        
        # Definir aba ativa
        tabs.setCurrentIndex(tab_index)
        
        self.content_layout.addWidget(tabs)
        self.content_layout.addStretch()
    
    def show_clientes(self):
        """Exibe tela de cadastro de clientes"""
        self.clear_content()
        
        # Desmarcar todos os botões
        for btn in self.menu_buttons:
            btn.setChecked(False)
        self.btn_cadastros.setChecked(True)
        
        # Garantir que o submenu está visível
        if not self.submenu_cadastros.isVisible():
            self.submenu_cadastros.setVisible(True)
            self.btn_cadastros.setText("Cadastros                    ▲")
        
        # Título
        title = QLabel("Cadastro de Clientes")
        title.setObjectName("pageTitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.content_layout.addWidget(title)
        
        # Adicionar a aba de clientes diretamente
        tab_clientes = self.create_tab_clientes()
        self.content_layout.addWidget(tab_clientes)
        self.content_layout.addStretch()
    
    def create_tab_categorias_receitas(self):
        """Cria a aba de categorias de receitas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Cabeçalho
        header = QHBoxLayout()
        header_label = QLabel("Gerenciar Categorias de Receitas")
        header_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header.addWidget(header_label)
        header.addStretch()
        
        btn_nova = QPushButton("+ Nova Categoria")
        btn_nova.setObjectName("primaryButton")
        btn_nova.clicked.connect(lambda: self.dialog_nova_categoria(TipoLancamento.RECEITA))
        header.addWidget(btn_nova)
        
        layout.addLayout(header)
        
        # Tabela de categorias
        table = QTableWidget()
        table.setObjectName("dataTable")
        
        categorias_receitas = [cat for cat in database.listar_categorias() 
                               if cat.tipo == TipoLancamento.RECEITA]
        
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Nome", "Subcategorias", "Ações"])
        table.setRowCount(len(categorias_receitas))
        vheader = table.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        
        for i, cat in enumerate(categorias_receitas):
            # Alternar cores das linhas (cinza e branco)
            cor_fundo = QColor("#e0e0e0") if i % 2 == 0 else QColor("#ffffff")
            
            item_nome = QTableWidgetItem(cat.nome)
            item_nome.setBackground(cor_fundo)
            item_nome.setForeground(QColor("#000000"))
            table.setItem(i, 0, item_nome)
            
            # Exibir número de subcategorias
            num_sub = len(cat.subcategorias)
            item_sub = QTableWidgetItem(f"{num_sub} subcategoria(s)")
            item_sub.setBackground(cor_fundo)
            item_sub.setForeground(QColor("#000000"))
            table.setItem(i, 1, item_sub)
            
            # Botões de ação: Pesquisar, Editar e Excluir
            actions_widget = QWidget()
            actions_widget.setStyleSheet(f"background-color: {cor_fundo.name()};")
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(3)
            
            btn_pesquisar = QPushButton("🔍")
            btn_pesquisar.setToolTip("Pesquisar subcategorias")
            btn_pesquisar.setMaximumWidth(30)
            btn_pesquisar.setStyleSheet("QPushButton { background-color: transparent; border: 1px solid #ddd; border-radius: 3px; padding: 3px; font-size: 14px; } QPushButton:hover { background-color: #f0f0f0; }")
            btn_pesquisar.clicked.connect(lambda checked=False, nome=cat.nome: self.dialog_gerenciar_subcategorias(nome))
            actions_layout.addWidget(btn_pesquisar)
            
            btn_editar = QPushButton("✏️")
            btn_editar.setToolTip("Editar categoria")
            btn_editar.setMaximumWidth(35)
            btn_editar.setStyleSheet("QPushButton { background-color: transparent; border: 1px solid #ddd; border-radius: 3px; padding: 5px; font-size: 18px; } QPushButton:hover { background-color: #f0f0f0; }")
            btn_editar.clicked.connect(lambda checked=False, c=cat: self.dialog_editar_categoria(c))
            actions_layout.addWidget(btn_editar)
            
            btn_excluir = QPushButton("🗑️")
            btn_excluir.setToolTip("Excluir categoria")
            btn_excluir.setMaximumWidth(35)
            btn_excluir.setStyleSheet("QPushButton { background-color: transparent; border: 1px solid #ddd; border-radius: 3px; padding: 5px; font-size: 18px; } QPushButton:hover { background-color: #f0f0f0; }")
            btn_excluir.clicked.connect(lambda checked=False, nome=cat.nome: self.excluir_categoria(nome))
            actions_layout.addWidget(btn_excluir)
            
            table.setCellWidget(i, 2, actions_widget)
        
        header = table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        # Configurar altura das linhas ajustável
        v_header = table.verticalHeader()
        if v_header:
            v_header.setVisible(False)  # Ocultar números das linhas
            v_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            v_header.setDefaultSectionSize(60)
        
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setMaximumWidth(900)
        
        # Centralizar tabela
        table_container = QHBoxLayout()
        table_container.addStretch()
        table_container.addWidget(table)
        table_container.addStretch()
        layout.addLayout(table_container)
        
        return widget
    
    def create_tab_categorias_despesas(self):
        """Cria a aba de categorias de despesas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Cabeçalho
        header = QHBoxLayout()
        header_label = QLabel("Gerenciar Categorias de Despesas")
        header_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header.addWidget(header_label)
        header.addStretch()
        
        btn_nova = QPushButton("+ Nova Categoria")
        btn_nova.setObjectName("primaryButton")
        btn_nova.clicked.connect(lambda: self.dialog_nova_categoria(TipoLancamento.DESPESA))
        header.addWidget(btn_nova)
        
        layout.addLayout(header)
        
        # Tabela de categorias
        table = QTableWidget()
        table.setObjectName("dataTable")
        
        categorias_despesas = [cat for cat in database.listar_categorias() 
                               if cat.tipo == TipoLancamento.DESPESA]
        
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Nome", "Subcategorias", "Ações"])
        table.setRowCount(len(categorias_despesas))
        vheader = table.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        
        for i, cat in enumerate(categorias_despesas):
            # Alternar cores das linhas (cinza e branco)
            cor_fundo = QColor("#e0e0e0") if i % 2 == 0 else QColor("#ffffff")
            
            item_nome = QTableWidgetItem(cat.nome)
            item_nome.setBackground(cor_fundo)
            item_nome.setForeground(QColor("#000000"))
            table.setItem(i, 0, item_nome)
            
            # Exibir número de subcategorias
            num_sub = len(cat.subcategorias)
            item_sub = QTableWidgetItem(f"{num_sub} subcategoria(s)")
            item_sub.setBackground(cor_fundo)
            item_sub.setForeground(QColor("#000000"))
            table.setItem(i, 1, item_sub)
            
            # Botões de ação: Pesquisar, Editar e Excluir
            actions_widget = QWidget()
            actions_widget.setStyleSheet(f"background-color: {cor_fundo.name()};")
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(3)
            
            btn_pesquisar = QPushButton("🔍")
            btn_pesquisar.setToolTip("Pesquisar subcategorias")
            btn_pesquisar.setMaximumWidth(35)
            btn_pesquisar.setStyleSheet("QPushButton { background-color: transparent; border: 1px solid #ddd; border-radius: 3px; padding: 5px; font-size: 18px; } QPushButton:hover { background-color: #f0f0f0; }")
            btn_pesquisar.clicked.connect(lambda checked=False, nome=cat.nome: self.dialog_gerenciar_subcategorias(nome))
            actions_layout.addWidget(btn_pesquisar)
            
            btn_editar = QPushButton("✏️")
            btn_editar.setToolTip("Editar categoria")
            btn_editar.setMaximumWidth(35)
            btn_editar.setStyleSheet("QPushButton { background-color: transparent; border: 1px solid #ddd; border-radius: 3px; padding: 5px; font-size: 18px; } QPushButton:hover { background-color: #f0f0f0; }")
            btn_editar.clicked.connect(lambda checked=False, c=cat: self.dialog_editar_categoria(c))
            actions_layout.addWidget(btn_editar)
            
            btn_excluir = QPushButton("✖")
            btn_excluir.setToolTip("Excluir categoria")
            btn_excluir.setMaximumWidth(35)
            btn_excluir.setStyleSheet("QPushButton { background-color: transparent; border: 1px solid #ddd; border-radius: 3px; padding: 5px; font-size: 18px; color: #dc3545; font-weight: bold; } QPushButton:hover { background-color: #fee; }")
            btn_excluir.clicked.connect(lambda checked=False, nome=cat.nome: self.excluir_categoria(nome))
            actions_layout.addWidget(btn_excluir)
            
            table.setCellWidget(i, 2, actions_widget)
        
        header = table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        # Configurar altura das linhas ajustável
        v_header = table.verticalHeader()
        if v_header:
            v_header.setVisible(False)  # Ocultar números das linhas
            v_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            v_header.setDefaultSectionSize(60)
        
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setMaximumWidth(900)
        
        # Centralizar tabela
        table_container = QHBoxLayout()
        table_container.addStretch()
        table_container.addWidget(table)
        table_container.addStretch()
        layout.addLayout(table_container)
        
        return widget
    
    def create_tab_clientes(self):
        """Cria a aba de cadastro de clientes"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Cabeçalho
        header = QHBoxLayout()
        header_label = QLabel("Gerenciar Clientes")
        header_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header.addWidget(header_label)
        header.addStretch()
        
        btn_novo = QPushButton("+ Novo Cliente")
        btn_novo.setObjectName("primaryButton")
        btn_novo.clicked.connect(self.dialog_novo_cliente)
        header.addWidget(btn_novo)
        
        layout.addLayout(header)
        
        # Tabela de clientes
        table = QTableWidget()
        table.setObjectName("dataTable")
        
        # Obter clientes do banco de dados
        _clientes = database.listar_clientes()
        
        table.setColumnCount(12)
        table.setHorizontalHeaderLabels(["Razão Social", "Nome Fantasia", "CNPJ", "IE", "IM", "Rua", "Número", "Bairro", "CEP", "Contato", "Email", "Ações"])
        table.setRowCount(len(_clientes))
        vheader = table.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        
        for i, cliente in enumerate(database.listar_clientes()):
            # Alternar cores das linhas (cinza e branco)
            cor_fundo = QColor("#e0e0e0") if i % 2 == 0 else QColor("#ffffff")
            
            item_razao = QTableWidgetItem(cliente.get('razao_social', cliente.get('nome', '')))
            item_razao.setBackground(cor_fundo)
            item_razao.setForeground(QColor("#000000"))
            table.setItem(i, 0, item_razao)
            
            item_fantasia = QTableWidgetItem(cliente.get('nome_fantasia', '-'))
            item_fantasia.setBackground(cor_fundo)
            item_fantasia.setForeground(QColor("#000000"))
            table.setItem(i, 1, item_fantasia)
            
            item_cnpj = QTableWidgetItem(cliente.get('cnpj', ''))
            item_cnpj.setBackground(cor_fundo)
            item_cnpj.setForeground(QColor("#000000"))
            table.setItem(i, 2, item_cnpj)
            
            item_ie = QTableWidgetItem(cliente.get('ie', '-'))
            item_ie.setBackground(cor_fundo)
            item_ie.setForeground(QColor("#000000"))
            table.setItem(i, 3, item_ie)
            
            item_im = QTableWidgetItem(cliente.get('im', '-'))
            item_im.setBackground(cor_fundo)
            item_im.setForeground(QColor("#000000"))
            table.setItem(i, 4, item_im)
            
            item_rua = QTableWidgetItem(cliente.get('rua', '-'))
            item_rua.setBackground(cor_fundo)
            item_rua.setForeground(QColor("#000000"))
            table.setItem(i, 5, item_rua)
            
            item_numero = QTableWidgetItem(cliente.get('numero', '-'))
            item_numero.setBackground(cor_fundo)
            item_numero.setForeground(QColor("#000000"))
            table.setItem(i, 6, item_numero)
            
            item_bairro = QTableWidgetItem(cliente.get('bairro', '-'))
            item_bairro.setBackground(cor_fundo)
            item_bairro.setForeground(QColor("#000000"))
            table.setItem(i, 7, item_bairro)
            
            item_cep = QTableWidgetItem(cliente.get('cep', '-'))
            item_cep.setBackground(cor_fundo)
            item_cep.setForeground(QColor("#000000"))
            table.setItem(i, 8, item_cep)
            
            item_contato = QTableWidgetItem(cliente.get('contato', cliente.get('telefone', '-')))
            item_contato.setBackground(cor_fundo)
            item_contato.setForeground(QColor("#000000"))
            table.setItem(i, 9, item_contato)
            
            item_email = QTableWidgetItem(cliente.get('email', '-'))
            item_email.setBackground(cor_fundo)
            item_email.setForeground(QColor("#000000"))
            table.setItem(i, 10, item_email)
            
            # Botões de ação: Editar e Excluir
            actions_widget = QWidget()
            actions_widget.setStyleSheet(f"background-color: {cor_fundo.name()};")
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(3)
            
            btn_editar = QPushButton("✏️")
            btn_editar.setToolTip("Editar cliente")
            btn_editar.setMaximumWidth(35)
            btn_editar.setStyleSheet("QPushButton { background-color: transparent; border: 1px solid #ddd; border-radius: 3px; padding: 5px; font-size: 18px; } QPushButton:hover { background-color: #f0f0f0; }")
            btn_editar.clicked.connect(lambda checked=False, c=cliente: self.dialog_editar_cliente(c, i))
            actions_layout.addWidget(btn_editar)
            
            btn_excluir = QPushButton("✖")
            btn_excluir.setToolTip("Excluir cliente")
            btn_excluir.setMaximumWidth(35)
            btn_excluir.setStyleSheet("QPushButton { background-color: transparent; border: 1px solid #ddd; border-radius: 3px; padding: 5px; font-size: 18px; color: #dc3545; font-weight: bold; } QPushButton:hover { background-color: #fee; }")
            btn_excluir.clicked.connect(lambda checked=False, idx=i: self.excluir_cliente(idx))
            actions_layout.addWidget(btn_excluir)
            
            table.setCellWidget(i, 11, actions_widget)
        
        # Cabeçalho horizontal - larguras para títulos completos
        header = table.horizontalHeader()
        if header:
            # Configurar modo de redimensionamento responsivo
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Razão Social
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Nome Fantasia
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # CNPJ
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # IE
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # IM
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Rua
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Número
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Bairro
            header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # CEP
            header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Contato
            header.setSectionResizeMode(10, QHeaderView.ResizeMode.Stretch)  # Email
            header.setSectionResizeMode(11, QHeaderView.ResizeMode.Fixed)  # Ações
            table.setColumnWidth(11, 100)  # Ações largura fixa
        
        # Configurar altura das linhas ajustável
        vertical_header = table.verticalHeader()
        if vertical_header:
            vertical_header.setVisible(False)  # Ocultar números das linhas
            vertical_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            vertical_header.setDefaultSectionSize(60)
        
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(table)
        
        return widget
    
    def dialog_selecionar_cliente(self):
        """Diálogo para selecionar um cliente cadastrado"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Selecionar Cliente")
        dialog.resize(1400, 700)
        dialog.setStyleSheet("""
            QDialog { 
                background-color: white; 
            }
            QTableWidget {
                background-color: #2d2d2d;
                color: white;
                gridline-color: #404040;
                selection-background-color: #0d47a1;
            }
            QTableWidget::item {
                background-color: #2d2d2d;
                color: white;
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #0d47a1;
            }
            QHeaderView::section {
                background-color: #1e1e1e;
                color: white;
                padding: 8px;
                border: 1px solid #404040;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("Clientes Cadastrados")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)
        
        # Campo de busca
        search_layout = QHBoxLayout()
        search_label = QLabel("Buscar:")
        search_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        search_layout.addWidget(search_label)
        
        search_box = QLineEdit()
        search_box.setPlaceholderText("Digite o nome do cliente...")
        search_box.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
                color: black;
            }
        """)
        search_layout.addWidget(search_box)
        layout.addLayout(search_layout)
        
        # Tabela de clientes
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Nome/Razão Social", "CNPJ", "Contato", "Email"])
        header = table.horizontalHeader()
        if header:
            header.setStretchLastSection(True)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        v_header = table.verticalHeader()
        if v_header:
            v_header.setVisible(True)
            v_header.setDefaultSectionSize(40)
        
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #d0d0d0;
                background-color: #ffffff;
            }
        """)
        table.setShowGrid(True)
        
        # Obter clientes do banco
        
        # Também pegar clientes dos lançamentos
        clientes_lancamentos = list(set([r.pessoa for r in database.listar_lancamentos() if r.pessoa]))
        
        # Combinar listas
        todos_clientes = []
        for cliente in database.listar_clientes():
            todos_clientes.append({
                'nome': cliente.get('razao_social', cliente.get('nome', '')),
                'cnpj': cliente.get('cnpj', '-'),
                'contato': cliente.get('contato', cliente.get('telefone', '-')),
                'email': cliente.get('email', '-')
            })
        
        # Adicionar clientes de lançamentos que não estão na lista
        for nome in clientes_lancamentos:
            if not any(c['nome'] == nome for c in todos_clientes):
                todos_clientes.append({
                    'nome': nome,
                    'cnpj': '-',
                    'contato': '-',
                    'email': '-'
                })
        
        def atualizar_tabela(filtro=""):
            table.setRowCount(0)
            clientes_filtrados = [c for c in todos_clientes if filtro.lower() in c['nome'].lower()] if filtro else todos_clientes
            table.setRowCount(len(clientes_filtrados))
            
            for i, cliente in enumerate(clientes_filtrados):
                table.setItem(i, 0, QTableWidgetItem(cliente['nome']))
                table.setItem(i, 1, QTableWidgetItem(cliente['cnpj']))
                table.setItem(i, 2, QTableWidgetItem(cliente['contato']))
                table.setItem(i, 3, QTableWidgetItem(cliente['email']))
        
        # Preencher tabela inicialmente
        atualizar_tabela()
        
        # Conectar busca
        search_box.textChanged.connect(atualizar_tabela)
        
        layout.addWidget(table)
        
        # Botões
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        btn_selecionar = QPushButton("Selecionar")
        btn_selecionar.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 30px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_selecionar.clicked.connect(lambda: self.selecionar_cliente_da_tabela(table, dialog))
        buttons_layout.addWidget(btn_selecionar)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 30px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_cancelar.clicked.connect(dialog.reject)
        buttons_layout.addWidget(btn_cancelar)
        
        layout.addLayout(buttons_layout)
        
        # Duplo clique para selecionar
        table.doubleClicked.connect(lambda: self.selecionar_cliente_da_tabela(table, dialog))
        
        dialog.exec()
    
    def selecionar_cliente_da_tabela(self, table, dialog):
        """Seleciona o cliente da tabela e preenche o campo de busca"""
        current_row = table.currentRow()
        if current_row >= 0:
            nome_cliente = table.item(current_row, 0).text()
            if hasattr(self, 'search_receber'):
                self.search_receber.setText(nome_cliente)
            dialog.accept()
        else:
            QMessageBox.warning(dialog, "Aviso", "Por favor, selecione um cliente da lista.")
    
    def dialog_novo_cliente(self):
        """Diálogo para cadastrar um novo cliente"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Novo Cliente")
        dialog.resize(980, 780)
        dialog.setStyleSheet("QDialog { background-color: white; }")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(40, 30, 40, 20)
        layout.setSpacing(10)
        
        # Formulário direto no layout
        form = QVBoxLayout()
        
        # Estilo para labels
        label_style = "color: #2c3e50; font-weight: bold; font-size: 13px; margin-top: 5px;"
        
        # Razão Social
        label_rs = QLabel("*Razão Social:")
        label_rs.setStyleSheet(label_style)
        form.addWidget(label_rs)
        input_razao_social = UpperCaseLineEdit()
        form.addWidget(input_razao_social)
        
        # Nome Fantasia
        label_nf = QLabel("*Nome Fantasia:")
        label_nf.setStyleSheet(label_style)
        form.addWidget(label_nf)
        input_nome_fantasia = UpperCaseLineEdit()
        form.addWidget(input_nome_fantasia)
        
        # CNPJ
        label_cnpj = QLabel("*CNPJ:")
        label_cnpj.setStyleSheet(label_style)
        form.addWidget(label_cnpj)
        input_cnpj = UpperCaseLineEdit()
        input_cnpj.setPlaceholderText("00.000.000/0000-00")
        form.addWidget(input_cnpj)
        
        # Inscrição Estadual
        label_ie = QLabel("Inscrição Estadual:")
        label_ie.setStyleSheet(label_style)
        form.addWidget(label_ie)
        input_ie = UpperCaseLineEdit()
        form.addWidget(input_ie)
        
        # Inscrição Municipal
        label_im = QLabel("Inscrição Municipal:")
        label_im.setStyleSheet(label_style)
        form.addWidget(label_im)
        input_im = UpperCaseLineEdit()
        form.addWidget(input_im)
        
        # Separador de endereço
        separator = QLabel("─── Endereço ───")
        separator.setStyleSheet("color: #3498db; font-weight: bold; margin-top: 15px; font-size: 14px;")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addWidget(separator)
        
        # CEP (primeiro para buscar endereço)
        label_cep = QLabel("CEP:")
        label_cep.setStyleSheet(label_style)
        form.addWidget(label_cep)
        input_cep = UpperCaseLineEdit()
        input_cep.setPlaceholderText("00000-000")
        form.addWidget(input_cep)
        
        # Rua/Avenida
        label_rua = QLabel("Rua/Avenida:")
        label_rua.setStyleSheet(label_style)
        form.addWidget(label_rua)
        input_rua = UpperCaseLineEdit()
        form.addWidget(input_rua)
        
        # Número
        label_num = QLabel("Número:")
        label_num.setStyleSheet(label_style)
        form.addWidget(label_num)
        input_numero = UpperCaseLineEdit()
        form.addWidget(input_numero)
        
        # Complemento
        label_comp = QLabel("Complemento:")
        label_comp.setStyleSheet(label_style)
        form.addWidget(label_comp)
        input_complemento = UpperCaseLineEdit()
        form.addWidget(input_complemento)
        
        # Bairro
        label_bairro = QLabel("Bairro:")
        label_bairro.setStyleSheet(label_style)
        form.addWidget(label_bairro)
        input_bairro = UpperCaseLineEdit()
        form.addWidget(input_bairro)
        
        # Cidade
        label_cidade = QLabel("Cidade:")
        label_cidade.setStyleSheet(label_style)
        form.addWidget(label_cidade)
        input_cidade = UpperCaseLineEdit()
        form.addWidget(input_cidade)
        
        # Estado
        label_estado = QLabel("Estado:")
        label_estado.setStyleSheet(label_style)
        form.addWidget(label_estado)
        input_estado = QComboBox()
        input_estado.addItems(["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"])
        input_estado.setMaximumWidth(100)
        input_estado.setStyleSheet("QComboBox { background-color: white; color: black; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        form.addWidget(input_estado)
        
        # Função para buscar endereço pelo CEP
        def buscar_cep():
            cep = input_cep.text().replace("-", "").replace(".", "").strip()
            if len(cep) == 8:
                try:
                    response = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=5)
                    if response.status_code == 200:
                        dados = response.json()
                        if "erro" not in dados:
                            input_rua.setText(dados.get("logradouro", ""))
                            input_bairro.setText(dados.get("bairro", ""))
                            input_cidade.setText(dados.get("localidade", ""))
                            input_estado.setCurrentText(dados.get("uf", ""))
                            QMessageBox.information(dialog, "Sucesso", "Endereço encontrado!")
                        else:
                            QMessageBox.warning(dialog, "Aviso", "CEP não encontrado.")
                except Exception as e:
                    QMessageBox.warning(dialog, "Erro", f"Erro ao buscar CEP: {str(e)}")
        
        input_cep.editingFinished.connect(buscar_cep)
        
        # Separador de contato
        separator2 = QLabel("─── Contato ───")
        separator2.setStyleSheet("color: #3498db; font-weight: bold; margin-top: 15px; font-size: 14px;")
        separator2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addWidget(separator2)
        
        # Contato
        label_contato = QLabel("Contato:")
        label_contato.setStyleSheet(label_style)
        form.addWidget(label_contato)
        input_contato = UpperCaseLineEdit()
        input_contato.setPlaceholderText("(00) 00000-0000")
        form.addWidget(input_contato)
        
        # Email
        label_email = QLabel("Email:")
        label_email.setStyleSheet(label_style)
        form.addWidget(label_email)
        input_email = QLineEdit()
        input_email.setPlaceholderText("email@exemplo.com")
        form.addWidget(input_email)
        
        layout.addLayout(form)
        layout.addStretch()
        
        # Botões
        buttons = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(dialog.reject)
        buttons.addWidget(btn_cancelar)
        
        btn_salvar = QPushButton("Salvar")
        btn_salvar.setObjectName("primaryButton")
        btn_salvar.clicked.connect(lambda: self.salvar_cliente(
            dialog, input_razao_social, input_nome_fantasia, input_cnpj, input_ie, input_im,
            input_cep, input_rua, input_numero, input_complemento, input_bairro, input_cidade, input_estado,
            input_contato, input_email
        ))
        buttons.addWidget(btn_salvar)
        
        layout.addLayout(buttons)
        dialog.exec()
    
    def salvar_cliente(self, dialog, input_razao_social, input_nome_fantasia, input_cnpj, input_ie, input_im,
                       input_cep, input_rua, input_numero, input_complemento, input_bairro, input_cidade, input_estado,
                       input_contato, input_email):
        """Salva um novo cliente"""
        razao_social = input_razao_social.text().strip()
        nome_fantasia = input_nome_fantasia.text().strip()
        cnpj = input_cnpj.text().strip()
        
        if not razao_social:
            QMessageBox.warning(dialog, "Atenção", "A razão social é obrigatória!")
            return
        
        if not nome_fantasia:
            QMessageBox.warning(dialog, "Atenção", "O nome fantasia é obrigatório!")
            return
        
        if not cnpj:
            QMessageBox.warning(dialog, "Atenção", "O CNPJ é obrigatório!")
            return
        
        # Validar formato básico do CNPJ (apenas números)
        cnpj_numeros = ''.join(filter(str.isdigit, cnpj))
        if len(cnpj_numeros) != 14:
            QMessageBox.warning(dialog, "Atenção", "CNPJ inválido! Deve conter 14 dígitos.")
            return
        
        # Verificar se CNPJ já existe
        for cliente in database.listar_clientes():
            if cliente.get('cnpj') == cnpj:
                QMessageBox.warning(dialog, "Atenção", "Este CNPJ já está cadastrado!")
                return
        
        cliente = {
            'nome': razao_social.upper(),  # Campo 'nome' é obrigatório
            'razao_social': razao_social.upper(),
            'nome_fantasia': nome_fantasia.upper(),
            'cnpj': cnpj,
            'ie': input_ie.text().strip().upper(),
            'im': input_im.text().strip().upper(),
            'cep': input_cep.text().strip(),
            'rua': input_rua.text().strip().upper(),
            'numero': input_numero.text().strip(),
            'complemento': input_complemento.text().strip().upper(),
            'bairro': input_bairro.text().strip().upper(),
            'cidade': input_cidade.text().strip().upper(),
            'estado': input_estado.currentText(),
            'telefone': input_contato.text().strip(),
            'contato': input_contato.text().strip(),
            'email': input_email.text().strip().lower(),
            'endereco': f"{input_rua.text().strip().upper()}, {input_numero.text().strip()}",
            'documento': cnpj  # documento é o CNPJ
        }
        
        try:
            database.adicionar_cliente(cliente)
            dialog.accept()
            QMessageBox.information(self, "Sucesso", "Cliente cadastrado com sucesso!")
            self.show_clientes()  # Atualizar tela de clientes
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao cadastrar cliente: {str(e)}")
    
    def dialog_editar_cliente(self, cliente, index):
        """Diálogo para editar um cliente existente"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Cliente")
        dialog.resize(980, 780)
        dialog.setStyleSheet("QDialog { background-color: white; }")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(40, 30, 40, 20)
        layout.setSpacing(10)
        
        # Formulário direto no layout
        form = QVBoxLayout()
        
        # Estilo para labels
        label_style = "color: #2c3e50; font-weight: bold; font-size: 13px; margin-top: 5px;"
        
        # Razão Social
        label_rs = QLabel("*Razão Social:")
        label_rs.setStyleSheet(label_style)
        form.addWidget(label_rs)
        input_razao_social = UpperCaseLineEdit()
        input_razao_social.setText(cliente.get('razao_social', cliente.get('nome', '')))
        form.addWidget(input_razao_social)
        
        # Nome Fantasia
        label_nf = QLabel("*Nome Fantasia:")
        label_nf.setStyleSheet(label_style)
        form.addWidget(label_nf)
        input_nome_fantasia = UpperCaseLineEdit()
        input_nome_fantasia.setText(cliente.get('nome_fantasia', ''))
        form.addWidget(input_nome_fantasia)
        
        # CNPJ
        label_cnpj = QLabel("*CNPJ:")
        label_cnpj.setStyleSheet(label_style)
        form.addWidget(label_cnpj)
        input_cnpj = UpperCaseLineEdit()
        input_cnpj.setText(cliente.get('cnpj', ''))
        input_cnpj.setPlaceholderText("00.000.000/0000-00")
        form.addWidget(input_cnpj)
        
        # Inscrição Estadual
        label_ie = QLabel("Inscrição Estadual:")
        label_ie.setStyleSheet(label_style)
        form.addWidget(label_ie)
        input_ie = UpperCaseLineEdit()
        input_ie.setText(cliente.get('ie', ''))
        form.addWidget(input_ie)
        
        # Inscrição Municipal
        label_im = QLabel("Inscrição Municipal:")
        label_im.setStyleSheet(label_style)
        form.addWidget(label_im)
        input_im = UpperCaseLineEdit()
        input_im.setText(cliente.get('im', ''))
        form.addWidget(input_im)
        
        # Separador de endereço
        separator = QLabel("─── Endereço ───")
        separator.setStyleSheet("color: #3498db; font-weight: bold; margin-top: 15px; font-size: 14px;")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addWidget(separator)
        
        # CEP (primeiro para buscar endereço)
        label_cep = QLabel("CEP:")
        label_cep.setStyleSheet(label_style)
        form.addWidget(label_cep)
        input_cep = UpperCaseLineEdit()
        input_cep.setText(cliente.get('cep', ''))
        input_cep.setPlaceholderText("00000-000")
        form.addWidget(input_cep)
        
        # Rua/Avenida
        label_rua = QLabel("Rua/Avenida:")
        label_rua.setStyleSheet(label_style)
        form.addWidget(label_rua)
        input_rua = UpperCaseLineEdit()
        input_rua.setText(cliente.get('rua', ''))
        form.addWidget(input_rua)
        
        # Número
        label_num = QLabel("Número:")
        label_num.setStyleSheet(label_style)
        form.addWidget(label_num)
        input_numero = UpperCaseLineEdit()
        input_numero.setText(cliente.get('numero', ''))
        form.addWidget(input_numero)
        
        # Complemento
        label_comp = QLabel("Complemento:")
        label_comp.setStyleSheet(label_style)
        form.addWidget(label_comp)
        input_complemento = UpperCaseLineEdit()
        input_complemento.setText(cliente.get('complemento', ''))
        form.addWidget(input_complemento)
        
        # Bairro
        label_bairro = QLabel("Bairro:")
        label_bairro.setStyleSheet(label_style)
        form.addWidget(label_bairro)
        input_bairro = UpperCaseLineEdit()
        input_bairro.setText(cliente.get('bairro', ''))
        form.addWidget(input_bairro)
        
        # Cidade
        label_cidade = QLabel("Cidade:")
        label_cidade.setStyleSheet(label_style)
        form.addWidget(label_cidade)
        input_cidade = UpperCaseLineEdit()
        input_cidade.setText(cliente.get('cidade', ''))
        form.addWidget(input_cidade)
        
        # Estado
        label_estado = QLabel("Estado:")
        label_estado.setStyleSheet(label_style)
        form.addWidget(label_estado)
        input_estado = QComboBox()
        input_estado.addItems(["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"])
        input_estado.setCurrentText(cliente.get('estado', ''))
        input_estado.setMaximumWidth(100)
        input_estado.setStyleSheet("QComboBox { background-color: white; color: black; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        form.addWidget(input_estado)
        
        # Função para buscar endereço pelo CEP
        def buscar_cep():
            cep = input_cep.text().replace("-", "").replace(".", "").strip()
            if len(cep) == 8:
                try:
                    response = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=5)
                    if response.status_code == 200:
                        dados = response.json()
                        if "erro" not in dados:
                            input_rua.setText(dados.get("logradouro", ""))
                            input_bairro.setText(dados.get("bairro", ""))
                            input_cidade.setText(dados.get("localidade", ""))
                            input_estado.setCurrentText(dados.get("uf", ""))
                            QMessageBox.information(dialog, "Sucesso", "Endereço encontrado!")
                        else:
                            QMessageBox.warning(dialog, "Aviso", "CEP não encontrado.")
                except Exception as e:
                    QMessageBox.warning(dialog, "Erro", f"Erro ao buscar CEP: {str(e)}")
        
        input_cep.editingFinished.connect(buscar_cep)
        
        # Separador de contato
        separator2 = QLabel("─── Contato ───")
        separator2.setStyleSheet("color: #3498db; font-weight: bold; margin-top: 15px; font-size: 14px;")
        separator2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addWidget(separator2)
        
        # Contato
        label_contato = QLabel("Contato:")
        label_contato.setStyleSheet(label_style)
        form.addWidget(label_contato)
        input_contato = UpperCaseLineEdit()
        input_contato.setText(cliente.get('contato', cliente.get('telefone', '')))
        input_contato.setPlaceholderText("(00) 00000-0000")
        form.addWidget(input_contato)
        
        # Email
        label_email = QLabel("Email:")
        label_email.setStyleSheet(label_style)
        form.addWidget(label_email)
        input_email = QLineEdit()
        input_email.setText(cliente.get('email', ''))
        input_email.setPlaceholderText("email@exemplo.com")
        form.addWidget(input_email)
        
        layout.addLayout(form)
        layout.addStretch()
        
        # Botões
        buttons = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(dialog.reject)
        buttons.addWidget(btn_cancelar)
        
        btn_salvar = QPushButton("Salvar")
        btn_salvar.setObjectName("primaryButton")
        btn_salvar.clicked.connect(lambda: self.atualizar_cliente(
            dialog, index, input_razao_social, input_nome_fantasia, input_cnpj, input_ie, input_im,
            input_cep, input_rua, input_numero, input_complemento, input_bairro, input_cidade, input_estado,
            input_contato, input_email
        ))
        buttons.addWidget(btn_salvar)
        
        layout.addLayout(buttons)
        dialog.exec()
    
    def atualizar_cliente(self, dialog, index, input_razao_social, input_nome_fantasia, input_cnpj, input_ie, input_im,
                          input_cep, input_rua, input_numero, input_complemento, input_bairro, input_cidade, input_estado,
                          input_contato, input_email):
        """Atualiza os dados de um cliente existente"""
        razao_social = input_razao_social.text().strip()
        nome_fantasia = input_nome_fantasia.text().strip()
        cnpj = input_cnpj.text().strip()
        
        if not razao_social:
            QMessageBox.warning(dialog, "Atenção", "A razão social é obrigatória!")
            return
        
        if not nome_fantasia:
            QMessageBox.warning(dialog, "Atenção", "O nome fantasia é obrigatório!")
            return
        
        if not cnpj:
            QMessageBox.warning(dialog, "Atenção", "O CNPJ é obrigatório!")
            return
        
        # Validar formato básico do CNPJ (apenas números)
        cnpj_numeros = ''.join(filter(str.isdigit, cnpj))
        if len(cnpj_numeros) != 14:
            QMessageBox.warning(dialog, "Atenção", "CNPJ inválido! Deve conter 14 dígitos.")
            return
        
        # Verificar se CNPJ já existe em outro cliente
        for i, cliente in enumerate(database.listar_clientes()):
            if i != index and cliente.get('cnpj') == cnpj:
                QMessageBox.warning(dialog, "Atenção", "Este CNPJ já está cadastrado em outro cliente!")
                return
        
        cliente_atualizado = {
            'razao_social': razao_social.upper(),
            'nome_fantasia': nome_fantasia.upper(),
            'cnpj': cnpj,
            'ie': input_ie.text().strip().upper(),
            'im': input_im.text().strip().upper(),
            'cep': input_cep.text().strip(),
            'rua': input_rua.text().strip().upper(),
            'numero': input_numero.text().strip(),
            'complemento': input_complemento.text().strip().upper(),
            'bairro': input_bairro.text().strip().upper(),
            'cidade': input_cidade.text().strip().upper(),
            'estado': input_estado.currentText(),
            'contato': input_contato.text().strip(),
            'email': input_email.text().strip().lower()
        }
        
        # auto-save in SQLite
        dialog.accept()
        self.show_clientes()  # Atualizar tela de clientes
    
    def excluir_cliente(self, index):
        """Exclui um cliente"""
        clientes = database.listar_clientes()
        if index >= len(clientes):
            return
        cliente = clientes[index]
        nome = cliente.get('razao_social', cliente.get('nome', 'este cliente'))
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar Exclusão")
        msg_box.setText(f"Deseja realmente excluir o cliente '{nome}'?")
        btn_sim = msg_box.addButton("Sim", QMessageBox.ButtonRole.YesRole)
        btn_nao = msg_box.addButton("Não", QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(btn_nao)
        msg_box.exec()
        
        if msg_box.clickedButton() == btn_sim:
            database.excluir_cliente(nome)
            self.show_clientes()  # Atualizar tela de clientes
    
    def show_fornecedores(self):
        """Exibe tela de cadastro de fornecedores"""
        self.clear_content()
        
        # Desmarcar todos os botões
        for btn in self.menu_buttons:
            btn.setChecked(False)
        self.btn_cadastros.setChecked(True)
        
        # Garantir que o submenu está visível
        if not self.submenu_cadastros.isVisible():
            self.submenu_cadastros.setVisible(True)
            self.btn_cadastros.setText("Cadastros                    ▲")
        
        # Título
        title = QLabel("Cadastro de Fornecedores")
        title.setObjectName("pageTitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.content_layout.addWidget(title)
        
        # Adicionar a aba de fornecedores diretamente
        tab_fornecedores = self.create_tab_fornecedores()
        self.content_layout.addWidget(tab_fornecedores)
        self.content_layout.addStretch()
    
    def create_tab_fornecedores(self):
        """Cria a aba de cadastro de fornecedores"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Cabeçalho
        header = QHBoxLayout()
        header_label = QLabel("Gerenciar Fornecedores")
        header_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header.addWidget(header_label)
        header.addStretch()
        
        btn_novo = QPushButton("+ Novo Fornecedor")
        btn_novo.setObjectName("primaryButton")
        btn_novo.clicked.connect(self.dialog_novo_fornecedor)
        header.addWidget(btn_novo)
        
        layout.addLayout(header)
        
        # Tabela de fornecedores
        table = QTableWidget()
        table.setObjectName("dataTable")
        
        # Obter fornecedores do banco de dados
        _fornecedores = database.listar_fornecedores()
        
        table.setColumnCount(13)
        table.setHorizontalHeaderLabels([
            "Razão Social", "Nome Fantasia", "CNPJ", "IE", "IM", 
            "Rua", "Número", "Bairro", "Cidade", "CEP", "Contato", "Email", "Ações"
        ])
        table.setRowCount(len(_fornecedores))
        vheader = table.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        
        for i, fornecedor in enumerate(database.listar_fornecedores()):
            # Alternar cores das linhas (cinza e branco)
            cor_fundo = QColor("#e0e0e0") if i % 2 == 0 else QColor("#ffffff")
            
            item_razao = QTableWidgetItem(fornecedor.get('razao_social', ''))
            item_razao.setBackground(cor_fundo)
            item_razao.setForeground(QColor("#000000"))
            table.setItem(i, 0, item_razao)
            
            item_fantasia = QTableWidgetItem(fornecedor.get('nome_fantasia', '-'))
            item_fantasia.setBackground(cor_fundo)
            item_fantasia.setForeground(QColor("#000000"))
            table.setItem(i, 1, item_fantasia)
            
            item_cnpj = QTableWidgetItem(fornecedor.get('cnpj', ''))
            item_cnpj.setBackground(cor_fundo)
            item_cnpj.setForeground(QColor("#000000"))
            table.setItem(i, 2, item_cnpj)
            
            item_ie = QTableWidgetItem(fornecedor.get('ie', '-'))
            item_ie.setBackground(cor_fundo)
            item_ie.setForeground(QColor("#000000"))
            table.setItem(i, 3, item_ie)
            
            item_im = QTableWidgetItem(fornecedor.get('im', '-'))
            item_im.setBackground(cor_fundo)
            item_im.setForeground(QColor("#000000"))
            table.setItem(i, 4, item_im)
            
            item_rua = QTableWidgetItem(fornecedor.get('rua', '-'))
            item_rua.setBackground(cor_fundo)
            item_rua.setForeground(QColor("#000000"))
            table.setItem(i, 5, item_rua)
            
            item_numero = QTableWidgetItem(fornecedor.get('numero', '-'))
            item_numero.setBackground(cor_fundo)
            item_numero.setForeground(QColor("#000000"))
            table.setItem(i, 6, item_numero)
            
            item_bairro = QTableWidgetItem(fornecedor.get('bairro', '-'))
            item_bairro.setBackground(cor_fundo)
            item_bairro.setForeground(QColor("#000000"))
            table.setItem(i, 7, item_bairro)
            
            item_cidade = QTableWidgetItem(fornecedor.get('cidade', '-'))
            item_cidade.setBackground(cor_fundo)
            item_cidade.setForeground(QColor("#000000"))
            table.setItem(i, 8, item_cidade)
            
            item_cep = QTableWidgetItem(fornecedor.get('cep', '-'))
            item_cep.setBackground(cor_fundo)
            item_cep.setForeground(QColor("#000000"))
            table.setItem(i, 9, item_cep)
            
            item_contato = QTableWidgetItem(fornecedor.get('contato', '-'))
            item_contato.setBackground(cor_fundo)
            item_contato.setForeground(QColor("#000000"))
            table.setItem(i, 10, item_contato)
            
            item_email = QTableWidgetItem(fornecedor.get('email', '-'))
            item_email.setBackground(cor_fundo)
            item_email.setForeground(QColor("#000000"))
            table.setItem(i, 11, item_email)
            
            # Botões de ação: Editar e Excluir
            actions_widget = QWidget()
            actions_widget.setStyleSheet(f"background-color: {cor_fundo.name()};")
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(3)
            
            btn_editar = QPushButton("✏️")
            btn_editar.setToolTip("Editar fornecedor")
            btn_editar.setMaximumWidth(35)
            btn_editar.setStyleSheet("QPushButton { background-color: transparent; border: 1px solid #ddd; border-radius: 3px; padding: 5px; font-size: 18px; } QPushButton:hover { background-color: #f0f0f0; }")
            btn_editar.clicked.connect(lambda checked=False, f=fornecedor: self.dialog_editar_fornecedor(f, i))
            actions_layout.addWidget(btn_editar)
            
            btn_excluir = QPushButton("✖")
            btn_excluir.setToolTip("Excluir fornecedor")
            btn_excluir.setMaximumWidth(35)
            btn_excluir.setStyleSheet("QPushButton { background-color: transparent; border: 1px solid #ddd; border-radius: 3px; padding: 5px; font-size: 18px; color: #dc3545; font-weight: bold; } QPushButton:hover { background-color: #fee; }")
            btn_excluir.clicked.connect(lambda checked=False, idx=i: self.excluir_fornecedor(idx))
            actions_layout.addWidget(btn_excluir)
            
            table.setCellWidget(i, 12, actions_widget)
        
        # Cabeçalho horizontal - larguras pré-definidas para títulos completos
        header = table.horizontalHeader()
        if header:
            # Definir larguras fixas para cada coluna
            table.setColumnWidth(0, 250)   # Razão Social
            table.setColumnWidth(1, 250)   # Nome Fantasia
            table.setColumnWidth(2, 140)   # CNPJ
            table.setColumnWidth(3, 80)    # IE
            table.setColumnWidth(4, 80)    # IM
            table.setColumnWidth(5, 250)   # Rua
            table.setColumnWidth(6, 80)    # Número
            table.setColumnWidth(7, 120)   # Bairro
            table.setColumnWidth(8, 120)   # Cidade
            table.setColumnWidth(9, 100)   # CEP
            table.setColumnWidth(10, 120)  # Contato
            table.setColumnWidth(11, 200)  # Email
            
            # Configurar modo de redimensionamento
            for col in range(12):
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
            
            # Última coluna preenche espaço restante
            header.setSectionResizeMode(12, QHeaderView.ResizeMode.Stretch)
            header.setStretchLastSection(True)
        
        # Configurar altura das linhas ajustável
        vertical_header = table.verticalHeader()
        if vertical_header:
            vertical_header.setVisible(False)  # Ocultar números das linhas
            vertical_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            vertical_header.setDefaultSectionSize(60)
        
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(table)
        
        return widget
    
    def dialog_novo_fornecedor(self):
        """Diálogo para cadastrar um novo fornecedor"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Novo Fornecedor")
        dialog.resize(980, 780)
        dialog.setStyleSheet("QDialog { background-color: white; }")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(40, 30, 40, 20)
        layout.setSpacing(10)
        
        # Formulário direto no layout
        form = QVBoxLayout()
        
        # Estilo para labels
        label_style = "color: #2c3e50; font-weight: bold; font-size: 13px; margin-top: 5px;"
        
        # Razão Social
        label_rs = QLabel("*Razão Social:")
        label_rs.setStyleSheet(label_style)
        form.addWidget(label_rs)
        input_razao_social = UpperCaseLineEdit()
        form.addWidget(input_razao_social)
        
        # Nome Fantasia
        label_nf = QLabel("*Nome Fantasia:")
        label_nf.setStyleSheet(label_style)
        form.addWidget(label_nf)
        input_nome_fantasia = UpperCaseLineEdit()
        form.addWidget(input_nome_fantasia)
        
        # CNPJ
        label_cnpj = QLabel("*CNPJ:")
        label_cnpj.setStyleSheet(label_style)
        form.addWidget(label_cnpj)
        input_cnpj = UpperCaseLineEdit()
        input_cnpj.setPlaceholderText("00.000.000/0000-00")
        form.addWidget(input_cnpj)
        
        # Inscrição Estadual
        label_ie = QLabel("Inscrição Estadual:")
        label_ie.setStyleSheet(label_style)
        form.addWidget(label_ie)
        input_ie = UpperCaseLineEdit()
        form.addWidget(input_ie)
        
        # Inscrição Municipal
        label_im = QLabel("Inscrição Municipal:")
        label_im.setStyleSheet(label_style)
        form.addWidget(label_im)
        input_im = UpperCaseLineEdit()
        form.addWidget(input_im)
        
        # Separador de endereço
        separator = QLabel("─── Endereço ───")
        separator.setStyleSheet("color: #3498db; font-weight: bold; margin-top: 15px; font-size: 14px;")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addWidget(separator)
        
        # CEP (primeiro para buscar endereço)
        label_cep = QLabel("CEP:")
        label_cep.setStyleSheet(label_style)
        form.addWidget(label_cep)
        input_cep = UpperCaseLineEdit()
        input_cep.setPlaceholderText("00000-000")
        form.addWidget(input_cep)
        
        # Rua/Avenida
        label_rua = QLabel("Rua/Avenida:")
        label_rua.setStyleSheet(label_style)
        form.addWidget(label_rua)
        input_rua = UpperCaseLineEdit()
        form.addWidget(input_rua)
        
        # Número
        label_num = QLabel("Número:")
        label_num.setStyleSheet(label_style)
        form.addWidget(label_num)
        input_numero = UpperCaseLineEdit()
        form.addWidget(input_numero)
        
        # Complemento
        label_comp = QLabel("Complemento:")
        label_comp.setStyleSheet(label_style)
        form.addWidget(label_comp)
        input_complemento = UpperCaseLineEdit()
        form.addWidget(input_complemento)
        
        # Bairro
        label_bairro = QLabel("Bairro:")
        label_bairro.setStyleSheet(label_style)
        form.addWidget(label_bairro)
        input_bairro = UpperCaseLineEdit()
        form.addWidget(input_bairro)
        
        # Cidade
        label_cidade = QLabel("Cidade:")
        label_cidade.setStyleSheet(label_style)
        form.addWidget(label_cidade)
        input_cidade = UpperCaseLineEdit()
        form.addWidget(input_cidade)
        
        # Estado
        label_estado = QLabel("Estado:")
        label_estado.setStyleSheet(label_style)
        form.addWidget(label_estado)
        input_estado = QComboBox()
        input_estado.addItems(["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"])
        input_estado.setMaximumWidth(100)
        input_estado.setStyleSheet("QComboBox { background-color: white; color: black; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        form.addWidget(input_estado)
        
        # Função para buscar endereço pelo CEP
        def buscar_cep():
            cep = input_cep.text().replace("-", "").replace(".", "").strip()
            if len(cep) == 8:
                try:
                    response = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=5)
                    if response.status_code == 200:
                        dados = response.json()
                        if "erro" not in dados:
                            input_rua.setText(dados.get("logradouro", ""))
                            input_bairro.setText(dados.get("bairro", ""))
                            input_cidade.setText(dados.get("localidade", ""))
                            input_estado.setCurrentText(dados.get("uf", ""))
                            QMessageBox.information(dialog, "Sucesso", "Endereço encontrado!")
                        else:
                            QMessageBox.warning(dialog, "Aviso", "CEP não encontrado.")
                except Exception as e:
                    QMessageBox.warning(dialog, "Erro", f"Erro ao buscar CEP: {str(e)}")
        
        input_cep.editingFinished.connect(buscar_cep)
        
        # Separador de contato
        separator2 = QLabel("─── Contato ───")
        separator2.setStyleSheet("color: #3498db; font-weight: bold; margin-top: 15px; font-size: 14px;")
        separator2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addWidget(separator2)
        
        # Contato
        label_contato = QLabel("Contato:")
        label_contato.setStyleSheet(label_style)
        form.addWidget(label_contato)
        input_contato = UpperCaseLineEdit()
        input_contato.setPlaceholderText("(00) 00000-0000")
        form.addWidget(input_contato)
        
        # Email
        label_email = QLabel("Email:")
        label_email.setStyleSheet(label_style)
        form.addWidget(label_email)
        input_email = QLineEdit()
        input_email.setPlaceholderText("email@exemplo.com")
        form.addWidget(input_email)
        
        layout.addLayout(form)
        layout.addStretch()
        
        # Botões
        buttons = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(dialog.reject)
        buttons.addWidget(btn_cancelar)
        
        btn_salvar = QPushButton("Salvar")
        btn_salvar.setObjectName("primaryButton")
        btn_salvar.clicked.connect(lambda: self.salvar_fornecedor(
            dialog, input_razao_social, input_nome_fantasia, input_cnpj, input_ie, input_im,
            input_cep, input_rua, input_numero, input_complemento, input_bairro, input_cidade, input_estado,
            input_contato, input_email
        ))
        buttons.addWidget(btn_salvar)
        
        layout.addLayout(buttons)
        dialog.exec()
    
    def salvar_fornecedor(self, dialog, input_razao_social, input_nome_fantasia, input_cnpj, input_ie, input_im,
                          input_cep, input_rua, input_numero, input_complemento, input_bairro, input_cidade, input_estado,
                          input_contato, input_email):
        """Salva um novo fornecedor"""
        razao_social = input_razao_social.text().strip()
        nome_fantasia = input_nome_fantasia.text().strip()
        cnpj = input_cnpj.text().strip()
        
        if not razao_social:
            QMessageBox.warning(dialog, "Atenção", "A razão social é obrigatória!")
            return
        
        if not nome_fantasia:
            QMessageBox.warning(dialog, "Atenção", "O nome fantasia é obrigatório!")
            return
        
        if not cnpj:
            QMessageBox.warning(dialog, "Atenção", "O CNPJ é obrigatório!")
            return
        
        # Validar formato básico do CNPJ (apenas números)
        cnpj_numeros = ''.join(filter(str.isdigit, cnpj))
        if len(cnpj_numeros) != 14:
            QMessageBox.warning(dialog, "Atenção", "CNPJ inválido! Deve conter 14 dígitos.")
            return
        
        # Verificar se CNPJ já existe
        for fornecedor in database.listar_fornecedores():
            if fornecedor.get('cnpj') == cnpj:
                QMessageBox.warning(dialog, "Atenção", "Este CNPJ já está cadastrado!")
                return
        
        fornecedor = {
            'nome': razao_social.upper(),  # Campo 'nome' é obrigatório
            'razao_social': razao_social.upper(),
            'nome_fantasia': nome_fantasia.upper(),
            'cnpj': cnpj,
            'ie': input_ie.text().strip().upper(),
            'im': input_im.text().strip().upper(),
            'cep': input_cep.text().strip(),
            'rua': input_rua.text().strip().upper(),
            'numero': input_numero.text().strip(),
            'complemento': input_complemento.text().strip().upper(),
            'bairro': input_bairro.text().strip().upper(),
            'cidade': input_cidade.text().strip().upper(),
            'estado': input_estado.currentText(),
            'telefone': input_contato.text().strip(),
            'contato': input_contato.text().strip(),
            'email': input_email.text().strip().lower(),
            'endereco': f"{input_rua.text().strip().upper()}, {input_numero.text().strip()}",
            'documento': cnpj  # documento é o CNPJ
        }
        
        try:
            database.adicionar_fornecedor(fornecedor)
            dialog.accept()
            QMessageBox.information(self, "Sucesso", "Fornecedor cadastrado com sucesso!")
            self.show_fornecedores()  # Atualizar tela de fornecedores
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao cadastrar fornecedor: {str(e)}")
    
    def dialog_editar_fornecedor(self, fornecedor, index):
        """Diálogo para editar um fornecedor existente"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Fornecedor")
        dialog.resize(980, 780)
        dialog.setStyleSheet("QDialog { background-color: white; }")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(40, 30, 40, 20)
        layout.setSpacing(10)
        
        # Formulário direto no layout
        form = QVBoxLayout()
        
        # Estilo para labels
        label_style = "color: #2c3e50; font-weight: bold; font-size: 13px; margin-top: 5px;"
        
        # Razão Social
        label_rs = QLabel("*Razão Social:")
        label_rs.setStyleSheet(label_style)
        form.addWidget(label_rs)
        input_razao_social = UpperCaseLineEdit()
        input_razao_social.setText(fornecedor.get('razao_social', ''))
        form.addWidget(input_razao_social)
        
        # Nome Fantasia
        label_nf = QLabel("*Nome Fantasia:")
        label_nf.setStyleSheet(label_style)
        form.addWidget(label_nf)
        input_nome_fantasia = UpperCaseLineEdit()
        input_nome_fantasia.setText(fornecedor.get('nome_fantasia', ''))
        form.addWidget(input_nome_fantasia)
        
        # CNPJ
        label_cnpj = QLabel("*CNPJ:")
        label_cnpj.setStyleSheet(label_style)
        form.addWidget(label_cnpj)
        input_cnpj = UpperCaseLineEdit()
        input_cnpj.setText(fornecedor.get('cnpj', ''))
        input_cnpj.setPlaceholderText("00.000.000/0000-00")
        form.addWidget(input_cnpj)
        
        # Inscrição Estadual
        label_ie = QLabel("Inscrição Estadual:")
        label_ie.setStyleSheet(label_style)
        form.addWidget(label_ie)
        input_ie = UpperCaseLineEdit()
        input_ie.setText(fornecedor.get('ie', ''))
        form.addWidget(input_ie)
        
        # Inscrição Municipal
        label_im = QLabel("Inscrição Municipal:")
        label_im.setStyleSheet(label_style)
        form.addWidget(label_im)
        input_im = UpperCaseLineEdit()
        input_im.setText(fornecedor.get('im', ''))
        form.addWidget(input_im)
        
        # Separador de endereço
        separator = QLabel("─── Endereço ───")
        separator.setStyleSheet("color: #3498db; font-weight: bold; margin-top: 15px; font-size: 14px;")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addWidget(separator)
        
        # CEP (primeiro para buscar endereço)
        label_cep = QLabel("CEP:")
        label_cep.setStyleSheet(label_style)
        form.addWidget(label_cep)
        input_cep = UpperCaseLineEdit()
        input_cep.setText(fornecedor.get('cep', ''))
        input_cep.setPlaceholderText("00000-000")
        form.addWidget(input_cep)
        
        # Rua/Avenida
        label_rua = QLabel("Rua/Avenida:")
        label_rua.setStyleSheet(label_style)
        form.addWidget(label_rua)
        input_rua = UpperCaseLineEdit()
        input_rua.setText(fornecedor.get('rua', ''))
        form.addWidget(input_rua)
        
        # Número
        label_num = QLabel("Número:")
        label_num.setStyleSheet(label_style)
        form.addWidget(label_num)
        input_numero = UpperCaseLineEdit()
        input_numero.setText(fornecedor.get('numero', ''))
        form.addWidget(input_numero)
        
        # Complemento
        label_comp = QLabel("Complemento:")
        label_comp.setStyleSheet(label_style)
        form.addWidget(label_comp)
        input_complemento = UpperCaseLineEdit()
        input_complemento.setText(fornecedor.get('complemento', ''))
        form.addWidget(input_complemento)
        
        # Bairro
        label_bairro = QLabel("Bairro:")
        label_bairro.setStyleSheet(label_style)
        form.addWidget(label_bairro)
        input_bairro = UpperCaseLineEdit()
        input_bairro.setText(fornecedor.get('bairro', ''))
        form.addWidget(input_bairro)
        
        # Cidade
        label_cidade = QLabel("Cidade:")
        label_cidade.setStyleSheet(label_style)
        form.addWidget(label_cidade)
        input_cidade = UpperCaseLineEdit()
        input_cidade.setText(fornecedor.get('cidade', ''))
        form.addWidget(input_cidade)
        
        # Estado
        label_estado = QLabel("Estado:")
        label_estado.setStyleSheet(label_style)
        form.addWidget(label_estado)
        input_estado = QComboBox()
        input_estado.addItems(["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"])
        input_estado.setCurrentText(fornecedor.get('estado', ''))
        input_estado.setMaximumWidth(100)
        input_estado.setStyleSheet("QComboBox { background-color: white; color: black; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        form.addWidget(input_estado)
        
        # Função para buscar endereço pelo CEP
        def buscar_cep():
            cep = input_cep.text().replace("-", "").replace(".", "").strip()
            if len(cep) == 8:
                try:
                    response = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=5)
                    if response.status_code == 200:
                        dados = response.json()
                        if "erro" not in dados:
                            input_rua.setText(dados.get("logradouro", ""))
                            input_bairro.setText(dados.get("bairro", ""))
                            input_cidade.setText(dados.get("localidade", ""))
                            input_estado.setCurrentText(dados.get("uf", ""))
                            QMessageBox.information(dialog, "Sucesso", "Endereço encontrado!")
                        else:
                            QMessageBox.warning(dialog, "Aviso", "CEP não encontrado.")
                except Exception as e:
                    QMessageBox.warning(dialog, "Erro", f"Erro ao buscar CEP: {str(e)}")
        
        input_cep.editingFinished.connect(buscar_cep)
        
        # Separador de contato
        separator2 = QLabel("─── Contato ───")
        separator2.setStyleSheet("color: #3498db; font-weight: bold; margin-top: 15px; font-size: 14px;")
        separator2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addWidget(separator2)
        
        # Contato
        label_contato = QLabel("Contato:")
        label_contato.setStyleSheet(label_style)
        form.addWidget(label_contato)
        input_contato = UpperCaseLineEdit()
        input_contato.setText(fornecedor.get('contato', ''))
        input_contato.setPlaceholderText("(00) 00000-0000")
        form.addWidget(input_contato)
        
        # Email
        label_email = QLabel("Email:")
        label_email.setStyleSheet(label_style)
        form.addWidget(label_email)
        input_email = QLineEdit()
        input_email.setText(fornecedor.get('email', ''))
        input_email.setPlaceholderText("email@exemplo.com")
        form.addWidget(input_email)
        
        layout.addLayout(form)
        layout.addStretch()
        
        # Botões
        buttons = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(dialog.reject)
        buttons.addWidget(btn_cancelar)
        
        btn_salvar = QPushButton("Salvar")
        btn_salvar.setObjectName("primaryButton")
        btn_salvar.clicked.connect(lambda: self.atualizar_fornecedor(
            dialog, index, input_razao_social, input_nome_fantasia, input_cnpj, input_ie, input_im,
            input_cep, input_rua, input_numero, input_complemento, input_bairro, input_cidade, input_estado,
            input_contato, input_email
        ))
        buttons.addWidget(btn_salvar)
        
        layout.addLayout(buttons)
        dialog.exec()
    
    def atualizar_fornecedor(self, dialog, index, input_razao_social, input_nome_fantasia, input_cnpj, input_ie, input_im,
                             input_cep, input_rua, input_numero, input_complemento, input_bairro, input_cidade, input_estado,
                             input_contato, input_email):
        """Atualiza os dados de um fornecedor existente"""
        razao_social = input_razao_social.text().strip()
        nome_fantasia = input_nome_fantasia.text().strip()
        cnpj = input_cnpj.text().strip()
        
        if not razao_social:
            QMessageBox.warning(dialog, "Atenção", "A razão social é obrigatória!")
            return
        
        if not nome_fantasia:
            QMessageBox.warning(dialog, "Atenção", "O nome fantasia é obrigatório!")
            return
        
        if not cnpj:
            QMessageBox.warning(dialog, "Atenção", "O CNPJ é obrigatório!")
            return
        
        # Validar formato básico do CNPJ (apenas números)
        cnpj_numeros = ''.join(filter(str.isdigit, cnpj))
        if len(cnpj_numeros) != 14:
            QMessageBox.warning(dialog, "Atenção", "CNPJ inválido! Deve conter 14 dígitos.")
            return
        
        # Verificar se CNPJ já existe em outro fornecedor
        for i, fornecedor in enumerate(database.listar_fornecedores()):
            if i != index and fornecedor.get('cnpj') == cnpj:
                QMessageBox.warning(dialog, "Atenção", "Este CNPJ já está cadastrado em outro fornecedor!")
                return
        
        fornecedor_atualizado = {
            'razao_social': razao_social.upper(),
            'nome_fantasia': nome_fantasia.upper(),
            'cnpj': cnpj,
            'ie': input_ie.text().strip().upper(),
            'im': input_im.text().strip().upper(),
            'cep': input_cep.text().strip(),
            'rua': input_rua.text().strip().upper(),
            'numero': input_numero.text().strip(),
            'complemento': input_complemento.text().strip().upper(),
            'bairro': input_bairro.text().strip().upper(),
            'cidade': input_cidade.text().strip().upper(),
            'estado': input_estado.currentText(),
            'contato': input_contato.text().strip(),
            'email': input_email.text().strip().lower()
        }
        
        # auto-save in SQLite
        dialog.accept()
        self.show_fornecedores()  # Atualizar tela de fornecedores
    
    def excluir_fornecedor(self, index):
        """Exclui um fornecedor"""
        fornecedores = database.listar_fornecedores()
        if index >= len(fornecedores):
            return
        fornecedor = fornecedores[index]
        nome = fornecedor.get('razao_social', 'este fornecedor')
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar Exclusão")
        msg_box.setText(f"Deseja realmente excluir o fornecedor '{nome}'?")
        btn_sim = msg_box.addButton("Sim", QMessageBox.ButtonRole.YesRole)
        btn_nao = msg_box.addButton("Não", QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(btn_nao)
        msg_box.exec()
        
        if msg_box.clickedButton() == btn_sim:
            pass  # já excluído com database.excluir_fornecedor
            # auto-save in SQLite
            self.show_fornecedores()
    
    def editar_categoria_selecionada(self, table, tipo: TipoLancamento):
        """Edita a categoria selecionada na tabela"""
        selected_rows = table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Atenção", "Selecione uma categoria para editar!")
            return
        
        row = selected_rows[0].row()
        nome_categoria = table.item(row, 0).text()
        categoria = next((c for c in database.listar_categorias() if c.nome == nome_categoria), None)
        
        if not categoria:
            return
        
        self.dialog_editar_categoria(categoria)
    
    def excluir_categoria_selecionada(self, table):
        """Exclui a categoria selecionada na tabela"""
        selected_rows = table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Atenção", "Selecione uma categoria para excluir!")
            return
        
        row = selected_rows[0].row()
        nome_categoria = table.item(row, 0).text()
        self.excluir_categoria(nome_categoria)
    
    def dialog_editar_categoria(self, categoria):
        """Diálogo para editar uma categoria existente"""
        dialog = QDialog(self)
        tipo_texto = "Receita" if categoria.tipo == TipoLancamento.RECEITA else "Despesa"
        dialog.setWindowTitle(f"Editar Categoria de {tipo_texto}")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(200)
        
        layout = QVBoxLayout(dialog)
        
        # Label do nome
        nome_label = QLabel("Nome da Categoria:")
        nome_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(nome_label)
        
        # Campo para editar o nome
        nome_input = UpperCaseLineEdit()
        nome_input.setText(categoria.nome)
        layout.addWidget(nome_input)
        
        layout.addStretch()
        
        # Botões
        btns_layout = QHBoxLayout()
        btns_layout.addStretch()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(dialog.reject)
        btns_layout.addWidget(btn_cancelar)
        
        btn_salvar = QPushButton("Salvar")
        btn_salvar.setObjectName("primaryButton")
        btns_layout.addWidget(btn_salvar)
        
        layout.addLayout(btns_layout)
        
        def salvar():
            novo_nome = nome_input.text().strip()
            if not novo_nome:
                QMessageBox.warning(dialog, "Erro", "O nome da categoria não pode estar vazio!")
                return
            
            # Verificar se já existe uma categoria com o novo nome (exceto a própria)
            categorias = database.listar_categorias()
            if any(c.nome == novo_nome and c.nome != categoria.nome for c in categorias):
                QMessageBox.warning(dialog, "Erro", f"Já existe uma categoria chamada '{novo_nome}'!")
                return
            
            # Atualizar o nome da categoria no banco
            nome_antigo = categoria.nome
            try:
                database.atualizar_nome_categoria(nome_antigo, novo_nome)
                QMessageBox.information(dialog, "Sucesso", "Categoria atualizada com sucesso!")
                dialog.accept()
                # Recarregar a tela de categorias
                self.show_cadastros(0 if categoria.tipo == TipoLancamento.RECEITA else 1)
            except Exception as e:
                QMessageBox.critical(dialog, "Erro", f"Erro ao atualizar categoria: {str(e)}")
        
        btn_salvar.clicked.connect(salvar)
        dialog.exec()
    
    def dialog_nova_categoria(self, tipo: TipoLancamento):
        """Diálogo para adicionar nova categoria"""
        dialog = QDialog(self)
        tipo_texto = "Receita" if tipo == TipoLancamento.RECEITA else "Despesa"
        dialog.setWindowTitle(f"Nova Categoria de {tipo_texto}")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)
        
        main_layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        
        nome_input = UpperCaseLineEdit()
        
        form_layout.addRow("Nome da Categoria:", nome_input)
        
        main_layout.addLayout(form_layout)
        
        # Seção de subcategorias
        subcat_label = QLabel("Subcategorias:")
        subcat_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        main_layout.addWidget(subcat_label)
        
        # Lista de subcategorias
        subcategorias_list = QListWidget()
        subcategorias_list.setMaximumHeight(150)
        subcategorias_list.setStyleSheet("QListWidget { background-color: white; }")
        main_layout.addWidget(subcategorias_list)
        
        # Botões para gerenciar subcategorias
        subcat_buttons = QHBoxLayout()
        subcat_buttons.addStretch()
        
        btn_add_subcat = QPushButton("+ Adicionar Subcategoria")
        btn_add_subcat.setObjectName("successButton")
        subcat_buttons.addWidget(btn_add_subcat)
        
        btn_remove_subcat = QPushButton("Remover Selecionada")
        btn_remove_subcat.setObjectName("dangerButton")
        subcat_buttons.addWidget(btn_remove_subcat)
        
        main_layout.addLayout(subcat_buttons)
        
        # Funções para gerenciar subcategorias
        subcategorias_temp = []
        
        def adicionar_subcategoria():
            from PyQt6.QtWidgets import QInputDialog
            nome_sub, ok = QInputDialog.getText(dialog, "Nova Subcategoria", "Nome da subcategoria:")
            if ok and nome_sub.strip():
                nome_sub = nome_sub.strip()
                if nome_sub in subcategorias_temp:
                    QMessageBox.warning(dialog, "Atenção", "Esta subcategoria já foi adicionada!")
                else:
                    subcategorias_temp.append(nome_sub)
                    subcategorias_list.addItem(nome_sub)
        
        def remover_subcategoria():
            current_item = subcategorias_list.currentItem()
            if current_item:
                nome_sub = current_item.text()
                subcategorias_temp.remove(nome_sub)
                subcategorias_list.takeItem(subcategorias_list.currentRow())
            else:
                QMessageBox.warning(dialog, "Atenção", "Selecione uma subcategoria para remover!")
        
        btn_add_subcat.clicked.connect(adicionar_subcategoria)
        btn_remove_subcat.clicked.connect(remover_subcategoria)
        
        # Botões finais
        btns_layout = QHBoxLayout()
        btns_layout.addStretch()
        btn_cancelar = QPushButton("Cancelar")
        btn_salvar = QPushButton("Salvar")
        btn_salvar.setObjectName("primaryButton")
        
        btns_layout.addWidget(btn_cancelar)
        btns_layout.addWidget(btn_salvar)
        main_layout.addLayout(btns_layout)
        
        btn_cancelar.clicked.connect(dialog.reject)
        
        def salvar():
            try:
                nome = nome_input.text().strip()
                
                if not nome:
                    QMessageBox.warning(self, "Atenção", "O nome da categoria é obrigatório!")
                    return
                
                # Verificar se já existe
                if any(c.nome == nome for c in database.listar_categorias()):
                    QMessageBox.warning(self, "Atenção", "Já existe uma categoria com este nome!")
                    return
                
                # Adicionar categoria com subcategorias
                from models import Categoria
                nova_categoria = Categoria(nome=nome, tipo=tipo, descricao="", subcategorias=subcategorias_temp.copy())
                database.adicionar_categoria(nova_categoria)
                
                dialog.accept()
                # Mostrar a aba correta: 0 para receitas, 1 para despesas
                aba_index = 0 if tipo == TipoLancamento.RECEITA else 1
                self.show_cadastros(aba_index)
                num_sub = len(subcategorias_temp)
                msg = f"Categoria de {tipo_texto} adicionada com sucesso!"
                if num_sub > 0:
                    msg += f"\n{num_sub} subcategoria(s) adicionada(s)."
                QMessageBox.information(self, "Sucesso", msg)
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao adicionar categoria: {str(e)}")
        
        btn_salvar.clicked.connect(salvar)
        dialog.exec()
    
    def dialog_gerenciar_subcategorias(self, nome_categoria):
        """Diálogo para gerenciar subcategorias de uma categoria"""
        categoria = next((c for c in database.listar_categorias() if c.nome == nome_categoria), None)
        if not categoria:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Gerenciar Subcategorias - {nome_categoria}")
        dialog.setMinimumWidth(750)
        dialog.setMinimumHeight(550)
        dialog.resize(750, 550)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Cabeçalho
        header = QHBoxLayout()
        header_label = QLabel(f"Subcategorias de '{nome_categoria}'")
        header_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header.addWidget(header_label)
        header.addStretch()
        
        btn_nova_sub = QPushButton("+ Nova Subcategoria")
        btn_nova_sub.setObjectName("primaryButton")
        header.addWidget(btn_nova_sub)
        
        layout.addLayout(header)
        
        # Tabela de subcategorias
        table = QTableWidget()
        table.setObjectName("dataTable")
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Nome da Subcategoria", "Ações"])
        vheader = table.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        
        def atualizar_tabela():
            table.setRowCount(len(categoria.subcategorias))
            for i, subcat in enumerate(categoria.subcategorias):
                item = QTableWidgetItem(subcat)
                
                # Alternar cores das linhas (cinza e branco)
                if i % 2 == 0:
                    item.setBackground(QColor("#e0e0e0"))  # Cinza mais escuro
                else:
                    item.setBackground(QColor("#ffffff"))  # Branco
                
                # Definir cor do texto como preto
                item.setForeground(QColor("#000000"))
                
                table.setItem(i, 0, item)
                
                # Botões de ação: Editar e Excluir
                actions_widget = QWidget()
                
                # Aplicar mesma cor de fundo nos botões
                if i % 2 == 0:
                    actions_widget.setStyleSheet("background-color: #e0e0e0;")
                else:
                    actions_widget.setStyleSheet("background-color: #ffffff;")
                
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2, 2, 2, 2)
                actions_layout.setSpacing(3)
                
                btn_editar_sub = QPushButton("✏️")
                btn_editar_sub.setToolTip("Editar subcategoria")
                btn_editar_sub.setFixedSize(26, 26)
                btn_editar_sub.setStyleSheet("QPushButton { background-color: #3498db; color: white; border: none; border-radius: 3px; padding: 0px; font-size: 11px; } QPushButton:hover { background-color: #2980b9; }")
                btn_editar_sub.clicked.connect(lambda checked=False, s=subcat: editar_subcategoria(s))
                actions_layout.addWidget(btn_editar_sub)
                
                btn_excluir_sub = QPushButton("✖")
                btn_excluir_sub.setToolTip("Excluir subcategoria")
                btn_excluir_sub.setFixedSize(26, 26)
                btn_excluir_sub.setStyleSheet("QPushButton { background-color: #dc3545; color: white; border: none; border-radius: 3px; padding: 0px; font-size: 11px; font-weight: bold; } QPushButton:hover { background-color: #c82333; }")
                btn_excluir_sub.clicked.connect(lambda checked=False, s=subcat: excluir_subcategoria(s))
                actions_layout.addWidget(btn_excluir_sub)
                
                actions_layout.addStretch()
                
                table.setCellWidget(i, 1, actions_widget)
                table.setRowHeight(i, 50)
            
            header = table.horizontalHeader()
            if header:
                # Primeira coluna estica, segunda coluna (Ações) tem tamanho fixo
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
                header.setMinimumSectionSize(90)
            
            # Ocultar cabeçalho vertical (números das linhas)
            v_header = table.verticalHeader()
            if v_header:
                v_header.setVisible(False)
        
        def adicionar_subcategoria():
            from PyQt6.QtWidgets import QInputDialog
            nome_sub, ok = QInputDialog.getText(dialog, "Nova Subcategoria", "Nome da subcategoria:")
            if ok and nome_sub.strip():
                nome_sub = nome_sub.strip()
                if nome_sub in categoria.subcategorias:
                    QMessageBox.warning(dialog, "Atenção", "Esta subcategoria já existe!")
                else:
                    categoria.adicionar_subcategoria(nome_sub)
                    # auto-save in SQLite
                    atualizar_tabela()
        
        def editar_subcategoria(nome_sub_antigo):
            from PyQt6.QtWidgets import QInputDialog, QLineEdit, QVBoxLayout, QLabel
            # Criar diálogo customizado com campo maior
            edit_dialog = QDialog(dialog)
            edit_dialog.setWindowTitle("Editar Subcategoria")
            edit_dialog.setMinimumWidth(500)
            
            layout = QVBoxLayout(edit_dialog)
            
            label = QLabel("Novo nome da subcategoria:")
            layout.addWidget(label)
            
            line_edit = UpperCaseLineEdit()
            line_edit.setText(nome_sub_antigo)
            line_edit.setMinimumWidth(480)
            layout.addWidget(line_edit)
            
            # Botões
            btns_layout = QHBoxLayout()
            btn_ok = QPushButton("OK")
            btn_ok.setObjectName("primaryButton")
            btn_cancel = QPushButton("Cancel")
            btns_layout.addStretch()
            btns_layout.addWidget(btn_ok)
            btns_layout.addWidget(btn_cancel)
            layout.addLayout(btns_layout)
            
            btn_cancel.clicked.connect(edit_dialog.reject)
            btn_ok.clicked.connect(edit_dialog.accept)
            
            if edit_dialog.exec() == QDialog.DialogCode.Accepted:
                nome_novo = line_edit.text().strip()
                if nome_novo:
                    if nome_novo != nome_sub_antigo:
                        if nome_novo in categoria.subcategorias:
                            QMessageBox.warning(dialog, "Atenção", "Já existe uma subcategoria com este nome!")
                        else:
                            # Remover antiga e adicionar nova
                            categoria.remover_subcategoria(nome_sub_antigo)
                            categoria.adicionar_subcategoria(nome_novo)
                            # auto-save in SQLite
                            atualizar_tabela()
        
        def excluir_subcategoria(nome_sub):
            msg_box = QMessageBox(dialog)
            msg_box.setWindowTitle("Confirmar Exclusão")
            msg_box.setText(f"Deseja realmente excluir a subcategoria '{nome_sub}'?")
            btn_sim = msg_box.addButton("Sim", QMessageBox.ButtonRole.YesRole)
            btn_nao = msg_box.addButton("Não", QMessageBox.ButtonRole.NoRole)
            msg_box.setDefaultButton(btn_nao)
            msg_box.exec()
            
            if msg_box.clickedButton() == btn_sim:
                categoria.remover_subcategoria(nome_sub)
                # auto-save in SQLite
                atualizar_tabela()
        
        btn_nova_sub.clicked.connect(adicionar_subcategoria)
        
        atualizar_tabela()
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers   )
        layout.addWidget(table, 1)  # Stretch factor 1 para preencher espaço
        
        # Botão fechar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_fechar = QPushButton("Fechar")
        btn_fechar.setObjectName("primaryButton")
        btn_fechar.setMinimumWidth(100)
        btn_fechar.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_fechar)
        layout.addLayout(btn_layout)
        
        dialog.exec()
        # Atualizar tela principal mantendo a aba correta
        tab_index = 0 if categoria.tipo == TipoLancamento.RECEITA else 1
        self.show_cadastros(tab_index)
    
    def excluir_categoria(self, nome):
        """Exclui uma categoria"""
        # Verificar se há lançamentos usando esta categoria
        lancamentos = database.listar_lancamentos()
        lancamentos_categoria = [l for l in lancamentos if l.categoria == nome]
        
        if lancamentos_categoria:
            QMessageBox.warning(
                self, "Atenção",
                f"Não é possível excluir esta categoria pois existem {len(lancamentos_categoria)} lançamento(s) associado(s) a ela."
            )
            return
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar Exclusão")
        msg_box.setText(f"Deseja realmente excluir a categoria '{nome}'?")
        btn_sim = msg_box.addButton("Sim", QMessageBox.ButtonRole.YesRole)
        btn_nao = msg_box.addButton("Não", QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(btn_nao)
        msg_box.exec()
        
        if msg_box.clickedButton() == btn_sim:
            if any(c.nome == nome for c in database.listar_categorias()):
                categoria = next((c for c in database.listar_categorias() if c.nome == nome), None)
                if not categoria:
                    return
                # Mostrar a aba correta: 0 para receitas, 1 para despesas
                aba_index = 0 if categoria.tipo == TipoLancamento.RECEITA else 1
                # Excluir categoria do banco
                # Já foi excluído acima com database.excluir_categoria(nome)
                self.show_cadastros(aba_index)
                QMessageBox.information(self, "Sucesso", "Categoria excluída com sucesso!")
    
    def show_fluxo_caixa(self):
        """Exibe fluxo de caixa"""
        self.clear_content()
        
        # Desmarcar todos os botões
        for btn in self.menu_buttons:
            btn.setChecked(False)
        self.btn_fluxo.setChecked(True)
        
        # Header com título e botões
        header = QHBoxLayout()
        title = QLabel("Fluxo de Caixa")
        title.setObjectName("pageTitle")
        title.setFont(QFont("Segoe UI", self.scale_size(24), QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        
        # Botões de exportação no header
        btn_exportar_pdf = QPushButton("📄 Exportar PDF")
        btn_exportar_pdf.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 70px;
                height: 28px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        btn_exportar_pdf.clicked.connect(self.exportar_fluxo_pdf)
        header.addWidget(btn_exportar_pdf)
        
        btn_exportar_excel = QPushButton("📊 Exportar Excel")
        btn_exportar_excel.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 70px;
                height: 28px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        btn_exportar_excel.clicked.connect(self.exportar_fluxo_excel)
        header.addWidget(btn_exportar_excel)
        
        btn_atualizar = QPushButton("🔄 Atualizar")
        btn_atualizar.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 70px;
                height: 28px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        btn_atualizar.clicked.connect(self.show_fluxo_caixa)
        header.addWidget(btn_atualizar)
        
        self.content_layout.addLayout(header)
        
        # Barra de filtros
        filtros_frame = QFrame()
        filtros_frame.setObjectName("filterFrame")
        filtros_layout = QHBoxLayout(filtros_frame)
        filtros_layout.setSpacing(15)
        
        # Filtros de data (De e Até)
        self.label_data_de = QLabel("De:")
        filtros_layout.addWidget(self.label_data_de)
        self.date_fluxo_de = QDateEdit()
        self.date_fluxo_de.setCalendarPopup(True)
        self.date_fluxo_de.setDisplayFormat("dd/MM/yyyy")
        self.date_fluxo_de.setDate(QDate.currentDate().addDays(-30))
        self.date_fluxo_de.setMinimumWidth(120)
        self.date_fluxo_de.setStyleSheet("QDateEdit { background-color: white; color: black; padding: 3px; }")
        self.date_fluxo_de.dateChanged.connect(self.atualizar_fluxo_caixa)
        filtros_layout.addWidget(self.date_fluxo_de)
        
        self.label_data_ate = QLabel("Até:")
        filtros_layout.addWidget(self.label_data_ate)
        self.date_fluxo_ate = QDateEdit()
        self.date_fluxo_ate.setCalendarPopup(True)
        self.date_fluxo_ate.setDisplayFormat("dd/MM/yyyy")
        self.date_fluxo_ate.setDate(QDate.currentDate())
        self.date_fluxo_ate.setMinimumWidth(120)
        self.date_fluxo_ate.setStyleSheet("QDateEdit { background-color: white; color: black; padding: 3px; }")
        self.date_fluxo_ate.dateChanged.connect(self.atualizar_fluxo_caixa)
        filtros_layout.addWidget(self.date_fluxo_ate)
        
        # Botão de pesquisa por data
        btn_filtrar_data_fluxo = QPushButton("🔍")
        btn_filtrar_data_fluxo.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ddd;
                padding: 8px 12px;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-color: #999;
            }
        """)
        btn_filtrar_data_fluxo.setToolTip("Filtrar por período")
        btn_filtrar_data_fluxo.clicked.connect(self.atualizar_fluxo_caixa)
        filtros_layout.addWidget(btn_filtrar_data_fluxo)
        
        # Filtro por banco
        filtros_layout.addWidget(QLabel("Banco:"))
        self.combo_banco_fluxo = QComboBox()
        self.combo_banco_fluxo.addItem("Todos")
        bancos = list(set([conta.banco for conta in database.listar_contas()]))
        self.combo_banco_fluxo.addItems(sorted(bancos))
        self.combo_banco_fluxo.setMinimumWidth(150)
        self.combo_banco_fluxo.setStyleSheet("QComboBox { background-color: white; color: black; min-width: 150px; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        self.combo_banco_fluxo.currentTextChanged.connect(self.atualizar_fluxo_caixa)
        filtros_layout.addWidget(self.combo_banco_fluxo)
        
        # Botão Resumo por Categoria
        btn_resumo_categoria = QPushButton("📊 Resumo por Categoria")
        btn_resumo_categoria.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 70px;
                height: 28px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        btn_resumo_categoria.clicked.connect(self.mostrar_resumo_categoria)
        filtros_layout.addWidget(btn_resumo_categoria)
        
        filtros_layout.addStretch()
        self.content_layout.addWidget(filtros_frame)
        
        # Tabela de lançamentos liquidados
        self.liquidados_label = QLabel("Lançamentos Liquidados")
        self.liquidados_label.setFont(QFont("Segoe UI", self.scale_size(16), QFont.Weight.Bold))
        self.liquidados_label.setStyleSheet("margin-top: 20px;")
        self.content_layout.addWidget(self.liquidados_label)
        
        self.table_fluxo = QTableWidget()
        self.table_fluxo.setColumnCount(8)
        self.table_fluxo.setHorizontalHeaderLabels(["Tipo", "Data Liquidação", "Descrição", "Categoria", "Subcategoria", "Cliente/Fornecedor", "Entrada", "Saída"])
        self.table_fluxo.setShowGrid(False)
        self.table_fluxo.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_fluxo.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table_fluxo.setAlternatingRowColors(True)
        self.table_fluxo.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #d0d0d0;
                background-color: white;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        self.table_fluxo.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        vheader = self.table_fluxo.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        
        h_header = self.table_fluxo.horizontalHeader()
        if h_header is not None:
            h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            h_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
            h_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
            h_header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
            h_header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
            h_header.resizeSection(0, self.scale_size(80))   # Tipo
            h_header.resizeSection(1, self.scale_size(110))  # Data Liquidação
            h_header.resizeSection(2, self.scale_size(200))  # Descrição
            h_header.resizeSection(3, self.scale_size(130))  # Categoria
            h_header.resizeSection(4, self.scale_size(130))  # Subcategoria
            h_header.resizeSection(6, self.scale_size(110))  # Entrada
            h_header.resizeSection(7, self.scale_size(110))  # Saída
        
        v_header = self.table_fluxo.verticalHeader()
        if v_header is not None:
            v_header.setVisible(False)
            v_header.setDefaultSectionSize(45)
        
        # Adicionar scrollbar customizado
        scrollbar_fluxo = QScrollBar()
        scrollbar_fluxo.setStyleSheet(f"""
            QScrollBar:vertical {{
                border: none;
                background: #f0f0f0;
                width: {self.scale_size(10)}px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: #2196F3;
                min-height: 20px;
                border-radius: {self.scale_size(5)}px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #1976D2;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        self.table_fluxo.setVerticalScrollBar(scrollbar_fluxo)
        self.table_fluxo.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        self.table_fluxo.setMinimumHeight(self.scale_size(500))
        font_size = self.scale_size(11)
        self.table_fluxo.setStyleSheet(f"""
            QTableWidget {{ 
                background-color: white;
                alternate-background-color: #d0d0d0;
                font-size: {font_size}px;
                gridline-color: #e0e0e0;
                border: none;
                border-radius: 5px;
            }} 
            QHeaderView::section {{ 
                background-color: #f8f9fa;
                color: #495057;
                font-size: {font_size}px;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
                text-align: left;
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }}
            QTableWidget::item:selected {{
                background-color: #e3f2fd;
                color: #1976d2;
            }}
            QTableWidget::item:hover {{
                background-color: #f5f5f5;
            }}
        """)
        self.content_layout.addWidget(self.table_fluxo)
        
        # Frame de totais
        totais_frame = QFrame()
        totais_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        totais_layout = QHBoxLayout(totais_frame)
        
        # Saldo Inicial
        self.label_saldo_inicial = QLabel("Saldo Inicial: R$ 0,00")
        self.label_saldo_inicial.setStyleSheet("""
            QLabel {
                color: black;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        totais_layout.addWidget(self.label_saldo_inicial)
        
        totais_layout.addStretch()
        
        # Total de Entradas
        self.label_total_entradas = QLabel("Total Entradas: R$ 0,00")
        self.label_total_entradas.setStyleSheet("""
            QLabel {
                color: black;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        totais_layout.addWidget(self.label_total_entradas)
        
        totais_layout.addStretch()
        
        # Total de Saídas
        self.label_total_saidas = QLabel("Total Saídas: R$ 0,00")
        self.label_total_saidas.setStyleSheet("""
            QLabel {
                color: black;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        totais_layout.addWidget(self.label_total_saidas)
        
        totais_layout.addStretch()
        
        # Saldo Final
        self.label_saldo_fluxo = QLabel("Saldo Final: R$ 0,00")
        self.label_saldo_fluxo.setStyleSheet("""
            QLabel {
                color: black;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        totais_layout.addWidget(self.label_saldo_fluxo)
        
        # Label do banco selecionado
        self.label_banco_fluxo = QLabel("Banco: Todos")
        self.label_banco_fluxo.setStyleSheet("""
            QLabel {
                color: #555;
                font-size: 14px;
                font-weight: bold;
                padding-left: 20px;
            }
        """)
        totais_layout.addWidget(self.label_banco_fluxo)
        
        self.content_layout.addWidget(totais_frame)
        
        # Atualizar dados inicialmente
        self.atualizar_fluxo_caixa()
        
        self.content_layout.addStretch()
    
    def atualizar_fluxo_caixa(self):
        """Atualiza os dados do fluxo de caixa"""
        # Limpar tabela
        self.table_fluxo.setRowCount(0)
        
        # Usar as datas selecionadas nos campos De e Até
        qdate_de = self.date_fluxo_de.date()
        qdate_ate = self.date_fluxo_ate.date()
        data_inicio = datetime(qdate_de.year(), qdate_de.month(), qdate_de.day()).date()
        data_fim = datetime(qdate_ate.year(), qdate_ate.month(), qdate_ate.day()).date()
        
        banco_selecionado = self.combo_banco_fluxo.currentText()
        
        # Atualizar o label com o nome do banco
        if banco_selecionado == "Todos":
            self.liquidados_label.setText("Lançamentos Liquidados - Todos os Bancos")
        else:
            self.liquidados_label.setText(f"Lançamentos Liquidados - Banco: {banco_selecionado}")
        lancamentos = database.listar_lancamentos()
        
        # Filtrar por banco se necessário
        if banco_selecionado != "Todos":
            lancamentos = [l for l in lancamentos if l.conta_bancaria == banco_selecionado]
        
        # Filtrar apenas lançamentos PAGOS dentro do período
        lancamentos_liquidados = []
        for l in lancamentos:
            if l.status == StatusLancamento.PAGO and l.data_pagamento:
                data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                if data_inicio <= data_pag <= data_fim:
                    lancamentos_liquidados.append(l)
        
        # Ordenar por data de pagamento (mais recente primeiro)
        lancamentos_liquidados.sort(key=lambda x: x.data_pagamento if x.data_pagamento else datetime.min, reverse=True)
        
        # Preencher tabela
        for lancamento in lancamentos_liquidados:
            row = self.table_fluxo.rowCount()
            self.table_fluxo.insertRow(row)
            
            # Tipo
            tipo_text = "Receita" if lancamento.tipo == TipoLancamento.RECEITA else "Despesa"
            tipo_item = QTableWidgetItem(tipo_text)
            tipo_item.setForeground(QColor("#4CAF50" if lancamento.tipo == TipoLancamento.RECEITA else "#f44336"))
            tipo_item.setFont(QFont("Segoe UI", self.scale_size(10), QFont.Weight.Bold))
            self.table_fluxo.setItem(row, 0, tipo_item)
            
            # Data Liquidação
            if lancamento.data_pagamento:
                data_str = lancamento.data_pagamento.strftime("%d/%m/%Y")
            else:
                data_str = "-"
            data_item = QTableWidgetItem(data_str)
            data_item.setForeground(QColor("#000000"))
            self.table_fluxo.setItem(row, 1, data_item)
            
            # Descrição
            descricao_item = QTableWidgetItem(lancamento.descricao if lancamento.descricao else "-")
            descricao_item.setForeground(QColor("#000000"))
            self.table_fluxo.setItem(row, 2, descricao_item)
            
            # Categoria
            categoria_item = QTableWidgetItem(lancamento.categoria if lancamento.categoria else "-")
            categoria_item.setForeground(QColor("#000000"))
            self.table_fluxo.setItem(row, 3, categoria_item)
            
            # Subcategoria
            subcategoria_item = QTableWidgetItem(lancamento.subcategoria if lancamento.subcategoria else "-")
            subcategoria_item.setForeground(QColor("#000000"))
            self.table_fluxo.setItem(row, 4, subcategoria_item)
            
            # Cliente/Fornecedor (campo "pessoa")
            cliente_item = QTableWidgetItem(lancamento.pessoa if lancamento.pessoa else "-")
            cliente_item.setForeground(QColor("#000000"))
            self.table_fluxo.setItem(row, 5, cliente_item)
            
            # Entrada (somente para RECEITAS)
            if lancamento.tipo == TipoLancamento.RECEITA:
                entrada_item = QTableWidgetItem(self.formatar_moeda(lancamento.valor))
                entrada_item.setFont(QFont("Segoe UI", self.scale_size(10), QFont.Weight.Bold))
                entrada_item.setForeground(QColor("#4CAF50"))
                self.table_fluxo.setItem(row, 6, entrada_item)
                self.table_fluxo.setItem(row, 7, QTableWidgetItem(""))
            else:
                # Saída (somente para DESPESAS)
                self.table_fluxo.setItem(row, 6, QTableWidgetItem(""))
                saida_item = QTableWidgetItem("-" + self.formatar_moeda(lancamento.valor))
                saida_item.setFont(QFont("Segoe UI", self.scale_size(10), QFont.Weight.Bold))
                saida_item.setForeground(QColor("#f44336"))
                self.table_fluxo.setItem(row, 7, saida_item)
        
        # Calcular saldo inicial (antes do período)
        saldo_inicial = Decimal('0')
        contas = database.listar_contas()
        
        if banco_selecionado != "Todos":
            # Saldo inicial da conta específica
            conta_filtrada = [c for c in contas if c.banco == banco_selecionado]
            if conta_filtrada:
                saldo_inicial = conta_filtrada[0].saldo_inicial
                # Somar lançamentos pagos antes do período
                for l in lancamentos:
                    if l.status == StatusLancamento.PAGO and l.data_pagamento and l.conta_bancaria == banco_selecionado:
                        data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                        if data_pag < data_inicio:
                            if l.tipo == TipoLancamento.RECEITA:
                                saldo_inicial += l.valor
                            else:
                                saldo_inicial -= l.valor
        else:
            # Soma dos saldos iniciais de todas as contas
            saldo_inicial = sum(c.saldo_inicial for c in contas)
            # Somar lançamentos pagos antes do período
            for l in lancamentos:
                if l.status == StatusLancamento.PAGO and l.data_pagamento:
                    data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                    if data_pag < data_inicio:
                        if l.tipo == TipoLancamento.RECEITA:
                            saldo_inicial += l.valor
                        else:
                            saldo_inicial -= l.valor
        
        # Calcular totais do período
        total_entradas = sum(l.valor for l in lancamentos_liquidados if l.tipo == TipoLancamento.RECEITA)
        total_saidas = sum(l.valor for l in lancamentos_liquidados if l.tipo == TipoLancamento.DESPESA)
        saldo_final = saldo_inicial + total_entradas - total_saidas
        
        # Atualizar labels de totais
        self.label_saldo_inicial.setText(f"Saldo Inicial: {self.formatar_moeda(saldo_inicial)}")
        self.label_total_entradas.setText(f"Total Entradas: {self.formatar_moeda(total_entradas)}")
        self.label_total_saidas.setText(f"Total Saídas: {self.formatar_moeda(total_saidas)}")
        self.label_saldo_fluxo.setText(f"Saldo Final: {self.formatar_moeda(saldo_final)}")
        
        # Atualizar label do banco
        banco_selecionado = self.combo_banco_fluxo.currentText()
        self.label_banco_fluxo.setText(f"Banco: {banco_selecionado}")
    
    def mostrar_resumo_categoria(self):
        """Mostra diálogo com resumo por categoria"""
        # Usar as datas selecionadas nos campos De e Até
        qdate_de = self.date_fluxo_de.date()
        qdate_ate = self.date_fluxo_ate.date()
        data_inicio = datetime(qdate_de.year(), qdate_de.month(), qdate_de.day()).date()
        data_fim = datetime(qdate_ate.year(), qdate_ate.month(), qdate_ate.day()).date()
        periodo_texto = f"{qdate_de.toString('dd/MM/yyyy')} - {qdate_ate.toString('dd/MM/yyyy')}"
        
        banco_selecionado = self.combo_banco_fluxo.currentText()
        lancamentos = database.listar_lancamentos()
        
        # Filtrar por banco se necessário
        if banco_selecionado != "Todos":
            lancamentos = [l for l in lancamentos if l.conta_bancaria == banco_selecionado]
        
        # Filtrar apenas lançamentos PAGOS dentro do período
        lancamentos_liquidados = []
        for l in lancamentos:
            if l.status == StatusLancamento.PAGO and l.data_pagamento:
                data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                if data_inicio <= data_pag <= data_fim:
                    lancamentos_liquidados.append(l)
        
        # Agrupar por categoria e subcategoria
        resumo_receitas = {}  # {categoria: {subcategoria: valor}}
        resumo_despesas = {}
        
        for lanc in lancamentos_liquidados:
            categoria = lanc.categoria if lanc.categoria else "Sem Categoria"
            subcategoria = lanc.subcategoria if lanc.subcategoria else "Sem Subcategoria"
            
            if lanc.tipo == TipoLancamento.RECEITA:
                if categoria not in resumo_receitas:
                    resumo_receitas[categoria] = {}
                if subcategoria not in resumo_receitas[categoria]:
                    resumo_receitas[categoria][subcategoria] = 0
                resumo_receitas[categoria][subcategoria] += lanc.valor
            else:
                if categoria not in resumo_despesas:
                    resumo_despesas[categoria] = {}
                if subcategoria not in resumo_despesas[categoria]:
                    resumo_despesas[categoria][subcategoria] = 0
                resumo_despesas[categoria][subcategoria] += lanc.valor
        
        # Criar diálogo
        dialog = QDialog(self)
        dialog.setWindowTitle("DRE - Demonstrativo de Resultado do Exercício")
        dialog.resize(self.scale_size(750), self.scale_size(1000))
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Cabeçalho do DRE - compacto
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(3)
        
        titulo = QLabel("DEMONSTRATIVO DE RESULTADO DO EXERCÍCIO (DRE)")
        titulo.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("color: white;")
        header_layout.addWidget(titulo)
        
        info_line = QLabel(f"{periodo_texto}" + (f" | Banco: {banco_selecionado}" if banco_selecionado != "Todos" else ""))
        info_line.setFont(QFont("Segoe UI", 9))
        info_line.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_line.setStyleSheet("color: #bdc3c7;")
        header_layout.addWidget(info_line)
        
        layout.addWidget(header_frame)
        
        # Seção de Receitas - compacta
        receitas_frame = QFrame()
        receitas_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
        """)
        receitas_layout = QVBoxLayout(receitas_frame)
        receitas_layout.setSpacing(0)
        receitas_layout.setContentsMargins(0, 0, 0, 0)
        
        label_receitas = QLabel(" (+) RECEITAS OPERACIONAIS")
        label_receitas.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        label_receitas.setStyleSheet("background-color: #3498db; color: white; padding: 6px;")
        receitas_layout.addWidget(label_receitas)
        
        # Calcular número de linhas (categorias + subcategorias)
        num_linhas_receitas = sum(len(subcats) + 1 for subcats in resumo_receitas.values())
        
        table_receitas = QTableWidget()
        table_receitas.setColumnCount(2)
        table_receitas.setHorizontalHeaderLabels(["Descrição", "Valor"])
        table_receitas.setRowCount(num_linhas_receitas)
        vheader = table_receitas.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        table_receitas.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table_receitas.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table_receitas.setShowGrid(False)
        table_receitas.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        table_receitas.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                font-size: 9pt;
            }
            QTableWidget::item {
                border-bottom: 1px solid #f5f5f5;
                padding: 3px 8px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #666;
                padding: 4px;
                border: none;
                border-bottom: 1px solid #dee2e6;
                font-weight: bold;
                font-size: 8pt;
            }
        """)
        h_rec = table_receitas.horizontalHeader()
        if h_rec is not None:
            h_rec.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            h_rec.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            h_rec.resizeSection(1, 120)
        
        v_rec = table_receitas.verticalHeader()
        if v_rec is not None:
            v_rec.setVisible(False)
            v_rec.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        total_receitas = 0
        row = 0
        
        # Ordenar categorias por valor total
        categorias_ordenadas = sorted(resumo_receitas.items(), 
                                      key=lambda x: sum(x[1].values()), 
                                      reverse=True)
        
        for categoria, subcategorias in categorias_ordenadas:
            total_categoria = sum(subcategorias.values())
            
            # Linha da categoria
            cat_item = QTableWidgetItem(f"  {categoria.upper()}")
            cat_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            cat_item.setForeground(QColor("#2c3e50"))
            cat_item.setBackground(QColor("#e3f2fd"))
            table_receitas.setItem(row, 0, cat_item)
            
            valor_cat_item = QTableWidgetItem(f"+{self.formatar_moeda(total_categoria)}")
            valor_cat_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            valor_cat_item.setForeground(QColor("#27ae60"))
            valor_cat_item.setBackground(QColor("#e3f2fd"))
            valor_cat_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table_receitas.setItem(row, 1, valor_cat_item)
            row += 1
            
            # Linhas das subcategorias
            for subcategoria, valor in sorted(subcategorias.items(), key=lambda x: x[1], reverse=True):
                sub_item = QTableWidgetItem(f"      • {subcategoria}")
                sub_item.setForeground(QColor("#666666"))
                sub_item.setFont(QFont("Segoe UI", 9))
                table_receitas.setItem(row, 0, sub_item)
                
                valor_item = QTableWidgetItem(f"+{self.formatar_moeda(valor)}")
                valor_item.setForeground(QColor("#1e8449"))
                valor_item.setFont(QFont("Segoe UI", 9))
                valor_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table_receitas.setItem(row, 1, valor_item)
                row += 1
            
            total_receitas += total_categoria
        
        receitas_layout.addWidget(table_receitas)
        
        # Total Receitas
        total_rec_frame = QFrame()
        total_rec_frame.setStyleSheet("""
            QFrame {
                background-color: #d3d3d3;
                padding: 6px 10px;
            }
        """)
        total_rec_layout = QHBoxLayout(total_rec_frame)
        total_rec_layout.setContentsMargins(0, 0, 0, 0)
        total_rec_label = QLabel("TOTAL DE RECEITAS")
        total_rec_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        total_rec_label.setStyleSheet("color: #000000;")
        total_rec_layout.addWidget(total_rec_label)
        total_rec_layout.addStretch()
        total_rec_valor = QLabel(f"+{self.formatar_moeda(total_receitas)}")
        total_rec_valor.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        total_rec_valor.setStyleSheet("color: #1e8449;")
        total_rec_layout.addWidget(total_rec_valor)
        receitas_layout.addWidget(total_rec_frame)
        
        layout.addWidget(receitas_frame)
        
        # Seção de Despesas
        despesas_frame = QFrame()
        despesas_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
        """)
        despesas_layout = QVBoxLayout(despesas_frame)
        despesas_layout.setSpacing(0)
        despesas_layout.setContentsMargins(0, 0, 0, 0)
        
        label_despesas = QLabel(" (-) DESPESAS OPERACIONAIS")
        label_despesas.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        label_despesas.setStyleSheet("background-color: #2980b9; color: white; padding: 6px;")
        despesas_layout.addWidget(label_despesas)
        
        # Calcular número de linhas (categorias + subcategorias)
        num_linhas_despesas = sum(len(subcats) + 1 for subcats in resumo_despesas.values())
        
        table_despesas = QTableWidget()
        table_despesas.setColumnCount(2)
        table_despesas.setHorizontalHeaderLabels(["Descrição", "Valor"])
        table_despesas.setRowCount(num_linhas_despesas)
        vheader = table_despesas.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        table_despesas.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table_despesas.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table_despesas.setShowGrid(False)
        table_despesas.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        table_despesas.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                font-size: 9pt;
            }
            QTableWidget::item {
                border-bottom: 1px solid #f5f5f5;
                padding: 3px 8px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #666;
                padding: 4px;
                border: none;
                border-bottom: 1px solid #dee2e6;
                font-weight: bold;
                font-size: 8pt;
            }
        """)
        h_desp = table_despesas.horizontalHeader()
        if h_desp is not None:
            h_desp.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            h_desp.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            h_desp.resizeSection(1, 120)
        
        v_desp = table_despesas.verticalHeader()
        if v_desp is not None:
            v_desp.setVisible(False)
            v_desp.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        total_despesas = 0
        row = 0
        
        # Ordenar categorias por valor total
        categorias_ordenadas = sorted(resumo_despesas.items(), 
                                      key=lambda x: sum(x[1].values()), 
                                      reverse=True)
        
        for categoria, subcategorias in categorias_ordenadas:
            total_categoria = sum(subcategorias.values())
            
            # Linha da categoria
            cat_item = QTableWidgetItem(f"  {categoria.upper()}")
            cat_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            cat_item.setForeground(QColor("#2c3e50"))
            cat_item.setBackground(QColor("#ecf0f1"))
            table_despesas.setItem(row, 0, cat_item)
            
            valor_cat_item = QTableWidgetItem(f"-{self.formatar_moeda(total_categoria)}")
            valor_cat_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            valor_cat_item.setForeground(QColor("#e74c3c"))
            valor_cat_item.setBackground(QColor("#ecf0f1"))
            valor_cat_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table_despesas.setItem(row, 1, valor_cat_item)
            row += 1
            
            # Linhas das subcategorias
            for subcategoria, valor in sorted(subcategorias.items(), key=lambda x: x[1], reverse=True):
                sub_item = QTableWidgetItem(f"      • {subcategoria}")
                sub_item.setForeground(QColor("#666666"))
                sub_item.setFont(QFont("Segoe UI", 9))
                table_despesas.setItem(row, 0, sub_item)
                
                valor_item = QTableWidgetItem(f"-{self.formatar_moeda(valor)}")
                valor_item.setForeground(QColor("#e74c3c"))
                valor_item.setFont(QFont("Segoe UI", 9))
                valor_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table_despesas.setItem(row, 1, valor_item)
                row += 1
            
            total_despesas += total_categoria
        
        despesas_layout.addWidget(table_despesas)
        
        # Total Despesas
        total_desp_frame = QFrame()
        total_desp_frame.setStyleSheet("""
            QFrame {
                background-color: #d3d3d3;
                padding: 6px 10px;
            }
        """)
        total_desp_layout = QHBoxLayout(total_desp_frame)
        total_desp_layout.setContentsMargins(0, 0, 0, 0)
        total_desp_label = QLabel("TOTAL DE DESPESAS")
        total_desp_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        total_desp_label.setStyleSheet("color: #000000;")
        total_desp_layout.addWidget(total_desp_label)
        total_desp_layout.addStretch()
        total_desp_valor = QLabel(f"-{self.formatar_moeda(total_despesas)}")
        total_desp_valor.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        total_desp_valor.setStyleSheet("color: #e74c3c;")
        total_desp_layout.addWidget(total_desp_valor)
        despesas_layout.addWidget(total_desp_frame)
        
        layout.addWidget(despesas_frame)
        
        # Resultado do Período - compacto
        saldo = total_receitas - total_despesas
        resultado_frame = QFrame()
        resultado_cor = "#2c3e50"
        resultado_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {resultado_cor};
                border-radius: 5px;
                padding: 10px;
            }}
        """)
        resultado_layout = QHBoxLayout(resultado_frame)
        resultado_layout.setContentsMargins(10, 8, 10, 8)
        
        # Lado esquerdo - Título e tipo
        left_layout = QVBoxLayout()
        left_layout.setSpacing(2)
        
        resultado_titulo = QLabel("RESULTADO DO EXERCÍCIO")
        resultado_titulo.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        resultado_titulo.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        left_layout.addWidget(resultado_titulo)
        
        resultado_tipo = QLabel(f"{'LUCRO LÍQUIDO' if saldo >= 0 else 'PREJUÍZO'}")
        resultado_tipo.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        resultado_tipo.setStyleSheet("color: white;")
        left_layout.addWidget(resultado_tipo)
        
        resultado_layout.addLayout(left_layout)
        resultado_layout.addStretch()
        
        # Lado direito - Valor e margem
        right_layout = QVBoxLayout()
        right_layout.setSpacing(0)
        
        sinal = "+" if saldo >= 0 else "-"
        saldo_label = QLabel(f"{sinal}{self.formatar_moeda(abs(saldo))}")
        saldo_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        saldo_label.setStyleSheet("color: white;")
        saldo_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_layout.addWidget(saldo_label)
        
        if total_receitas > 0:
            margem = (saldo / total_receitas) * 100
            margem_label = QLabel(f"Margem: {margem:.1f}%")
            margem_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            margem_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
            margem_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            right_layout.addWidget(margem_label)
        
        resultado_layout.addLayout(right_layout)
        layout.addWidget(resultado_frame)
        
        # Botões de ação
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(5)
        
        # Botão Exportar PDF
        btn_pdf = QPushButton("📄 Exportar PDF")
        btn_pdf.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 6px 15px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        btn_pdf.setMaximumWidth(140)
        btn_pdf.clicked.connect(lambda: self.exportar_resumo_pdf(resumo_receitas, resumo_despesas, total_receitas, total_despesas, periodo_texto))
        botoes_layout.addWidget(btn_pdf)
        
        # Botão Exportar Excel
        btn_excel = QPushButton("📊 Exportar Excel")
        btn_excel.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 6px 15px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        btn_excel.setMaximumWidth(140)
        btn_excel.clicked.connect(lambda: self.exportar_resumo_excel(resumo_receitas, resumo_despesas, total_receitas, total_despesas, periodo_texto))
        botoes_layout.addWidget(btn_excel)
        
        # Botão Imprimir
        btn_imprimir = QPushButton("🖨️ Imprimir")
        btn_imprimir.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 6px 15px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        btn_imprimir.setMaximumWidth(140)
        btn_imprimir.clicked.connect(lambda: self.imprimir_resumo(resumo_receitas, resumo_despesas, total_receitas, total_despesas, periodo_texto))
        botoes_layout.addWidget(btn_imprimir)
        
        # Botão Fechar
        btn_fechar = QPushButton("Fechar")
        btn_fechar.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 6px 15px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        btn_fechar.setMaximumWidth(140)
        btn_fechar.clicked.connect(dialog.close)
        botoes_layout.addWidget(btn_fechar)
        botoes_layout.addStretch()
        
        layout.addLayout(botoes_layout)
        
        dialog.exec()
    
    def exportar_resumo_pdf(self, resumo_receitas, resumo_despesas, total_receitas, total_despesas, periodo):
        """Exporta resumo por categoria para PDF no formato DRE"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
            
            # Diálogo para escolher onde salvar
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar DRE em PDF",
                f"DRE_{periodo.replace(' ', '_').replace('/', '-')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if not file_path:
                return
            
            # Criar PDF
            doc = SimpleDocTemplate(file_path, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
            elementos = []
            
            # Cabeçalho - fundo azul escuro
            header_data = [
                [Paragraph('<font size=14 color=white><b>DEMONSTRATIVO DE RESULTADO DO EXERCÍCIO (DRE)</b></font>', 
                          ParagraphStyle('center', alignment=TA_CENTER))],
                [Paragraph(f'<font size=10 color=white>{periodo}</font>', 
                          ParagraphStyle('center', alignment=TA_CENTER))]
            ]
            header_table = Table(header_data, colWidths=[17*cm])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elementos.append(header_table)
            elementos.append(Spacer(1, 0.5*cm))
            
            # RECEITAS OPERACIONAIS
            data_receitas = [[Paragraph('<font size=10 color=white><b>(+) RECEITAS OPERACIONAIS</b></font>', 
                                       ParagraphStyle('left', alignment=TA_LEFT)), '']]
            
            # Adicionar categorias e subcategorias de receitas
            for categoria, subcategorias in sorted(resumo_receitas.items(), key=lambda x: sum(x[1].values()), reverse=True):
                total_cat = sum(subcategorias.values())
                data_receitas.append([Paragraph(f'<font size=9><b>{categoria.upper()}</b></font>', 
                                                ParagraphStyle('left', alignment=TA_LEFT)), 
                                     f'+{self.formatar_moeda(total_cat)}'])
                # Adicionar subcategorias identadas
                for subcat, valor in sorted(subcategorias.items(), key=lambda x: x[1], reverse=True):
                    data_receitas.append([Paragraph(f'<font size=8>• {subcat}</font>', 
                                                   ParagraphStyle('left', alignment=TA_LEFT, leftIndent=10)), 
                                         f'+{self.formatar_moeda(valor)}'])
            
            # Total de receitas
            data_receitas.append(['', ''])
            data_receitas.append([Paragraph('<font size=9><b>TOTAL DE RECEITAS</b></font>', 
                                           ParagraphStyle('left', alignment=TA_LEFT)), 
                                 Paragraph(f'<font size=10 color=#1e8449><b>+{self.formatar_moeda(total_receitas)}</b></font>', 
                                          ParagraphStyle('right', alignment=TA_RIGHT))])
            
            table_receitas = Table(data_receitas, colWidths=[13*cm, 4*cm])
            table_receitas.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d3d3d3')),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.grey),
                ('LINEBELOW', (0, -1), (-1, -1), 1, colors.grey),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elementos.append(table_receitas)
            elementos.append(Spacer(1, 0.5*cm))
            
            # DESPESAS OPERACIONAIS
            data_despesas = [[Paragraph('<font size=10 color=white><b>(-) DESPESAS OPERACIONAIS</b></font>', 
                                       ParagraphStyle('left', alignment=TA_LEFT)), '']]
            
            # Adicionar categorias e subcategorias de despesas
            for categoria, subcategorias in sorted(resumo_despesas.items(), key=lambda x: sum(x[1].values()), reverse=True):
                total_cat = sum(subcategorias.values())
                data_despesas.append([Paragraph(f'<font size=9><b>{categoria.upper()}</b></font>', 
                                                ParagraphStyle('left', alignment=TA_LEFT)), 
                                     f'-{self.formatar_moeda(total_cat)}'])
                # Adicionar subcategorias identadas
                for subcat, valor in sorted(subcategorias.items(), key=lambda x: x[1], reverse=True):
                    data_despesas.append([Paragraph(f'<font size=8>• {subcat}</font>', 
                                                   ParagraphStyle('left', alignment=TA_LEFT, leftIndent=10)), 
                                         f'-{self.formatar_moeda(valor)}'])
            
            # Total de despesas
            data_despesas.append(['', ''])
            data_despesas.append([Paragraph('<font size=9><b>TOTAL DE DESPESAS</b></font>', 
                                           ParagraphStyle('left', alignment=TA_LEFT)), 
                                 Paragraph(f'<font size=10 color=#e74c3c><b>-{self.formatar_moeda(total_despesas)}</b></font>', 
                                          ParagraphStyle('right', alignment=TA_RIGHT))])
            
            table_despesas = Table(data_despesas, colWidths=[13*cm, 4*cm])
            table_despesas.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d3d3d3')),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.grey),
                ('LINEBELOW', (0, -1), (-1, -1), 1, colors.grey),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elementos.append(table_despesas)
            elementos.append(Spacer(1, 0.5*cm))
            
            # RESULTADO DO EXERCÍCIO
            saldo = total_receitas - total_despesas
            tipo_resultado = "LUCRO LÍQUIDO" if saldo >= 0 else "PREJUÍZO"
            sinal = "+" if saldo >= 0 else "-"
            margem = (saldo / total_receitas * 100) if total_receitas > 0 else 0
            
            resultado_data = [
                [Paragraph('<font size=10 color=white><b>RESULTADO DO EXERCÍCIO</b></font>', 
                          ParagraphStyle('left', alignment=TA_LEFT)), 
                 Paragraph(f'<font size=12 color=white><b>{sinal}{self.formatar_moeda(abs(saldo))}</b></font>', 
                          ParagraphStyle('right', alignment=TA_RIGHT))],
                [Paragraph(f'<font size=9 color=white><b>{tipo_resultado}</b></font>', 
                          ParagraphStyle('left', alignment=TA_LEFT)),
                 Paragraph(f'<font size=9 color=white><b>Margem: {margem:.1f}%</b></font>', 
                          ParagraphStyle('right', alignment=TA_RIGHT))]
            ]
            
            resultado_table = Table(resultado_data, colWidths=[13*cm, 4*cm])
            resultado_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elementos.append(resultado_table)
            
            doc.build(elementos)
            QMessageBox.information(self, "Sucesso", f"DRE exportado com sucesso!\n{file_path}")
            
        except ImportError:
            QMessageBox.warning(self, "Erro", "Biblioteca reportlab não instalada.\nInstale com: pip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {str(e)}")
    
    def exportar_resumo_excel(self, resumo_receitas, resumo_despesas, total_receitas, total_despesas, periodo):
        """Exporta resumo por categoria para Excel"""
        try:
            import pandas as pd
            
            # Diálogo para escolher onde salvar
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Resumo em Excel",
                f"resumo_categoria_{periodo.replace(' ', '_')}.xlsx",
                "Excel Files (*.xlsx)"
            )
            
            if not file_path:
                return
            
            # Criar DataFrames
            df_receitas = pd.DataFrame(list(resumo_receitas.items()), columns=['Categoria', 'Total'])
            df_receitas = df_receitas.sort_values('Total', ascending=False)
            df_receitas.loc[len(df_receitas)] = ['TOTAL', total_receitas]
            
            df_despesas = pd.DataFrame(list(resumo_despesas.items()), columns=['Categoria', 'Total'])
            df_despesas = df_despesas.sort_values('Total', ascending=False)
            df_despesas.loc[len(df_despesas)] = ['TOTAL', total_despesas]
            
            saldo = total_receitas - total_despesas
            df_saldo = pd.DataFrame([['Saldo do Período', saldo]], columns=['Descrição', 'Valor'])
            
            # Salvar no Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df_receitas.to_excel(writer, sheet_name='Receitas', index=False)
                df_despesas.to_excel(writer, sheet_name='Despesas', index=False)
                df_saldo.to_excel(writer, sheet_name='Saldo', index=False)
            
            QMessageBox.information(self, "Sucesso", f"Resumo exportado com sucesso!\n{file_path}")
            
        except ImportError:
            QMessageBox.warning(self, "Erro", "Biblioteca pandas não instalada.\nInstale com: pip install pandas openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar Excel: {str(e)}")
    
    def imprimir_resumo(self, resumo_receitas, resumo_despesas, total_receitas, total_despesas, periodo):
        """Imprime resumo por categoria"""
        try:
            from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
            from PyQt6.QtGui import QPainter, QTextDocument
            
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            dialog = QPrintDialog(printer, self)
            
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                # Criar documento HTML para impressão
                html = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        h1 {{ text-align: center; color: #2c3e50; }}
                        h2 {{ color: #4CAF50; margin-top: 30px; }}
                        h2.despesas {{ color: #f44336; }}
                        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                        th {{ background-color: #f0f0f0; padding: 10px; text-align: left; border: 1px solid #ddd; }}
                        td {{ padding: 8px; border: 1px solid #ddd; }}
                        tr:nth-child(even) {{ background-color: #f9f9f9; }}
                        .total {{ font-weight: bold; background-color: #e0e0e0; }}
                        .saldo {{ text-align: center; font-size: 18px; font-weight: bold; margin-top: 30px; padding: 15px; background-color: #f0f0f0; border-radius: 5px; }}
                    </style>
                </head>
                <body>
                    <h1>Resumo por Categoria - {periodo}</h1>
                    
                    <h2>📈 RECEITAS</h2>
                    <table>
                        <tr><th>Categoria</th><th>Total</th></tr>
                """
                
                for categoria, valor in sorted(resumo_receitas.items(), key=lambda x: x[1], reverse=True):
                    html += f"<tr><td>{categoria}</td><td>{self.formatar_moeda(valor)}</td></tr>"
                
                html += f"""
                        <tr class="total"><td>TOTAL</td><td>{self.formatar_moeda(total_receitas)}</td></tr>
                    </table>
                    
                    <h2 class="despesas">📉 DESPESAS</h2>
                    <table>
                        <tr><th>Categoria</th><th>Total</th></tr>
                """
                
                for categoria, valor in sorted(resumo_despesas.items(), key=lambda x: x[1], reverse=True):
                    html += f"<tr><td>{categoria}</td><td>{self.formatar_moeda(valor)}</td></tr>"
                
                saldo = total_receitas - total_despesas
                saldo_color = '#4CAF50' if saldo >= 0 else '#f44336'
                
                html += f"""
                        <tr class="total"><td>TOTAL</td><td>{self.formatar_moeda(total_despesas)}</td></tr>
                    </table>
                    
                    <div class="saldo" style="color: {saldo_color};">
                        💰 Saldo do Período: {self.formatar_moeda(saldo)}
                    </div>
                </body>
                </html>
                """
                
                document = QTextDocument()
                document.setHtml(html)
                document.print(printer)
                
                QMessageBox.information(self, "Sucesso", "Documento enviado para impressão!")
        
        except ImportError:
            QMessageBox.warning(self, "Erro", "Módulo de impressão não disponível.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao imprimir: {str(e)}")
    
    def exportar_fluxo_pdf(self):
        """Exporta fluxo de caixa para PDF"""
        try:
            from reportlab.lib.pagesizes import A3, landscape
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER
            
            # Verificar se há dados na tabela
            if self.table_fluxo.rowCount() == 0:
                QMessageBox.warning(self, "Aviso", "Não há dados para exportar!")
                return
            
            # Obter período selecionado
            data_inicio = self.date_fluxo_de.date().toPyDate()
            data_fim = self.date_fluxo_ate.date().toPyDate()
            periodo = f"{data_inicio.strftime('%d/%m/%Y')} - {data_fim.strftime('%d/%m/%Y')}"
            banco = self.combo_banco_fluxo.currentText()
            
            # Diálogo para salvar
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Fluxo de Caixa em PDF",
                f"fluxo_caixa_{data_inicio.strftime('%Y%m%d')}_{data_fim.strftime('%Y%m%d')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if not file_path:
                return
            
            # Criar PDF em paisagem com tamanho A3
            doc = SimpleDocTemplate(file_path, pagesize=landscape(A3), 
                                  topMargin=1.5*cm, bottomMargin=1.5*cm,
                                  leftMargin=1.5*cm, rightMargin=1.5*cm)
            elementos = []
            
            # Cabeçalho
            header_data = [
                [Paragraph('<font size=14 color=white><b>FLUXO DE CAIXA</b></font>', 
                          ParagraphStyle('center', alignment=TA_CENTER))],
                [Paragraph(f'<font size=10 color=white>{periodo} | Banco: {banco}</font>', 
                          ParagraphStyle('center', alignment=TA_CENTER))]
            ]
            header_table = Table(header_data, colWidths=[36*cm])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elementos.append(header_table)
            elementos.append(Spacer(1, 0.5*cm))
            
            # Coletar dados da tabela (excluir coluna Descrição - índice 2)
            data = [['Tipo', 'Data', 'Categoria', 'Subcategoria', 'Cliente/Fornecedor', 'Entrada', 'Saída']]
            
            for row in range(self.table_fluxo.rowCount()):
                row_data = []
                for col in range(self.table_fluxo.columnCount()):
                    if col == 2:  # Pular coluna Descrição
                        continue
                    item = self.table_fluxo.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            
            # Criar tabela com larguras ajustadas (total = 36cm)
            table = Table(data, colWidths=[2.5*cm, 2.8*cm, 5.5*cm, 5.5*cm, 9.7*cm, 5*cm, 5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (5, 0), (6, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elementos.append(table)
            
            # Adicionar espaço antes dos totais
            elementos.append(Spacer(1, 0.8*cm))
            
            # Calcular totais (mesmo cálculo da interface)
            from decimal import Decimal
            
            # Obter lançamentos liquidados do período
            lancamentos = database.listar_lancamentos()
            
            # Filtrar por banco se necessário
            if banco != "Todos":
                lancamentos = [l for l in lancamentos if l.conta_bancaria == banco]
            
            # Filtrar apenas lançamentos PAGOS dentro do período
            lancamentos_liquidados = []
            for l in lancamentos:
                if l.status == StatusLancamento.PAGO and l.data_pagamento:
                    data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                    if data_inicio <= data_pag <= data_fim:
                        lancamentos_liquidados.append(l)
            
            # Calcular saldo inicial (antes do período)
            saldo_inicial = Decimal('0')
            contas = database.listar_contas()
            
            if banco != "Todos":
                conta_filtrada = [c for c in contas if c.banco == banco]
                if conta_filtrada:
                    saldo_inicial = conta_filtrada[0].saldo_inicial
                    for l in lancamentos:
                        if l.status == StatusLancamento.PAGO and l.data_pagamento and l.conta_bancaria == banco:
                            data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                            if data_pag < data_inicio:
                                if l.tipo == TipoLancamento.RECEITA:
                                    saldo_inicial += l.valor
                                else:
                                    saldo_inicial -= l.valor
            else:
                saldo_inicial = sum(c.saldo_inicial for c in contas)
                for l in lancamentos:
                    if l.status == StatusLancamento.PAGO and l.data_pagamento:
                        data_pag = l.data_pagamento.date() if hasattr(l.data_pagamento, 'date') else l.data_pagamento
                        if data_pag < data_inicio:
                            if l.tipo == TipoLancamento.RECEITA:
                                saldo_inicial += l.valor
                            else:
                                saldo_inicial -= l.valor
            
            # Calcular totais do período
            total_entradas = sum(l.valor for l in lancamentos_liquidados if l.tipo == TipoLancamento.RECEITA)
            total_saidas = sum(l.valor for l in lancamentos_liquidados if l.tipo == TipoLancamento.DESPESA)
            saldo_final = saldo_inicial + total_entradas - total_saidas
            
            # Criar tabela de totais em linha única
            totais_data = [
                ['Saldo Inicial:', self.formatar_moeda(saldo_inicial), 
                 'Total Entradas:', self.formatar_moeda(total_entradas),
                 'Total Saídas:', self.formatar_moeda(total_saidas),
                 'Saldo Final:', self.formatar_moeda(saldo_final)]
            ]
            
            totais_table = Table(totais_data, colWidths=[2.8*cm, 3*cm, 3*cm, 3.2*cm, 2.5*cm, 3.2*cm, 2.5*cm, 3*cm])
            totais_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f8f9fa')),
                ('BACKGROUND', (1, 0), (1, 0), colors.white),
                ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#f8f9fa')),
                ('BACKGROUND', (3, 0), (3, 0), colors.white),
                ('BACKGROUND', (4, 0), (4, 0), colors.HexColor('#f8f9fa')),
                ('BACKGROUND', (5, 0), (5, 0), colors.white),
                ('BACKGROUND', (6, 0), (6, 0), colors.HexColor('#f8f9fa')),
                ('BACKGROUND', (7, 0), (7, 0), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('ALIGN', (2, 0), (2, 0), 'LEFT'),
                ('ALIGN', (3, 0), (3, 0), 'RIGHT'),
                ('ALIGN', (4, 0), (4, 0), 'LEFT'),
                ('ALIGN', (5, 0), (5, 0), 'RIGHT'),
                ('ALIGN', (6, 0), (6, 0), 'LEFT'),
                ('ALIGN', (7, 0), (7, 0), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('LEFTPADDING', (0, 0), (-1, 0), 3),
                ('RIGHTPADDING', (0, 0), (-1, 0), 3),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elementos.append(totais_table)
            
            doc.build(elementos)
            QMessageBox.information(self, "Sucesso", f"Fluxo de caixa exportado com sucesso!\n{file_path}")
            
        except ImportError:
            QMessageBox.warning(self, "Erro", "Biblioteca reportlab não instalada.\nInstale com: pip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {str(e)}")
    
    def exportar_fluxo_excel(self):
        """Exporta fluxo de caixa para Excel"""
        try:
            import pandas as pd
            
            # Verificar se há dados na tabela
            if self.table_fluxo.rowCount() == 0:
                QMessageBox.warning(self, "Aviso", "Não há dados para exportar!")
                return
            
            # Obter período selecionado
            data_inicio = self.date_fluxo_de.date().toPyDate()
            data_fim = self.date_fluxo_ate.date().toPyDate()
            
            # Diálogo para salvar
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Fluxo de Caixa em Excel",
                f"fluxo_caixa_{data_inicio.strftime('%Y%m%d')}_{data_fim.strftime('%Y%m%d')}.xlsx",
                "Excel Files (*.xlsx)"
            )
            
            if not file_path:
                return
            
            # Coletar dados da tabela
            data = []
            headers = []
            for col in range(self.table_fluxo.columnCount()):
                item = self.table_fluxo.horizontalHeaderItem(col)
                headers.append(item.text() if item else f"Coluna {col+1}")
            
            for row in range(self.table_fluxo.rowCount()):
                row_data = []
                for col in range(self.table_fluxo.columnCount()):
                    item = self.table_fluxo.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            
            # Criar DataFrame
            df = pd.DataFrame(data, columns=headers)
            
            # Salvar em Excel
            df.to_excel(file_path, index=False, sheet_name='Fluxo de Caixa')
            
            QMessageBox.information(self, "Sucesso", f"Fluxo de caixa exportado com sucesso!\n{file_path}")
            
        except ImportError:
            QMessageBox.warning(self, "Erro", "Biblioteca pandas não instalada.\nInstale com: pip install pandas openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar Excel: {str(e)}")
    
    def show_relatorios(self):
        """Exibe relatórios"""
        self.clear_content()
        
        # Desmarcar todos os botões
        for btn in self.menu_buttons:
            btn.setChecked(False)
        self.btn_relatorios.setChecked(True)
        
        title = QLabel("Relatorios")
        title.setObjectName("pageTitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.content_layout.addWidget(title)
        
        # Período
        periodo_layout = QHBoxLayout()
        periodo_layout.addWidget(QLabel("De:"))
        data_inicio = QDateEdit()
        data_inicio.setDate(QDate.currentDate().addMonths(-1))
        data_inicio.setCalendarPopup(True)
        periodo_layout.addWidget(data_inicio)
        
        periodo_layout.addWidget(QLabel("Até:"))
        data_fim = QDateEdit()
        data_fim.setDate(QDate.currentDate())
        data_fim.setCalendarPopup(True)
        periodo_layout.addWidget(data_fim)
        
        btn_gerar = QPushButton("Gerar Relatorio")
        btn_gerar.setObjectName("primaryButton")
        periodo_layout.addWidget(btn_gerar)
        
        periodo_layout.addStretch()
        self.content_layout.addLayout(periodo_layout)
        
        # Área de resultado
        resultado_frame = QFrame()
        resultado_frame.setObjectName("card")
        resultado_layout = QVBoxLayout(resultado_frame)
        
        label_info = QLabel("Selecione um periodo e clique em 'Gerar Relatorio'")
        label_info.setFont(QFont("Segoe UI", 11))
        resultado_layout.addWidget(label_info)
        
        self.content_layout.addWidget(resultado_frame)
        self.content_layout.addStretch()
    
    def show_fluxo_projetado(self):
        """Exibe o relatório de Fluxo de Caixa Projetado"""
        self.clear_content()
        
        for btn in self.menu_buttons:
            btn.setChecked(False)
        self.btn_relatorios.setChecked(True)
        
        if not self.submenu_relatorios.isVisible():
            self.submenu_relatorios.setVisible(True)
            self.btn_relatorios.setText("Relatorios                   ▲")
        
        title = QLabel("Fluxo de Caixa Projetado")
        title.setObjectName("pageTitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.content_layout.addWidget(title)
        
        # Filtros
        filtros_frame = QFrame()
        filtros_frame.setObjectName("filterFrame")
        filtros_layout = QHBoxLayout(filtros_frame)
        
        filtros_layout.addWidget(QLabel("Projetar até:"))
        self.date_projecao = QDateEdit()
        self.date_projecao.setDate(QDate.currentDate().addMonths(3))
        self.date_projecao.setCalendarPopup(True)
        self.date_projecao.setDisplayFormat("dd/MM/yyyy")
        self.date_projecao.setMinimumWidth(120)
        filtros_layout.addWidget(self.date_projecao)
        
        btn_gerar = QPushButton("🔄 Gerar Projeção")
        btn_gerar.setObjectName("primaryButton")
        btn_gerar.clicked.connect(self.gerar_fluxo_projetado)
        filtros_layout.addWidget(btn_gerar)
        
        filtros_layout.addStretch()
        self.content_layout.addLayout(filtros_layout)
        
        # Tabela
        self.table_projecao = QTableWidget()
        self.table_projecao.setColumnCount(5)
        self.table_projecao.setHorizontalHeaderLabels(["Data", "Descrição", "Tipo", "Valor", "Saldo Projetado"])
        vheader = self.table_projecao.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        header = self.table_projecao.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_projecao.setAlternatingRowColors(True)
        self.table_projecao.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_projecao.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.content_layout.addWidget(self.table_projecao)
        
        self.gerar_fluxo_projetado()
        self.content_layout.addStretch()
    
    def gerar_fluxo_projetado(self):
        """Gera a projeção de fluxo de caixa"""
        self.table_projecao.setRowCount(0)
        
        data_final = self.date_projecao.date().toPyDate()
        hoje = datetime.now().date()
        
        # Saldo inicial (soma de todas as contas)
        saldo_atual = sum([conta.saldo_inicial for conta in database.listar_contas()])
        
        # Buscar lançamentos pendentes
        lancamentos = database.listar_lancamentos()
        lancamentos_pendentes = [
            l for l in lancamentos 
            if l.status == StatusLancamento.PENDENTE and 
            (l.data_vencimento.date() if hasattr(l.data_vencimento, 'date') else l.data_vencimento) <= data_final
        ]
        
        # Ordenar por data de vencimento
        lancamentos_pendentes.sort(key=lambda x: x.data_vencimento)
        
        for lanc in lancamentos_pendentes:
            row = self.table_projecao.rowCount()
            self.table_projecao.insertRow(row)
            
            # Converter data_vencimento para date se necessário
            data_venc = lanc.data_vencimento.date() if hasattr(lanc.data_vencimento, 'date') else lanc.data_vencimento
            
            # Data
            data_item = QTableWidgetItem(data_venc.strftime("%d/%m/%Y"))
            if data_venc < hoje:
                data_item.setForeground(QColor("#e74c3c"))
            self.table_projecao.setItem(row, 0, data_item)
            
            # Descrição
            descricao = f"{lanc.descricao} ({lanc.categoria} - {lanc.subcategoria})"
            self.table_projecao.setItem(row, 1, QTableWidgetItem(descricao))
            
            # Tipo
            tipo_texto = "RECEITA" if lanc.tipo == TipoLancamento.RECEITA else "DESPESA"
            tipo_item = QTableWidgetItem(tipo_texto)
            if lanc.tipo == TipoLancamento.RECEITA:
                tipo_item.setForeground(QColor("#1e8449"))
            else:
                tipo_item.setForeground(QColor("#e74c3c"))
            self.table_projecao.setItem(row, 2, tipo_item)
            
            # Valor
            valor_formatado = self.formatar_moeda(lanc.valor)
            valor_item = QTableWidgetItem(valor_formatado)
            if lanc.tipo == TipoLancamento.RECEITA:
                valor_item.setForeground(QColor("#1e8449"))
            else:
                valor_item.setForeground(QColor("#e74c3c"))
            self.table_projecao.setItem(row, 3, valor_item)
            
            # Calcular saldo projetado
            if lanc.tipo == TipoLancamento.RECEITA:
                saldo_atual += lanc.valor
            else:
                saldo_atual -= lanc.valor
            
            saldo_item = QTableWidgetItem(self.formatar_moeda(saldo_atual))
            if saldo_atual < 0:
                saldo_item.setForeground(QColor("#e74c3c"))
            else:
                saldo_item.setForeground(QColor("#1e8449"))
            self.table_projecao.setItem(row, 4, saldo_item)
        
        self.table_projecao.resizeColumnsToContents()
    
    def show_analise_contas(self):
        """Exibe análise de contas a pagar e receber"""
        self.clear_content()
        
        for btn in self.menu_buttons:
            btn.setChecked(False)
        self.btn_relatorios.setChecked(True)
        
        if not self.submenu_relatorios.isVisible():
            self.submenu_relatorios.setVisible(True)
            self.btn_relatorios.setText("Relatorios                   ▲")
        
        title = QLabel("Análise de Contas a Pagar e Receber")
        title.setObjectName("pageTitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.content_layout.addWidget(title)
        
        # Cards de resumo
        cards_layout = QHBoxLayout()
        
        lancamentos = database.listar_lancamentos()
        hoje = datetime.now().date()
        
        # Calcular totais
        total_receber = sum([l.valor for l in lancamentos if l.tipo == TipoLancamento.RECEITA and l.status == StatusLancamento.PENDENTE])
        total_pagar = sum([l.valor for l in lancamentos if l.tipo == TipoLancamento.DESPESA and l.status == StatusLancamento.PENDENTE])
        
        receber_vencidos = sum([l.valor for l in lancamentos if l.tipo == TipoLancamento.RECEITA and l.status == StatusLancamento.PENDENTE and (l.data_vencimento.date() if hasattr(l.data_vencimento, 'date') else l.data_vencimento) < hoje])
        pagar_vencidos = sum([l.valor for l in lancamentos if l.tipo == TipoLancamento.DESPESA and l.status == StatusLancamento.PENDENTE and (l.data_vencimento.date() if hasattr(l.data_vencimento, 'date') else l.data_vencimento) < hoje])
        
        # Card Contas a Receber
        card_receber = QFrame()
        card_receber.setObjectName("card")
        card_receber.setStyleSheet("QFrame#card { background-color: #d4edda; border-left: 5px solid #1e8449; }")
        receber_layout = QVBoxLayout(card_receber)
        receber_layout.addWidget(QLabel("💰 Contas a Receber"))
        label_total_receber = QLabel(self.formatar_moeda(total_receber))
        label_total_receber.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        label_total_receber.setStyleSheet("color: #1e8449;")
        receber_layout.addWidget(label_total_receber)
        if receber_vencidos > 0:
            label_vencidos = QLabel(f"Vencidos: {self.formatar_moeda(receber_vencidos)}")
            label_vencidos.setStyleSheet("color: #e74c3c; font-weight: bold;")
            receber_layout.addWidget(label_vencidos)
        cards_layout.addWidget(card_receber)
        
        # Card Contas a Pagar
        card_pagar = QFrame()
        card_pagar.setObjectName("card")
        card_pagar.setStyleSheet("QFrame#card { background-color: #f8d7da; border-left: 5px solid #e74c3c; }")
        pagar_layout = QVBoxLayout(card_pagar)
        pagar_layout.addWidget(QLabel("💳 Contas a Pagar"))
        label_total_pagar = QLabel(self.formatar_moeda(total_pagar))
        label_total_pagar.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        label_total_pagar.setStyleSheet("color: #e74c3c;")
        pagar_layout.addWidget(label_total_pagar)
        if pagar_vencidos > 0:
            label_vencidos = QLabel(f"Vencidos: {self.formatar_moeda(pagar_vencidos)}")
            label_vencidos.setStyleSheet("color: #c0392b; font-weight: bold;")
            pagar_layout.addWidget(label_vencidos)
        cards_layout.addWidget(card_pagar)
        
        # Card Saldo
        saldo = total_receber - total_pagar
        card_saldo = QFrame()
        card_saldo.setObjectName("card")
        card_saldo.setStyleSheet(f"QFrame#card {{ background-color: {'#d1ecf1' if saldo >= 0 else '#fff3cd'}; border-left: 5px solid {'#17a2b8' if saldo >= 0 else '#ffc107'}; }}")
        saldo_layout = QVBoxLayout(card_saldo)
        saldo_layout.addWidget(QLabel("📊 Saldo Projetado"))
        label_saldo = QLabel(self.formatar_moeda(abs(saldo)))
        label_saldo.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        label_saldo.setStyleSheet(f"color: {'#17a2b8' if saldo >= 0 else '#ffc107'};")
        saldo_layout.addWidget(label_saldo)
        cards_layout.addWidget(card_saldo)
        
        self.content_layout.addLayout(cards_layout)
        
        # Aging (30/60/90 dias)
        aging_frame = QFrame()
        aging_frame.setObjectName("card")
        aging_layout = QVBoxLayout(aging_frame)
        
        aging_title = QLabel("Análise de Vencimentos (Aging)")
        aging_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        aging_layout.addWidget(aging_title)
        
        # Calcular aging
        from datetime import date as date_type
        from typing import Union
        
        def get_date(dt: Union[datetime, date_type]) -> date_type:
            if isinstance(dt, datetime):
                return dt.date()
            return dt
        
        ate_30 = sum([l.valor for l in lancamentos if l.status == StatusLancamento.PENDENTE and get_date(l.data_vencimento) >= hoje and (get_date(l.data_vencimento) - hoje).days <= 30])
        ate_60 = sum([l.valor for l in lancamentos if l.status == StatusLancamento.PENDENTE and (get_date(l.data_vencimento) - hoje).days > 30 and (get_date(l.data_vencimento) - hoje).days <= 60])
        ate_90 = sum([l.valor for l in lancamentos if l.status == StatusLancamento.PENDENTE and (get_date(l.data_vencimento) - hoje).days > 60 and (get_date(l.data_vencimento) - hoje).days <= 90])
        acima_90 = sum([l.valor for l in lancamentos if l.status == StatusLancamento.PENDENTE and (get_date(l.data_vencimento) - hoje).days > 90])
        
        aging_text = f"""
        <table style='width: 100%; border-collapse: collapse;'>
            <tr style='background-color: #f0f0f0; font-weight: bold;'>
                <th style='padding: 10px; text-align: left; border: 1px solid #ddd;'>Período</th>
                <th style='padding: 10px; text-align: right; border: 1px solid #ddd;'>Valor</th>
            </tr>
            <tr>
                <td style='padding: 8px; border: 1px solid #ddd;'>Até 30 dias</td>
                <td style='padding: 8px; text-align: right; border: 1px solid #ddd;'>{self.formatar_moeda(ate_30)}</td>
            </tr>
            <tr style='background-color: #f9f9f9;'>
                <td style='padding: 8px; border: 1px solid #ddd;'>31 a 60 dias</td>
                <td style='padding: 8px; text-align: right; border: 1px solid #ddd;'>{self.formatar_moeda(ate_60)}</td>
            </tr>
            <tr>
                <td style='padding: 8px; border: 1px solid #ddd;'>61 a 90 dias</td>
                <td style='padding: 8px; text-align: right; border: 1px solid #ddd;'>{self.formatar_moeda(ate_90)}</td>
            </tr>
            <tr style='background-color: #f9f9f9;'>
                <td style='padding: 8px; border: 1px solid #ddd;'>Acima de 90 dias</td>
                <td style='padding: 8px; text-align: right; border: 1px solid #ddd;'>{self.formatar_moeda(acima_90)}</td>
            </tr>
        </table>
        """
        
        aging_label = QLabel()
        aging_label.setTextFormat(Qt.TextFormat.RichText)
        aging_label.setText(aging_text)
        aging_layout.addWidget(aging_label)
        
        self.content_layout.addWidget(aging_frame)
        self.content_layout.addStretch()
    
    def show_resumo_parceiros(self):
        """Exibe resumo por cliente/fornecedor"""
        self.clear_content()
        
        for btn in self.menu_buttons:
            btn.setChecked(False)
        self.btn_relatorios.setChecked(True)
        
        if not self.submenu_relatorios.isVisible():
            self.submenu_relatorios.setVisible(True)
            self.btn_relatorios.setText("Relatorios                   ▲")
        
        title = QLabel("Resumo por Cliente/Fornecedor")
        title.setObjectName("pageTitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.content_layout.addWidget(title)
        
        # Tabs para Clientes e Fornecedores
        tabs = QTabWidget()
        
        # Tab Clientes
        tab_clientes = QWidget()
        layout_clientes = QVBoxLayout(tab_clientes)
        
        table_clientes = QTableWidget()
        table_clientes.setColumnCount(4)
        table_clientes.setHorizontalHeaderLabels(["Cliente", "Total Recebido", "A Receber", "Total"])
        vheader = table_clientes.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        header_cli = table_clientes.horizontalHeader()
        if header_cli:
            header_cli.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_clientes.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table_clientes.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Processar dados de clientes
        clientes_data = {}
        lancamentos = database.listar_lancamentos()
        
        for lanc in lancamentos:
            if lanc.tipo == TipoLancamento.RECEITA and lanc.pessoa:
                if lanc.pessoa not in clientes_data:
                    clientes_data[lanc.pessoa] = {"recebido": 0, "a_receber": 0}
                
                if lanc.status == StatusLancamento.PAGO:
                    clientes_data[lanc.pessoa]["recebido"] += lanc.valor
                else:
                    clientes_data[lanc.pessoa]["a_receber"] += lanc.valor
        
        for cliente, dados in sorted(clientes_data.items()):
            row = table_clientes.rowCount()
            table_clientes.insertRow(row)
            
            table_clientes.setItem(row, 0, QTableWidgetItem(cliente))
            table_clientes.setItem(row, 1, QTableWidgetItem(self.formatar_moeda(dados["recebido"])))
            table_clientes.setItem(row, 2, QTableWidgetItem(self.formatar_moeda(dados["a_receber"])))
            total = dados["recebido"] + dados["a_receber"]
            table_clientes.setItem(row, 3, QTableWidgetItem(self.formatar_moeda(total)))
        
        table_clientes.resizeColumnsToContents()
        layout_clientes.addWidget(table_clientes)
        
        # Tab Fornecedores
        tab_fornecedores = QWidget()
        layout_fornecedores = QVBoxLayout(tab_fornecedores)
        
        table_fornecedores = QTableWidget()
        table_fornecedores.setColumnCount(4)
        table_fornecedores.setHorizontalHeaderLabels(["Fornecedor", "Total Pago", "A Pagar", "Total"])
        vheader = table_fornecedores.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        header_forn = table_fornecedores.horizontalHeader()
        if header_forn:
            header_forn.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_fornecedores.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table_fornecedores.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Processar dados de fornecedores
        fornecedores_data = {}
        
        for lanc in lancamentos:
            if lanc.tipo == TipoLancamento.DESPESA and lanc.pessoa:
                if lanc.pessoa not in fornecedores_data:
                    fornecedores_data[lanc.pessoa] = {"pago": 0, "a_pagar": 0}
                
                if lanc.status == StatusLancamento.PAGO:
                    fornecedores_data[lanc.pessoa]["pago"] += lanc.valor
                else:
                    fornecedores_data[lanc.pessoa]["a_pagar"] += lanc.valor
        
        for fornecedor, dados in sorted(fornecedores_data.items()):
            row = table_fornecedores.rowCount()
            table_fornecedores.insertRow(row)
            
            table_fornecedores.setItem(row, 0, QTableWidgetItem(fornecedor))
            table_fornecedores.setItem(row, 1, QTableWidgetItem(self.formatar_moeda(dados["pago"])))
            table_fornecedores.setItem(row, 2, QTableWidgetItem(self.formatar_moeda(dados["a_pagar"])))
            total = dados["pago"] + dados["a_pagar"]
            table_fornecedores.setItem(row, 3, QTableWidgetItem(self.formatar_moeda(total)))
        
        table_fornecedores.resizeColumnsToContents()
        layout_fornecedores.addWidget(table_fornecedores)
        
        tabs.addTab(tab_clientes, "Clientes")
        tabs.addTab(tab_fornecedores, "Fornecedores")
        
        self.content_layout.addWidget(tabs)
        self.content_layout.addStretch()
    
    def show_analise_categorias(self):
        """Exibe análise de categorias"""
        self.clear_content()
        
        for btn in self.menu_buttons:
            btn.setChecked(False)
        self.btn_relatorios.setChecked(True)
        
        if not self.submenu_relatorios.isVisible():
            self.submenu_relatorios.setVisible(True)
            self.btn_relatorios.setText("Relatorios                   ▲")
        
        title = QLabel("Análise de Categorias")
        title.setObjectName("pageTitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.content_layout.addWidget(title)
        
        # Filtros de período
        filtros_layout = QHBoxLayout()
        filtros_layout.addWidget(QLabel("De:"))
        self.date_categoria_de = QDateEdit()
        self.date_categoria_de.setDate(QDate.currentDate().addMonths(-1))
        self.date_categoria_de.setCalendarPopup(True)
        self.date_categoria_de.setDisplayFormat("dd/MM/yyyy")
        filtros_layout.addWidget(self.date_categoria_de)
        
        filtros_layout.addWidget(QLabel("Até:"))
        self.date_categoria_ate = QDateEdit()
        self.date_categoria_ate.setDate(QDate.currentDate())
        self.date_categoria_ate.setCalendarPopup(True)
        self.date_categoria_ate.setDisplayFormat("dd/MM/yyyy")
        filtros_layout.addWidget(self.date_categoria_ate)
        
        btn_gerar = QPushButton("🔄 Atualizar")
        btn_gerar.setObjectName("primaryButton")
        btn_gerar.clicked.connect(self.gerar_analise_categorias)
        filtros_layout.addWidget(btn_gerar)
        
        btn_excel = QPushButton("📊 Exportar Excel")
        btn_excel.setObjectName("successButton")
        btn_excel.clicked.connect(self.exportar_categorias_excel)
        filtros_layout.addWidget(btn_excel)
        
        btn_pdf = QPushButton("📄 Exportar PDF")
        btn_pdf.setObjectName("successButton")
        btn_pdf.clicked.connect(self.exportar_categorias_pdf)
        filtros_layout.addWidget(btn_pdf)
        
        filtros_layout.addStretch()
        self.content_layout.addLayout(filtros_layout)
        
        # Container para os dados
        self.categorias_container = QWidget()
        self.categorias_layout = QVBoxLayout(self.categorias_container)
        self.content_layout.addWidget(self.categorias_container)
        
        self.gerar_analise_categorias()
        self.content_layout.addStretch()
    
    def gerar_analise_categorias(self):
        """Gera análise de categorias"""
        # Limpar layout anterior
        for i in reversed(range(self.categorias_layout.count())):
            item = self.categorias_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        
        data_inicio = self.date_categoria_de.date().toPyDate()
        data_fim = self.date_categoria_ate.date().toPyDate()
        
        lancamentos = database.listar_lancamentos()
        lancamentos_periodo = [
            l for l in lancamentos 
            if l.status == StatusLancamento.PAGO and l.data_pagamento and
            data_inicio <= l.data_pagamento.date() <= data_fim
        ]
        
        # Separar por tipo
        receitas = {}
        despesas = {}
        
        for lanc in lancamentos_periodo:
            if lanc.tipo == TipoLancamento.RECEITA:
                if lanc.categoria not in receitas:
                    receitas[lanc.categoria] = {}
                if lanc.subcategoria not in receitas[lanc.categoria]:
                    receitas[lanc.categoria][lanc.subcategoria] = 0
                receitas[lanc.categoria][lanc.subcategoria] += lanc.valor
            else:
                if lanc.categoria not in despesas:
                    despesas[lanc.categoria] = {}
                if lanc.subcategoria not in despesas[lanc.categoria]:
                    despesas[lanc.categoria][lanc.subcategoria] = 0
                despesas[lanc.categoria][lanc.subcategoria] += lanc.valor
        
        # Tabela Receitas com Scroll
        receitas_frame = QFrame()
        receitas_frame.setObjectName("card")
        receitas_main_layout = QVBoxLayout(receitas_frame)
        
        receitas_title = QLabel("💰 RECEITAS")
        receitas_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        receitas_title.setStyleSheet("color: #1e8449;")
        receitas_title.setWordWrap(True)
        receitas_main_layout.addWidget(receitas_title)
        
        # ScrollArea para receitas
        receitas_scroll = QScrollArea()
        receitas_scroll.setWidgetResizable(True)
        receitas_scroll.setMaximumHeight(400)
        receitas_scroll.setFrameShape(QFrame.Shape.NoFrame)
        receitas_scroll.setStyleSheet("QScrollArea { background-color: white; }")
        receitas_content = QWidget()
        receitas_content.setStyleSheet("background-color: white;")
        receitas_layout = QVBoxLayout(receitas_content)
        receitas_scroll.setWidget(receitas_content)
        
        total_receitas = 0
        for categoria in sorted(receitas.keys()):
            # Calcular total da categoria
            total_categoria = sum(receitas[categoria].values())
            cat_label = QLabel(f"<b>{categoria} ({self.formatar_moeda(total_categoria)})</b>")
            cat_label.setStyleSheet("font-size: 12pt; color: #2c3e50; padding-top: 10px;")
            cat_label.setWordWrap(True)
            cat_label.setTextFormat(Qt.TextFormat.RichText)
            cat_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            receitas_layout.addWidget(cat_label)
            
            for subcategoria, valor in sorted(receitas[categoria].items()):
                total_receitas += valor
                sub_label = QLabel(f"  • {subcategoria}: <span style='color: #1e8449; font-weight: bold;'>{self.formatar_moeda(valor)}</span>")
                sub_label.setWordWrap(True)
                sub_label.setTextFormat(Qt.TextFormat.RichText)
                sub_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
                receitas_layout.addWidget(sub_label)
        
        receitas_main_layout.addWidget(receitas_scroll)
        
        total_rec_label = QLabel(f"<b>TOTAL: {self.formatar_moeda(total_receitas)}</b>")
        total_rec_label.setStyleSheet("font-size: 14pt; color: #1e8449; margin-top: 10px; padding: 10px; background-color: #d4edda;")
        total_rec_label.setWordWrap(True)
        receitas_main_layout.addWidget(total_rec_label)
        
        self.categorias_layout.addWidget(receitas_frame)
        
        # Tabela Despesas com Scroll
        despesas_frame = QFrame()
        despesas_frame.setObjectName("card")
        despesas_main_layout = QVBoxLayout(despesas_frame)
        
        despesas_title = QLabel("💳 DESPESAS")
        despesas_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        despesas_title.setStyleSheet("color: #e74c3c;")
        despesas_title.setWordWrap(True)
        despesas_main_layout.addWidget(despesas_title)
        
        # ScrollArea para despesas
        despesas_scroll = QScrollArea()
        despesas_scroll.setWidgetResizable(True)
        despesas_scroll.setMaximumHeight(400)
        despesas_scroll.setFrameShape(QFrame.Shape.NoFrame)
        despesas_scroll.setStyleSheet("QScrollArea { background-color: white; }")
        despesas_content = QWidget()
        despesas_content.setStyleSheet("background-color: white;")
        despesas_layout = QVBoxLayout(despesas_content)
        despesas_scroll.setWidget(despesas_content)
        
        total_despesas = 0
        for categoria in sorted(despesas.keys()):
            # Calcular total da categoria
            total_categoria = sum(despesas[categoria].values())
            cat_label = QLabel(f"<b>{categoria} ({self.formatar_moeda(total_categoria)})</b>")
            cat_label.setStyleSheet("font-size: 12pt; color: #2c3e50; padding-top: 10px;")
            cat_label.setWordWrap(True)
            cat_label.setTextFormat(Qt.TextFormat.RichText)
            cat_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            despesas_layout.addWidget(cat_label)
            
            for subcategoria, valor in sorted(despesas[categoria].items()):
                total_despesas += valor
                sub_label = QLabel(f"  • {subcategoria}: <span style='color: #e74c3c; font-weight: bold;'>{self.formatar_moeda(valor)}</span>")
                sub_label.setWordWrap(True)
                sub_label.setTextFormat(Qt.TextFormat.RichText)
                sub_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
                despesas_layout.addWidget(sub_label)
        
        despesas_main_layout.addWidget(despesas_scroll)
        
        total_desp_label = QLabel(f"<b>TOTAL: {self.formatar_moeda(total_despesas)}</b>")
        total_desp_label.setStyleSheet("font-size: 14pt; color: #e74c3c; margin-top: 10px; padding: 10px; background-color: #f8d7da;")
        total_desp_label.setWordWrap(True)
        despesas_main_layout.addWidget(total_desp_label)
        
        self.categorias_layout.addWidget(despesas_frame)
        
        # Resultado
        resultado = total_receitas - total_despesas
        resultado_frame = QFrame()
        resultado_frame.setObjectName("card")
        resultado_layout = QVBoxLayout(resultado_frame)
        
        resultado_texto = "LUCRO" if resultado >= 0 else "PREJUÍZO"
        cor = "#1e8449" if resultado >= 0 else "#e74c3c"
        bg_cor = "#d4edda" if resultado >= 0 else "#f8d7da"
        
        resultado_label = QLabel(f"<b>RESULTADO: {resultado_texto} de {self.formatar_moeda(abs(resultado))}</b>")
        resultado_label.setStyleSheet(f"font-size: 16pt; color: {cor}; padding: 15px; background-color: {bg_cor};")
        resultado_layout.addWidget(resultado_label)
        
        self.categorias_layout.addWidget(resultado_frame)
    
    def show_comparativo_periodos(self):
        """Exibe comparativo de períodos"""
        self.clear_content()
        
        for btn in self.menu_buttons:
            btn.setChecked(False)
        self.btn_relatorios.setChecked(True)
        
        if not self.submenu_relatorios.isVisible():
            self.submenu_relatorios.setVisible(True)
            self.btn_relatorios.setText("Relatorios                   ▲")
        
        title = QLabel("Comparativo de Períodos")
        title.setObjectName("pageTitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.content_layout.addWidget(title)
        
        # Seleção de tipo de comparação
        filtros_layout = QHBoxLayout()
        filtros_layout.addWidget(QLabel("Comparar:"))
        
        self.combo_tipo_comparacao = QComboBox()
        self.combo_tipo_comparacao.addItems(["Últimos 6 Meses", "Últimos 12 Meses", "Por Trimestre", "Por Ano"])
        filtros_layout.addWidget(self.combo_tipo_comparacao)
        
        btn_gerar = QPushButton("🔄 Gerar Comparativo")
        btn_gerar.setObjectName("primaryButton")
        btn_gerar.clicked.connect(self.gerar_comparativo)
        filtros_layout.addWidget(btn_gerar)
        
        filtros_layout.addStretch()
        self.content_layout.addLayout(filtros_layout)
        
        # Tabela de comparação
        self.table_comparativo = QTableWidget()
        self.table_comparativo.setColumnCount(5)
        self.table_comparativo.setHorizontalHeaderLabels(["Período", "Receitas", "Despesas", "Resultado", "Variação %"])
        vheader = self.table_comparativo.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        header_comp = self.table_comparativo.horizontalHeader()
        if header_comp:
            # Ajustar larguras das colunas
            header_comp.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Período
            header_comp.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Receitas
            header_comp.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Despesas
            header_comp.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Resultado
            header_comp.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Variação %
        self.table_comparativo.setAlternatingRowColors(True)
        self.table_comparativo.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_comparativo.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.content_layout.addWidget(self.table_comparativo)
        
        self.gerar_comparativo()
        self.content_layout.addStretch()
    
    def gerar_comparativo(self):
        """Gera o comparativo de períodos"""
        self.table_comparativo.setRowCount(0)
        
        tipo = self.combo_tipo_comparacao.currentText()
        lancamentos = database.listar_lancamentos()
        hoje = datetime.now()
        
        periodos = []
        
        if tipo == "Últimos 6 Meses":
            for i in range(6):
                data = hoje - relativedelta(months=i)
                mes_nome = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                           "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"][data.month - 1]
                periodos.append({
                    "nome": f"{mes_nome}/{data.year}",
                    "inicio": datetime(data.year, data.month, 1).date(),
                    "fim": (datetime(data.year, data.month, 1) + relativedelta(months=1) - relativedelta(days=1)).date()
                })
        
        elif tipo == "Últimos 12 Meses":
            for i in range(12):
                data = hoje - relativedelta(months=i)
                mes_nome = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                           "Jul", "Ago", "Set", "Out", "Nov", "Dez"][data.month - 1]
                periodos.append({
                    "nome": f"{mes_nome}/{data.year}",
                    "inicio": datetime(data.year, data.month, 1).date(),
                    "fim": (datetime(data.year, data.month, 1) + relativedelta(months=1) - relativedelta(days=1)).date()
                })
        
        elif tipo == "Por Trimestre":
            for i in range(4):
                data = hoje - relativedelta(months=i*3)
                trimestre = (data.month - 1) // 3 + 1
                periodos.append({
                    "nome": f"Q{trimestre}/{data.year}",
                    "inicio": datetime(data.year, (trimestre-1)*3 + 1, 1).date(),
                    "fim": (datetime(data.year, trimestre*3, 1) + relativedelta(months=1) - relativedelta(days=1)).date()
                })
        
        else:  # Por Ano
            for i in range(3):
                ano = hoje.year - i
                periodos.append({
                    "nome": str(ano),
                    "inicio": datetime(ano, 1, 1).date(),
                    "fim": datetime(ano, 12, 31).date()
                })
        
        periodos.reverse()
        receitas_anterior = None
        
        for periodo in periodos:
            receitas = sum([l.valor for l in lancamentos 
                          if l.tipo == TipoLancamento.RECEITA and 
                          l.status == StatusLancamento.PAGO and
                          l.data_pagamento and
                          periodo["inicio"] <= l.data_pagamento.date() <= periodo["fim"]])
            
            despesas = sum([l.valor for l in lancamentos 
                          if l.tipo == TipoLancamento.DESPESA and 
                          l.status == StatusLancamento.PAGO and
                          l.data_pagamento and
                          periodo["inicio"] <= l.data_pagamento.date() <= periodo["fim"]])
            
            resultado = receitas - despesas
            
            # Calcular variação percentual baseada nas RECEITAS
            if receitas_anterior is not None and receitas_anterior != 0:
                variacao = ((receitas - receitas_anterior) / receitas_anterior) * 100
            else:
                variacao = 0
            
            row = self.table_comparativo.rowCount()
            self.table_comparativo.insertRow(row)
            
            self.table_comparativo.setItem(row, 0, QTableWidgetItem(periodo["nome"]))
            
            receitas_item = QTableWidgetItem(self.formatar_moeda(receitas))
            receitas_item.setForeground(QColor("#1e8449"))
            self.table_comparativo.setItem(row, 1, receitas_item)
            
            despesas_item = QTableWidgetItem(self.formatar_moeda(despesas))
            despesas_item.setForeground(QColor("#e74c3c"))
            self.table_comparativo.setItem(row, 2, despesas_item)
            
            resultado_item = QTableWidgetItem(self.formatar_moeda(resultado))
            resultado_item.setForeground(QColor("#1e8449" if resultado >= 0 else "#e74c3c"))
            self.table_comparativo.setItem(row, 3, resultado_item)
            
            variacao_texto = f"{variacao:+.1f}%" if receitas_anterior is not None else "-"
            variacao_item = QTableWidgetItem(variacao_texto)
            if receitas_anterior is not None:
                variacao_item.setForeground(QColor("#1e8449" if variacao >= 0 else "#e74c3c"))
            self.table_comparativo.setItem(row, 4, variacao_item)
            
            receitas_anterior = receitas
        
        self.table_comparativo.resizeColumnsToContents()
    
    def show_indicadores(self):
        """Exibe indicadores financeiros"""
        self.clear_content()
        
        for btn in self.menu_buttons:
            btn.setChecked(False)
        self.btn_relatorios.setChecked(True)
        
        if not self.submenu_relatorios.isVisible():
            self.submenu_relatorios.setVisible(True)
            self.btn_relatorios.setText("Relatorios                   ▲")
        
        title = QLabel("Indicadores Financeiros")
        title.setObjectName("pageTitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.content_layout.addWidget(title)
        
        lancamentos = database.listar_lancamentos()
        contas = database.listar_contas()
        hoje = datetime.now().date()
        
        # Calcular indicadores
        total_caixa = sum([c.saldo_inicial for c in contas])
        
        receitas_pagas = sum([l.valor for l in lancamentos if l.tipo == TipoLancamento.RECEITA and l.status == StatusLancamento.PAGO])
        despesas_pagas = sum([l.valor for l in lancamentos if l.tipo == TipoLancamento.DESPESA and l.status == StatusLancamento.PAGO])
        
        contas_receber = sum([l.valor for l in lancamentos if l.tipo == TipoLancamento.RECEITA and l.status == StatusLancamento.PENDENTE])
        contas_pagar = sum([l.valor for l in lancamentos if l.tipo == TipoLancamento.DESPESA and l.status == StatusLancamento.PENDENTE])
        
        # Liquidez Corrente
        liquidez = (total_caixa + contas_receber) / contas_pagar if contas_pagar > 0 else 0
        
        # Margem Operacional
        margem = ((receitas_pagas - despesas_pagas) / receitas_pagas * 100) if receitas_pagas > 0 else 0
        
        # Ticket Médio
        num_receitas = len([l for l in lancamentos if l.tipo == TipoLancamento.RECEITA and l.status == StatusLancamento.PAGO])
        ticket_medio = receitas_pagas / num_receitas if num_receitas > 0 else 0
        
        # Ciclo de Caixa (média de dias para recebimento)
        dias_recebimento = []
        for l in lancamentos:
            if l.tipo == TipoLancamento.RECEITA and l.status == StatusLancamento.PAGO and l.data_pagamento:
                # Converter para date() se necessário
                if isinstance(l.data_pagamento, datetime):
                    data_pag = l.data_pagamento.date()
                else:
                    data_pag = l.data_pagamento
                
                if isinstance(l.data_vencimento, datetime):
                    data_venc = l.data_vencimento.date()
                else:
                    data_venc = l.data_vencimento
                
                dias = (data_pag - data_venc).days
                dias_recebimento.append(dias)
        
        ciclo_caixa = sum(dias_recebimento) / len(dias_recebimento) if dias_recebimento else 0
        
        # Grid de cards
        grid_layout = QHBoxLayout()
        
        # Card Liquidez
        card1 = self.criar_card_indicador("💰 Liquidez Corrente", 
                                          f"{liquidez:.2f}", 
                                          "Capacidade de pagar dívidas",
                                          "#17a2b8" if liquidez >= 1 else "#ffc107")
        grid_layout.addWidget(card1)
        
        # Card Margem
        card2 = self.criar_card_indicador("📊 Margem Operacional", 
                                          f"{margem:.1f}%", 
                                          "Lucratividade das operações",
                                          "#1e8449" if margem > 0 else "#e74c3c")
        grid_layout.addWidget(card2)
        
        # Card Ticket Médio
        card3 = self.criar_card_indicador("🎫 Ticket Médio", 
                                          self.formatar_moeda(ticket_medio), 
                                          "Valor médio por receita",
                                          "#6c757d")
        grid_layout.addWidget(card3)
        
        self.content_layout.addLayout(grid_layout)
        
        # Segunda linha
        grid_layout2 = QHBoxLayout()
        
        # Card Ciclo de Caixa
        card4 = self.criar_card_indicador("🔄 Ciclo de Caixa", 
                                          f"{ciclo_caixa:.0f} dias", 
                                          "Tempo médio de recebimento",
                                          "#6f42c1")
        grid_layout2.addWidget(card4)
        
        # Card Saldo
        saldo_total = receitas_pagas - despesas_pagas
        card5 = self.criar_card_indicador("💵 Saldo Realizado", 
                                          self.formatar_moeda(saldo_total), 
                                          "Resultado acumulado",
                                          "#1e8449" if saldo_total >= 0 else "#e74c3c")
        grid_layout2.addWidget(card5)
        
        # Card Projeção
        saldo_projetado = saldo_total + contas_receber - contas_pagar
        card6 = self.criar_card_indicador("🔮 Saldo Projetado", 
                                          self.formatar_moeda(saldo_projetado), 
                                          "Considerando pendências",
                                          "#1e8449" if saldo_projetado >= 0 else "#e74c3c")
        grid_layout2.addWidget(card6)
        
        self.content_layout.addLayout(grid_layout2)
        self.content_layout.addStretch()
    
    def criar_card_indicador(self, titulo, valor, descricao, cor):
        """Cria um card de indicador"""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(f"QFrame#card {{ border-left: 5px solid {cor}; }}")
        layout = QVBoxLayout(card)
        
        titulo_label = QLabel(titulo)
        titulo_label.setFont(QFont("Segoe UI", 11))
        titulo_label.setStyleSheet("color: #666;")
        layout.addWidget(titulo_label)
        
        valor_label = QLabel(valor)
        valor_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        valor_label.setStyleSheet(f"color: {cor};")
        layout.addWidget(valor_label)
        
        desc_label = QLabel(descricao)
        desc_label.setFont(QFont("Segoe UI", 9))
        desc_label.setStyleSheet("color: #999;")
        layout.addWidget(desc_label)
        
        return card
    
    def exportar_categorias_excel(self):
        """Exporta análise de categorias para Excel"""
        try:
            import pandas as pd
            
            # Obter período selecionado
            data_inicio = self.date_categoria_de.date().toPyDate()
            data_fim = self.date_categoria_ate.date().toPyDate()
            
            # Diálogo para salvar
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Análise de Categorias em Excel",
                f"analise_categorias_{data_inicio.strftime('%Y%m%d')}_{data_fim.strftime('%Y%m%d')}.xlsx",
                "Excel Files (*.xlsx)"
            )
            
            if not file_path:
                return
            
            # Obter dados
            lancamentos = database.listar_lancamentos()
            lancamentos_periodo = [
                l for l in lancamentos 
                if l.status == StatusLancamento.PAGO and l.data_pagamento and
                data_inicio <= l.data_pagamento.date() <= data_fim
            ]
            
            # Separar por tipo
            receitas = {}
            despesas = {}
            
            for lanc in lancamentos_periodo:
                if lanc.tipo == TipoLancamento.RECEITA:
                    if lanc.categoria not in receitas:
                        receitas[lanc.categoria] = {}
                    if lanc.subcategoria not in receitas[lanc.categoria]:
                        receitas[lanc.categoria][lanc.subcategoria] = 0
                    receitas[lanc.categoria][lanc.subcategoria] += lanc.valor
                else:
                    if lanc.categoria not in despesas:
                        despesas[lanc.categoria] = {}
                    if lanc.subcategoria not in despesas[lanc.categoria]:
                        despesas[lanc.categoria][lanc.subcategoria] = 0
                    despesas[lanc.categoria][lanc.subcategoria] += lanc.valor
            
            # Criar DataFrames
            data_receitas = []
            for categoria in sorted(receitas.keys()):
                for subcategoria, valor in sorted(receitas[categoria].items()):
                    data_receitas.append({
                        'Tipo': 'RECEITA',
                        'Categoria': categoria,
                        'Subcategoria': subcategoria,
                        'Valor': float(valor)
                    })
            
            data_despesas = []
            for categoria in sorted(despesas.keys()):
                for subcategoria, valor in sorted(despesas[categoria].items()):
                    data_despesas.append({
                        'Tipo': 'DESPESA',
                        'Categoria': categoria,
                        'Subcategoria': subcategoria,
                        'Valor': float(valor)
                    })
            
            # Criar Excel com múltiplas abas
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                if data_receitas:
                    df_receitas = pd.DataFrame(data_receitas)
                    df_receitas.to_excel(writer, sheet_name='Receitas', index=False)
                
                if data_despesas:
                    df_despesas = pd.DataFrame(data_despesas)
                    df_despesas.to_excel(writer, sheet_name='Despesas', index=False)
                
                # Aba resumo
                total_receitas = sum([d['Valor'] for d in data_receitas])
                total_despesas = sum([d['Valor'] for d in data_despesas])
                df_resumo = pd.DataFrame([
                    {'Descrição': 'Total Receitas', 'Valor': total_receitas},
                    {'Descrição': 'Total Despesas', 'Valor': total_despesas},
                    {'Descrição': 'Resultado', 'Valor': total_receitas - total_despesas}
                ])
                df_resumo.to_excel(writer, sheet_name='Resumo', index=False)
            
            QMessageBox.information(self, "Sucesso", f"Análise de categorias exportada com sucesso!\n{file_path}")
            
        except ImportError:
            QMessageBox.warning(self, "Erro", "Biblioteca pandas não instalada.\nInstale com: pip install pandas openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar Excel: {str(e)}")
    
    def exportar_categorias_pdf(self):
        """Exporta análise de categorias para PDF"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            
            # Obter período selecionado
            data_inicio = self.date_categoria_de.date().toPyDate()
            data_fim = self.date_categoria_ate.date().toPyDate()
            
            # Diálogo para salvar
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Análise de Categorias em PDF",
                f"analise_categorias_{data_inicio.strftime('%Y%m%d')}_{data_fim.strftime('%Y%m%d')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if not file_path:
                return
            
            # Obter dados
            lancamentos = database.listar_lancamentos()
            lancamentos_periodo = [
                l for l in lancamentos 
                if l.status == StatusLancamento.PAGO and l.data_pagamento and
                data_inicio <= l.data_pagamento.date() <= data_fim
            ]
            
            # Separar por tipo
            receitas = {}
            despesas = {}
            
            for lanc in lancamentos_periodo:
                if lanc.tipo == TipoLancamento.RECEITA:
                    if lanc.categoria not in receitas:
                        receitas[lanc.categoria] = {}
                    if lanc.subcategoria not in receitas[lanc.categoria]:
                        receitas[lanc.categoria][lanc.subcategoria] = 0
                    receitas[lanc.categoria][lanc.subcategoria] += lanc.valor
                else:
                    if lanc.categoria not in despesas:
                        despesas[lanc.categoria] = {}
                    if lanc.subcategoria not in despesas[lanc.categoria]:
                        despesas[lanc.categoria][lanc.subcategoria] = 0
                    despesas[lanc.categoria][lanc.subcategoria] += lanc.valor
            
            # Criar PDF
            doc = SimpleDocTemplate(file_path, pagesize=A4, 
                                  topMargin=2*cm, bottomMargin=2*cm,
                                  leftMargin=2*cm, rightMargin=2*cm)
            
            elements = []
            styles = getSampleStyleSheet()
            
            # Título
            title = Paragraph(f"<b>Análise de Categorias</b><br/>Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}", styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 0.5*cm))
            
            # Inicializar totais
            total_receitas = 0
            total_despesas = 0
            
            # Tabela Receitas
            if receitas:
                elements.append(Paragraph("<b>RECEITAS</b>", styles['Heading2']))
                elements.append(Spacer(1, 0.3*cm))
                
                data_receitas = [['Categoria', 'Subcategoria', 'Valor']]
                
                for categoria in sorted(receitas.keys()):
                    for subcategoria, valor in sorted(receitas[categoria].items()):
                        data_receitas.append([categoria, subcategoria, self.formatar_moeda(valor)])
                        total_receitas += valor
                
                data_receitas.append(['', 'TOTAL', self.formatar_moeda(total_receitas)])
                
                table = Table(data_receitas, colWidths=[6*cm, 6*cm, 4*cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.lightgreen),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.8*cm))
            
            # Tabela Despesas
            if despesas:
                elements.append(Paragraph("<b>DESPESAS</b>", styles['Heading2']))
                elements.append(Spacer(1, 0.3*cm))
                
                data_despesas = [['Categoria', 'Subcategoria', 'Valor']]
                
                for categoria in sorted(despesas.keys()):
                    for subcategoria, valor in sorted(despesas[categoria].items()):
                        data_despesas.append([categoria, subcategoria, self.formatar_moeda(valor)])
                        total_despesas += valor
                
                data_despesas.append(['', 'TOTAL', self.formatar_moeda(total_despesas)])
                
                table = Table(data_despesas, colWidths=[6*cm, 6*cm, 4*cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.lightcoral),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.8*cm))
            
            # Resumo
            if receitas or despesas:
                elements.append(Paragraph("<b>RESUMO</b>", styles['Heading2']))
                elements.append(Spacer(1, 0.3*cm))
                
                resultado = total_receitas - total_despesas
                data_resumo = [
                    ['Total Receitas:', self.formatar_moeda(total_receitas)],
                    ['Total Despesas:', self.formatar_moeda(total_despesas)],
                    ['Resultado:', self.formatar_moeda(resultado)]
                ]
                
                table = Table(data_resumo, colWidths=[10*cm, 6*cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.yellow if resultado >= 0 else colors.lightcoral)
                ]))
                elements.append(table)
            
            # Gerar PDF
            doc.build(elements)
            
            QMessageBox.information(self, "Sucesso", f"Análise de categorias exportada com sucesso!\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {str(e)}")
    
    def show_inadimplencia(self):
        """Exibe relatório de inadimplência"""
        self.clear_content()
        
        for btn in self.menu_buttons:
            btn.setChecked(False)
        self.btn_relatorios.setChecked(True)
        
        if not self.submenu_relatorios.isVisible():
            self.submenu_relatorios.setVisible(True)
            self.btn_relatorios.setText("Relatorios                   ▲")
        
        title = QLabel("Relatório de Inadimplência")
        title.setObjectName("pageTitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.content_layout.addWidget(title)
        
        lancamentos = database.listar_lancamentos()
        hoje = datetime.now().date()
        
        # Filtrar contas a receber vencidas
        vencidas = [l for l in lancamentos 
                   if l.tipo == TipoLancamento.RECEITA and 
                   l.status == StatusLancamento.PENDENTE and 
                   (l.data_vencimento.date() if hasattr(l.data_vencimento, 'date') else l.data_vencimento) < hoje]
        
        total_vencido = sum([l.valor for l in vencidas])
        total_receber = sum([l.valor for l in lancamentos 
                            if l.tipo == TipoLancamento.RECEITA and 
                            l.status == StatusLancamento.PENDENTE])
        
        taxa_inadimplencia = (total_vencido / total_receber * 100) if total_receber > 0 else 0
        
        # Cards de resumo
        cards_layout = QHBoxLayout()
        
        card1 = QFrame()
        card1.setObjectName("card")
        card1.setStyleSheet("QFrame#card { background-color: #f8d7da; border-left: 5px solid #e74c3c; }")
        layout1 = QVBoxLayout(card1)
        layout1.addWidget(QLabel("⚠️ Total Vencido"))
        valor1 = QLabel(self.formatar_moeda(total_vencido))
        valor1.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        valor1.setStyleSheet("color: #e74c3c;")
        layout1.addWidget(valor1)
        cards_layout.addWidget(card1)
        
        card2 = QFrame()
        card2.setObjectName("card")
        card2.setStyleSheet("QFrame#card { background-color: #fff3cd; border-left: 5px solid #ffc107; }")
        layout2 = QVBoxLayout(card2)
        layout2.addWidget(QLabel("📊 Taxa de Inadimplência"))
        valor2 = QLabel(f"{taxa_inadimplencia:.1f}%")
        valor2.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        valor2.setStyleSheet("color: #ffc107;")
        layout2.addWidget(valor2)
        cards_layout.addWidget(card2)
        
        card3 = QFrame()
        card3.setObjectName("card")
        card3.setStyleSheet("QFrame#card { background-color: #f8d7da; border-left: 5px solid #c0392b; }")
        layout3 = QVBoxLayout(card3)
        layout3.addWidget(QLabel("🔢 Contas Vencidas"))
        valor3 = QLabel(str(len(vencidas)))
        valor3.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        valor3.setStyleSheet("color: #c0392b;")
        layout3.addWidget(valor3)
        cards_layout.addWidget(card3)
        
        self.content_layout.addLayout(cards_layout)
        
        # Tabela de contas vencidas
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Cliente", "Descrição", "Vencimento", "Dias em Atraso", "Valor"])
        vheader = table.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        header_inad = table.horizontalHeader()
        if header_inad:
            # Configurar larguras das colunas
            header_inad.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Cliente
            header_inad.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Descrição
            header_inad.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Vencimento
            header_inad.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Dias em Atraso
            header_inad.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Valor
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        for lanc in sorted(vencidas, key=lambda x: x.data_vencimento):
            row = table.rowCount()
            table.insertRow(row)
            
            table.setItem(row, 0, QTableWidgetItem(lanc.pessoa or "-"))
            table.setItem(row, 1, QTableWidgetItem(lanc.descricao))
            
            data_venc = lanc.data_vencimento.date() if hasattr(lanc.data_vencimento, 'date') else lanc.data_vencimento
            table.setItem(row, 2, QTableWidgetItem(data_venc.strftime("%d/%m/%Y")))
            
            dias_atraso = (hoje - data_venc).days
            dias_item = QTableWidgetItem(str(dias_atraso))
            if dias_atraso > 60:
                dias_item.setForeground(QColor("#c0392b"))
            elif dias_atraso > 30:
                dias_item.setForeground(QColor("#e74c3c"))
            else:
                dias_item.setForeground(QColor("#ffc107"))
            table.setItem(row, 3, dias_item)
            
            valor_item = QTableWidgetItem(self.formatar_moeda(lanc.valor))
            valor_item.setForeground(QColor("#e74c3c"))
            table.setItem(row, 4, valor_item)
        
        table.resizeColumnsToContents()
        self.content_layout.addWidget(table)
        self.content_layout.addStretch()
    
    def show_evolucao_patrimonial(self):
        """Exibe evolução patrimonial"""
        self.clear_content()
        
        for btn in self.menu_buttons:
            btn.setChecked(False)
        self.btn_relatorios.setChecked(True)
        
        if not self.submenu_relatorios.isVisible():
            self.submenu_relatorios.setVisible(True)
            self.btn_relatorios.setText("Relatorios                   ▲")
        
        title = QLabel("Evolução Patrimonial")
        title.setObjectName("pageTitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.content_layout.addWidget(title)
        
        # Filtro de período
        filtros_layout = QHBoxLayout()
        filtros_layout.addWidget(QLabel("Período:"))
        
        self.combo_periodo_evolucao = QComboBox()
        self.combo_periodo_evolucao.addItems(["Últimos 6 Meses", "Últimos 12 Meses", "Último Ano", "Últimos 2 Anos"])
        filtros_layout.addWidget(self.combo_periodo_evolucao)
        
        btn_gerar = QPushButton("🔄 Atualizar")
        btn_gerar.setObjectName("primaryButton")
        btn_gerar.clicked.connect(self.gerar_evolucao)
        filtros_layout.addWidget(btn_gerar)
        
        filtros_layout.addStretch()
        self.content_layout.addLayout(filtros_layout)
        
        # Container para gráfico de linha
        self.grafico_linha_frame = QFrame()
        self.grafico_linha_frame.setObjectName("card")
        self.grafico_linha_frame.setMinimumHeight(350)
        self.grafico_linha_layout = QVBoxLayout(self.grafico_linha_frame)
        
        titulo_linha = QLabel("📈 Evolução do Patrimônio")
        titulo_linha.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.grafico_linha_layout.addWidget(titulo_linha)
        
        self.canvas_linha = None  # Será criado no gerar_evolucao
        
        self.content_layout.addWidget(self.grafico_linha_frame)
        
        # Container para gráfico de barras
        self.grafico_barras_frame = QFrame()
        self.grafico_barras_frame.setObjectName("card")
        self.grafico_barras_frame.setMinimumHeight(350)
        self.grafico_barras_layout = QVBoxLayout(self.grafico_barras_frame)
        
        titulo_barras = QLabel("📊 Entradas vs Saídas Mensais")
        titulo_barras.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.grafico_barras_layout.addWidget(titulo_barras)
        
        self.canvas_barras = None  # Será criado no gerar_evolucao
        
        self.content_layout.addWidget(self.grafico_barras_frame)
        
        # Label e título para tabela
        titulo_tabela = QLabel("📋 Detalhamento Mensal")
        titulo_tabela.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo_tabela.setStyleSheet("margin-top: 20px; margin-bottom: 10px;")
        self.content_layout.addWidget(titulo_tabela)
        
        # Tabela de evolução
        self.table_evolucao = QTableWidget()
        self.table_evolucao.setColumnCount(5)
        self.table_evolucao.setHorizontalHeaderLabels(["Período", "Saldo Inicial", "Entradas", "Saídas", "Saldo Final"])
        self.table_evolucao.setMinimumHeight(300)
        
        # Configurar header para stretch (auto ajustável)
        header_evol = self.table_evolucao.horizontalHeader()
        if header_evol:
            header_evol.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Ajustar altura das linhas e ocultar números de linha
        vheader = self.table_evolucao.verticalHeader()
        if vheader:
            vheader.setDefaultSectionSize(40)
            vheader.setVisible(False)
        
        self.table_evolucao.setAlternatingRowColors(True)
        self.table_evolucao.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_evolucao.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.content_layout.addWidget(self.table_evolucao)
        
        self.gerar_evolucao()
        self.content_layout.addStretch()
    
    def gerar_evolucao(self):
        """Gera o relatório de evolução patrimonial"""
        self.table_evolucao.setRowCount(0)
        
        periodo = self.combo_periodo_evolucao.currentText()
        lancamentos = database.listar_lancamentos()
        hoje = datetime.now()
        
        # Determinar meses a mostrar
        if periodo == "Últimos 6 Meses":
            num_meses = 6
        elif periodo == "Últimos 12 Meses":
            num_meses = 12
        elif periodo == "Último Ano":
            num_meses = 12
        else:  # Últimos 2 Anos
            num_meses = 24
        
        # Saldo inicial das contas
        saldo_inicial_total = sum([c.saldo_inicial for c in database.listar_contas()])
        saldo_acumulado = saldo_inicial_total
        
        meses_nomes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                      "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        
        # Listas para armazenar dados dos gráficos
        periodos_lista = []
        saldos_finais = []
        entradas_lista = []
        saidas_lista = []
        saldos_iniciais = []
        
        for i in range(num_meses - 1, -1, -1):
            data = hoje - relativedelta(months=i)
            mes_inicio = datetime(data.year, data.month, 1).date()
            mes_fim = (datetime(data.year, data.month, 1) + relativedelta(months=1) - relativedelta(days=1)).date()
            
            # Calcular entradas e saídas do mês
            entradas = sum([l.valor for l in lancamentos 
                           if l.tipo == TipoLancamento.RECEITA and 
                           l.status == StatusLancamento.PAGO and
                           l.data_pagamento and
                           mes_inicio <= l.data_pagamento.date() <= mes_fim])
            
            saidas = sum([l.valor for l in lancamentos 
                         if l.tipo == TipoLancamento.DESPESA and 
                         l.status == StatusLancamento.PAGO and
                         l.data_pagamento and
                         mes_inicio <= l.data_pagamento.date() <= mes_fim])
            
            saldo_final = saldo_acumulado + entradas - saidas
            
            row = self.table_evolucao.rowCount()
            self.table_evolucao.insertRow(row)
            
            # Período
            if num_meses > 12:
                periodo_texto = f"{meses_nomes[data.month - 1][:3]}/{data.year}"
            else:
                periodo_texto = f"{meses_nomes[data.month - 1]}/{data.year}"
            self.table_evolucao.setItem(row, 0, QTableWidgetItem(periodo_texto))
            
            # Saldo Inicial
            item_inicial = QTableWidgetItem(self.formatar_moeda(saldo_acumulado))
            item_inicial.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_evolucao.setItem(row, 1, item_inicial)
            
            # Entradas
            entradas_item = QTableWidgetItem(self.formatar_moeda(entradas))
            entradas_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            entradas_item.setForeground(QColor("#1e8449"))
            self.table_evolucao.setItem(row, 2, entradas_item)
            
            # Saídas
            saidas_item = QTableWidgetItem(self.formatar_moeda(saidas))
            saidas_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            saidas_item.setForeground(QColor("#e74c3c"))
            self.table_evolucao.setItem(row, 3, saidas_item)
            
            # Saldo Final
            saldo_item = QTableWidgetItem(self.formatar_moeda(saldo_final))
            saldo_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            saldo_item.setForeground(QColor("#1e8449" if saldo_final >= 0 else "#e74c3c"))
            saldo_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table_evolucao.setItem(row, 4, saldo_item)
            
            # Armazenar dados para gráficos
            periodos_lista.append(periodo_texto)
            saldos_iniciais.append(float(saldo_acumulado))
            entradas_lista.append(float(entradas))
            saidas_lista.append(float(saidas))
            saldos_finais.append(float(saldo_final))
            
            saldo_acumulado = saldo_final
        
        # Forçar ocultação dos números de linha após popular tabela
        vheader = self.table_evolucao.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        
        # Gerar gráficos
        self.gerar_grafico_linha_evolucao(periodos_lista, saldos_finais)
        self.gerar_grafico_barras_evolucao(periodos_lista, entradas_lista, saidas_lista)
    
    def gerar_grafico_linha_evolucao(self, periodos, saldos):
        """Gera gráfico de linha da evolução do patrimônio"""
        # Remover canvas antigo se existir
        if self.canvas_linha:
            self.canvas_linha.setParent(None)
        
        # Criar figura e eixo
        fig = Figure(figsize=(12, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        # Cores condicionais
        cores = ['#28a745' if s >= 0 else '#dc3545' for s in saldos]
        
        # Plotar linha
        ax.plot(periodos, saldos, marker='o', linewidth=2.5, markersize=8, 
                color='#4a90e2', label='Saldo Final')
        
        # Preencher área abaixo da linha
        ax.fill_between(range(len(periodos)), saldos, alpha=0.3, color='#4a90e2')
        
        # Linha zero
        ax.axhline(y=0, color='#666', linestyle='--', linewidth=1, alpha=0.5)
        
        # Configurações
        ax.set_xlabel('Período', fontsize=10, fontweight='bold')
        ax.set_ylabel('Saldo (R$)', fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='upper left', framealpha=0.9)
        
        # Rotacionar labels do eixo x se necessário
        if len(periodos) > 12:
            ax.tick_params(axis='x', rotation=45)
        else:
            ax.tick_params(axis='x', rotation=30)
        
        fig.tight_layout()
        
        # Criar canvas e adicionar ao layout
        self.canvas_linha = FigureCanvas(fig)
        self.grafico_linha_layout.addWidget(self.canvas_linha)
    
    def gerar_grafico_barras_evolucao(self, periodos, entradas, saidas):
        """Gera gráfico de barras comparando entradas e saídas"""
        # Remover canvas antigo se existir
        if self.canvas_barras:
            self.canvas_barras.setParent(None)
        
        # Criar figura e eixo
        fig = Figure(figsize=(12, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        # Posições das barras
        x = range(len(periodos))
        largura = 0.35
        
        # Plotar barras
        barras_entradas = ax.bar([i - largura/2 for i in x], entradas, largura, 
                                 label='Entradas', color='#28a745', alpha=0.8)
        barras_saidas = ax.bar([i + largura/2 for i in x], saidas, largura, 
                               label='Saídas', color='#dc3545', alpha=0.8)
        
        # Configurações
        ax.set_xlabel('Período', fontsize=10, fontweight='bold')
        ax.set_ylabel('Valor (R$)', fontsize=10, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(periodos)
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.legend(loc='upper left', framealpha=0.9)
        
        # Rotacionar labels do eixo x se necessário
        if len(periodos) > 12:
            ax.tick_params(axis='x', rotation=45)
        else:
            ax.tick_params(axis='x', rotation=30)
        
        fig.tight_layout()
        
        # Criar canvas e adicionar ao layout
        self.canvas_barras = FigureCanvas(fig)
        self.grafico_barras_layout.addWidget(self.canvas_barras)
    
    # Diálogos
    
    def dialog_nova_conta(self):
        """Diálogo para adicionar nova conta"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Nova Conta Bancaria")
        dialog.setMinimumWidth(450)
        dialog.setMinimumHeight(300)
        
        layout = QFormLayout(dialog)
        
        banco_input = UpperCaseLineEdit()
        agencia_input = UpperCaseLineEdit()
        conta_input = UpperCaseLineEdit()
        saldo_input = QDoubleSpinBox()
        saldo_input.setMaximum(999999999.99)
        saldo_input.setPrefix("R$ ")
        
        layout.addRow("Banco:", banco_input)
        layout.addRow("Agência:", agencia_input)
        layout.addRow("Conta:", conta_input)
        layout.addRow("Saldo Inicial:", saldo_input)
        
        # Botões
        btns_layout = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_salvar = QPushButton("Salvar")
        btn_salvar.setObjectName("primaryButton")
        
        btns_layout.addWidget(btn_cancelar)
        btns_layout.addWidget(btn_salvar)
        layout.addRow(btns_layout)
        
        btn_cancelar.clicked.connect(dialog.reject)
        
        def salvar():
            try:
                conta = ContaBancaria(
                    nome=f"{banco_input.text()} - {conta_input.text()}",
                    banco=banco_input.text(),
                    agencia=agencia_input.text(),
                    conta=conta_input.text(),
                    saldo_inicial=saldo_input.value()
                )
                database.adicionar_conta(conta)
                dialog.accept()
                self.show_contas_bancarias()
                QMessageBox.information(self, "Sucesso", "Conta adicionada com sucesso!")
            except ValueError as e:
                QMessageBox.warning(self, "Atencao", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao adicionar conta: {str(e)}")
        
        btn_salvar.clicked.connect(salvar)
        dialog.exec()
    
    def dialog_editar_conta(self, conta: ContaBancaria, index: int):
        """Diálogo para editar uma conta bancária"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Conta Bancária")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(300)
        
        layout = QFormLayout(dialog)
        
        nome_input = QLineEdit(conta.nome)
        banco_input = QLineEdit(conta.banco)
        agencia_input = QLineEdit(conta.agencia)
        conta_input = QLineEdit(conta.conta)
        saldo_input = QDoubleSpinBox()
        saldo_input.setMaximum(999999999.99)
        saldo_input.setPrefix("R$ ")
        saldo_input.setValue(conta.saldo_inicial)
        
        layout.addRow("Nome da Conta:", nome_input)
        layout.addRow("Banco:", banco_input)
        layout.addRow("Agência:", agencia_input)
        layout.addRow("Conta:", conta_input)
        layout.addRow("Saldo Inicial:", saldo_input)
        
        # Botões
        btns_layout = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_salvar = QPushButton("Salvar")
        btn_salvar.setObjectName("primaryButton")
        
        btns_layout.addWidget(btn_cancelar)
        btns_layout.addWidget(btn_salvar)
        layout.addRow(btns_layout)
        
        btn_cancelar.clicked.connect(dialog.reject)
        
        def salvar():
            try:
                # Atualizar dados da conta
                conta.nome = nome_input.text()
                conta.banco = banco_input.text()
                conta.agencia = agencia_input.text()
                conta.conta = conta_input.text()
                
                # Ajustar saldo atual se o saldo inicial mudou
                diferenca = saldo_input.value() - conta.saldo_inicial
                conta.saldo_inicial = saldo_input.value()
                conta.saldo_atual += diferenca
                
                # Salvar no gerenciador
                # auto-save in SQLite
                
                dialog.accept()
                self.show_contas_bancarias()
                QMessageBox.information(self, "Sucesso", "Conta atualizada com sucesso!")
            except ValueError as e:
                QMessageBox.warning(self, "Atenção", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao atualizar conta: {str(e)}")
        
        btn_salvar.clicked.connect(salvar)
        dialog.exec()
    
    def dialog_novo_lancamento(self, tipo: TipoLancamento):
        """Diálogo para adicionar novo lançamento"""
        dialog = QDialog(self)
        tipo_texto = "Receita" if tipo == TipoLancamento.RECEITA else "Despesa"
        dialog.setWindowTitle(f"Nova {tipo_texto}")
        dialog.setMinimumWidth(550)
        dialog.setMinimumHeight(450)
        
        layout = QFormLayout(dialog)
        
        descricao_input = UpperCaseLineEdit()
        valor_input = QDoubleSpinBox()
        valor_input.setMaximum(999999999.99)
        valor_input.setPrefix("R$ ")
        
        # Categorias
        categorias = [cat for cat in database.listar_categorias() if cat.tipo == tipo]
        categoria_combo = QComboBox()
        categoria_combo.addItems([cat.nome for cat in categorias])
        categoria_combo.setStyleSheet("QComboBox { background-color: white; color: black; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        
        # Subcategorias - atualiza dinamicamente baseado na categoria selecionada
        subcategoria_combo = QComboBox()
        subcategoria_combo.setEditable(True)
        subcategoria_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        subcategoria_combo.setStyleSheet("QComboBox { background-color: white; color: black; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        
        def atualizar_subcategorias():
            subcategoria_combo.clear()
            categoria_selecionada = categoria_combo.currentText()
            if categoria_selecionada:
                for cat in categorias:
                    if cat.nome == categoria_selecionada:
                        subcategoria_combo.addItem("")  # Opção vazia
                        for sub in cat.subcategorias:
                            subcategoria_combo.addItem(sub)
                        break
        
        # Conectar mudança de categoria para atualizar subcategorias
        categoria_combo.currentTextChanged.connect(atualizar_subcategorias)
        atualizar_subcategorias()  # Carregar subcategorias iniciais
        
        vencimento_input = QDateEdit()
        vencimento_input.setSpecialValueText(" ")  # Deixa vazio inicialmente
        vencimento_input.setDate(QDate.currentDate().addDays(-1))  # Um dia antes da data atual para aparecer vazio
        vencimento_input.setMinimumDate(QDate(2000, 1, 1))
        vencimento_input.setCalendarPopup(True)
        vencimento_input.setStyleSheet("QDateEdit { background-color: white; color: black; }")
        
        # ComboBox para selecionar Cliente ou Fornecedor cadastrado
        pessoa_combo = QComboBox()
        pessoa_combo.setEditable(True)  # Permite digitação manual
        pessoa_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        pessoa_combo.setStyleSheet("QComboBox { background-color: white; color: black; } QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #3498db; }")
        
        # Buscar clientes ou fornecedores cadastrados
        if tipo == TipoLancamento.RECEITA:
            clientes = database.listar_clientes()
            pessoa_combo.addItem("")  # Opção vazia
            for cliente in clientes:
                pessoa_combo.addItem(cliente.get("razao_social", "") or cliente.get("nome", ""))
            pessoa_label = "Cliente:"
        else:
            fornecedores = database.listar_fornecedores()
            pessoa_combo.addItem("")  # Opção vazia
            for fornecedor in fornecedores:
                pessoa_combo.addItem(fornecedor.get("razao_social", "") or fornecedor.get("nome", ""))
            pessoa_label = "Fornecedor:"
        
        documento_input = UpperCaseLineEdit()
        
        # Data de Emissão
        data_emissao_input = QDateEdit()
        data_emissao_input.setDate(QDate.currentDate())
        data_emissao_input.setCalendarPopup(True)
        data_emissao_input.setStyleSheet("QDateEdit { background-color: white; color: black; }")
        
        # Competência
        competencia_input = QDateEdit()
        competencia_input.setDate(QDate.currentDate())
        competencia_input.setCalendarPopup(True)
        competencia_input.setDisplayFormat("MM/yyyy")
        competencia_input.setStyleSheet("QDateEdit { background-color: white; color: black; }")
        
        # Data de Liquidação
        data_liquidacao_input = QDateEdit()
        data_liquidacao_input.setSpecialValueText(" ")  # Deixa vazio inicialmente
        data_liquidacao_input.setDate(QDate.currentDate().addDays(-1))  # Um dia antes da data atual para aparecer vazio
        data_liquidacao_input.setMinimumDate(QDate(2000, 1, 1))
        data_liquidacao_input.setCalendarPopup(True)
        data_liquidacao_input.setEnabled(False)  # Desabilitado inicialmente
        data_liquidacao_input.setStyleSheet("QDateEdit { background-color: white; color: black; }")
        
        observacoes_input = UpperCaseTextEdit()
        observacoes_input.setMaximumHeight(100)
        
        # Nova ordem dos campos
        layout.addRow(pessoa_label, pessoa_combo)
        layout.addRow("Categoria:", categoria_combo)
        layout.addRow("Subcategoria:", subcategoria_combo)
        layout.addRow("Nº Documento:", documento_input)
        layout.addRow("Data de Emissão:", data_emissao_input)
        layout.addRow("Competência:", competencia_input)
        layout.addRow("Vencimento:", vencimento_input)
        layout.addRow("Data de Liquidação:", data_liquidacao_input)
        layout.addRow("Descrição:", descricao_input)
        layout.addRow("Valor:", valor_input)
        layout.addRow("Observações:", observacoes_input)
        
        # Botões
        btns_layout = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_salvar = QPushButton("Salvar")
        btn_salvar.setObjectName("primaryButton")
        
        btns_layout.addWidget(btn_cancelar)
        btns_layout.addWidget(btn_salvar)
        layout.addRow(btns_layout)
        
        btn_cancelar.clicked.connect(dialog.reject)
        
        def salvar():
            try:
                qdate = vencimento_input.date()
                data_venc = datetime(qdate.year(), qdate.month(), qdate.day())
                
                lancamento = Lancamento(
                    descricao=descricao_input.text(),
                    valor=valor_input.value(),
                    tipo=tipo,
                    categoria=categoria_combo.currentText(),
                    subcategoria=subcategoria_combo.currentText(),
                    data_vencimento=data_venc,
                    pessoa=pessoa_combo.currentText(),
                    num_documento=documento_input.text(),
                    observacoes=observacoes_input.toPlainText()
                )
                database.adicionar_lancamento(lancamento)
                dialog.accept()
                
                # Atualizar tela apropriada
                if tipo == TipoLancamento.RECEITA:
                    self.show_contas_receber()
                else:
                    self.show_contas_pagar()
                
                QMessageBox.information(self, "Sucesso", f"{tipo_texto} adicionada com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))
        
        btn_salvar.clicked.connect(salvar)
        dialog.exec()
    
    def dialog_pagar_lancamento(self, id_lancamento):
        """Diálogo para pagar um lançamento"""
        lancamento = next((l for l in database.listar_lancamentos() if l.id == id_lancamento), None)
        if not lancamento:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Pagar Lancamento")
        dialog.setMinimumWidth(450)
        dialog.setMinimumHeight(250)
        
        layout = QFormLayout(dialog)
        
        # Informações do lançamento
        layout.addRow("Valor:", QLabel(self.formatar_moeda(lancamento.valor)))
        
        # Conta bancária
        contas = database.listar_contas()
        if not contas:
            QMessageBox.warning(self, "Aviso", "Cadastre uma conta bancária primeiro!")
            return
        
        conta_combo = QComboBox()
        conta_combo.addItems([c.nome for c in contas])
        layout.addRow("Conta:", conta_combo)
        
        # Data de pagamento
        data_input = QDateEdit()
        data_input.setDate(QDate.currentDate())
        data_input.setCalendarPopup(True)
        layout.addRow("Data Pagamento:", data_input)
        
        # Valor de juros
        juros_input = QDoubleSpinBox()
        juros_input.setPrefix("R$ ")
        juros_input.setDecimals(2)
        juros_input.setMinimum(0.00)
        juros_input.setMaximum(999999.99)
        juros_input.setValue(0.00)
        juros_input.setStyleSheet("QDoubleSpinBox { background-color: white; color: black; }")
        layout.addRow("Juros:", juros_input)
        
        # Valor total (valor original + juros)
        valor_total_label = QLabel(self.formatar_moeda(lancamento.valor))
        valor_total_label.setStyleSheet("font-weight: bold; color: #007bff;")
        layout.addRow("Valor Total:", valor_total_label)
        
        # Atualizar valor total quando juros mudar
        def atualizar_total():
            total = lancamento.valor + juros_input.value()
            valor_total_label.setText(self.formatar_moeda(total))
        
        juros_input.valueChanged.connect(atualizar_total)
        
        # Botões
        btns_layout = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_pagar = QPushButton("Confirmar Pagamento")
        btn_pagar.setObjectName("primaryButton")
        
        btns_layout.addWidget(btn_cancelar)
        btns_layout.addWidget(btn_pagar)
        layout.addRow(btns_layout)
        
        btn_cancelar.clicked.connect(dialog.reject)
        
        def pagar():
            conta_idx = conta_combo.currentIndex()
            conta_nome = contas[conta_idx].nome
            
            qdate = data_input.date()
            data_pag = datetime(qdate.year(), qdate.month(), qdate.day())
            
            juros = juros_input.value()
            
            if database.pagar_lancamento(id_lancamento, conta_nome, data_pag, juros):
                dialog.accept()
                
                # Atualizar tela
                if lancamento.tipo == TipoLancamento.RECEITA:
                    self.show_contas_receber()
                else:
                    self.show_contas_pagar()
                
                valor_total = lancamento.valor + juros
                msg = f"Pagamento realizado com sucesso!\n\nValor Original: {self.formatar_moeda(lancamento.valor)}\nJuros: {self.formatar_moeda(juros)}\nValor Total Pago: {self.formatar_moeda(valor_total)}"
                QMessageBox.information(self, "Sucesso", msg)
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível realizar o pagamento. Verifique o saldo.")
        
        btn_pagar.clicked.connect(pagar)
        dialog.exec()
    
    # Métodos de filtro para Contas a Pagar
    def filtrar_pagar_vence_hoje(self):
        """Filtra contas a pagar que vencem hoje"""
        from datetime import datetime
        hoje = datetime.now().date()
        if hasattr(self, 'data_inicio_pagar') and hasattr(self, 'data_fim_pagar'):
            self.data_inicio_pagar.setDate(QDate(hoje.year, hoje.month, hoje.day))
            self.data_fim_pagar.setDate(QDate(hoje.year, hoje.month, hoje.day))
            self.atualizar_contas_pagar()
    
    def filtrar_pagar_vencidos(self):
        """Filtra contas a pagar vencidas"""
        from datetime import datetime
        hoje = datetime.now().date()
        if hasattr(self, 'data_inicio_pagar') and hasattr(self, 'data_fim_pagar'):
            self.data_inicio_pagar.setDate(QDate(2000, 1, 1))
            self.data_fim_pagar.setDate(QDate(hoje.year, hoje.month, hoje.day))
            self.combo_status_pagar.setCurrentText("Vencidas")
            self.atualizar_contas_pagar()
    
    def filtrar_pagar_proximos_7dias(self):
        """Filtra contas a pagar dos próximos 7 dias"""
        from datetime import datetime, timedelta
        hoje = datetime.now().date()
        fim = hoje + timedelta(days=7)
        if hasattr(self, 'data_inicio_pagar') and hasattr(self, 'data_fim_pagar'):
            self.data_inicio_pagar.setDate(QDate(hoje.year, hoje.month, hoje.day))
            self.data_fim_pagar.setDate(QDate(fim.year, fim.month, fim.day))
            self.atualizar_contas_pagar()
    
    def filtrar_pagar_este_mes(self):
        """Filtra contas a pagar do mês atual"""
        from datetime import datetime
        from calendar import monthrange
        hoje = datetime.now().date()
        ultimo_dia = monthrange(hoje.year, hoje.month)[1]
        if hasattr(self, 'data_inicio_pagar') and hasattr(self, 'data_fim_pagar'):
            self.data_inicio_pagar.setDate(QDate(hoje.year, hoje.month, 1))
            self.data_fim_pagar.setDate(QDate(hoje.year, hoje.month, ultimo_dia))
            self.atualizar_contas_pagar()
    
    def limpar_filtros_pagar(self):
        """Limpa todos os filtros de contas a pagar"""
        from datetime import datetime
        hoje = datetime.now().date()
        if hasattr(self, 'combo_status_pagar'):
            self.combo_status_pagar.setCurrentText("Todas")
        if hasattr(self, 'data_inicio_pagar') and hasattr(self, 'data_fim_pagar'):
            self.data_inicio_pagar.setDate(QDate(hoje.year, 1, 1))
            self.data_fim_pagar.setDate(QDate(hoje.year, 12, 31))
        if hasattr(self, 'search_pagar'):
            self.search_pagar.clear()
        if hasattr(self, 'combo_categoria_pagar'):
            self.combo_categoria_pagar.setCurrentText("Todas")
        if hasattr(self, 'combo_fornecedor_pagar'):
            self.combo_fornecedor_pagar.setCurrentText("Todos")
        self.atualizar_contas_pagar()
    
    # Métodos de filtro para Contas a Receber
    def filtrar_receber_vence_hoje(self):
        """Filtra contas a receber que vencem hoje"""
        from datetime import datetime
        hoje = datetime.now().date()
        if hasattr(self, 'data_inicio_receber') and hasattr(self, 'data_fim_receber'):
            self.data_inicio_receber.setDate(QDate(hoje.year, hoje.month, hoje.day))
            self.data_fim_receber.setDate(QDate(hoje.year, hoje.month, hoje.day))
            self.atualizar_contas_receber()
    
    def filtrar_receber_vencidos(self):
        """Filtra contas a receber vencidas"""
        from datetime import datetime
        hoje = datetime.now().date()
        if hasattr(self, 'data_inicio_receber') and hasattr(self, 'data_fim_receber'):
            self.data_inicio_receber.setDate(QDate(2000, 1, 1))
            self.data_fim_receber.setDate(QDate(hoje.year, hoje.month, hoje.day))
            self.combo_status_receber.setCurrentText("Vencidas")
            self.atualizar_contas_receber()
    
    def filtrar_receber_proximos_7dias(self):
        """Filtra contas a receber dos próximos 7 dias"""
        from datetime import datetime, timedelta
        hoje = datetime.now().date()
        fim = hoje + timedelta(days=7)
        if hasattr(self, 'data_inicio_receber') and hasattr(self, 'data_fim_receber'):
            self.data_inicio_receber.setDate(QDate(hoje.year, hoje.month, hoje.day))
            self.data_fim_receber.setDate(QDate(fim.year, fim.month, fim.day))
            self.atualizar_contas_receber()
    
    def filtrar_receber_este_mes(self):
        """Filtra contas a receber do mês atual"""
        from datetime import datetime
        from calendar import monthrange
        hoje = datetime.now().date()
        ultimo_dia = monthrange(hoje.year, hoje.month)[1]
        if hasattr(self, 'data_inicio_receber') and hasattr(self, 'data_fim_receber'):
            self.data_inicio_receber.setDate(QDate(hoje.year, hoje.month, 1))
            self.data_fim_receber.setDate(QDate(hoje.year, hoje.month, ultimo_dia))
            self.atualizar_contas_receber()
    
    def dialog_editar_lancamento(self, lancamento):
        """Diálogo para editar um lançamento"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Lançamento")
        dialog.setMinimumWidth(550)
        dialog.setMinimumHeight(500)
        
        layout = QFormLayout(dialog)
        
        # Cliente/Fornecedor
        pessoa_input = UpperCaseLineEdit()
        pessoa_input.setText(lancamento.pessoa or "")
        label_pessoa = "Cliente:" if lancamento.tipo == TipoLancamento.RECEITA else "Fornecedor:"
        layout.addRow(label_pessoa, pessoa_input)
        
        # Categoria
        categorias = [cat for cat in database.listar_categorias() if cat.tipo == lancamento.tipo]
        categoria_combo = QComboBox()
        categoria_combo.addItems([cat.nome for cat in categorias])
        if lancamento.categoria:
            idx = next((i for i, cat in enumerate(categorias) if cat.nome == lancamento.categoria), 0)
            categoria_combo.setCurrentIndex(idx)
        layout.addRow("Categoria:", categoria_combo)
        
        # Subcategoria - dinâmica baseada na categoria
        subcategoria_combo = QComboBox()
        subcategoria_combo.setEditable(True)
        subcategoria_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        def atualizar_subcategorias_edit():
            subcategoria_combo.clear()
            categoria_selecionada = categoria_combo.currentText()
            if categoria_selecionada:
                for cat in categorias:
                    if cat.nome == categoria_selecionada:
                        subcategoria_combo.addItem("")  # Opção vazia
                        for sub in cat.subcategorias:
                            subcategoria_combo.addItem(sub)
                        break
                # Se o lançamento já tinha uma subcategoria, selecionar
                if lancamento.subcategoria:
                    idx = subcategoria_combo.findText(lancamento.subcategoria)
                    if idx >= 0:
                        subcategoria_combo.setCurrentIndex(idx)
        
        categoria_combo.currentTextChanged.connect(atualizar_subcategorias_edit)
        atualizar_subcategorias_edit()  # Carregar subcategorias iniciais
        
        layout.addRow("Subcategoria:", subcategoria_combo)
        
        # Número do documento
        num_doc_input = UpperCaseLineEdit()
        num_doc_input.setText(lancamento.num_documento or "")
        layout.addRow("Nº Documento:", num_doc_input)
        
        # Descrição
        descricao_input = UpperCaseLineEdit()
        descricao_input.setText(lancamento.descricao)
        layout.addRow("Descrição:", descricao_input)
        
        # Valor
        valor_input = QDoubleSpinBox()
        valor_input.setPrefix("R$ ")
        valor_input.setMaximum(999999999.99)
        valor_input.setDecimals(2)
        valor_input.setValue(lancamento.valor)
        layout.addRow("Valor:", valor_input)
        
        # Data de vencimento
        data_venc_input = QDateEdit()
        data_venc_input.setDate(QDate(lancamento.data_vencimento.year, lancamento.data_vencimento.month, lancamento.data_vencimento.day))
        data_venc_input.setCalendarPopup(True)
        layout.addRow("Data Vencimento:", data_venc_input)
        
        # Observações
        obs_input = UpperCaseTextEdit()
        obs_input.setPlainText(lancamento.observacoes or "")
        obs_input.setMaximumHeight(100)
        layout.addRow("Observações:", obs_input)
        
        # Botões
        btns_layout = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_salvar = QPushButton("Salvar")
        btn_salvar.setObjectName("primaryButton")
        
        btns_layout.addWidget(btn_cancelar)
        btns_layout.addWidget(btn_salvar)
        layout.addRow(btns_layout)
        
        btn_cancelar.clicked.connect(dialog.reject)
        
        def salvar():
            # Atualizar campos do lançamento
            lancamento.pessoa = pessoa_input.text() or None
            lancamento.categoria = categoria_combo.currentText()
            lancamento.subcategoria = subcategoria_combo.currentText()
            lancamento.num_documento = num_doc_input.text() or None
            lancamento.descricao = descricao_input.text()
            lancamento.valor = valor_input.value()
            
            qdate = data_venc_input.date()
            lancamento.data_vencimento = datetime(qdate.year(), qdate.month(), qdate.day())
            lancamento.observacoes = obs_input.toPlainText() or None
            
            # auto-save in SQLite
            dialog.accept()
            
            # Atualizar tela
            if lancamento.tipo == TipoLancamento.RECEITA:
                self.show_contas_receber()
            else:
                self.show_contas_pagar()
            
            QMessageBox.information(self, "Sucesso", "Lançamento atualizado com sucesso!")
        
        btn_salvar.clicked.connect(salvar)
        dialog.exec()
    
    def duplicar_lancamento(self, lancamento):
        """Duplica um lançamento existente"""
        from copy import deepcopy
        
        # Criar cópia do lançamento
        novo_lancamento = deepcopy(lancamento)
        novo_lancamento.id = None  # Will be auto-generated
        novo_lancamento.descricao = f"{lancamento.descricao} (Cópia)"
        novo_lancamento.status = StatusLancamento.PENDENTE
        
        # Adicionar ao banco
        database.adicionar_lancamento(novo_lancamento)
        
        # Atualizar tela
        if lancamento.tipo == TipoLancamento.RECEITA:
            self.show_contas_receber()
        else:
            self.show_contas_pagar()
        
        QMessageBox.information(self, "Sucesso", "Lançamento duplicado com sucesso!")
    
    def excluir_lancamento(self, id_lancamento):
        """Exclui um lançamento"""
        lancamento = next((l for l in database.listar_lancamentos() if l.id == id_lancamento), None)
        if not lancamento:
            return
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar Exclusão")
        msg_box.setText(f"Deseja realmente excluir o lançamento '{lancamento.descricao}'?")
        btn_sim = msg_box.addButton("Sim", QMessageBox.ButtonRole.YesRole)
        btn_nao = msg_box.addButton("Não", QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(btn_nao)
        msg_box.exec()
        
        if msg_box.clickedButton() == btn_sim:
            # Remover lançamento do banco
            database.excluir_lancamento(id_lancamento)
            
            # Atualizar tela
            if lancamento.tipo == TipoLancamento.RECEITA:
                self.show_contas_receber()
            else:
                self.show_contas_pagar()
            
            QMessageBox.information(self, "Sucesso", "Lançamento excluído com sucesso!")
    
    def excluir_conta(self, nome):
        """Exclui uma conta bancária"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar Exclusão")
        msg_box.setText(f"Deseja realmente excluir a conta '{nome}'?")
        btn_sim = msg_box.addButton("Sim", QMessageBox.ButtonRole.YesRole)
        btn_nao = msg_box.addButton("Não", QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(btn_nao)
        msg_box.exec()
        
        if msg_box.clickedButton() == btn_sim:
            database.excluir_conta(nome)
            self.show_contas_bancarias()
    
    def recalcular_saldos(self):
        """Recalcula os saldos de todas as contas baseado nos lançamentos"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Recalcular Saldos")
        msg_box.setText("Esta operação irá recalcular o saldo de todas as contas baseado nos lançamentos pagos.\n\nDeseja continuar?")
        msg_box.setIcon(QMessageBox.Icon.Question)
        btn_sim = msg_box.addButton("Sim", QMessageBox.ButtonRole.YesRole)
        btn_nao = msg_box.addButton("Não", QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(btn_nao)
        msg_box.exec()
        
        if msg_box.clickedButton() == btn_sim:
            # recalcular não necessário em SQLite
            self.show_contas_bancarias()
            QMessageBox.information(self, "Sucesso", "Saldos recalculados com sucesso!")
    
    def cancelar_lancamento(self, id_lancamento):
        """Cancela um lançamento"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmar Cancelamento")
        msg_box.setText("Deseja realmente cancelar este lançamento?")
        btn_sim = msg_box.addButton("Sim", QMessageBox.ButtonRole.YesRole)
        btn_nao = msg_box.addButton("Não", QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(btn_nao)
        msg_box.exec()
        
        if msg_box.clickedButton() == btn_sim:
            database.cancelar_lancamento(id_lancamento)
            self.show_contas_pagar()
    
    def abrir_calculadora(self):
        """Abre a calculadora do sistema operacional"""
        import subprocess
        import platform
        
        try:
            sistema = platform.system()
            if sistema == "Windows":
                subprocess.Popen("calc.exe")
            elif sistema == "Darwin":  # macOS
                subprocess.Popen(["open", "-a", "Calculator"])
            else:  # Linux
                # Tentar várias calculadoras comuns no Linux
                for calc in ["gnome-calculator", "kcalc", "xcalc", "galculator"]:
                    try:
                        subprocess.Popen([calc])
                        break
                    except FileNotFoundError:
                        continue
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível abrir a calculadora: {str(e)}")
    
    def apply_styles(self):
        """Aplica estilos CSS à aplicação"""
        self.setStyleSheet("""
            /* Geral */
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            /* Sidebar */
            #sidebar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1f3a, stop:0.5 #2c3e50, stop:1 #1a252f);
                color: white;
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            #sidebarHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 25px 20px;
                border-bottom: 2px solid rgba(255, 255, 255, 0.1);
                letter-spacing: 1px;
            }
            
            #sidebarFooter {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(26, 37, 47, 0.5), stop:1 #0d1117);
                color: #95a5a6;
                font-size: 9px;
                border-top: 1px solid rgba(255, 255, 255, 0.05);
                padding: 10px;
            }
            
            SidebarButton {
                background-color: transparent;
                color: #e8eaf6;
                text-align: left;
                padding: 14px 24px;
                border: none;
                border-left: 4px solid transparent;
                font-size: 13px;
                font-family: "Segoe UI", Arial, sans-serif;
                font-weight: 500;
                letter-spacing: 0.3px;
                margin: 2px 0;
            }
            
            SidebarButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 0.15), stop:1 rgba(118, 75, 162, 0.15));
                border-left: 4px solid #667eea;
                color: #ffffff;
                padding-left: 28px;
            }
            
            SidebarButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 0.25), stop:1 rgba(118, 75, 162, 0.25));
                border-left: 4px solid #667eea;
                color: #ffffff;
                font-weight: 600;
            }
            
            /* Submenu de Cadastros */
            #submenuCadastros {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(13, 17, 23, 0.6), stop:1 rgba(26, 37, 47, 0.8));
                border-left: 2px solid rgba(102, 126, 234, 0.3);
                margin-left: 12px;
            }
            
            #submenuCadastros SidebarButton {
                font-size: 12px;
                padding: 11px 20px;
                color: #bdc3c7;
                font-weight: 400;
            }
            
            #submenuCadastros SidebarButton:hover {
                background: rgba(102, 126, 234, 0.12);
                color: #ecf0f1;
                padding-left: 24px;
            }
            
            #submenuCadastros SidebarButton:checked {
                background: rgba(102, 126, 234, 0.2);
                color: #ffffff;
                font-weight: 500;
            }
            
            /* Submenu de Relatórios */
            #submenuRelatorios {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(13, 17, 23, 0.6), stop:1 rgba(26, 37, 47, 0.8));
                border-left: 2px solid rgba(102, 126, 234, 0.3);
                margin-left: 12px;
            }
            
            #submenuRelatorios SidebarButton {
                font-size: 12px;
                padding: 11px 20px;
                color: #bdc3c7;
                font-weight: 400;
            }
            
            #submenuRelatorios SidebarButton:hover {
                background: rgba(102, 126, 234, 0.12);
                color: #ecf0f1;
                padding-left: 24px;
            }
            
            #submenuRelatorios SidebarButton:checked {
                background: rgba(102, 126, 234, 0.2);
                color: #ffffff;
                font-weight: 500;
            }
            
            /* Área de Conteúdo */
            #contentArea {
                background-color: #f5f5f5;
            }
            
            #pageTitle {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 20px;
                padding: 5px;
            }
            
            /* Cards */
            #card {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
                margin: 5px;
                min-width: 180px;
            }
            
            #cardTitle {
                font-size: 10px;
                color: #7f8c8d;
                margin-bottom: 10px;
                padding: 2px;
            }
            
            #cardValue {
                font-size: 20px;
                font-weight: bold;
                margin-top: 10px;
                padding: 5px;
            }
            
            /* Filtros */
            #filterFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
            }
            
            #summaryFrame {
                background-color: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
            }
            
            /* Botões */
            #primaryButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            
            #primaryButton:hover {
                background-color: #2980b9;
            }
            
            #successButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 10px;
            }
            
            #successButton:hover {
                background-color: #229954;
            }
            
            #dangerButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 10px;
            }
            
            #dangerButton:hover {
                background-color: #c0392b;
            }
            
            /* Tabelas */
            #dataTable {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                gridline-color: #dcdcdc;
                selection-background-color: #e3f2fd;
            }
            
            #dataTable::item {
                padding: 8px 6px;
                min-height: 30px;
                border-bottom: 1px solid #e0e0e0;
                font-size: 11px;
            }
            
            #dataTable::item:selected {
                background-color: #e3f2fd;
                color: #000000;
            }
            
            QHeaderView::section {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #bdc3c7;
                font-weight: bold;
                font-size: 11px;
            }
            
            /* Inputs */
            QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
                padding: 6px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
                color: #000000;
                font-size: 11px;
            }
            
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
                border: 1px solid #3498db;
            }
            
            /* Diálogos */
            QDialog {
                background-color: white;
            }
            
            QLabel {
                color: #2c3e50;
                padding: 2px;
                margin: 1px;
            }
            
            /* Abas de Cadastro */
            #cadastroTabs {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            
            #cadastroTabs::pane {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                padding: 15px;
            }
            
            #cadastroTabs QTabBar::tab {
                background-color: #f5f5f5;
                color: #2c3e50;
                padding: 10px 20px;
                margin-right: 2px;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            
            #cadastroTabs QTabBar::tab:selected {
                background-color: white;
                color: #3498db;
                font-weight: bold;
                border-bottom: 2px solid white;
            }
            
            #cadastroTabs QTabBar::tab:hover {
                background-color: #ecf0f1;
            }
        """)


class LoginDialog(QDialog):
    """Diálogo de login para acesso ao sistema"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - Sistema Financeiro")
        self.setModal(True)
        
        # Credenciais corretas
        self.login_correto = "admin"
        self.senha_correta = "admin"
        self.autenticado = False
        
        # Calcular escala baseada na tela
        screen = QApplication.primaryScreen()
        if screen:
            screen_height = screen.geometry().height()
            self.scale_factor = max(0.8, min(1.5, screen_height / 1080.0))
        else:
            self.scale_factor = 1.0
        
        self.setup_ui()
        
    def scale_size(self, size):
        """Escala um tamanho baseado no fator de escala"""
        return int(size * self.scale_factor)
        
    def setup_ui(self):
        """Configura a interface do login"""
        # Definir tamanho responsivo
        width = self.scale_size(450)
        height = self.scale_size(500)
        self.setFixedSize(width, height)
        
        layout = QVBoxLayout(self)
        spacing = self.scale_size(15)
        margins = self.scale_size(50)
        layout.setSpacing(spacing)
        layout.setContentsMargins(margins, margins, margins, margins)
        
        # Estilo do diálogo com tamanhos responsivos
        font_size_label = self.scale_size(13)
        font_size_input = self.scale_size(12)
        font_size_button = self.scale_size(13)
        padding_input = self.scale_size(12)
        padding_button = self.scale_size(14)
        border_radius = self.scale_size(6)
        
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
            }}
            QLabel {{
                color: white;
                font-size: {font_size_label}px;
            }}
            QLineEdit {{
                padding: {padding_input}px;
                border: 2px solid #ddd;
                border-radius: {border_radius}px;
                background-color: white;
                color: black;
                font-size: {font_size_input}px;
                min-height: {self.scale_size(20)}px;
            }}
            QLineEdit:focus {{
                border: 2px solid #667eea;
            }}
            QPushButton {{
                padding: {padding_button}px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: {border_radius}px;
                font-size: {font_size_button}px;
                font-weight: bold;
                min-height: {self.scale_size(25)}px;
            }}
            QPushButton:hover {{
                background-color: #45a049;
            }}
            QPushButton:pressed {{
                background-color: #3d8b40;
            }}
        """)
        
        # Título
        title_label = QLabel("🔐 Sistema Financeiro")
        title_label.setFont(QFont("Segoe UI", self.scale_size(22), QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Faça login para continuar")
        subtitle_label.setFont(QFont("Segoe UI", self.scale_size(11)))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(self.scale_size(20))
        
        # Campo de login
        login_label = QLabel("Usuário:")
        login_label.setFont(QFont("Segoe UI", self.scale_size(11), QFont.Weight.Bold))
        layout.addWidget(login_label)
        
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Digite seu usuário")
        self.login_input.returnPressed.connect(self.tentar_login)
        layout.addWidget(self.login_input)
        
        # Campo de senha
        senha_label = QLabel("Senha:")
        senha_label.setFont(QFont("Segoe UI", self.scale_size(11), QFont.Weight.Bold))
        layout.addWidget(senha_label)
        
        self.senha_input = QLineEdit()
        self.senha_input.setPlaceholderText("Digite sua senha")
        self.senha_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.senha_input.returnPressed.connect(self.tentar_login)
        layout.addWidget(self.senha_input)
        
        layout.addSpacing(self.scale_size(15))
        
        # Botão de login
        btn_login = QPushButton("Entrar")
        btn_login.clicked.connect(self.tentar_login)
        layout.addWidget(btn_login)
        
        # Label de erro
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_padding = self.scale_size(10)
        error_radius = self.scale_size(5)
        error_font = self.scale_size(11)
        self.error_label.setStyleSheet(f"""
            color: #ff6b6b;
            background-color: rgba(255, 255, 255, 0.9);
            padding: {error_padding}px;
            border-radius: {error_radius}px;
            font-weight: bold;
            font-size: {error_font}px;
        """)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        layout.addStretch()
        
        # Focar no campo de login
        self.login_input.setFocus()
    
    def tentar_login(self):
        """Valida as credenciais e fecha o diálogo se corretas"""
        login = self.login_input.text().strip()
        senha = self.senha_input.text()
        
        if login == self.login_correto and senha == self.senha_correta:
            self.autenticado = True
            self.accept()
        else:
            self.error_label.setText("❌ Usuário ou senha incorretos!")
            self.error_label.show()
            self.senha_input.clear()
            self.senha_input.setFocus()
            
            # Efeito de shake (simples) com tamanhos responsivos
            padding_input = self.scale_size(12)
            font_size_input = self.scale_size(12)
            border_radius = self.scale_size(6)
            
            self.senha_input.setStyleSheet(f"""
                QLineEdit {{
                    padding: {padding_input}px;
                    border: 2px solid #ff6b6b;
                    border-radius: {border_radius}px;
                    background-color: white;
                    color: black;
                    font-size: {font_size_input}px;
                    min-height: {self.scale_size(20)}px;
                }}
            """)
            
            # Restaurar estilo após 1 segundo
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: self.senha_input.setStyleSheet(f"""
                QLineEdit {{
                    padding: {padding_input}px;
                    border: 2px solid #ddd;
                    border-radius: {border_radius}px;
                    background-color: white;
                    color: black;
                    font-size: {font_size_input}px;
                    min-height: {self.scale_size(20)}px;
                }}
                QLineEdit:focus {{
                    border: 2px solid #667eea;
                }}
            """))


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Configurar fonte padrão adaptativa baseada na resolução
    screen = app.primaryScreen()
    if screen:
        screen_width = screen.geometry().width()
        scale_factor = max(0.7, min(2.0, screen_width / 1920.0))
        base_font_size = int(10 * scale_factor)
    else:
        base_font_size = 10
    
    font = QFont("Segoe UI", base_font_size)
    app.setFont(font)
    
    # Exibir tela de login
    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.DialogCode.Accepted and login_dialog.autenticado:
        # Se autenticado, mostrar a janela principal
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    else:
        # Se cancelou ou fechou, sair
        sys.exit(0)


if __name__ == "__main__":
    main()







