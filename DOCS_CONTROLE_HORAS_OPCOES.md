# 📊 Controle de Horas - Documentação de Opções

**Data**: 22/02/2026  
**Versão**: 1.0  
**Status**: Opção A - IMPLEMENTADA ✅

---

## 📋 Visão Geral

O sistema de **Controle de Horas** gerencia pacotes de horas contratadas por clientes e o consumo através de sessões de fotografia.

---

## ⚙️ Opções de Funcionamento

### **Opção A - Controle Apenas de Contratos** ✅ **(IMPLEMENTADA)**

#### **Descrição**
- O Controle de Horas mostra **apenas sessões vinculadas a contratos**
- Sessões avulsas (sem contrato) **não aparecem no relatório**
- Permite separação clara entre:
  - **Pacotes contratados** (300h mensais, 1000h anuais, etc.)
  - **Serviços avulsos** (sessões pontuais cobradas separadamente)

#### **Comportamento Prático**

| Situação | Contrato ID | Aparece no Controle? | Desconta Horas? |
|----------|-------------|---------------------|-----------------|
| Cliente com pacote 300h/mês | `32` | ✅ SIM | ✅ SIM |
| Sessão vinculada ao pacote | `32` | ✅ SIM | ✅ SIM |
| Sessão avulsa do mesmo cliente | `NULL` | ❌ NÃO | ❌ NÃO |

#### **Vantagens** ✅
- ✅ **Clareza contábil**: Separa pacotes de serviços avulsos
- ✅ **Cobrança separada**: Cliente não "gasta" horas do pacote em extras
- ✅ **Flexibilidade**: Cliente pode ter pacote mensal + sessões avulsas simultâneas
- ✅ **Relatórios limpos**: Foco apenas no consumo de pacotes

#### **Desvantagens** ⚠️
- ⚠️ Sessões avulsas não aparecem no controle de horas
- ⚠️ Precisa de outro relatório para ver sessões avulsas

#### **Casos de Uso Ideais** 🎯
1. **Cliente Corporativo**: Pacote 500h/ano + sessões extras sob demanda
2. **Cliente Mensal**: 100h/mês fixo + ensaios especiais avulsos
3. **Cliente Misto**: Contrato regular + eventos pontuais

#### **Implementação Técnica**
```sql
-- Relatório busca APENAS contratos com controle ativo
SELECT * FROM contratos 
WHERE empresa_id = %s 
  AND controle_horas_ativo = true

-- Sessões DEVEM ter contrato_id para aparecer
SELECT * FROM sessoes 
WHERE contrato_id = %s  -- contrato_id NULL = excluído
  AND empresa_id = %s
```

**Arquivo**: `database_postgresql.py:8055-8095`

---

### **Opção B - Controle Completo do Cliente** ⚠️ **(NÃO IMPLEMENTADA)**

#### **Descrição**
- O Controle de Horas mostra **todas as sessões do cliente**
- Inclui sessões vinculadas a contratos **E** sessões avulsas
- Visão unificada de todo o trabalho realizado

#### **Comportamento Prático**

| Situação | Contrato ID | Aparece no Controle? | Desconta Horas? |
|----------|-------------|---------------------|-----------------|
| Cliente com pacote 300h/mês | `32` | ✅ SIM | ✅ SIM |
| Sessão vinculada ao pacote | `32` | ✅ SIM | ✅ SIM |
| Sessão avulsa do mesmo cliente | `NULL` | ✅ SIM | ❌ NÃO* |

*Sessões avulsas aparecem no relatório mas não descontam do pacote

#### **Vantagens** ✅
- ✅ **Visão completa**: Todas as sessões do cliente em um lugar
- ✅ **Histórico unificado**: Fácil ver todo o trabalho realizado
- ✅ **Análise de produtividade**: Horas totais trabalhadas para o cliente

#### **Desvantagens** ⚠️
- ⚠️ **Confusão contábil**: Mistura pacotes com serviços avulsos
- ⚠️ **Complexidade**: Precisa distinguir visualmente o que é pacote vs avulso
- ⚠️ **Relatório poluído**: Dificulta análise de consumo de pacotes
- ⚠️ **Risco de erro**: Cliente pode achar que avulso consome horas do pacote

#### **Casos de Uso Ideais** 🎯
1. **Análise de produtividade**: Quanto tempo total gastos com o cliente
2. **Planejamento de equipe**: Todas as atividades em um dashboard
3. **Clientes pequenos**: Poucos contratos, fácil distinguir

#### **Implementação Técnica** (Se fosse implementar)
```sql
-- Relatório buscaria TODOS os contratos do cliente
SELECT * FROM contratos 
WHERE empresa_id = %s 
  AND (cliente_id IN (...) OR controle_horas_ativo = true)

-- Sessões com OU sem contrato
SELECT * FROM sessoes 
WHERE (contrato_id = %s OR (contrato_id IS NULL AND cliente_id = %s))
  AND empresa_id = %s
```

---

## 🔄 Funcionalidade Futura: Compensação de Horas Entre Contratos

### **Objetivo**
Permitir que um cliente com **múltiplos contratos** possa compensar horas de um contrato em outro.

### **Cenário Exemplo**
```
Cliente: João Silva (ID: 64)

Contrato A (CONT-2026-001):
  - Tipo: Fotografia Comercial
  - Horas: 300h
  - Utilizadas: 280h
  - Restantes: 20h ✅

Contrato B (CONT-2026-002):
  - Tipo: Fotografia de Eventos
  - Horas: 200h
  - Utilizadas: 210h
  - Restantes: -10h ⚠️ (10h extras)

💡 Compensação: Transferir 10h do Contrato A → Contrato B
```

### **Resultado Após Compensação**
```
Contrato A:
  - Restantes: 10h (20h - 10h transferidas)

Contrato B:
  - Restantes: 0h (-10h + 10h recebidas)
  - Horas extras: 0h
```

### **Requisitos Técnicos** (A Implementar)

#### **1. Interface de Usuário**
```html
<!-- Modal de Compensação -->
<button onclick="abrirCompensacaoHoras(contratoId)">
  🔄 Compensar Horas
</button>

<div id="modal-compensacao">
  <h3>Compensar Horas Entre Contratos</h3>
  
  <div>
    <label>Contrato Origem (com saldo):</label>
    <select id="contrato-origem">
      <option value="32">CONT-2026-001 - 20h disponíveis</option>
    </select>
  </div>
  
  <div>
    <label>Contrato Destino (deficit):</label>
    <select id="contrato-destino">
      <option value="33">CONT-2026-002 - 10h extras</option>
    </select>
  </div>
  
  <div>
    <label>Quantidade de Horas:</label>
    <input type="number" id="horas-compensar" max="20" min="1">
  </div>
  
  <div>
    <label>Motivo/Observação:</label>
    <textarea id="compensacao-obs"></textarea>
  </div>
  
  <button onclick="executarCompensacao()">Confirmar Compensação</button>
</div>
```

#### **2. Backend - Nova Rota**
```python
# app/routes/contratos.py

@contratos_bp.route('/<int:origem_id>/compensar-horas', methods=['POST'])
@require_permission('contratos_edit')
def compensar_horas_contratos(origem_id: int):
    """
    Transfere horas de um contrato para outro do mesmo cliente
    
    POST /api/contratos/32/compensar-horas
    {
        "contrato_destino_id": 33,
        "quantidade_horas": 10,
        "observacao": "Compensação por excesso em eventos"
    }
    """
    try:
        empresa_id = session.get('empresa_id')
        data = request.json
        
        destino_id = data.get('contrato_destino_id')
        horas = float(data.get('quantidade_horas', 0))
        observacao = data.get('observacao', '')
        
        # Validações
        if horas <= 0:
            return jsonify({'error': 'Quantidade inválida'}), 400
        
        # Buscar contratos
        origem = db.obter_contrato(empresa_id, origem_id)
        destino = db.obter_contrato(empresa_id, destino_id)
        
        # Validar mesmo cliente
        if origem['cliente_id'] != destino['cliente_id']:
            return jsonify({'error': 'Contratos de clientes diferentes'}), 400
        
        # Validar saldo disponível
        saldo_origem = float(origem['horas_totais']) - float(origem['horas_utilizadas'])
        if saldo_origem < horas:
            return jsonify({'error': f'Saldo insuficiente: {saldo_origem}h'}), 400
        
        # Executar compensação
        resultado = db.compensar_horas_contratos(
            empresa_id=empresa_id,
            origem_id=origem_id,
            destino_id=destino_id,
            quantidade_horas=horas,
            observacao=observacao,
            usuario_id=session.get('user_id')
        )
        
        return jsonify({
            'success': True,
            'message': f'Compensadas {horas}h com sucesso',
            'origem': resultado['origem'],
            'destino': resultado['destino']
        }), 200
        
    except Exception as e:
        print(f"Erro compensação: {e}")
        return jsonify({'error': str(e)}), 500
```

#### **3. Banco de Dados - Nova Função**
```python
# database_postgresql.py

def compensar_horas_contratos(
    empresa_id: int,
    origem_id: int,
    destino_id: int,
    quantidade_horas: float,
    observacao: str,
    usuario_id: int
) -> Dict:
    """
    Transfere horas de um contrato para outro
    
    Lógica:
    1. Subtrai horas do contrato origem (horas_totais)
    2. Adiciona horas ao contrato destino (horas_totais)
    3. Registra log da compensação
    """
    with get_db_connection(empresa_id=empresa_id) as conn:
        cursor = conn.cursor()
        
        # 1. Remover horas do origem
        cursor.execute("""
            UPDATE contratos
            SET horas_totais = horas_totais - %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND empresa_id = %s
            RETURNING horas_totais, horas_utilizadas
        """, (quantidade_horas, origem_id, empresa_id))
        
        origem_result = cursor.fetchone()
        
        # 2. Adicionar horas ao destino
        cursor.execute("""
            UPDATE contratos
            SET horas_totais = horas_totais + %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND empresa_id = %s
            RETURNING horas_totais, horas_utilizadas
        """, (quantidade_horas, destino_id, empresa_id))
        
        destino_result = cursor.fetchone()
        
        # 3. Registrar log (criar tabela se necessário)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compensacoes_horas (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER NOT NULL,
                contrato_origem_id INTEGER NOT NULL,
                contrato_destino_id INTEGER NOT NULL,
                quantidade_horas DECIMAL(10,2) NOT NULL,
                observacao TEXT,
                usuario_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT INTO compensacoes_horas 
            (empresa_id, contrato_origem_id, contrato_destino_id, quantidade_horas, observacao, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (empresa_id, origem_id, destino_id, quantidade_horas, observacao, usuario_id))
        
        conn.commit()
        
        return {
            'origem': {
                'horas_totais': float(origem_result['horas_totais']),
                'horas_utilizadas': float(origem_result['horas_utilizadas'])
            },
            'destino': {
                'horas_totais': float(destino_result['horas_totais']),
                'horas_utilizadas': float(destino_result['horas_utilizadas'])
            }
        }
```

#### **4. Auditoria e Histórico**
```sql
-- Rastreabilidade completa
SELECT 
    ch.id,
    ch.created_at,
    co.numero as origem_numero,
    cd.numero as destino_numero,
    ch.quantidade_horas,
    ch.observacao,
    u.nome as usuario_nome
FROM compensacoes_horas ch
JOIN contratos co ON ch.contrato_origem_id = co.id
JOIN contratos cd ON ch.contrato_destino_id = cd.id
LEFT JOIN usuarios u ON ch.usuario_id = u.id
WHERE ch.empresa_id = %s
ORDER BY ch.created_at DESC
```

#### **5. Validações de Negócio**
- ✅ Ambos contratos devem pertencer ao **mesmo cliente**
- ✅ Contrato origem deve ter **saldo positivo**
- ✅ Quantidade não pode exceder **horas disponíveis**
- ✅ Somente usuários com permissão `contratos_edit`
- ✅ Log completo com **usuário, data, motivo**
- ✅ Operação **transacional** (rollback em caso de erro)

---

## 📊 Resumo de Status

| Funcionalidade | Status | Versão |
|----------------|--------|--------|
| **Opção A** - Controle apenas de contratos | ✅ Implementada | 1.0 |
| **Opção B** - Controle completo do cliente | ❌ Não implementada | - |
| **Compensação entre contratos** | 📋 Planejada | 2.0 |

---

## 🔗 Arquivos Relacionados

1. **Backend**:
   - `database_postgresql.py:7972-8149` - Função `gerar_relatorio_controle_horas()`
   - `app/routes/relatorios.py:1069-1176` - Rotas de relatório e exportação

2. **Frontend**:
   - `static/app.js:2693-2850` - Função `loadControleHoras()`
   - `templates/interface_nova.html:5479-5535` - Tab Controle de Horas

3. **Exportação**:
   - `pdf_export.py:1915-2065` - Geração de PDF
   - `pdf_export.py:2065-2200` - Geração de Excel

---

## 📝 Notas de Implementação

### **Decisão Atual: Opção A**
- Data: 22/02/2026
- Razão: Clareza contábil e separação de pacotes vs serviços avulsos
- Solicitante: Cliente/Usuário do sistema

### **Próximos Passos**
1. ✅ Manter Opção A como padrão
2. 📋 Planejar implementação de compensação entre contratos
3. 📋 Criar testes unitários para compensação
4. 📋 Documentar processo de compensação no manual do usuário

---

**Última atualização**: 22/02/2026  
**Responsável**: Sistema Financeiro DWM  
**Versão**: 1.0
