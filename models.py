"""
Modelos de dados para o Sistema Financeiro
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
import json


class TipoLancamento(Enum):
    """Tipos de lançamento financeiro"""
    RECEITA = "receita"
    DESPESA = "despesa"
    TRANSFERENCIA = "transferencia"


class StatusLancamento(Enum):
    """Status do lançamento"""
    PENDENTE = "pendente"
    PAGO = "pago"
    CANCELADO = "cancelado"
    VENCIDO = "vencido"


class Categoria:
    """Categoria de lançamento financeiro"""
    def __init__(self, nome: str, tipo: TipoLancamento, descricao: str = "", subcategorias: Optional[List[str]] = None):
        self.nome = nome
        self.tipo = tipo
        self.descricao = descricao
        self.subcategorias = subcategorias if subcategorias is not None else []
    
    def adicionar_subcategoria(self, nome_subcategoria: str):
        """Adiciona uma subcategoria"""
        if nome_subcategoria not in self.subcategorias:
            self.subcategorias.append(nome_subcategoria)
            # Salvar no banco de dados
            import database  # type: ignore
            database.atualizar_categoria(self)  # type: ignore
    
    def remover_subcategoria(self, nome_subcategoria: str):
        """Remove uma subcategoria"""
        if nome_subcategoria in self.subcategorias:
            self.subcategorias.remove(nome_subcategoria)
            # Salvar no banco de dados
            import database  # type: ignore
            database.atualizar_categoria(self)  # type: ignore
    
    def to_dict(self):
        return {
            "nome": self.nome,
            "tipo": self.tipo.value,
            "descricao": self.descricao,
            "subcategorias": self.subcategorias
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            nome=data["nome"],
            tipo=TipoLancamento(data["tipo"]),
            descricao=data.get("descricao", ""),
            subcategorias=data.get("subcategorias", [])
        )


class ContaBancaria:
    """Representa uma conta bancária"""
    _next_id = 1
    
    def __init__(self, nome: str, banco: str, agencia: str, conta: str, 
                 saldo_inicial: float = 0.0, id: Optional[int] = None):
        if saldo_inicial < 0:
            raise ValueError("O saldo inicial não pode ser negativo")
        
        if id is None:
            self.id = ContaBancaria._next_id
            ContaBancaria._next_id += 1
        else:
            self.id = id
            if id >= ContaBancaria._next_id:
                ContaBancaria._next_id = id + 1
        
        self.nome = nome
        self.banco = banco
        self.agencia = agencia
        self.conta = conta
        self.saldo_inicial = saldo_inicial
        self.saldo_atual = saldo_inicial
    
    def depositar(self, valor: float):
        """Adiciona valor ao saldo"""
        self.saldo_atual += valor
    
    def sacar(self, valor: float) -> bool:
        """Remove valor do saldo se houver saldo suficiente"""
        if self.saldo_atual >= valor:
            self.saldo_atual -= valor
            return True
        return False
    
    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "banco": self.banco,
            "agencia": self.agencia,
            "conta": self.conta,
            "saldo_inicial": self.saldo_inicial,
            "saldo_atual": self.saldo_atual
        }
    
    @classmethod
    def from_dict(cls, data):
        conta = cls(
            nome=data["nome"],
            banco=data["banco"],
            agencia=data["agencia"],
            conta=data["conta"],
            saldo_inicial=data["saldo_inicial"],
            id=data.get("id")
        )
        conta.saldo_atual = data["saldo_atual"]
        return conta


class Lancamento:
    """Representa um lançamento financeiro (receita ou despesa)"""
    _contador = 1
    
    def __init__(self, descricao: str, valor: float, tipo: TipoLancamento,
                 categoria: str, data_vencimento: datetime, 
                 data_pagamento: Optional[datetime] = None,
                 conta_bancaria: Optional[str] = None,
                 pessoa: str = "", observacoes: str = "",
                 num_documento: str = "", subcategoria: str = ""):
        if valor <= 0:
            raise ValueError("O valor deve ser maior que zero")
        
        self.id = Lancamento._contador
        Lancamento._contador += 1
        self.descricao = descricao
        self.valor = valor
        self.tipo = tipo
        self.categoria = categoria
        self.subcategoria = subcategoria
        self.data_vencimento = data_vencimento
        self.data_pagamento = data_pagamento
        self.conta_bancaria = conta_bancaria
        self.pessoa = pessoa
        self.observacoes = observacoes
        self.num_documento = num_documento
        self.status = self._calcular_status()
    
    def _calcular_status(self) -> StatusLancamento:
        """Calcula o status do lançamento"""
        if self.data_pagamento:
            return StatusLancamento.PAGO
        
        # Converter data_vencimento para date se necessário
        data_venc = self.data_vencimento.date() if isinstance(self.data_vencimento, datetime) else self.data_vencimento
        hoje = datetime.now().date()
        
        if hoje > data_venc:
            return StatusLancamento.VENCIDO
        else:
            return StatusLancamento.PENDENTE
    
    def pagar(self, data_pagamento: datetime, conta: ContaBancaria, juros: float = 0.0) -> bool:
        """Marca o lançamento como pago"""
        # Verificar se já foi pago
        if self.status == StatusLancamento.PAGO:
            return False
        
        # Calcular valor total (valor original + juros)
        valor_total = self.valor + juros
        
        # Se for despesa, verificar saldo antes de pagar
        if self.tipo == TipoLancamento.DESPESA:
            if not conta.sacar(valor_total):
                return False
        else:
            conta.depositar(valor_total)
        
        self.data_pagamento = data_pagamento
        self.conta_bancaria = conta.nome
        self.status = StatusLancamento.PAGO
        return True
    
    def cancelar(self):
        """Cancela o lançamento"""
        self.status = StatusLancamento.CANCELADO
    
    def atualizar_status(self):
        """Atualiza o status do lançamento"""
        if self.status != StatusLancamento.CANCELADO:
            self.status = self._calcular_status()
    
    def to_dict(self):
        return {
            "id": self.id,
            "descricao": self.descricao,
            "valor": self.valor,
            "tipo": self.tipo.value,
            "categoria": self.categoria,
            "subcategoria": self.subcategoria,
            "data_vencimento": self.data_vencimento.isoformat(),
            "data_pagamento": self.data_pagamento.isoformat() if self.data_pagamento else None,
            "conta_bancaria": self.conta_bancaria,
            "pessoa": self.pessoa,
            "observacoes": self.observacoes,
            "num_documento": self.num_documento,
            "status": self.status.value
        }
    
    @classmethod
    def from_dict(cls, data):
        lancamento = cls(
            descricao=data["descricao"],
            valor=data["valor"],
            tipo=TipoLancamento(data["tipo"]),
            categoria=data["categoria"],
            data_vencimento=datetime.fromisoformat(data["data_vencimento"]),
            data_pagamento=datetime.fromisoformat(data["data_pagamento"]) if data["data_pagamento"] else None,
            conta_bancaria=data.get("conta_bancaria"),
            pessoa=data.get("pessoa", ""),
            observacoes=data.get("observacoes", ""),
            num_documento=data.get("num_documento", ""),
            subcategoria=data.get("subcategoria", "")
        )
        lancamento.id = data["id"]
        lancamento.status = StatusLancamento(data["status"])
        
        # Atualizar o contador estático
        if lancamento.id >= Lancamento._contador:
            Lancamento._contador = lancamento.id + 1
        
        return lancamento
