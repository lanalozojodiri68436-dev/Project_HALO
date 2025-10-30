A3 — Dispatcher Integration Plan (Phase 3.9)

版本：V3.9 Draft 1
适配对象：core_dispatcher.py (V3.8) + Intent Layer (A1) + Cognitive Graph (A2)

1. 目标（一段话）

把现有 core_dispatcher.py (V3.8) 无缝升级为 认知驱动的调度中心：在接收用户输入时优先调用 IntentLayer.analyze_intent() 得到标准化 intent metadata；基于 route 决策（direct / llm）选择执行路径；无论是直接执行 (direct) 还是 LLM-driven Tool Use (llm)，都在执行前后将意图/工具/实体/结果按标准节点/边写入 CognitiveGraph；提供可回退的错误处理与事务语义，保证系统稳定性与审计可追踪性。

2. 总体流程（一句话版）

User input → IntentLayer.analyze_intent() → IntentRouter decision → CoreDispatcher 执行（direct 或 llm_tool_use）→ ToolResult → CognitiveGraph.add_node/add_edge（回写）→ StateManager persist → 返回用户/UI。

3. 需要修改的文件与位置（概要）

src/main_app/core_dispatcher.py

在入口处替换现有意图判断逻辑，改为调用 IntentLayer.analyze_intent()（非本地字符串规则）。

将现有的 direct_tool_execute 和 process_with_llm_tool_use 两条路径规范为子方法，并在它们执行前后增加 CognitiveGraph 回写步骤与统一的事务/日志钩子。

添加 dispatch_context（临时对象）用于在一次交互中携带 intent、route、tool_call、tool_result、graph_nodes_created 等数据，以便出错时回滚/审计。

新增/修改点（位于 src/main_app/）：

intent_layer 模块 — 已实现（A1），接口 analyze_intent(user_input, context) -> IntentMeta（见接口契约）。

cognitive_graph 模块 — 已实现 (A2)，接口 add_node(node_dict), add_edge(src_id, dst_id, relation, metadata)。

state_manager — 在 dispatch 末尾持久化 dispatch_context 的快照（审计/回溯用）。

4. 接口契约（关键，文字版）
4.1 IntentLayer (已实现，A1) — 输入 / 输出

调用函数（契约）

IntentMeta = IntentLayer.analyze_intent(user_input: str, context: dict)

IntentMeta（返回结构，必须支持）:

{
  "intent": "search_files" | "read_file_lines" | "get_time" | "chat" | "unknown",
  "confidence": float,                 # 0.0 - 1.0
  "route": "direct" | "llm" | "llm_fallback",
  "complexity": "low"|"medium"|"high",
  "suggested_subtasks": [ ... ],      # optional high-level plan fragments
  "raw_text": "<original input>"
}


约定：IntentLayer 不返回具体工具参数（V3.9 设计决策），除非 intent 是 get_time 或其他 trivial direct action（这些可含 minimal params）。复杂参数由 LLM 在 llm 路径中生成。

4.2 CognitiveGraph（已实现，A2）— 写入契约

函数

node_id = CognitiveGraph.add_node(node_dict)
node_dict 包含 type（Intent/Tool/Entity/Memory）、label、meta 等。

edge_id = CognitiveGraph.add_edge(src_node_id, dst_node_id, relation, meta)

写入约定

在 执行前：写入 Intent Node（type=Intent）并记录返回的 intent_node_id；

在 执行时：若执行工具，写入/确认 Tool Node（type=Tool），并建立 uses_tool 边： intent_node -> uses_tool -> tool_node；

在 执行后：写入 Memory Node（type=Memory，内容为 tool_result 摘要），并建立 produces_memory 边： intent_node -> produces_memory -> memory_node。另外若出现实体（比如文件路径），写入 Entity Node 并建立 targets_entity 边。

5. CoreDispatcher 修改详述（步骤 + 规范化行为）

下面以调用流程的阶段划分说明 core_dispatcher._handle_user_input() 应如何改造（仅描述，不写代码）。

5.1 入口：接收 & 建立 dispatch_context

新增 dispatch_context（内存对象）字段范例：

dispatch_context = {
  "session_id": "<session>",
  "user_input": "<text>",
  "timestamp": "<ISO>",
  "intent_meta": None,
  "intent_node_id": None,
  "tool_node_id": None,
  "entity_node_ids": [],
  "tool_call": None,
  "tool_result": None,
  "graph_nodes_created": []
}


目的：统一传递并供审计/回滚使用。

5.2 步骤 A — 调用 IntentLayer

调用：intent_meta = IntentLayer.analyze_intent(user_input, context)

将 intent_meta 写入 dispatch_context.intent_meta。

写入 CognitiveGraph：创建 Intent Node：

intent_node = {"type":"Intent","label":intent_meta["intent"], "meta": {"confidence":..., "raw_text": ...}}

intent_node_id = CognitiveGraph.add_node(intent_node)

dispatch_context.intent_node_id = intent_node_id

5.3 步骤 B — 路由决策

根据 intent_meta["route"] 决定：

direct → 转 direct_tool_execute（但只允许在 intent_meta["complexity"] == "low" 或明确白名单的工具如 get_time）

llm / llm_fallback → 转 process_with_llm_tool_use（使用 existing V3.6 LLM tool use flow）

记录 dispatch_context["route"] = chosen_route。

5.4 步骤 C — direct_tool_execute（若被选中）

前置：确认 intent_meta 的 intent 属于 direct 可接受列表；否则改回 llm。

写入：确保 Tool Node 已存在或创建并建立 uses_tool 边（Intent → uses_tool → Tool）。

执行：调用本地 plugin 的 execute(params)；注意：因为 IntentLayer 不提供 params，direct path 只适用于不需参数或 minimal parameters actions（e.g., get_time）。

后置：

将执行结果摘要写入 Memory Node，并建立 produces_memory 边。

若执行产出实体（如路径），写入 Entity Node，并建立 targets_entity 边。

将 tool_result 存入 dispatch_context，并 StateManager.persist(dispatch_context)。

5.5 步骤 D — process_with_llm_tool_use（主路径）

构建 LLM 请求：把 user_input, intent_meta, 当前 Tool Schema（从 ToolRegistry）和近期记忆摘要（由 StateManager 提供）打包为 LLM 请求。注：必须包含 tool schema，以便 LLM 可能返回 function_call/tool_call。

调用 LLM（现用 GenAI 的 generate_content flow 已在 V3.6 中被调通）：

第一次请求：LLM 决定是否要 tool_call 或直接回应文本。

若 LLM 返回 tool_call：解析 tool_call（工具名 + args），写入 dispatch_context.tool_call 并在 CognitiveGraph 中创建/确认 Tool Node 与 uses_tool 边；接着由 ToolExecutor 调用本地 execute(args)。

ToolExecutor 得到 result（或 error），将 result 写回给 LLM（第二次请求）且在第二次调用中显式禁用工具调用（mode="NONE"），让 LLM 产出最终自然语言回复。

Graph 回写（在获得 tool_result 后）：

创建 Memory Node 描述 tool_result。

连接 intent_node -> produces_memory -> memory_node。

若 tool_result 包含实体（文件路径、url、数字），为每个 entity 创造 Entity Node 并建立 targets_entity 边。

状态持久化：StateManager.persist(dispatch_context)。

5.6 步骤 E — 事务与错误策略

在 direct 或 llm 路径中，任何必须写入 CognitiveGraph 的步骤都应当：

写入节点/边后把 node_id 加入 dispatch_context.graph_nodes_created。

若在后续步骤（例如 tool 执行）出现致命错误（异常、权限拒绝、工具崩溃），则：

如果错误可回退（非破坏性），保持 graph 中已写入节点，记录 error node；

如果错误造成不一致（极少情况），触发 compensating action：标记这些节点为 invalid=true（preferred），不要物理删除（避免失去审计痕迹）。

永不在本地删除历史节点，使用标记/状态来表示生效/失效（审计与可回溯原则）。

6. CognitiveGraph 回写细则（细化）
6.1 执行前（每次请求）

写入 Intent Node （必做）

建立 session 标签（用于后续聚合查询）

6.2 执行中（当 LLM 返回 tool_call 或 direct path）

确认/创建 Tool Node：

tool_node.meta 包含 module, entry_point, tool_spec_version。

建立边： intent_node -> uses_tool -> tool_node

6.3 执行后（tool_result）

创建 Memory Node：

memory_node.meta 包含 summary、result_type、result_size、timestamp

边： intent_node -> produces_memory -> memory_node

如果工具输出包含实体（file paths / urls / names）：为每个 entity 建 Node（type=Entity）并 intent_node -> targets_entity -> entity_node，同时 memory_node -> context_of -> entity_node。

6.4 回写最小粒度

强制最小化写入体积：Memory Node 存储 summary（例如：top-3 results），而非完整原始数据（若需完整数据存储在 logs / artifacts store，并在 memory_node.meta 引用路径）。

7. 安全、权限、与审计

执行前：SecurityManager 校验 tool_call 与 params（白名单、文件路径限制、危险命令检测）。

审计日志：每次 dispatch 都写入 dispatch_audit.log（包含 dispatch_context）。

不可撤销操作（例如文件删除/外部脚本执行）必须有双重确认（UI confirm 或 explicit user_auth token）。

PII 筛查：在写入 CognitiveGraph 的任何节点 meta 前运行 PII 检查器；若检测到敏感信息，mask 并做特殊标记。

8. 单元/集成测试计划（要点）
8.1 单元测试（建议）

test_intent_integration.py：

用例：给定 user_input，断言 IntentLayer.analyze_intent() 返回 route 为 llm 或 direct（按预期）。

test_dispatch_direct_path.py：

模拟 get_time intent，assert dispatch 调用了 direct path，graph 中产生 Intent Node 和 Memory Node。

test_dispatch_llm_path_toolcall.py：

模拟 LLM 返回 tool_call，断言 tool executor 被调用，graph 中产生 Intent Node、Tool Node、Memory Node 与 edges。

8.2 集成测试（端到端）

e2e_search_and_read_flow：

输入：帮我找 requirements.txt 并读前10行（复杂复合意图示例）

期望：IntentLayer route=llm → LLM 返回 first tool_call search_files → tool executes → LLM return second tool_call read_file_lines or final text → final reply returned; CognitiveGraph 应包含 Intent, Tool(s), Memory(s), Entity(s) 以及相关 edges。

运行：pytest -q tests/test_dispatcher_integration.py::test_e2e_search_and_read_flow

9. 回滚与演进策略（开发流程建议）

在 phase3_cognitive 分支上实现变更；每个功能点拆小 PR：

PR #1：IntentLayer 调用点 + Intent Node 写入

PR #2：LLM tool use request wrapper 增强（include intent_meta）

PR #3：Graph 回写（tool_node + memory_node）

PR #4：安全层 / audit logging

每次 PR 附带 smoke test 脚本与运行日志（PR 模板必填）。将变更逐步合入 phase3_cognitive，最后合并回 phase2 / dev。

兼容性：保留现有 core_dispatcher 的 V3.6 逻辑路径开关（feature flag 或 config），以便快速回退到只用 LLM 的旧流程。

10. 示例 interaction（文本化的调用序列示例）

用户：帮我找 requirements.txt 文件

Dispatcher 调用 IntentLayer.analyze_intent("帮我找 requirements.txt 文件", context) → 返回 {"intent":"search_files","route":"llm","confidence":0.7}；Dispatcher 创建 Intent Node I1.

Dispatcher 进入 process_with_llm_tool_use：构建 LLM payload 包含 I1 的 meta、Tool Schemas、短期 memory.

LLM 返回 tool_call：search_files with args {"query":"requirements.txt","max_results":5}。Dispatcher 写入/确认 Tool Node T1 并建立 I1 -> uses_tool -> T1。

Dispatcher 调用 ToolExecutor.execute(T1,args) → 返回 tool_result（top 3 files）。

Dispatcher 创建 Memory Node M1（summary of results），并建立 I1 -> produces_memory -> M1，若返回路径则为每路径建立 Entity Node E1,E2 并 I1 -> targets_entity -> Ex.

Dispatcher 将 tool_result 回传 LLM（第二次请求，mode="NONE"），获得 final reply 并返回给用户。

dispatch_context 完整写入 StateManager。

11. 交付物清单（实现后应提交）

docs/dispatcher_integration_plan.md（本文件）

tests/test_dispatcher_integration.py（含 e2e cases）

新或更新的 core_dispatcher.py 变更记录（PR 描述）

logs/dispatch_audit.log（sample output）

docs/graph_schema.md（记录写入的 Node/Edge schema）

12. 结语（工程注意点）

关键原则是不删除历史、标记状态、审计优先；任何回滚都应通过 config 或 feature flag 实现。

IntentLayer 保持简洁（不做复杂参数抽取），复杂语义交由 LLM 在 Tool Use 流程中生成参数并调用工具。

CognitiveGraph 的回写应以summary-first 为主，避免将大量原始结果直接写入 graph（仅引用 artifact 路径以便后续检索）。