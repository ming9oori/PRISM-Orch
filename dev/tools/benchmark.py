#!/usr/bin/env python3
"""
vLLM 서버 성능 벤치마크 스크립트
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict


class VLLMBenchmark:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    async def single_request(self, session: aiohttp.ClientSession, request_data: dict) -> Dict:
        """단일 요청 실행"""
        start_time = time.time()
        
        try:
            async with session.post(
                f"{self.base_url}/api/v1/generate",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                result = await response.json()
                end_time = time.time()
                
                return {
                    "success": True,
                    "response_time": end_time - start_time,
                    "tokens_generated": result.get("tokens_generated", 0),
                    "status_code": response.status
                }
        except Exception as e:
            return {
                "success": False,
                "response_time": time.time() - start_time,
                "error": str(e),
                "tokens_generated": 0
            }
    
    async def concurrent_benchmark(self, concurrency: int, total_requests: int):
        """동시성 벤치마크"""
        print(f"\n🚀 Running benchmark: {total_requests} requests with {concurrency} concurrency")
        
        # 테스트 요청 데이터
        request_data = {
            "agent_type": "monitoring",
            "prompt": "제조 라인에서 온도 이상이 감지되었습니다. 현재 온도는 195도이고 정상 범위는 150-200도입니다. 상황을 분석하고 권장 조치를 제공해주세요.",
            "max_tokens": 256,
            "temperature": 0.1
        }
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            # 동시 요청 실행
            semaphore = asyncio.Semaphore(concurrency)
            
            async def limited_request():
                async with semaphore:
                    return await self.single_request(session, request_data)
            
            tasks = [limited_request() for _ in range(total_requests)]
            results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 결과 분석
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            tokens_generated = [r["tokens_generated"] for r in successful_requests]
            total_tokens = sum(tokens_generated)
            
            print(f"📊 Results:")
            print(f"  ✅ Successful requests: {len(successful_requests)}/{total_requests}")
            print(f"  ❌ Failed requests: {len(failed_requests)}")
            print(f"  🕐 Total time: {total_time:.2f}s")
            print(f"  📈 Requests/sec: {len(successful_requests)/total_time:.2f}")
            print(f"  🎯 Tokens/sec: {total_tokens/total_time:.2f}")
            print(f"  ⏱️  Response time - Avg: {statistics.mean(response_times):.2f}s")
            print(f"  ⏱️  Response time - P50: {statistics.median(response_times):.2f}s")
            print(f"  ⏱️  Response time - P95: {sorted(response_times)[int(len(response_times)*0.95)]:.2f}s")
            print(f"  ⏱️  Response time - P99: {sorted(response_times)[int(len(response_times)*0.99)]:.2f}s")
            
            # 결과 저장
            self.results.append({
                "concurrency": concurrency,
                "total_requests": total_requests,
                "successful_requests": len(successful_requests),
                "requests_per_sec": len(successful_requests)/total_time,
                "tokens_per_sec": total_tokens/total_time,
                "avg_response_time": statistics.mean(response_times),
                "p95_response_time": sorted(response_times)[int(len(response_times)*0.95)],
                "total_time": total_time
            })
    
    async def run_full_benchmark(self):
        """전체 벤치마크 실행"""
        print("🎯 vLLM Performance Benchmark Starting...")
        
        # 다양한 동시성 레벨 테스트
        test_scenarios = [
            (1, 10),    # 1 concurrent, 10 requests
            (5, 50),    # 5 concurrent, 50 requests  
            (10, 100),  # 10 concurrent, 100 requests
            (20, 200),  # 20 concurrent, 200 requests
            (50, 500),  # 50 concurrent, 500 requests
        ]
        
        for concurrency, requests in test_scenarios:
            await self.concurrent_benchmark(concurrency, requests)
            await asyncio.sleep(2)  # 서버 휴식 시간
        
        # 결과 요약
        print("\n📈 Benchmark Summary:")
        print("Concurrency | Requests | RPS   | Tokens/s | Avg RT | P95 RT")
        print("-" * 60)
        for result in self.results:
            print(f"{result['concurrency']:10d} | {result['total_requests']:8d} | "
                  f"{result['requests_per_sec']:5.1f} | {result['tokens_per_sec']:8.1f} | "
                  f"{result['avg_response_time']:6.2f} | {result['p95_response_time']:6.2f}")
        
        # JSON 결과 저장
        with open("benchmark_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Results saved to benchmark_results.json")


if __name__ == "__main__":
    benchmark = VLLMBenchmark()
    asyncio.run(benchmark.run_full_benchmark()) 