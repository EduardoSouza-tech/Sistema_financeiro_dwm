"""
Interface de Usuário - Sistema Financeiro
Menu interativo para operações do sistema
"""
import sys
import os
from datetime import datetime, timedelta

# Adicionar o diretório do script ao path para permitir importações locais
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gerenciador import GerenciadorFinanceiro
from models import TipoLancamento, StatusLancamento


class InterfaceUsuario:
    """Interface de linha de comando para o sistema financeiro"""
    
    def __init__(self):
        self.gerenciador = GerenciadorFinanceiro()
    
    def limpar_tela(self):
        """Limpa a tela do console"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def exibir_cabecalho(self, titulo: str):
        """Exibe cabeçalho formatado"""
        print("\n" + "=" * 70)
        print(f"  {titulo}".center(70))
        print("=" * 70 + "\n")
    
    def pausar(self):
        """Pausa a execução até o usuário pressionar Enter"""
        input("\nPressione Enter para continuar...")
    
    def ler_data(self, mensagem: str) -> datetime:
        """Lê uma data do usuário"""
        while True:
            try:
                data_str = input(f"{mensagem} (dd/mm/aaaa): ")
                return datetime.strptime(data_str, "%d/%m/%Y")
            except ValueError:
                print("Data inválida! Use o formato dd/mm/aaaa")
    
    def ler_valor(self, mensagem: str) -> float:
        """Lê um valor monetário do usuário"""
        while True:
            try:
                valor_str = input(f"{mensagem}: R$ ")
                valor = float(valor_str.replace(",", "."))
                if valor <= 0:
                    print("O valor deve ser maior que zero!")
                    continue
                return valor
            except ValueError:
                print("Valor inválido! Digite um número.")
    
    # === MENU PRINCIPAL ===
    
    def exibir_menu_principal(self):
        """Exibe o menu principal"""
        self.limpar_tela()
        self.exibir_cabecalho("SISTEMA FINANCEIRO")
        
        # Exibir resumo rápido
        saldo_total = self.gerenciador.calcular_saldo_total()
        contas_receber = self.gerenciador.calcular_contas_receber()
        contas_pagar = self.gerenciador.calcular_contas_pagar()
        
        print(f"💰 Saldo Total: R$ {saldo_total:,.2f}")
        print(f"📈 Contas a Receber: R$ {contas_receber:,.2f}")
        print(f"📉 Contas a Pagar: R$ {contas_pagar:,.2f}")
        print(f"💵 Saldo Projetado: R$ {(saldo_total + contas_receber - contas_pagar):,.2f}")
        
        print("\n" + "-" * 70)
        print("\n[1] Contas Bancárias")
        print("[2] Lançamentos Financeiros")
        print("[3] Contas a Receber")
        print("[4] Contas a Pagar")
        print("[5] Fluxo de Caixa")
        print("[6] Relatórios")
        print("[0] Sair")
        print("\n" + "-" * 70)
    
    def menu_principal(self):
        """Loop principal do menu"""
        while True:
            self.exibir_menu_principal()
            opcao = input("\nEscolha uma opção: ")
            
            if opcao == "1":
                self.menu_contas_bancarias()
            elif opcao == "2":
                self.menu_lancamentos()
            elif opcao == "3":
                self.menu_contas_receber()
            elif opcao == "4":
                self.menu_contas_pagar()
            elif opcao == "5":
                self.exibir_fluxo_caixa()
            elif opcao == "6":
                self.menu_relatorios()
            elif opcao == "0":
                print("\nSaindo do sistema...")
                break
            else:
                print("\nOpção inválida!")
                self.pausar()
    
    # === MENU CONTAS BANCÁRIAS ===
    
    def menu_contas_bancarias(self):
        """Menu de gerenciamento de contas bancárias"""
        while True:
            self.limpar_tela()
            self.exibir_cabecalho("CONTAS BANCÁRIAS")
            
            contas = self.gerenciador.listar_contas()
            if contas:
                print("Contas cadastradas:\n")
                for conta in contas:
                    print(f"  • {conta.nome} - {conta.banco}")
                    print(f"    Agência: {conta.agencia} | Conta: {conta.conta}")
                    print(f"    Saldo: R$ {conta.saldo_atual:,.2f}\n")
            else:
                print("Nenhuma conta cadastrada.\n")
            
            print("-" * 70)
            print("\n[1] Adicionar Conta")
            print("[2] Remover Conta")
            print("[0] Voltar")
            
            opcao = input("\nEscolha uma opção: ")
            
            if opcao == "1":
                self.adicionar_conta()
            elif opcao == "2":
                self.remover_conta()
            elif opcao == "0":
                break
            else:
                print("\nOpção inválida!")
                self.pausar()
    
    def adicionar_conta(self):
        """Adiciona uma nova conta bancária"""
        self.limpar_tela()
        self.exibir_cabecalho("ADICIONAR CONTA BANCÁRIA")
        
        try:
            nome = input("Nome da conta: ")
            banco = input("Banco: ")
            agencia = input("Agência: ")
            conta = input("Número da conta: ")
            saldo_inicial = self.ler_valor("Saldo inicial")
            
            self.gerenciador.adicionar_conta(nome, banco, agencia, conta, saldo_inicial)
            print("\n✓ Conta adicionada com sucesso!")
        except ValueError as e:
            print(f"\n✗ Erro: {e}")
        
        self.pausar()
    
    def remover_conta(self):
        """Remove uma conta bancária"""
        contas = self.gerenciador.listar_contas()
        if not contas:
            print("\nNenhuma conta para remover.")
            self.pausar()
            return
        
        print("\nContas disponíveis:")
        for i, conta in enumerate(contas, 1):
            print(f"[{i}] {conta.nome}")
        
        try:
            idx = int(input("\nNúmero da conta a remover: ")) - 1
            if 0 <= idx < len(contas):
                conta = contas[idx]
                confirmacao = input(f"Confirma a remoção de '{conta.nome}'? (s/n): ")
                if confirmacao.lower() == 's':
                    self.gerenciador.remover_conta(conta.nome)
                    print("\n✓ Conta removida com sucesso!")
            else:
                print("\nNúmero inválido!")
        except ValueError:
            print("\nNúmero inválido!")
        
        self.pausar()
    
    # === MENU LANÇAMENTOS ===
    
    def menu_lancamentos(self):
        """Menu de gerenciamento de lançamentos"""
        while True:
            self.limpar_tela()
            self.exibir_cabecalho("LANÇAMENTOS FINANCEIROS")
            
            print("[1] Listar Todos os Lançamentos")
            print("[2] Adicionar Receita")
            print("[3] Adicionar Despesa")
            print("[4] Pagar Lançamento")
            print("[5] Cancelar Lançamento")
            print("[0] Voltar")
            
            opcao = input("\nEscolha uma opção: ")
            
            if opcao == "1":
                self.listar_lancamentos()
            elif opcao == "2":
                self.adicionar_lancamento(TipoLancamento.RECEITA)
            elif opcao == "3":
                self.adicionar_lancamento(TipoLancamento.DESPESA)
            elif opcao == "4":
                self.pagar_lancamento()
            elif opcao == "5":
                self.cancelar_lancamento()
            elif opcao == "0":
                break
            else:
                print("\nOpção inválida!")
                self.pausar()
    
    def listar_lancamentos(self):
        """Lista todos os lançamentos"""
        self.limpar_tela()
        self.exibir_cabecalho("TODOS OS LANÇAMENTOS")
        
        lancamentos = self.gerenciador.listar_lancamentos()
        if not lancamentos:
            print("Nenhum lançamento cadastrado.")
        else:
            for lanc in sorted(lancamentos, key=lambda x: x.data_vencimento):
                tipo_icon = "📈" if lanc.tipo == TipoLancamento.RECEITA else "📉"
                status_texto = self._obter_status_texto(lanc.status)
                
                print(f"\n{tipo_icon} ID: {lanc.id} | {lanc.descricao}")
                print(f"   Valor: R$ {lanc.valor:,.2f} | Categoria: {lanc.categoria}")
                print(f"   Vencimento: {lanc.data_vencimento.strftime('%d/%m/%Y')} | Status: {status_texto}")
                if lanc.pessoa:
                    print(f"   Pessoa: {lanc.pessoa}")
                if lanc.data_pagamento:
                    print(f"   Pagamento: {lanc.data_pagamento.strftime('%d/%m/%Y')} | Conta: {lanc.conta_bancaria}")
        
        self.pausar()
    
    def _obter_status_texto(self, status: StatusLancamento) -> str:
        """Retorna texto formatado do status"""
        status_map = {
            StatusLancamento.PENDENTE: "⏳ Pendente",
            StatusLancamento.PAGO: "✓ Pago",
            StatusLancamento.VENCIDO: "⚠ Vencido",
            StatusLancamento.CANCELADO: "✗ Cancelado"
        }
        return status_map.get(status, str(status))
    
    def adicionar_lancamento(self, tipo: TipoLancamento):
        """Adiciona um novo lançamento"""
        self.limpar_tela()
        tipo_texto = "RECEITA" if tipo == TipoLancamento.RECEITA else "DESPESA"
        self.exibir_cabecalho(f"ADICIONAR {tipo_texto}")
        
        # Exibir categorias disponíveis
        categorias = [cat for cat in self.gerenciador.categorias.values() if cat.tipo == tipo]
        print("Categorias disponíveis:\n")
        for i, cat in enumerate(categorias, 1):
            print(f"[{i}] {cat.nome} - {cat.descricao}")
        
        try:
            cat_idx = int(input("\nEscolha a categoria: ")) - 1
            if not (0 <= cat_idx < len(categorias)):
                print("\nCategoria inválida!")
                self.pausar()
                return
            
            categoria = categorias[cat_idx].nome
            
            descricao = input("Descrição: ")
            valor = self.ler_valor("Valor")
            data_vencimento = self.ler_data("Data de vencimento")
            pessoa = input("Cliente/Fornecedor (opcional): ")
            num_documento = input("Número do documento (opcional): ")
            observacoes = input("Observações (opcional): ")
            
            self.gerenciador.adicionar_lancamento(
                descricao=descricao,
                valor=valor,
                tipo=tipo,
                categoria=categoria,
                data_vencimento=data_vencimento,
                pessoa=pessoa,
                observacoes=observacoes,
                num_documento=num_documento
            )
            
            print(f"\n✓ {tipo_texto.capitalize()} adicionada com sucesso!")
        except ValueError as e:
            print(f"\n✗ Erro: {e}")
        
        self.pausar()
    
    def pagar_lancamento(self):
        """Marca um lançamento como pago"""
        self.limpar_tela()
        self.exibir_cabecalho("PAGAR LANÇAMENTO")
        
        # Listar lançamentos pendentes
        pendentes = self.gerenciador.listar_lancamentos(status=StatusLancamento.PENDENTE)
        if not pendentes:
            print("Nenhum lançamento pendente.")
            self.pausar()
            return
        
        print("Lançamentos pendentes:\n")
        for lanc in pendentes:
            tipo_icon = "📈" if lanc.tipo == TipoLancamento.RECEITA else "📉"
            print(f"{tipo_icon} [{lanc.id}] {lanc.descricao} - R$ {lanc.valor:,.2f}")
            print(f"    Vencimento: {lanc.data_vencimento.strftime('%d/%m/%Y')}\n")
        
        # Listar contas disponíveis
        contas = self.gerenciador.listar_contas()
        if not contas:
            print("Nenhuma conta bancária cadastrada. Cadastre uma conta primeiro.")
            self.pausar()
            return
        
        print("\nContas disponíveis:\n")
        for i, conta in enumerate(contas, 1):
            print(f"[{i}] {conta.nome} - Saldo: R$ {conta.saldo_atual:,.2f}")
        
        try:
            id_lanc = int(input("\nID do lançamento: "))
            idx_conta = int(input("Número da conta: ")) - 1
            
            if 0 <= idx_conta < len(contas):
                conta = contas[idx_conta]
                usar_hoje = input("Usar data de hoje? (s/n): ")
                
                if usar_hoje.lower() == 's':
                    data_pagamento = datetime.now()
                else:
                    data_pagamento = self.ler_data("Data de pagamento")
                
                if self.gerenciador.pagar_lancamento(id_lanc, conta.nome, data_pagamento):
                    print("\n✓ Lançamento pago com sucesso!")
                else:
                    print("\n✗ Erro ao pagar lançamento!")
            else:
                print("\nConta inválida!")
        except ValueError:
            print("\nValor inválido!")
        
        self.pausar()
    
    def cancelar_lancamento(self):
        """Cancela um lançamento"""
        try:
            id_lanc = int(input("\nID do lançamento a cancelar: "))
            confirmacao = input("Confirma o cancelamento? (s/n): ")
            
            if confirmacao.lower() == 's':
                if self.gerenciador.cancelar_lancamento(id_lanc):
                    print("\n✓ Lançamento cancelado com sucesso!")
                else:
                    print("\n✗ Lançamento não encontrado!")
        except ValueError:
            print("\nID inválido!")
        
        self.pausar()
    
    # === CONTAS A RECEBER ===
    
    def menu_contas_receber(self):
        """Exibe contas a receber"""
        self.limpar_tela()
        self.exibir_cabecalho("CONTAS A RECEBER")
        
        receitas = self.gerenciador.listar_lancamentos(tipo=TipoLancamento.RECEITA)
        
        pendentes = [r for r in receitas if r.status == StatusLancamento.PENDENTE]
        vencidas = [r for r in receitas if r.status == StatusLancamento.VENCIDO]
        pagas = [r for r in receitas if r.status == StatusLancamento.PAGO]
        
        print(f"📊 RESUMO")
        print(f"   Pendentes: {len(pendentes)} | Total: R$ {sum(r.valor for r in pendentes):,.2f}")
        print(f"   Vencidas: {len(vencidas)} | Total: R$ {sum(r.valor for r in vencidas):,.2f}")
        print(f"   Recebidas: {len(pagas)} | Total: R$ {sum(r.valor for r in pagas):,.2f}")
        
        if pendentes or vencidas:
            print("\n" + "-" * 70)
            print("\nDETALHES:\n")
            
            for lanc in sorted(pendentes + vencidas, key=lambda x: x.data_vencimento):
                status_texto = self._obter_status_texto(lanc.status)
                print(f"ID: {lanc.id} | {lanc.descricao}")
                print(f"Valor: R$ {lanc.valor:,.2f} | Vencimento: {lanc.data_vencimento.strftime('%d/%m/%Y')}")
                print(f"Status: {status_texto} | Cliente: {lanc.pessoa}\n")
        
        self.pausar()
    
    # === CONTAS A PAGAR ===
    
    def menu_contas_pagar(self):
        """Exibe contas a pagar"""
        self.limpar_tela()
        self.exibir_cabecalho("CONTAS A PAGAR")
        
        despesas = self.gerenciador.listar_lancamentos(tipo=TipoLancamento.DESPESA)
        
        pendentes = [d for d in despesas if d.status == StatusLancamento.PENDENTE]
        vencidas = [d for d in despesas if d.status == StatusLancamento.VENCIDO]
        pagas = [d for d in despesas if d.status == StatusLancamento.PAGO]
        
        print(f"📊 RESUMO")
        print(f"   Pendentes: {len(pendentes)} | Total: R$ {sum(d.valor for d in pendentes):,.2f}")
        print(f"   Vencidas: {len(vencidas)} | Total: R$ {sum(d.valor for d in vencidas):,.2f}")
        print(f"   Pagas: {len(pagas)} | Total: R$ {sum(d.valor for d in pagas):,.2f}")
        
        if pendentes or vencidas:
            print("\n" + "-" * 70)
            print("\nDETALHES:\n")
            
            for lanc in sorted(pendentes + vencidas, key=lambda x: x.data_vencimento):
                status_texto = self._obter_status_texto(lanc.status)
                print(f"ID: {lanc.id} | {lanc.descricao}")
                print(f"Valor: R$ {lanc.valor:,.2f} | Vencimento: {lanc.data_vencimento.strftime('%d/%m/%Y')}")
                print(f"Status: {status_texto} | Fornecedor: {lanc.pessoa}\n")
        
        self.pausar()
    
    # === FLUXO DE CAIXA ===
    
    def exibir_fluxo_caixa(self):
        """Exibe o fluxo de caixa projetado"""
        self.limpar_tela()
        self.exibir_cabecalho("FLUXO DE CAIXA")
        
        print("Períodos disponíveis:")
        print("[1] 7 dias")
        print("[2] 15 dias")
        print("[3] 30 dias")
        print("[4] 60 dias")
        print("[5] 90 dias")
        
        opcao = input("\nEscolha o período: ")
        
        dias_map = {"1": 7, "2": 15, "3": 30, "4": 60, "5": 90}
        dias = dias_map.get(opcao, 30)
        
        fluxo = self.gerenciador.obter_fluxo_caixa(dias)
        
        self.limpar_tela()
        self.exibir_cabecalho(f"FLUXO DE CAIXA - PRÓXIMOS {dias} DIAS")
        
        print(f"💰 Saldo Atual: R$ {fluxo['saldo_atual']:,.2f}")
        print(f"📈 Receitas Previstas: R$ {fluxo['receitas_previstas']:,.2f}")
        print(f"📉 Despesas Previstas: R$ {fluxo['despesas_previstas']:,.2f}")
        print(f"\n{'=' * 70}")
        print(f"💵 Saldo Projetado: R$ {fluxo['saldo_projetado']:,.2f}")
        print(f"{'=' * 70}")
        
        self.pausar()
    
    # === RELATÓRIOS ===
    
    def menu_relatorios(self):
        """Menu de relatórios"""
        while True:
            self.limpar_tela()
            self.exibir_cabecalho("RELATÓRIOS")
            
            print("[1] Relatório Mensal")
            print("[2] Relatório por Período")
            print("[3] Relatório por Categoria")
            print("[0] Voltar")
            
            opcao = input("\nEscolha uma opção: ")
            
            if opcao == "1":
                self.relatorio_mensal()
            elif opcao == "2":
                self.relatorio_periodo()
            elif opcao == "3":
                self.relatorio_categorias()
            elif opcao == "0":
                break
            else:
                print("\nOpção inválida!")
                self.pausar()
    
    def relatorio_mensal(self):
        """Gera relatório do mês atual"""
        hoje = datetime.now()
        inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calcular último dia do mês
        if hoje.month == 12:
            fim_mes = hoje.replace(year=hoje.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            fim_mes = hoje.replace(month=hoje.month + 1, day=1) - timedelta(days=1)
        
        fim_mes = fim_mes.replace(hour=23, minute=59, second=59)
        
        self._exibir_relatorio_periodo(inicio_mes, fim_mes, f"RELATÓRIO - {hoje.strftime('%B/%Y').upper()}")
    
    def relatorio_periodo(self):
        """Gera relatório de um período específico"""
        self.limpar_tela()
        self.exibir_cabecalho("RELATÓRIO POR PERÍODO")
        
        data_inicio = self.ler_data("Data inicial")
        data_fim = self.ler_data("Data final")
        
        self._exibir_relatorio_periodo(data_inicio, data_fim, 
                                      f"RELATÓRIO - {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    
    def _exibir_relatorio_periodo(self, data_inicio: datetime, data_fim: datetime, titulo: str):
        """Exibe relatório de um período"""
        self.limpar_tela()
        self.exibir_cabecalho(titulo)
        
        receitas = self.gerenciador.calcular_receitas_periodo(data_inicio, data_fim)
        despesas = self.gerenciador.calcular_despesas_periodo(data_inicio, data_fim)
        saldo = receitas - despesas
        
        print(f"📈 Total de Receitas: R$ {receitas:,.2f}")
        print(f"📉 Total de Despesas: R$ {despesas:,.2f}")
        print(f"\n{'=' * 70}")
        print(f"💵 Saldo do Período: R$ {saldo:,.2f}")
        print(f"{'=' * 70}")
        
        self.pausar()
    
    def relatorio_categorias(self):
        """Gera relatório por categorias"""
        self.limpar_tela()
        self.exibir_cabecalho("RELATÓRIO POR CATEGORIA")
        
        data_inicio = self.ler_data("Data inicial")
        data_fim = self.ler_data("Data final")
        
        resumo = self.gerenciador.obter_resumo_categorias(data_inicio, data_fim)
        
        self.limpar_tela()
        self.exibir_cabecalho(f"RELATÓRIO POR CATEGORIA - {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
        
        print("📈 RECEITAS POR CATEGORIA:\n")
        if resumo['receitas']:
            for cat, valor in sorted(resumo['receitas'].items(), key=lambda x: x[1], reverse=True):
                percentual = (valor / resumo['total_receitas'] * 100) if resumo['total_receitas'] > 0 else 0
                print(f"   {cat}: R$ {valor:,.2f} ({percentual:.1f}%)")
        else:
            print("   Nenhuma receita no período")
        
        print(f"\n   TOTAL: R$ {resumo['total_receitas']:,.2f}")
        
        print("\n" + "-" * 70)
        print("\n📉 DESPESAS POR CATEGORIA:\n")
        if resumo['despesas']:
            for cat, valor in sorted(resumo['despesas'].items(), key=lambda x: x[1], reverse=True):
                percentual = (valor / resumo['total_despesas'] * 100) if resumo['total_despesas'] > 0 else 0
                print(f"   {cat}: R$ {valor:,.2f} ({percentual:.1f}%)")
        else:
            print("   Nenhuma despesa no período")
        
        print(f"\n   TOTAL: R$ {resumo['total_despesas']:,.2f}")
        
        print("\n" + "=" * 70)
        print(f"💵 SALDO: R$ {resumo['saldo']:,.2f}")
        print("=" * 70)
        
        self.pausar()


def main():
    """Função principal"""
    interface = InterfaceUsuario()
    interface.menu_principal()


if __name__ == "__main__":
    main()
