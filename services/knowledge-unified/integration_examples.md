# 集成示例：各种专利应用使用通用智能后端

本文档展示如何将统一知识图谱服务集成到各种专利应用中。

## 1. 专利审查系统

### Python集成

```python
from services.knowledge_unified.client_sdk import create_client

# 创建客户端
kg_client = create_client()

class PatentReviewSystem:
    def __init__(self):
        self.kg_client = create_client()

    def review_patent(self, patent_data):
        """专利审查主流程"""
        # 1. 基础信息提取
        basic_info = self._extract_basic_info(patent_data)

        # 2. 调用知识图谱服务
        response = self.kg_client.query_knowledge(
            query=f"审查专利的新颖性、创造性和实用性",
            patent_text=patent_data['description'],
            context_type="patent_review",
            context={
                "application_number": patent_data['app_no'],
                "ipc_classification": patent_data['ipc']
            },
            application_id="patent_review_system"
        )

        # 3. 生成审查意见
        review_opinion = self._generate_review_opinion(response, basic_info)

        return review_opinion

    def check_novelty(self, patent_text):
        """新颖性专项检查"""
        # 提取新颖性相关规则
        rules = self.kg_client.extract_rules(
            patent_text=patent_text,
            rule_types=["novelty"],
            keywords=["现有技术", "申请日", "公开"]
        )

        # 分析新颖性
        novelty_analysis = self._analyze_novelty(patent_text, rules)

        return novelty_analysis
```

### JavaScript/Node.js集成

```javascript
// 使用fetch API调用
class PatentReviewService {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    async reviewPatent(patentData) {
        const response = await fetch(`${this.baseUrl}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: '评估专利的可专利性',
                patent_text: patentData.description,
                context_type: 'patent_review',
                context: {
                    application_number: patentData.appNo
                },
                application_id: 'web_review_system'
            })
        });

        const result = await response.json();
        return this.generateReviewOpinion(result);
    }

    async extractRules(patentText) {
        const response = await fetch(`${this.baseUrl}/rules/extract`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                patent_text: patentText,
                rule_types: ['novelty', 'creativity', 'procedure']
            })
        });

        return await response.json();
    }
}
```

## 2. 法律咨询系统

### 集成示例

```python
class LegalConsultationSystem:
    def __init__(self):
        self.kg_client = create_client()

    def assess_infringement_risk(self, product_tech, patent_claims):
        """侵权风险评估"""
        response = self.kg_client.query_knowledge(
            query="评估产品技术是否侵犯专利权",
            patent_text=f"产品技术：{product_tech}\n专利权利要求：{patent_claims}",
            context_type="legal_advice",
            context={
                "analysis_type": "infringement",
                "jurisdiction": "CN"
            }
        )

        # 提取法律依据
        legal_rules = response['prompts']['legal_basis']

        # 生成风险评估报告
        risk_report = {
            "risk_level": self._assess_risk_level(response),
            "legal_basis": legal_rules,
            "recommendations": self._generate_recommendations(response)
        }

        return risk_report

    def get_legal_advice(self, case_description):
        """获取法律建议"""
        response = self.kg_client.query_knowledge(
            query=f"针对以下情况提供法律建议：{case_description}",
            context_type="legal_advice",
            context={
                "case_type": self._classify_case(case_description)
            }
        )

        return response
```

## 3. 专利分析平台

### 批量分析示例

```python
class PatentAnalysisPlatform:
    def __init__(self):
        self.kg_client = create_client()

    def batch_analyze_patents(self, patent_list):
        """批量分析专利"""
        # 准备批量查询
        queries = []
        for i, patent in enumerate(patent_list):
            queries.append({
                "query": f"分析第{i+1}个专利的技术创新性",
                "patent_text": patent['title'] + '\n' + patent['abstract'],
                "context_type": "technical_analysis",
                "user_id": patent['id']
            })

        # 执行批量查询
        batch_result = self.kg_client.batch_query(
            queries=queries,
            max_parallel=10
        )

        # 处理结果
        analysis_results = []
        for result in batch_result['results']:
            analysis = self._process_analysis_result(result)
            analysis_results.append(analysis)

        return analysis_results

    def similarity_analysis(self, target_patent, comparison_patents):
        """相似性分析"""
        # 使用向量搜索
        search_results = self.kg_client.similarity_search(
            text=target_patent['abstract'],
            similarity_threshold=0.8,
            max_results=20
        )

        # 分析相似度
        similarity_report = {
            "target_patent": target_patent,
            "similar_patents": search_results['results'],
            "similarity_summary": self._summarize_similarity(search_results)
        }

        return similarity_report
```

## 4. 专利申请辅助工具

### Web前端集成

```javascript
// Vue.js组件示例
<template>
  <div class="patent-filing-assistant">
    <div class="input-section">
      <textarea v-model="patentText" placeholder="输入专利技术方案..."></textarea>
      <button @click="generateGuidance">生成申请指导</button>
    </div>

    <div class="guidance-section" v-if="guidance">
      <h3>申请指导</h3>
      <div v-html="guidance.system_role"></div>
      <div class="recommendations">
        <h4>建议操作</h4>
        <ul>
          <li v-for="action in guidance.suggested_actions" :key="action.action">
            {{ action.label }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { PatentFilingService } from '@/services/patent-filing';

export default {
  name: 'PatentFilingAssistant',
  data() {
    return {
      patentText: '',
      guidance: null,
      filingService: new PatentFilingService()
    };
  },
  methods: {
    async generateGuidance() {
      try {
        const response = await this.filingService.getFilingGuidance({
          patent_text: this.patentText,
          query: "如何准备专利申请文件"
        });

        this.guidance = response.prompts;
      } catch (error) {
        console.error('获取指导失败:', error);
        this.$message.error('获取申请指导失败');
      }
    }
  }
};
</script>
```

## 5. 移动端应用

### Flutter集成

```dart
// patent_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class PatentService {
  final String baseUrl = 'http://localhost:8000';

  Future<Map<String, dynamic>> queryPatentKnowledge({
    required String query,
    String patentText = '',
    String contextType = 'general',
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/query'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'query': query,
        'patent_text': patentText,
        'context_type': contextType,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to query patent knowledge');
    }
  }

  Future<Map<String, dynamic>> extractRules({
    required String patentText,
    List<String> ruleTypes = const ['novelty', 'creativity'],
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/rules/extract'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'patent_text': patentText,
        'rule_types': ruleTypes,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to extract rules');
    }
  }
}
```

## 6. 部署配置

### Docker部署

```bash
# 克隆服务代码
git clone <repository>
cd patent-knowledge-unified

# 使用Docker Compose部署
docker-compose up -d

# 验证服务
curl http://localhost:8000/health
```

### Kubernetes部署

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: patent-kg-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: patent-kg-api
  template:
    metadata:
      labels:
        app: patent-kg-api
    spec:
      containers:
      - name: api
        image: patent-kg-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: patent-kg-service
spec:
  selector:
    app: patent-kg-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 7. 监控和日志

### 监控指标

```python
# 监控客户端
class ServiceMonitor:
    def __init__(self):
        self.client = create_client()

    def collect_metrics(self):
        """收集服务指标"""
        stats = self.client.get_statistics()

        metrics = {
            "total_queries": stats['service_statistics']['total_queries'],
            "knowledge_hits": stats['service_statistics']['knowledge_hits'],
            "service_health": stats['service_statistics']['status'],
            "timestamp": datetime.now().isoformat()
        }

        # 发送到监控系统
        self.send_to_monitoring_system(metrics)

        return metrics
```

## 8. 错误处理和重试

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class RobustPatentClient:
    def __init__(self):
        self.client = create_client()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def query_with_retry(self, query, patent_text=""):
        """带重试的查询"""
        try:
            return self.client.query_knowledge(
                query=query,
                patent_text=patent_text
            )
        except Exception as e:
            logger.error(f"Query failed after retries: {e}")
            raise
```

## 9. 缓存策略

```python
from functools import lru_cache
import hashlib

class CachedPatentClient:
    def __init__(self, cache_size=1000):
        self.client = create_client()
        self.cache_size = cache_size

    @lru_cache(maxsize=1000)
    def cached_query(self, query, patent_text=""):
        """带缓存的查询"""
        # 生成缓存键
        cache_key = hashlib.md5(f"{query}{patent_text}".encode()).hexdigest()

        # 实际查询
        return self.client.query_knowledge(
            query=query,
            patent_text=patent_text
        )
```

## 10. 安全考虑

```python
class SecurePatentClient:
    def __init__(self, api_key, base_url):
        self.client = create_client(
            base_url=base_url,
            api_key=api_key
        )

    def secure_query(self, query, patent_text="", user_context=None):
        """安全查询"""
        # 验证输入
        if not self._validate_input(query, patent_text):
            raise ValueError("Invalid input")

        # 添加用户上下文
        context = {
            "user_authenticated": True,
            "timestamp": datetime.now().isoformat(),
            "input_hash": hashlib.sha256(
                f"{query}{patent_text}".encode()
            ).hexdigest()
        }

        if user_context:
            context.update(user_context)

        return self.client.query_knowledge(
            query=query,
            patent_text=patent_text,
            context=context
        )
```

## 总结

通过这些集成示例，各种专利应用可以：

1. **快速集成** - 使用SDK几行代码即可接入
2. **灵活调用** - 支持同步、异步、批量等多种调用方式
3. **智能响应** - 获得基于知识图谱的专业提示词
4. **稳定可靠** - 内置重试、缓存、错误处理机制

选择适合您技术栈的集成方式，快速为您的专利应用添加智能知识支持！