#!/usr/bin/env python3
"""
Vector Search Web Interface

Weaviate 벡터 DB에서 대화형 검색을 수행할 수 있는 웹 인터페이스
"""

import os
import json
import requests
from flask import Flask, request, jsonify, render_template_string
from typing import Dict, List, Any

app = Flask(__name__)

# 환경 설정
WEAVIATE_URL = os.getenv('WEAVIATE_URL', 'http://weaviate:8080')
CLASS_PREFIX = os.getenv('CLASS_PREFIX', 'KOSHA')

# 사용 가능한 클래스 매핑
CLASS_MAPPING = {
    "history": f"{CLASS_PREFIX}History",
    "compliance": f"{CLASS_PREFIX}Compliance", 
    "research": f"{CLASS_PREFIX}Research"
}

def search_weaviate(domain: str, query: str, top_k: int = 5) -> Dict[str, Any]:
    """Weaviate에서 벡터 검색 수행"""
    class_name = CLASS_MAPPING.get(domain)
    if not class_name:
        return {"success": False, "error": f"Unknown domain: {domain}"}
    
    # GraphQL query for nearText search
    graphql_query = {
        "query": f'''
        {{
            Get {{
                {class_name}(
                    nearText: {{
                        concepts: ["{query}"]
                    }}
                    limit: {top_k}
                ) {{
                    title
                    content
                    metadata
                    _additional {{
                        id
                        certainty
                        distance
                        vector
                    }}
                }}
            }}
        }}
        '''
    }
    
    try:
        response = requests.post(
            f"{WEAVIATE_URL}/v1/graphql",
            json=graphql_query,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                return {"success": False, "error": f"GraphQL errors: {data['errors']}"}
            
            results = data.get("data", {}).get("Get", {}).get(class_name, [])
            
            # 결과 후처리
            processed_results = []
            for idx, result in enumerate(results, 1):
                additional = result.get("_additional", {})
                title = result.get('title', 'N/A')
                content = result.get('content', '')
                metadata_raw = result.get('metadata', '{}')
                
                # Parse metadata
                try:
                    metadata = json.loads(metadata_raw) if isinstance(metadata_raw, str) else metadata_raw
                except:
                    metadata = {}
                
                processed_results.append({
                    "rank": idx,
                    "id": additional.get("id", ""),
                    "title": title,
                    "certainty": additional.get("certainty", 0),
                    "distance": additional.get("distance", 1),
                    "has_vector": additional.get("vector") is not None,
                    "content": content,
                    "content_preview": content[:300] + "..." if len(content) > 300 else content,
                    "metadata": metadata
                })
            
            return {"success": True, "results": processed_results}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}

@app.route('/')
def index():
    """메인 페이지"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/search', methods=['POST'])
def search():
    """검색 API 엔드포인트"""
    data = request.json
    query = data.get('query', '').strip()
    domain = data.get('domain', 'history')
    top_k = data.get('top_k', 5)
    
    if not query:
        return jsonify({"success": False, "error": "Query is required"})
    
    if domain not in CLASS_MAPPING:
        return jsonify({"success": False, "error": f"Invalid domain. Available: {list(CLASS_MAPPING.keys())}"})
    
    result = search_weaviate(domain, query, top_k)
    return jsonify(result)

@app.route('/health')
def health():
    """헬스 체크"""
    return jsonify({"status": "healthy", "weaviate_url": WEAVIATE_URL})

# HTML 템플릿
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vector Search Interface</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .search-section {
            padding: 40px;
            background: #f8f9ff;
        }
        
        .search-form {
            display: grid;
            grid-template-columns: 1fr 150px 100px 120px;
            gap: 15px;
            margin-bottom: 30px;
            align-items: end;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
        }
        
        .form-group label {
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        
        .form-group input,
        .form-group select {
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }
        
        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: #4facfe;
            box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.1);
        }
        
        .search-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .search-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .search-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .results-section {
            padding: 0 40px 40px;
        }
        
        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e1e5e9;
        }
        
        .results-count {
            font-size: 1.2rem;
            font-weight: 600;
            color: #667eea;
        }
        
        .result-item {
            background: white;
            border: 1px solid #e1e5e9;
            border-radius: 12px;
            margin-bottom: 20px;
            overflow: hidden;
            transition: box-shadow 0.3s ease;
        }
        
        .result-item:hover {
            box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        }
        
        .result-header {
            background: linear-gradient(135deg, #f8f9ff 0%, #e8f2ff 100%);
            padding: 20px;
            border-bottom: 1px solid #e1e5e9;
        }
        
        .result-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
            line-height: 1.4;
        }
        
        .result-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        
        .metric {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
        }
        
        .metric-label {
            font-weight: 600;
            color: #666;
        }
        
        .metric-value {
            padding: 4px 8px;
            border-radius: 6px;
            font-weight: 600;
        }
        
        .certainty-high { background: #d4edda; color: #155724; }
        .certainty-medium { background: #fff3cd; color: #856404; }
        .certainty-low { background: #f8d7da; color: #721c24; }
        
        .result-content {
            padding: 20px;
        }
        
        .content-preview {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            white-space: pre-wrap;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9rem;
            line-height: 1.5;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .metadata {
            background: #f1f3f4;
            padding: 15px;
            border-radius: 8px;
            font-size: 0.85rem;
        }
        
        .metadata-item {
            margin-bottom: 5px;
        }
        
        .metadata-key {
            font-weight: 600;
            color: #495057;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #667eea;
            font-size: 1.1rem;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border: 1px solid #f5c6cb;
        }
        
        .no-results {
            text-align: center;
            padding: 40px;
            color: #6c757d;
            font-size: 1.1rem;
        }
        
        .vector-status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .vector-yes {
            background: #d4edda;
            color: #155724;
        }
        
        .vector-no {
            background: #f8d7da;
            color: #721c24;
        }
        
        @media (max-width: 768px) {
            .search-form {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .search-section,
            .results-section {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Vector Search Interface</h1>
            <p>Weaviate 벡터 DB에서 의미적 검색을 수행합니다</p>
        </div>
        
        <div class="search-section">
            <div class="search-form">
                <div class="form-group">
                    <label for="query">검색 쿼리</label>
                    <input type="text" id="query" placeholder="예: 압력 이상 문제, 안전 규정..." />
                </div>
                <div class="form-group">
                    <label for="domain">도메인</label>
                    <select id="domain">
                        <option value="history">History</option>
                        <option value="compliance">Compliance</option>
                        <option value="research">Research</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="top_k">결과 수</label>
                    <select id="top_k">
                        <option value="3">3개</option>
                        <option value="5" selected>5개</option>
                        <option value="10">10개</option>
                    </select>
                </div>
                <div class="form-group">
                    <button class="search-btn" onclick="performSearch()" id="searchBtn">검색</button>
                </div>
            </div>
        </div>
        
        <div class="results-section" id="resultsSection" style="display: none;">
            <div class="results-header">
                <div class="results-count" id="resultsCount">검색 결과</div>
            </div>
            <div id="resultsContainer"></div>
        </div>
    </div>

    <script>
        async function performSearch() {
            const query = document.getElementById('query').value.trim();
            const domain = document.getElementById('domain').value;
            const top_k = parseInt(document.getElementById('top_k').value);
            const searchBtn = document.getElementById('searchBtn');
            const resultsSection = document.getElementById('resultsSection');
            const resultsContainer = document.getElementById('resultsContainer');
            const resultsCount = document.getElementById('resultsCount');
            
            if (!query) {
                alert('검색어를 입력해주세요.');
                return;
            }
            
            // 로딩 상태
            searchBtn.textContent = '검색 중...';
            searchBtn.disabled = true;
            resultsSection.style.display = 'block';
            resultsContainer.innerHTML = '<div class="loading">🔍 검색 중...</div>';
            
            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query, domain, top_k })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    displayResults(data.results, query, domain);
                } else {
                    resultsContainer.innerHTML = `<div class="error">❌ 오류: ${data.error}</div>`;
                }
            } catch (error) {
                resultsContainer.innerHTML = `<div class="error">❌ 요청 실패: ${error.message}</div>`;
            } finally {
                searchBtn.textContent = '검색';
                searchBtn.disabled = false;
            }
        }
        
        function displayResults(results, query, domain) {
            const resultsContainer = document.getElementById('resultsContainer');
            const resultsCount = document.getElementById('resultsCount');
            
            if (results.length === 0) {
                resultsContainer.innerHTML = '<div class="no-results">📝 검색 결과가 없습니다.</div>';
                resultsCount.textContent = '검색 결과 없음';
                return;
            }
            
            resultsCount.textContent = `"${query}" (${domain}) - ${results.length}개 결과`;
            
            const resultsHTML = results.map(result => {
                const certaintyClass = result.certainty > 0.8 ? 'certainty-high' : 
                                    result.certainty > 0.6 ? 'certainty-medium' : 'certainty-low';
                
                const metadataItems = Object.entries(result.metadata).map(([key, value]) => 
                    `<div class="metadata-item"><span class="metadata-key">${key}:</span> ${value}</div>`
                ).join('');
                
                return `
                    <div class="result-item">
                        <div class="result-header">
                            <div class="result-title">[${result.rank}] ${result.title}</div>
                            <div class="result-metrics">
                                <div class="metric">
                                    <span class="metric-label">Certainty:</span>
                                    <span class="metric-value ${certaintyClass}">${result.certainty.toFixed(4)}</span>
                                </div>
                                <div class="metric">
                                    <span class="metric-label">Distance:</span>
                                    <span class="metric-value">${result.distance.toFixed(4)}</span>
                                </div>
                                <div class="metric">
                                    <span class="metric-label">Vector:</span>
                                    <span class="vector-status ${result.has_vector ? 'vector-yes' : 'vector-no'}">
                                        ${result.has_vector ? '✅ Yes' : '❌ No'}
                                    </span>
                                </div>
                                <div class="metric">
                                    <span class="metric-label">ID:</span>
                                    <span class="metric-value">${result.id.substring(0, 8)}...</span>
                                </div>
                            </div>
                        </div>
                        <div class="result-content">
                            <div class="content-preview">${result.content_preview}</div>
                            ${metadataItems ? `<div class="metadata">${metadataItems}</div>` : ''}
                        </div>
                    </div>
                `;
            }).join('');
            
            resultsContainer.innerHTML = resultsHTML;
        }
        
        // Enter 키로 검색
        document.getElementById('query').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8200, debug=True)