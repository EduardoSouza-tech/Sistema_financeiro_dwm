"""
Scheduler de Notificações Automáticas
Executa verificação periódica de sessões e contratos
"""

import schedule
import time
import threading
from datetime import datetime
import notification_service

# Flag para controlar se o scheduler está rodando
scheduler_running = False
scheduler_thread = None

def job_check_notifications():
    """Job que executa a verificação de notificações"""
    try:
        print(f"\n{'='*60}")
        print(f"🔔 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Executando verificação de notificações...")
        print(f"{'='*60}")
        
        notification_service.run_notifications_for_all_companies()
        
        print(f"{'='*60}")
        print(f"✅ Verificação concluída às {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")
    except Exception as e:
        print(f"❌ Erro ao executar job de notificações: {e}")

def run_scheduler():
    """Executar o scheduler em loop"""
    global scheduler_running
    scheduler_running = True
    
    print("🚀 Scheduler de notificações iniciado")
    print("Horários de execução:")
    print("  - 08:00 (manhã)")
    print("  - 14:00 (tarde)")
    print("  - 18:00 (final do dia)")
    
    while scheduler_running:
        schedule.run_pending()
        time.sleep(60)  # Verificar a cada 1 minuto

def start_scheduler():
    """Iniciar o scheduler em thread separada"""
    global scheduler_thread
    
    if scheduler_thread and scheduler_thread.is_alive():
        print("⚠️ Scheduler já está rodando")
        return False
    
    # Agendar jobs
    # Executar 3 vezes por dia: manhã, tarde e noite
    schedule.every().day.at("08:00").do(job_check_notifications)
    schedule.every().day.at("14:00").do(job_check_notifications)
    schedule.every().day.at("18:00").do(job_check_notifications)
    
    # Também pode configurar para rodar a cada X horas
    # schedule.every(4).hours.do(job_check_notifications)
    
    # Iniciar thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    print("✅ Scheduler iniciado com sucesso")
    return True

def stop_scheduler():
    """Parar o scheduler"""
    global scheduler_running
    
    if not scheduler_running:
        print("⚠️ Scheduler não está rodando")
        return False
    
    scheduler_running = False
    schedule.clear()
    
    print("🛑 Scheduler parado")
    return True

def get_scheduler_status():
    """Obter status do scheduler"""
    global scheduler_thread
    
    is_running = scheduler_thread and scheduler_thread.is_alive() and scheduler_running
    
    return {
        'running': is_running,
        'jobs_count': len(schedule.jobs),
        'next_run': str(schedule.next_run()) if schedule.jobs else None,
        'jobs': [
            {
                'interval': job.interval,
                'unit': job.unit,
                'at_time': str(job.at_time) if hasattr(job, 'at_time') and job.at_time else None,
                'next_run': str(job.next_run) if job.next_run else None
            }
            for job in schedule.jobs
        ]
    }

def trigger_manual_check(empresa_id=None):
    """
    Executar verificação manual de notificações
    Args:
        empresa_id: ID da empresa (None = todas)
    """
    try:
        if empresa_id:
            print(f"🔔 Executando verificação manual para empresa {empresa_id}")
            notification_service.send_notification_batch(empresa_id)
        else:
            print("🔔 Executando verificação manual para todas as empresas")
            notification_service.run_notifications_for_all_companies()
        
        return True
    except Exception as e:
        print(f"❌ Erro na verificação manual: {e}")
        return False

if __name__ == '__main__':
    # Executar scheduler quando chamado diretamente
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'start':
            start_scheduler()
            print("\n💡 Pressione Ctrl+C para parar o scheduler\n")
            try:
                # Manter o script rodando
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\n🛑 Parando scheduler...")
                stop_scheduler()
                print("👋 Scheduler encerrado")
        
        elif command == 'test':
            print("🧪 Executando teste de notificações...")
            trigger_manual_check()
            print("✅ Teste concluído")
        
        elif command == 'status':
            status = get_scheduler_status()
            print("\n📊 Status do Scheduler:")
            print(f"  Running: {status['running']}")
            print(f"  Jobs: {status['jobs_count']}")
            print(f"  Next Run: {status['next_run']}")
            print()
        
        else:
            print("Comandos disponíveis:")
            print("  python notification_scheduler.py start    - Iniciar scheduler")
            print("  python notification_scheduler.py test     - Testar notificações")
            print("  python notification_scheduler.py status   - Ver status")
    
    else:
        print("Uso: python notification_scheduler.py [start|test|status]")
