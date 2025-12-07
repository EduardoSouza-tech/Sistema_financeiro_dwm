"""
Gerador de Documentação em PDF - Sistema Financeiro
Guia completo para estudo e aprendizado de Python
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Preformatted
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

def criar_pdf_documentacao():
    """Cria PDF completo com documentação educacional do sistema"""
    
    # Configurar PDF
    filename = f"documentacao/GUIA_ESTUDO_PYTHON_{datetime.now().strftime('%Y%m%d')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4,
                          leftMargin=0.75*inch, rightMargin=0.75*inch,
                          topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitulo_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    secao_style = ParagraphStyle(
        'CustomSection',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#059669'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    texto_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=8
    )
    
    codigo_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Code'],
        fontSize=8,
        leftIndent=20,
        fontName='Courier',
        textColor=colors.HexColor('#1f2937'),
        backColor=colors.HexColor('#f3f4f6'),
        borderColor=colors.HexColor('#d1d5db'),
        borderWidth=1,
        borderPadding=8
    )
    
    destaque_style = ParagraphStyle(
        'HighlightStyle',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.HexColor('#0369a1'),
        leftIndent=20,
        fontName='Helvetica-Bold',
        spaceAfter=6
    )
    
    # Conteúdo do PDF
    story = []
    
    # ========== CAPA ==========
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("🎓 GUIA COMPLETO DE ESTUDO", titulo_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Sistema Financeiro em Python", subtitulo_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Documentação Educacional para Aprendizado", texto_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", texto_style))
    story.append(PageBreak())
    
    # ========== ÍNDICE ==========
    story.append(Paragraph("📑 ÍNDICE", titulo_style))
    story.append(Spacer(1, 0.2*inch))
    
    indice_items = [
        "1. Introdução ao Sistema",
        "2. Estrutura do Projeto",
        "3. Arquivo config.py - Configurações",
        "4. Arquivo models.py - Modelos de Dados",
        "5. Arquivo database.py - Banco de Dados SQLite",
        "6. Arquivo database_postgresql.py - PostgreSQL",
        "7. Arquivo web_server.py - Servidor Flask",
        "8. Frontend - HTML, CSS e JavaScript",
        "9. Bibliotecas Python Utilizadas",
        "10. Conceitos de Programação Aplicados",
        "11. Deployment no Railway",
        "12. Exercícios Práticos"
    ]
    
    for item in indice_items:
        story.append(Paragraph(item, texto_style))
        story.append(Spacer(1, 6))
    
    story.append(PageBreak())
    
    # ========== 1. INTRODUÇÃO ==========
    story.append(Paragraph("1. 📚 INTRODUÇÃO AO SISTEMA", titulo_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("O que é este Sistema?", subtitulo_style))
    story.append(Paragraph(
        "Este é um <b>Sistema de Gestão Financeira</b> completo desenvolvido em Python. "
        "Ele permite gerenciar contas bancárias, categorias, clientes, fornecedores e lançamentos financeiros "
        "(receitas, despesas e transferências).",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Tecnologias Utilizadas:", subtitulo_style))
    
    tecnologias = [
        ["Tecnologia", "Propósito"],
        ["Python 3.11+", "Linguagem de programação principal"],
        ["Flask", "Framework web para criar APIs REST"],
        ["SQLite", "Banco de dados local (desenvolvimento)"],
        ["PostgreSQL", "Banco de dados em produção (Railway)"],
        ["HTML/CSS/JS", "Interface do usuário (frontend)"],
        ["Railway", "Plataforma de deployment/hospedagem"],
    ]
    
    t = Table(tecnologias, colWidths=[2*inch, 3.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(t)
    story.append(PageBreak())
    
    # ========== 2. ESTRUTURA DO PROJETO ==========
    story.append(Paragraph("2. 📁 ESTRUTURA DO PROJETO", titulo_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Organização dos Arquivos:", subtitulo_style))
    
    estrutura_texto = """
sistema_financeiro/
│
├── config.py                    # Configurações do sistema
├── models.py                    # Classes de modelo (POO)
├── database.py                  # Gerenciador SQLite
├── database_postgresql.py       # Gerenciador PostgreSQL
├── web_server.py               # Servidor Flask (API REST)
│
├── static/                     # Arquivos estáticos
│   ├── app.js                  # Lógica JavaScript
│   └── style.css               # Estilos CSS
│
├── templates/                  # Templates HTML
│   └── interface_nova.html     # Interface principal
│
├── documentacao/               # Documentação
│   ├── DOCUMENTACAO.md
│   ├── OTIMIZACOES.md
│   └── README_RAILWAY.md
│
├── requirements.txt            # Dependências Python
├── Procfile                    # Comando de inicialização (Railway)
├── runtime.txt                 # Versão do Python (Railway)
└── sistema_financeiro.db       # Banco SQLite (local)
"""
    
    story.append(Preformatted(estrutura_texto, codigo_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Explicação Detalhada de Cada Pasta e Arquivo:", subtitulo_style))
    story.append(Spacer(1, 8))
    
    # ARQUIVOS PRINCIPAIS
    story.append(Paragraph("📄 Arquivos Python Principais:", secao_style))
    
    story.append(Paragraph("<b>config.py</b> (32 linhas)", destaque_style))
    story.append(Paragraph(
        "• <b>Propósito:</b> Centralizar todas as configurações do sistema<br/>"
        "• <b>Conteúdo:</b> Variáveis de ambiente, configurações de banco (SQLite, MySQL, PostgreSQL)<br/>"
        "• <b>Por que existe:</b> Permite mudar configurações sem alterar código principal<br/>"
        "• <b>Importado por:</b> database.py, database_postgresql.py, web_server.py<br/>"
        "• <b>Conceitos:</b> Variáveis de ambiente (os.getenv), dicionários, valores padrão",
        texto_style
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>models.py</b> (273 linhas)", destaque_style))
    story.append(Paragraph(
        "• <b>Propósito:</b> Definir estrutura dos dados (classes)<br/>"
        "• <b>Classes:</b> TipoLancamento, StatusLancamento, Categoria, ContaBancaria, Lancamento<br/>"
        "• <b>Por que existe:</b> Organizar dados em objetos reutilizáveis (POO)<br/>"
        "• <b>Importado por:</b> database.py, database_postgresql.py, web_server.py<br/>"
        "• <b>Conceitos:</b> Classes, Enum, métodos, construtores (__init__), atributos",
        texto_style
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>database.py</b> (1245 linhas)", destaque_style))
    story.append(Paragraph(
        "• <b>Propósito:</b> Gerenciar banco de dados SQLite (desenvolvimento local)<br/>"
        "• <b>Classe Principal:</b> DatabaseManager com 30+ métodos CRUD<br/>"
        "• <b>Por que existe:</b> Separar lógica de banco de dados do resto do código<br/>"
        "• <b>Importado por:</b> web_server.py, scripts de migração<br/>"
        "• <b>Conceitos:</b> SQLite3, SQL queries, transações, conexões, cursores",
        texto_style
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>database_postgresql.py</b> (954 linhas)", destaque_style))
    story.append(Paragraph(
        "• <b>Propósito:</b> Gerenciar banco PostgreSQL (produção no Railway)<br/>"
        "• <b>Diferença do database.py:</b> Usa psycopg2, tipos SQL diferentes, DATABASE_URL<br/>"
        "• <b>Por que existe:</b> PostgreSQL não é compatível com SQLite, precisa driver próprio<br/>"
        "• <b>Importado por:</b> database.py (seleção dinâmica baseada em DATABASE_TYPE)<br/>"
        "• <b>Conceitos:</b> Psycopg2, RealDictCursor, autocommit, SERIAL, VARCHAR, NUMERIC",
        texto_style
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>web_server.py</b> (2040 linhas)", destaque_style))
    story.append(Paragraph(
        "• <b>Propósito:</b> Servidor web Flask que expõe API REST<br/>"
        "• <b>Endpoints:</b> 40+ rotas para contas, categorias, clientes, fornecedores, lançamentos<br/>"
        "• <b>Por que existe:</b> Ponte entre frontend (JavaScript) e backend (Python/Banco)<br/>"
        "• <b>Importa:</b> Flask, database.py, models.py<br/>"
        "• <b>Conceitos:</b> Flask, decoradores (@app.route), métodos HTTP, JSON, CORS",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    # PASTAS
    story.append(Paragraph("📁 Pastas do Projeto:", secao_style))
    
    story.append(Paragraph("<b>static/</b> - Arquivos Estáticos", destaque_style))
    story.append(Paragraph(
        "• <b>app.js</b> (4659 linhas): Lógica JavaScript do frontend<br/>"
        "  - Funções assíncronas (async/await) para comunicar com API<br/>"
        "  - Manipulação do DOM (Document Object Model)<br/>"
        "  - Event listeners (click, submit, DOMContentLoaded)<br/>"
        "  - Fetch API para requisições HTTP<br/>"
        "• <b>style.css</b>: Estilos visuais da interface<br/>"
        "  - Layout, cores, fontes, responsividade<br/>"
        "  - Classes CSS para cards, tabelas, botões<br/>"
        "• <b>Por que 'static'?</b> Flask serve arquivos desta pasta diretamente ao navegador",
        texto_style
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>templates/</b> - Templates HTML", destaque_style))
    story.append(Paragraph(
        "• <b>interface_nova.html</b> (2602 linhas): Interface principal do usuário<br/>"
        "  - Estrutura HTML completa da aplicação<br/>"
        "  - Formulários, tabelas, modais, dashboards<br/>"
        "  - Importa app.js e style.css<br/>"
        "• <b>Por que 'templates'?</b> Flask busca arquivos HTML nesta pasta por padrão<br/>"
        "• <b>Renderização:</b> render_template('interface_nova.html') no web_server.py",
        texto_style
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>documentacao/</b> - Arquivos de Documentação", destaque_style))
    story.append(Paragraph(
        "• <b>DOCUMENTACAO.md</b>: Documentação técnica completa do sistema<br/>"
        "• <b>OTIMIZACOES.md</b>: Histórico de otimizações e melhorias<br/>"
        "• <b>README_RAILWAY.md</b>: Guia de deployment no Railway<br/>"
        "• <b>Por que .md?</b> Markdown é formato padrão para documentação (legível e versionável)",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    # ARQUIVOS DE CONFIGURAÇÃO
    story.append(Paragraph("⚙️ Arquivos de Configuração:", secao_style))
    
    story.append(Paragraph("<b>requirements.txt</b>", destaque_style))
    story.append(Paragraph(
        "• <b>Propósito:</b> Lista todas as bibliotecas Python necessárias<br/>"
        "• <b>Formato:</b> nome_biblioteca==versão (ex: flask==3.0.0)<br/>"
        "• <b>Instalação:</b> pip install -r requirements.txt<br/>"
        "• <b>Por que existe:</b> Garante que todos instalem mesmas versões",
        texto_style
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>Procfile</b> (Railway/Heroku)", destaque_style))
    story.append(Paragraph(
        "• <b>Propósito:</b> Diz ao Railway qual comando executar<br/>"
        "• <b>Conteúdo:</b> web: python web_server.py<br/>"
        "• <b>Por que existe:</b> Railway precisa saber como iniciar aplicação<br/>"
        "• <b>Formato:</b> tipo_processo: comando",
        texto_style
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>runtime.txt</b> (Railway/Heroku)", destaque_style))
    story.append(Paragraph(
        "• <b>Propósito:</b> Define versão do Python<br/>"
        "• <b>Conteúdo:</b> python-3.11<br/>"
        "• <b>Por que existe:</b> Railway instala versão correta automaticamente<br/>"
        "• <b>Importante:</b> Deve ser versão disponível no Railway",
        texto_style
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>pyrightconfig.json</b> (Pylance/VS Code)", destaque_style))
    story.append(Paragraph(
        "• <b>Propósito:</b> Configurar analisador de tipos Pylance<br/>"
        "• <b>Conteúdo:</b> Arquivos a ignorar, versão Python, regras de tipo<br/>"
        "• <b>Por que existe:</b> Customizar verificação de erros no VS Code<br/>"
        "• <b>ignore:</b> database_postgresql.py, web_server.py (evitar avisos psycopg2)",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    # ARQUIVOS DE BANCO DE DADOS
    story.append(Paragraph("💾 Arquivos de Banco de Dados:", secao_style))
    
    story.append(Paragraph("<b>sistema_financeiro.db</b> (SQLite)", destaque_style))
    story.append(Paragraph(
        "• <b>Propósito:</b> Banco de dados local (desenvolvimento)<br/>"
        "• <b>Formato:</b> Arquivo binário SQLite<br/>"
        "• <b>Tabelas:</b> contas_bancarias, categorias, clientes, fornecedores, lancamentos<br/>"
        "• <b>Por que existe:</b> SQLite não precisa servidor, fácil para desenvolver<br/>"
        "• <b>Não vai para Railway:</b> Listado em .railwayignore",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Como os Arquivos se Interligam:", subtitulo_style))
    
    story.append(Paragraph("→ <b>config.py</b> fornece configurações para todos os outros módulos", destaque_style))
    story.append(Paragraph("→ <b>models.py</b> define as classes que representam os dados", destaque_style))
    story.append(Paragraph("→ <b>database.py</b> usa models.py para salvar/carregar dados do SQLite", destaque_style))
    story.append(Paragraph("→ <b>web_server.py</b> importa database.py e models.py para criar a API", destaque_style))
    story.append(Paragraph("→ <b>app.js</b> faz requisições para web_server.py e atualiza interface_nova.html", destaque_style))
    story.append(Paragraph("→ <b>Railway</b> lê Procfile e runtime.txt para configurar deployment", destaque_style))
    story.append(Paragraph("→ <b>Flask</b> serve static/ e templates/ automaticamente", destaque_style))
    
    story.append(PageBreak())
    
    # ========== 3. CONFIG.PY ==========
    story.append(Paragraph("3. ⚙️ ARQUIVO config.py - CONFIGURAÇÕES", titulo_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("O que é config.py?", subtitulo_style))
    story.append(Paragraph(
        "Este arquivo centraliza todas as configurações do sistema. "
        "É uma <b>boa prática</b> em Python separar configurações do código principal.",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Código Explicado Linha por Linha:", secao_style))
    
    codigo_config = '''import os

# Esta linha importa o módulo 'os' que permite acessar
# variáveis de ambiente do sistema operacional

DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite')

# os.getenv() busca uma variável de ambiente chamada 'DATABASE_TYPE'
# Se não encontrar, usa 'sqlite' como padrão (segundo parâmetro)
# Isso permite mudar o banco sem alterar código!

POSTGRESQL_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'port': int(os.getenv('PGPORT', '5432')),
    'user': os.getenv('PGUSER', 'postgres'),
    'password': os.getenv('PGPASSWORD', ''),
    'database': os.getenv('PGDATABASE', 'sistema_financeiro')
}

# Um DICIONÁRIO (dict) armazena pares chave-valor
# É como um objeto JSON: {'chave': 'valor'}
# int() converte string para número inteiro
'''
    
    story.append(Preformatted(codigo_config, codigo_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("📌 Conceitos Importantes:", secao_style))
    story.append(Paragraph("<b>1. Variáveis de Ambiente:</b> Valores armazenados no sistema operacional, não no código. "
                          "Útil para senhas e configurações que mudam entre ambientes (local, produção).", texto_style))
    story.append(Paragraph("<b>2. Dicionários (dict):</b> Estrutura de dados chave-valor. Acesso rápido: config['host']", texto_style))
    story.append(Paragraph("<b>3. Valores Padrão:</b> Segundo parâmetro de getenv() é usado se variável não existir", texto_style))
    
    story.append(PageBreak())
    
    # ========== 4. MODELS.PY ==========
    story.append(Paragraph("4. 🏗️ ARQUIVO models.py - MODELOS DE DADOS", titulo_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("O que são Modelos?", subtitulo_style))
    story.append(Paragraph(
        "Modelos são <b>classes Python</b> que representam entidades do mundo real. "
        "É o coração da <b>Programação Orientada a Objetos (POO)</b>.",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Classe Enum - TipoLancamento:", secao_style))
    
    codigo_enum = '''from enum import Enum

class TipoLancamento(Enum):
    """Enumeração para tipos de lançamento"""
    RECEITA = "receita"
    DESPESA = "despesa"
    TRANSFERENCIA = "transferencia"

# Enum é uma classe especial que define um conjunto fixo de valores
# Como um "menu de opções" - só pode ser uma dessas três
# Uso: tipo = TipoLancamento.RECEITA
# Vantagem: evita erros de digitação e garante valores válidos
'''
    
    story.append(Preformatted(codigo_enum, codigo_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Classe ContaBancaria:", secao_style))
    
    codigo_conta = '''class ContaBancaria:
    """Representa uma conta bancária"""
    _next_id = 1  # Variável de CLASSE (compartilhada entre todos os objetos)
    
    def __init__(self, nome: str, banco: str, agencia: str, conta: str,
                 saldo_inicial: float = 0.0, id: Optional[int] = None):
        # __init__ é o CONSTRUTOR - executado ao criar objeto
        # self representa a INSTÂNCIA do objeto (cada conta criada)
        # Parâmetros com = são OPCIONAIS (têm valor padrão)
        
        if saldo_inicial < 0:
            raise ValueError("Saldo não pode ser negativo")
        # raise lança uma EXCEÇÃO - para execução se condição inválida
        
        if id is None:
            self.id = ContaBancaria._next_id  # Gera ID automático
            ContaBancaria._next_id += 1  # Incrementa para próximo
        else:
            self.id = id  # Usa ID fornecido
        
        # Atribuir parâmetros aos ATRIBUTOS da instância
        self.nome = nome
        self.banco = banco
        self.saldo_atual = saldo_inicial
    
    def depositar(self, valor: float):
        """Método de INSTÂNCIA - opera sobre self"""
        self.saldo_atual += valor  # Operador += soma e atribui
    
    def to_dict(self):
        """Converte objeto em dicionário (para JSON)"""
        return {
            "id": self.id,
            "nome": self.nome,
            "banco": self.banco,
            "saldo": self.saldo_atual
        }
'''
    
    story.append(Preformatted(codigo_conta, codigo_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("📌 Conceitos de POO:", secao_style))
    story.append(Paragraph("<b>Classe:</b> Molde/template para criar objetos. Como uma 'planta de casa'.", texto_style))
    story.append(Paragraph("<b>Objeto/Instância:</b> Cada conta criada é um objeto da classe ContaBancaria.", texto_style))
    story.append(Paragraph("<b>Atributos:</b> Variáveis que guardam estado (self.nome, self.saldo).", texto_style))
    story.append(Paragraph("<b>Métodos:</b> Funções dentro da classe que operam sobre self.", texto_style))
    story.append(Paragraph("<b>self:</b> Referência ao objeto atual. Sempre primeiro parâmetro de métodos.", texto_style))
    story.append(Paragraph("<b>__init__:</b> Construtor - inicializa objeto quando criado.", texto_style))
    
    story.append(PageBreak())
    
    # ========== 5. DATABASE.PY ==========
    story.append(Paragraph("5. 💾 ARQUIVO database.py - BANCO DE DADOS SQLite", titulo_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("O que é um Banco de Dados?", subtitulo_style))
    story.append(Paragraph(
        "Banco de dados armazena informações de forma <b>persistente</b> (não se perde ao fechar programa). "
        "SQLite é um banco <b>embutido</b> - não precisa de servidor separado, salva em arquivo .db",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Classe DatabaseManager:", secao_style))
    
    codigo_db = '''import sqlite3
from models import ContaBancaria, Lancamento

class DatabaseManager:
    def __init__(self, db_path: str = "sistema_financeiro.db"):
        self.db_path = db_path  # Caminho do arquivo .db
        self.criar_tabelas()
    
    def get_connection(self):
        """Cria conexão com banco de dados"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        # sqlite3.connect() abre/cria arquivo .db
        # timeout: aguarda até 30s se banco estiver bloqueado
        
        conn.row_factory = sqlite3.Row
        # Permite acessar colunas por nome: row['nome']
        # Sem isso, só acessa por índice: row[0]
        
        return conn
    
    def criar_tabelas(self):
        """Cria estrutura do banco (tabelas)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Cursor executa comandos SQL
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contas_bancarias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                banco TEXT NOT NULL,
                saldo_inicial REAL NOT NULL
            )
        """)
        # SQL: Structured Query Language
        # CREATE TABLE: cria nova tabela
        # IF NOT EXISTS: só cria se não existir
        # INTEGER: número inteiro
        # TEXT: texto/string
        # REAL: número decimal
        # PRIMARY KEY: identificador único
        # AUTOINCREMENT: gera ID automaticamente
        # UNIQUE: não permite valores duplicados
        # NOT NULL: campo obrigatório
        
        conn.commit()  # Salva mudanças no banco
        conn.close()   # Fecha conexão
'''
    
    story.append(Preformatted(codigo_db, codigo_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("CRUD - Operações Básicas:", secao_style))
    
    codigo_crud = '''def adicionar_conta(self, conta: ContaBancaria) -> int:
    """CREATE - Insere nova conta"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO contas_bancarias (nome, banco, saldo_inicial)
        VALUES (?, ?, ?)
    """, (conta.nome, conta.banco, conta.saldo_inicial))
    # ? são PLACEHOLDERS - prevenção contra SQL Injection
    # Valores são passados na tupla (segundo parâmetro)
    
    conta_id = cursor.lastrowid  # ID gerado pelo banco
    conn.commit()
    conn.close()
    return conta_id

def listar_contas(self) -> List[ContaBancaria]:
    """READ - Busca todas as contas"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM contas_bancarias")
    # SELECT: busca dados
    # *: todas as colunas
    # FROM: de qual tabela
    
    contas = []
    for row in cursor.fetchall():  # fetchall() retorna todas as linhas
        conta = ContaBancaria(
            id=row['id'],
            nome=row['nome'],
            banco=row['banco'],
            saldo_inicial=row['saldo_inicial']
        )
        contas.append(conta)
    
    conn.close()
    return contas

def atualizar_conta(self, nome: str, conta: ContaBancaria) -> bool:
    """UPDATE - Modifica conta existente"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE contas_bancarias
        SET nome = ?, banco = ?, saldo_inicial = ?
        WHERE nome = ?
    """, (conta.nome, conta.banco, conta.saldo_inicial, nome))
    # UPDATE: modifica registros
    # SET: define novos valores
    # WHERE: filtra quais registros modificar
    
    success = cursor.rowcount > 0  # rowcount: linhas afetadas
    conn.commit()
    conn.close()
    return success

def excluir_conta(self, nome: str) -> bool:
    """DELETE - Remove conta"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM contas_bancarias WHERE nome = ?", (nome,))
    # DELETE: remove registros
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success
'''
    
    story.append(Preformatted(codigo_crud, codigo_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("📌 Conceitos de Banco de Dados:", secao_style))
    story.append(Paragraph("<b>Tabela:</b> Como planilha Excel - linhas (registros) e colunas (campos).", texto_style))
    story.append(Paragraph("<b>Primary Key:</b> Identificador único de cada registro.", texto_style))
    story.append(Paragraph("<b>SQL:</b> Linguagem para manipular bancos de dados.", texto_style))
    story.append(Paragraph("<b>CRUD:</b> Create, Read, Update, Delete - operações básicas.", texto_style))
    story.append(Paragraph("<b>Placeholders (?):</b> Evitam SQL Injection (ataque de segurança).", texto_style))
    story.append(Paragraph("<b>commit():</b> Confirma mudanças no banco.", texto_style))
    story.append(Paragraph("<b>close():</b> Libera recursos da conexão.", texto_style))
    
    story.append(PageBreak())
    
    # ========== 6. DATABASE_POSTGRESQL.PY ==========
    story.append(Paragraph("6. 🐘 ARQUIVO database_postgresql.py - PostgreSQL", titulo_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Por que PostgreSQL?", subtitulo_style))
    story.append(Paragraph(
        "PostgreSQL é um banco de dados <b>profissional</b> usado em produção. "
        "Diferente do SQLite (arquivo local), PostgreSQL é um <b>servidor</b> que aceita múltiplas conexões simultâneas.",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Diferenças entre SQLite e PostgreSQL:", secao_style))
    
    diff_table = [
        ["Aspecto", "SQLite", "PostgreSQL"],
        ["Tipo", "Arquivo local", "Servidor de rede"],
        ["Conexões simultâneas", "Limitadas", "Milhares"],
        ["Uso", "Desenvolvimento", "Produção"],
        ["Instalação", "Não precisa", "Precisa servidor"],
        ["Performance", "Boa para poucos usuários", "Excelente para muitos"],
    ]
    
    t2 = Table(diff_table, colWidths=[1.5*inch, 1.75*inch, 1.75*inch])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(t2)
    story.append(Spacer(1, 12))
    
    codigo_pg = '''import psycopg2
from psycopg2.extras import RealDictCursor

class DatabaseManager:
    def __init__(self):
        self.config = {
            'host': os.getenv('PGHOST'),
            'port': int(os.getenv('PGPORT', '5432')),
            'user': os.getenv('PGUSER'),
            'password': os.getenv('PGPASSWORD'),
            'database': os.getenv('PGDATABASE')
        }
    
    def get_connection(self):
        """Conecta ao servidor PostgreSQL"""
        conn = psycopg2.connect(**self.config, 
                               cursor_factory=RealDictCursor)
        # **self.config: desempacota dicionário em parâmetros
        # RealDictCursor: retorna linhas como dicionários
        
        conn.autocommit = True  # Commit automático (para Railway)
        return conn
    
    def criar_tabelas(self):
        """PostgreSQL usa tipos diferentes do SQLite"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contas_bancarias (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) UNIQUE NOT NULL,
                banco VARCHAR(255) NOT NULL,
                saldo_inicial NUMERIC(10, 2) NOT NULL
            )
        """)
        # SERIAL: autoincremento em PostgreSQL
        # VARCHAR(255): texto com limite de 255 caracteres
        # NUMERIC(10,2): número com 10 dígitos, 2 decimais
'''
    
    story.append(Preformatted(codigo_pg, codigo_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("📌 Conceitos de Produção:", secao_style))
    story.append(Paragraph("<b>Servidor:</b> Computador que fica sempre ligado processando requisições.", texto_style))
    story.append(Paragraph("<b>Variáveis de Ambiente:</b> Senhas nunca ficam no código em produção!", texto_style))
    story.append(Paragraph("<b>Autocommit:</b> Commit automático para evitar bloqueios.", texto_style))
    story.append(Paragraph("<b>Tipos de Dados:</b> PostgreSQL é mais rigoroso com tipos que SQLite.", texto_style))
    
    story.append(PageBreak())
    
    # ========== 7. WEB_SERVER.PY ==========
    story.append(Paragraph("7. 🌐 ARQUIVO web_server.py - SERVIDOR FLASK", titulo_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("O que é Flask?", subtitulo_style))
    story.append(Paragraph(
        "Flask é um <b>framework web</b> - facilita criar servidores HTTP. "
        "Nosso sistema usa Flask para criar uma <b>API REST</b> que o frontend JavaScript consome.",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Conceito de API REST:", secao_style))
    story.append(Paragraph(
        "<b>API:</b> Application Programming Interface - forma de programas conversarem entre si.<br/>"
        "<b>REST:</b> Padrão que usa HTTP (mesmo protocolo de sites) para trocar dados.<br/>"
        "<b>Endpoints:</b> URLs específicas que executam ações (/api/contas, /api/lancamentos).",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    codigo_flask = '''from flask import Flask, jsonify, request
from flask_cors import CORS
from database import DatabaseManager

app = Flask(__name__)
# Flask(__name__): cria aplicação Flask
# __name__: nome do módulo atual

CORS(app)
# CORS: Cross-Origin Resource Sharing
# Permite que JavaScript de outra origem acesse API
# Necessário para frontend acessar backend

db = DatabaseManager()
# Instancia gerenciador de banco de dados

@app.route('/api/contas', methods=['GET'])
# @app.route: DECORADOR - registra função como endpoint
# '/api/contas': URL que ativa esta função
# methods=['GET']: só aceita requisições HTTP GET

def listar_contas():
    """Endpoint para listar contas"""
    try:
        contas = db.listar_contas()  # Busca no banco
        
        # Converter objetos em dicionários
        contas_dict = [c.to_dict() for c in contas]
        # List comprehension - forma compacta de criar lista
        # Equivale a:
        # contas_dict = []
        # for c in contas:
        #     contas_dict.append(c.to_dict())
        
        return jsonify(contas_dict)
        # jsonify: converte Python dict para JSON
        # JSON: formato de texto para troca de dados
    
    except Exception as e:
        # Captura QUALQUER erro
        return jsonify({"error": str(e)}), 500
        # 500: código HTTP de erro do servidor

@app.route('/api/contas', methods=['POST'])
def adicionar_conta():
    """Endpoint para criar conta"""
    data = request.json  # Dados enviados pelo frontend
    # request.json: converte JSON recebido em dict Python
    
    conta = ContaBancaria(
        nome=data['nome'],
        banco=data['banco'],
        agencia=data['agencia'],
        conta=data['conta']
    )
    
    conta_id = db.adicionar_conta(conta)
    return jsonify({'success': True, 'id': conta_id}), 201
    # 201: código HTTP de "criado com sucesso"

@app.route('/api/contas/<nome>', methods=['DELETE'])
def excluir_conta(nome):
    """Endpoint para deletar conta"""
    # <nome>: parâmetro dinâmico da URL
    # /api/contas/Itaú → nome = "Itaú"
    
    success = db.excluir_conta(nome)
    return jsonify({'success': success})

if __name__ == '__main__':
    # Este bloco só executa se rodar diretamente este arquivo
    # (não quando importado)
    
    port = int(os.getenv('PORT', 5000))
    # Railway define PORT automaticamente
    
    app.run(host='0.0.0.0', port=port, debug=False)
    # host='0.0.0.0': aceita conexões de qualquer IP
    # debug=False: modo produção (não mostra erros detalhados)
'''
    
    story.append(Preformatted(codigo_flask, codigo_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Métodos HTTP:", secao_style))
    
    http_table = [
        ["Método", "Operação", "Exemplo"],
        ["GET", "Buscar dados", "Listar contas"],
        ["POST", "Criar novo", "Adicionar conta"],
        ["PUT", "Atualizar", "Modificar conta"],
        ["DELETE", "Remover", "Excluir conta"],
    ]
    
    t3 = Table(http_table, colWidths=[1.2*inch, 1.8*inch, 2*inch])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(t3)
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("📌 Conceitos Web:", secao_style))
    story.append(Paragraph("<b>HTTP:</b> Protocolo de comunicação da web.", texto_style))
    story.append(Paragraph("<b>JSON:</b> Formato de texto para trocar dados (similar a dicionário Python).", texto_style))
    story.append(Paragraph("<b>Endpoint:</b> URL específica que executa uma função.", texto_style))
    story.append(Paragraph("<b>Decorador (@):</b> Função que modifica outra função.", texto_style))
    story.append(Paragraph("<b>Status Codes:</b> 200 (OK), 201 (Criado), 404 (Não encontrado), 500 (Erro).", texto_style))
    
    story.append(PageBreak())
    
    # ========== 8. FRONTEND ==========
    story.append(Paragraph("8. 🎨 FRONTEND - HTML, CSS e JavaScript", titulo_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Como Frontend e Backend Conversam:", subtitulo_style))
    story.append(Paragraph(
        "Frontend (HTML/CSS/JS) roda no <b>navegador do usuário</b>. "
        "Backend (Flask/Python) roda no <b>servidor</b>. "
        "Eles conversam via <b>requisições HTTP</b> (fetch API).",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    codigo_js = '''// JavaScript - app.js

// Função assíncrona para buscar contas
async function loadContas() {
    // async: permite usar await (esperar resposta)
    
    try {
        const response = await fetch('/api/contas');
        // fetch: faz requisição HTTP GET
        // await: aguarda resposta do servidor
        
        const contas = await response.json();
        // .json(): converte resposta JSON em objeto JS
        
        // Atualizar interface
        const lista = document.getElementById('lista-contas');
        lista.innerHTML = '';  // Limpa lista
        
        contas.forEach(conta => {
            // forEach: loop em array
            const div = document.createElement('div');
            div.textContent = `${conta.nome} - ${conta.banco}`;
            lista.appendChild(div);
        });
        
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao carregar contas!');
    }
}

// Adicionar conta
async function adicionarConta() {
    const dados = {
        nome: document.getElementById('input-nome').value,
        banco: document.getElementById('input-banco').value
    };
    
    const response = await fetch('/api/contas', {
        method: 'POST',  // Método HTTP
        headers: {
            'Content-Type': 'application/json'
            // Informa que está enviando JSON
        },
        body: JSON.stringify(dados)
        // JSON.stringify: converte objeto JS em texto JSON
    });
    
    const resultado = await response.json();
    
    if (resultado.success) {
        alert('Conta adicionada!');
        loadContas();  // Recarrega lista
    }
}

// Executar quando página carregar
document.addEventListener('DOMContentLoaded', function() {
    // DOMContentLoaded: evento quando HTML está pronto
    loadContas();
    
    // Associar botão a função
    document.getElementById('btn-adicionar')
            .addEventListener('click', adicionarConta);
});
'''
    
    story.append(Preformatted(codigo_js, codigo_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("📌 Conceitos JavaScript:", secao_style))
    story.append(Paragraph("<b>async/await:</b> Forma moderna de lidar com operações assíncronas.", texto_style))
    story.append(Paragraph("<b>fetch:</b> API nativa do navegador para fazer requisições HTTP.", texto_style))
    story.append(Paragraph("<b>Promise:</b> Objeto que representa resultado futuro de operação assíncrona.", texto_style))
    story.append(Paragraph("<b>DOM:</b> Document Object Model - representação do HTML que JS manipula.", texto_style))
    story.append(Paragraph("<b>Event Listener:</b> Função que executa quando evento acontece (click, load).", texto_style))
    
    story.append(PageBreak())
    
    # ========== 9. BIBLIOTECAS ==========
    story.append(Paragraph("9. 📦 BIBLIOTECAS PYTHON UTILIZADAS", titulo_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Como Instalar Bibliotecas:", subtitulo_style))
    story.append(Paragraph(
        "Python tem um gerenciador de pacotes chamado <b>pip</b>. "
        "O arquivo <b>requirements.txt</b> lista todas as dependências do projeto.",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    codigo_requirements = '''# requirements.txt
flask==3.0.0
flask-cors==4.0.0
psycopg2-binary==2.9.9
gunicorn==21.2.0

# Comando para instalar:
# pip install -r requirements.txt

# Cada linha: nome_biblioteca==versão
# == força versão específica (garante compatibilidade)
'''
    
    story.append(Preformatted(codigo_requirements, codigo_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Principais Bibliotecas:", secao_style))
    
    libs_table = [
        ["Biblioteca", "Propósito"],
        ["flask", "Framework web para criar servidor HTTP"],
        ["flask-cors", "Permite requisições de outras origens"],
        ["psycopg2-binary", "Driver para conectar ao PostgreSQL"],
        ["gunicorn", "Servidor WSGI para produção (Railway)"],
        ["sqlite3", "Já vem com Python - banco local"],
        ["datetime", "Manipulação de datas e horários"],
        ["json", "Converter entre JSON e dict Python"],
        ["os", "Acessar sistema operacional e variáveis ambiente"],
    ]
    
    t4 = Table(libs_table, colWidths=[2.2*inch, 3.3*inch])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))
    story.append(t4)
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Como o Python Encontra Bibliotecas:", secao_style))
    story.append(Paragraph(
        "Python tem um diretório <b>site-packages</b> onde instala bibliotecas. "
        "Quando você faz <i>import flask</i>, Python busca em site-packages. "
        "Ambiente virtual (venv) isola dependências de cada projeto.",
        texto_style
    ))
    
    story.append(PageBreak())
    
    # ========== 10. CONCEITOS ==========
    story.append(Paragraph("10. 🧠 CONCEITOS DE PROGRAMAÇÃO APLICADOS", titulo_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("A. Programação Orientada a Objetos (POO)", subtitulo_style))
    
    conceitos_poo = [
        ["Conceito", "Definição", "Exemplo no Código"],
        ["Classe", "Template para criar objetos", "class ContaBancaria"],
        ["Objeto", "Instância de uma classe", "conta = ContaBancaria(...)"],
        ["Atributo", "Variável que guarda estado", "self.nome, self.saldo"],
        ["Método", "Função dentro da classe", "def depositar(self, valor)"],
        ["Construtor", "Inicializa objeto", "__init__(self, ...)"],
        ["Herança", "Classe filha herda da pai", "(não usado neste projeto)"],
        ["Encapsulamento", "Ocultar detalhes internos", "_next_id (privado)"],
    ]
    
    t5 = Table(conceitos_poo, colWidths=[1.3*inch, 1.8*inch, 2.4*inch])
    t5.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8)
    ]))
    story.append(t5)
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("B. Estruturas de Dados", subtitulo_style))
    
    codigo_estruturas = '''# LISTA (Array) - coleção ordenada mutável
contas = []
contas.append(conta1)  # Adiciona no final
contas[0]              # Acessa por índice
len(contas)            # Quantidade de elementos

# DICIONÁRIO (Dict) - pares chave-valor
config = {'host': 'localhost', 'port': 5432}
config['host']         # Acessa por chave
config.get('user', 'default')  # Valor padrão se não existir

# TUPLA - coleção ordenada imutável
coordenadas = (10, 20)
x, y = coordenadas     # Desempacotamento

# SET - coleção única sem ordem
numeros = {1, 2, 3, 3}  # Remove duplicatas automaticamente
'''
    
    story.append(Preformatted(codigo_estruturas, codigo_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("C. Tratamento de Erros", subtitulo_style))
    
    codigo_erros = '''try:
    # Código que pode gerar erro
    valor = int(input("Digite número: "))
    resultado = 10 / valor
    
except ValueError:
    # Erro de conversão (digitou texto)
    print("Não é um número válido!")
    
except ZeroDivisionError:
    # Divisão por zero
    print("Não pode dividir por zero!")
    
except Exception as e:
    # Captura qualquer outro erro
    print(f"Erro inesperado: {e}")
    
finally:
    # Sempre executa (mesmo com erro)
    print("Encerrando...")
'''
    
    story.append(Preformatted(codigo_erros, codigo_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("D. Type Hints (Anotação de Tipos)", subtitulo_style))
    
    codigo_types = '''from typing import List, Optional, Dict

def adicionar_conta(nome: str, saldo: float) -> int:
    # nome: str - parâmetro deve ser string
    # saldo: float - parâmetro deve ser número decimal
    # -> int - função retorna inteiro
    pass

def buscar_conta(nome: str) -> Optional[ContaBancaria]:
    # Optional: pode retornar ContaBancaria ou None
    pass

def listar_contas() -> List[ContaBancaria]:
    # List[ContaBancaria]: retorna lista de contas
    pass

# Type hints não são obrigatórios em Python,
# mas ajudam IDEs a detectar erros e melhoram legibilidade
'''
    
    story.append(Preformatted(codigo_types, codigo_style))
    
    story.append(PageBreak())
    
    # ========== 11. RAILWAY ==========
    story.append(Paragraph("11. 🚀 DEPLOYMENT NO RAILWAY", titulo_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("O que é Deployment?", subtitulo_style))
    story.append(Paragraph(
        "Deployment (implantação) é colocar sua aplicação online para outras pessoas acessarem. "
        "Railway é uma <b>plataforma PaaS</b> (Platform as a Service) que hospeda aplicações automaticamente.",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Arquivos de Configuração:", secao_style))
    
    codigo_railway = '''# Procfile - Comando que Railway executa
web: python web_server.py

# web: tipo de serviço (aceita HTTP)
# python web_server.py: comando para iniciar

# runtime.txt - Versão do Python
python-3.11

# Railway instala automaticamente esta versão

# .railwayignore - Arquivos que não sobem
sistema_financeiro.db
backups/
*.pyc
__pycache__/

# Similar a .gitignore - evita subir arquivos locais
'''
    
    story.append(Preformatted(codigo_railway, codigo_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Fluxo de Deploy:", secao_style))
    story.append(Paragraph("1️⃣ Você faz <i>git push</i> para GitHub", destaque_style))
    story.append(Paragraph("2️⃣ Railway detecta commit novo automaticamente", destaque_style))
    story.append(Paragraph("3️⃣ Railway baixa código, instala dependências (requirements.txt)", destaque_style))
    story.append(Paragraph("4️⃣ Railway executa comando do Procfile", destaque_style))
    story.append(Paragraph("5️⃣ Aplicação fica online com URL público", destaque_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Variáveis de Ambiente no Railway:", secao_style))
    story.append(Paragraph(
        "Railway fornece automaticamente: DATABASE_URL, PORT. "
        "Você adiciona manualmente: DATABASE_TYPE=postgresql. "
        "Isso permite que mesmo código rode em local (SQLite) e produção (PostgreSQL).",
        texto_style
    ))
    
    story.append(PageBreak())
    
    # ========== 12. EXERCÍCIOS ==========
    story.append(Paragraph("12. 📝 EXERCÍCIOS PRÁTICOS", titulo_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Exercício 1: Adicionar Campo em ContaBancaria", subtitulo_style))
    story.append(Paragraph(
        "<b>Objetivo:</b> Adicionar campo 'limite_credito' na classe ContaBancaria.<br/>"
        "<b>Passos:</b><br/>"
        "1. Adicionar parâmetro no __init__<br/>"
        "2. Atribuir a self.limite_credito<br/>"
        "3. Incluir em to_dict() e from_dict()<br/>"
        "4. Alterar CREATE TABLE no database.py<br/>"
        "5. Modificar INSERT e SELECT para incluir campo<br/>"
        "6. Atualizar frontend para exibir/editar limite",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Exercício 2: Criar Endpoint de Busca", subtitulo_style))
    story.append(Paragraph(
        "<b>Objetivo:</b> Criar endpoint /api/contas/buscar?nome=Itaú<br/>"
        "<b>Passos:</b><br/>"
        "1. Criar método buscar_conta_por_nome() em DatabaseManager<br/>"
        "2. Em web_server.py, criar rota @app.route('/api/contas/buscar')<br/>"
        "3. Usar request.args.get('nome') para pegar parâmetro da URL<br/>"
        "4. Chamar db.buscar_conta_por_nome()<br/>"
        "5. Retornar conta encontrada ou erro 404<br/>"
        "6. Testar no navegador: http://localhost:5000/api/contas/buscar?nome=Itaú",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Exercício 3: Validação de Dados", subtitulo_style))
    story.append(Paragraph(
        "<b>Objetivo:</b> Validar que saldo_inicial não seja negativo antes de salvar.<br/>"
        "<b>Passos:</b><br/>"
        "1. No endpoint adicionar_conta, adicionar if data['saldo_inicial'] < 0<br/>"
        "2. Se negativo, retornar jsonify({'error': 'Saldo não pode ser negativo'}), 400<br/>"
        "3. Testar enviando valor negativo via frontend<br/>"
        "4. Implementar validações similares para outros campos (nome vazio, etc)",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Exercício 4: Relatório de Contas", subtitulo_style))
    story.append(Paragraph(
        "<b>Objetivo:</b> Criar função que retorna total de saldo de todas as contas.<br/>"
        "<b>Passos:</b><br/>"
        "1. Criar método calcular_saldo_total() em DatabaseManager<br/>"
        "2. Usar SUM em SQL: SELECT SUM(saldo_inicial) FROM contas_bancarias<br/>"
        "3. Criar endpoint /api/relatorios/saldo-total<br/>"
        "4. Retornar {'total': valor}<br/>"
        "5. No frontend, exibir valor em dashboard",
        texto_style
    ))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Exercício 5: Migração de Banco", subtitulo_style))
    story.append(Paragraph(
        "<b>Objetivo:</b> Criar script para copiar dados entre bancos.<br/>"
        "<b>Passos:</b><br/>"
        "1. Criar arquivo migrar_dados.py<br/>"
        "2. Instanciar dois DatabaseManagers (origem e destino)<br/>"
        "3. Buscar todas as contas da origem<br/>"
        "4. Para cada conta, adicionar no destino<br/>"
        "5. Usar try/except para tratar erros<br/>"
        "6. Imprimir progresso (conta 1/10, 2/10, etc)",
        texto_style
    ))
    
    story.append(PageBreak())
    
    # ========== CONCLUSÃO ==========
    story.append(Paragraph("🎓 CONCLUSÃO", titulo_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Parabéns!", subtitulo_style))
    story.append(Paragraph(
        "Este sistema financeiro aplica conceitos fundamentais de programação:<br/><br/>"
        "✅ Programação Orientada a Objetos<br/>"
        "✅ Banco de Dados (SQL)<br/>"
        "✅ APIs REST<br/>"
        "✅ Frontend/Backend<br/>"
        "✅ Deploy em Produção<br/><br/>"
        "Continue praticando os exercícios e explorando o código!",
        texto_style
    ))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("📚 Recursos para Continuar Aprendendo:", secao_style))
    story.append(Paragraph("• Documentação oficial Python: docs.python.org", texto_style))
    story.append(Paragraph("• Flask: flask.palletsprojects.com", texto_style))
    story.append(Paragraph("• PostgreSQL: postgresql.org/docs", texto_style))
    story.append(Paragraph("• MDN Web Docs (JavaScript): developer.mozilla.org", texto_style))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("💡 Próximos Passos:", secao_style))
    story.append(Paragraph("1. Implemente os exercícios propostos", texto_style))
    story.append(Paragraph("2. Adicione novos recursos (relatórios, gráficos)", texto_style))
    story.append(Paragraph("3. Estude autenticação/autorização (login)", texto_style))
    story.append(Paragraph("4. Explore testes automatizados (pytest)", texto_style))
    story.append(Paragraph("5. Aprenda sobre Docker e containers", texto_style))
    
    # Gerar PDF
    doc.build(story)
    print(f"✅ PDF gerado com sucesso: {filename}")
    return filename

if __name__ == '__main__':
    criar_pdf_documentacao()
