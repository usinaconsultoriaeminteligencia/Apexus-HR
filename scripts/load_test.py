#!/usr/bin/env python3
"""
Script de teste de carga para produção
"""
import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime
import argparse

class LoadTester:
    def __init__(self, base_url, concurrent_users=10, duration=60):
        self.base_url = base_url.rstrip('/')
        self.concurrent_users = concurrent_users
        self.duration = duration
        self.results = []
        self.start_time = None
        self.end_time = None
    
    async def make_request(self, session, endpoint, method='GET', data=None):
        """Faz uma requisição HTTP"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        start_time = time.time()
        try:
            if method == 'GET':
                async with session.get(url, headers=headers) as response:
                    content = await response.text()
                    status_code = response.status
            elif method == 'POST':
                async with session.post(url, headers=headers, json=data) as response:
                    content = await response.text()
                    status_code = response.status
            else:
                raise ValueError(f"Método {method} não suportado")
            
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code,
                'response_time': response_time,
                'success': 200 <= status_code < 300,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                'endpoint': endpoint,
                'method': method,
                'status_code': 0,
                'response_time': response_time,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def user_simulation(self, session, user_id):
        """Simula um usuário fazendo requisições"""
        endpoints = [
            ('/health', 'GET'),
            ('/api/candidates', 'GET'),
            ('/api/interviews', 'GET'),
            ('/api/reports', 'GET'),
        ]
        
        while time.time() - self.start_time < self.duration:
            # Escolher endpoint aleatório
            import random
            endpoint, method = random.choice(endpoints)
            
            # Fazer requisição
            result = await self.make_request(session, endpoint, method)
            self.results.append(result)
            
            # Aguardar um pouco antes da próxima requisição
            await asyncio.sleep(random.uniform(0.5, 2.0))
    
    async def run_test(self):
        """Executa o teste de carga"""
        print(f"🚀 Iniciando teste de carga...")
        print(f"📊 Usuários concorrentes: {self.concurrent_users}")
        print(f"⏱️  Duração: {self.duration} segundos")
        print(f"🌐 URL base: {self.base_url}")
        print("=" * 50)
        
        self.start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            # Criar tarefas para cada usuário
            tasks = []
            for i in range(self.concurrent_users):
                task = asyncio.create_task(self.user_simulation(session, i))
                tasks.append(task)
            
            # Aguardar todas as tarefas
            await asyncio.gather(*tasks)
        
        self.end_time = time.time()
        self.print_results()
    
    def print_results(self):
        """Imprime os resultados do teste"""
        if not self.results:
            print("❌ Nenhum resultado encontrado")
            return
        
        total_requests = len(self.results)
        successful_requests = sum(1 for r in self.results if r['success'])
        failed_requests = total_requests - successful_requests
        
        response_times = [r['response_time'] for r in self.results if r['success']]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
        else:
            avg_response_time = min_response_time = max_response_time = 0
            median_response_time = p95_response_time = 0
        
        actual_duration = self.end_time - self.start_time
        requests_per_second = total_requests / actual_duration
        
        print("\n" + "=" * 50)
        print("📊 RESULTADOS DO TESTE DE CARGA")
        print("=" * 50)
        
        print(f"⏱️  Duração real: {actual_duration:.2f} segundos")
        print(f"📈 Total de requisições: {total_requests}")
        print(f"✅ Requisições bem-sucedidas: {successful_requests}")
        print(f"❌ Requisições falharam: {failed_requests}")
        print(f"📊 Taxa de sucesso: {(successful_requests/total_requests)*100:.2f}%")
        print(f"🚀 Requisições por segundo: {requests_per_second:.2f}")
        
        print(f"\n⏱️  TEMPOS DE RESPOSTA:")
        print(f"   Média: {avg_response_time:.3f}s")
        print(f"   Mediana: {median_response_time:.3f}s")
        print(f"   Mínimo: {min_response_time:.3f}s")
        print(f"   Máximo: {max_response_time:.3f}s")
        print(f"   95º percentil: {p95_response_time:.3f}s")
        
        # Análise por endpoint
        print(f"\n📋 ANÁLISE POR ENDPOINT:")
        endpoint_stats = {}
        for result in self.results:
            endpoint = result['endpoint']
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {'total': 0, 'success': 0, 'times': []}
            
            endpoint_stats[endpoint]['total'] += 1
            if result['success']:
                endpoint_stats[endpoint]['success'] += 1
                endpoint_stats[endpoint]['times'].append(result['response_time'])
        
        for endpoint, stats in endpoint_stats.items():
            success_rate = (stats['success'] / stats['total']) * 100
            avg_time = statistics.mean(stats['times']) if stats['times'] else 0
            print(f"   {endpoint}: {stats['total']} reqs, {success_rate:.1f}% sucesso, {avg_time:.3f}s média")
        
        # Salvar resultados em arquivo
        self.save_results()
    
    def save_results(self):
        """Salva os resultados em arquivo JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"load_test_results_{timestamp}.json"
        
        results_data = {
            'test_config': {
                'base_url': self.base_url,
                'concurrent_users': self.concurrent_users,
                'duration': self.duration
            },
            'test_results': {
                'start_time': self.start_time,
                'end_time': self.end_time,
                'total_requests': len(self.results),
                'successful_requests': sum(1 for r in self.results if r['success']),
                'failed_requests': sum(1 for r in self.results if not r['success'])
            },
            'detailed_results': self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n💾 Resultados salvos em: {filename}")

async def main():
    parser = argparse.ArgumentParser(description='Teste de carga para Assistente RH')
    parser.add_argument('--url', default='http://localhost:5000', help='URL base da aplicação')
    parser.add_argument('--users', type=int, default=10, help='Número de usuários concorrentes')
    parser.add_argument('--duration', type=int, default=60, help='Duração do teste em segundos')
    
    args = parser.parse_args()
    
    tester = LoadTester(args.url, args.users, args.duration)
    await tester.run_test()

if __name__ == "__main__":
    asyncio.run(main())
