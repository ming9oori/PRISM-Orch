"""
vLLM 서버 모니터링 스크립트
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime


async def monitor_server(base_url: str = "http://localhost:8000"):
    """서버 모니터링"""
    print("🔍 vLLM Server Monitoring Started...")
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # 헬스체크
                async with session.get(f"{base_url}/health") as response:
                    health_data = await response.json()
                
                # 통계 조회
                async with session.get(f"{base_url}/api/v1/stats") as response:
                    stats_data = await response.json()
                
                # 현재 시간
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 모니터링 정보 출력
                print(f"\n[{now}] Server Status:")
                print(f"  🟢 Status: {health_data['status']}")
                print(f"  💾 RAM Usage: {health_data['memory_usage']['ram_percent']:.1f}%")
                print(f"  🔥 GPU Count: {health_data['gpu_count']}")
                print(f"  📊 Active Requests: {health_data['active_requests']}")
                print(f"  📈 Total Requests: {health_data['total_requests']}")
                print(f"  ⚡ Throughput: {health_data['throughput']:.2f} tokens/sec")
                print(f"  ⏰ Uptime: {health_data['uptime']:.0f}s")
                
                if 'performance' in stats_data:
                    perf = stats_data['performance']
                    print(f"  🎯 Avg Tokens/Request: {perf['average_tokens_per_request']:.1f}")
                    print(f"  📊 Total Tokens: {perf['total_tokens_generated']}")
                
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
            
            await asyncio.sleep(10)  # 10초마다 모니터링


if __name__ == "__main__":
    asyncio.run(monitor_server()) 