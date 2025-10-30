🧩 Cognitive Graph Design Specification (V3.9 Draft 1)
1️⃣ Purpose – 设计目的

Cognitive Graph (CG) 是 HALO Phase 3.9 的核心语义结构，
负责统一管理 意图 (Intent)、工具 (Tool)、实体 (Entity) 与 记忆 (Memory) 的关系，
为系统提供具备“上下文理解与连续推理能力”的数据底座。

它连接以下模块：

Intent Layer  →  Cognitive Graph  →  Memory Manager  →  Core Dispatcher

2️⃣ Design Philosophy – 设计理念

图谱式认知模型：以节点 (Node) + 关系 (Edge) 形式表达语义。

轻量级内存融合：短期记忆存于内存，长期记忆可序列化为 JSON。

可自增长结构：每次交互后自动扩展图谱（增量式学习）。

可溯源推理：支持从任意意图反查关联的工具与上下文。

3️⃣ Conceptual Diagram
          ┌─────────────┐
          │ User Input  │
          └──────┬──────┘
                 │
          ┌──────▼──────┐
          │ Intent Node │────────┐
          └──────┬──────┘        │
                 │                │
     ┌───────────┴──────────────┐ │
     │  uses_tool  (Edge)       │ │
     └───────────┬──────────────┘ │
                 │                │
          ┌──────▼──────┐   ┌────▼────┐
          │ Tool Node   │   │ Entity  │
          └─────────────┘   └─────────┘
                 │                │
         ┌───────┴────────────┐   │
         │ stored_in (Memory) │<──┘
         └────────────────────┘

4️⃣ Node Types & Schemas
4.1 Intent Node

代表一次可执行任务的抽象。

{
  "type": "Intent",
  "id": "intent_search_files_001",
  "label": "search_files",
  "confidence": 0.92,
  "timestamp": "2025-10-29T17:27:45Z"
}

4.2 Tool Node

映射注册于 ToolRegistry 的函数或插件。

{
  "type": "Tool",
  "id": "tool_search_files",
  "module": "everything_plugin",
  "entry": "search_files"
}

4.3 Entity Node

代表用户输入中提及的对象（如文件、时间、路径）。

{
  "type": "Entity",
  "id": "entity_report_txt",
  "value": "report.txt",
  "category": "file"
}

4.4 Memory Node

记录意图-结果-上下文的持久快照。

{
  "type": "Memory",
  "id": "memory_20251029_001",
  "context": "user searched for report.txt",
  "result": "3 files found"
}

5️⃣ Edge Types & Semantics
边类型	说明	方向
uses_tool	意图调用工具	Intent → Tool
targets_entity	意图作用于实体	Intent → Entity
produces_memory	意图执行结果生成记忆	Intent → Memory
relates_to	意图间语义关联	Intent ↔ Intent
enhances_tool	工具经由学习优化	Memory → Tool
context_of	记忆关联上下文	Memory ↔ Entity
6️⃣ Graph Storage & Lifecycle
6.1 In-Memory Representation
{
  "nodes": [...],
  "edges": [...],
  "version": "V3.9",
  "session": "halo-20251029"
}

6.2 Persistence Policy

短期 (active session)：驻留内存。

中期 (task context)：写入 halo_state.json。

长期 (learning archive)：定期保存至 /data/cognitive_graph/。

6.3 Update Flow
Intent Executed
      ↓
Graph.add_node(Intent)
Graph.link_to(Tool, Entity)
Graph.create_memory_snapshot()
Graph.persist_if_needed()

7️⃣ API Design
函数	作用	示例返回
add_node(node: dict)	添加节点	node_id
add_edge(src, dst, relation)	连接两个节点	None
query_intent_graph(intent_id)	获取该意图的所有关联节点	dict
export_graph_json()	导出当前图谱	JSON string
summarize_recent_activity(n)	最近 n 次交互摘要	list of Memory
8️⃣ Integration Map
上游模块	下游模块	数据流
IntentLayer	CognitiveGraph	Intent Object → Node + Edge
CognitiveGraph	MemoryManager	Memory Node → ShortTerm Memory
CognitiveGraph	CoreDispatcher	推理链查询
CoreDispatcher	CognitiveGraph	执行结果反写 (Feedback)
9️⃣ Decision Matrix – Graph Expansion Rules
触发条件	动作
新意图首次出现	创建 Intent Node + uses_tool Edge
相同意图重复出现	更新置信度 (平均 + 衰减)
工具执行成功	添加 Memory Node + produces_memory Edge
执行失败	创建 Error Entity Node + context_of Edge
用户显式纠正	记录 Correction Edge (反馈学习)
🔟 Future Expansion (Phase 4 Preview)

Graph Embedding Model – 将整个图谱编码为向量，用于快速语义检索。

Cross-Session Merging – 不同会话间图谱合并与权重学习。

Causal Reasoning Engine (V4.1) – 在图谱上执行因果链推理。

GraphQL 接口层 – 对外提供 HALO Cognitive API 访问图谱。

🧾 Version Metadata
字段	值
Spec Version	V3.9 Draft 1
Compatible Modules	Intent Layer V3.9 / Memory Manager V3.8+
Author	HALO Cognitive Team
Status	📘 Design Approved – Prototype Pending