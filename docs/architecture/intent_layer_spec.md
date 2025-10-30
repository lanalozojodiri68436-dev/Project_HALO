📘 Intent Layer Architecture Specification (V3.9 Draft 1)
1️⃣ Overview：设计定位

Intent Layer (V3.9) 是 HALO 认知核心的首层模块，
负责将用户的自然语言输入转化为系统可理解的 “任务意图单元 (Intent Unit)”，
并决定该任务应采用 快速路径 还是 LLM Tool Use 路径 处理。

它是整个 Cognitive Core 的“认知入口层”，
位于 User Input 与 CoreDispatcher (V3.6+) 之间。

2️⃣ Functional Goals：功能目标
目标编号	目标描述
G1	对输入语句进行 意图分类 并输出标准化 Intent 对象。
G2	根据意图置信度和任务复杂度，决定 路由策略（direct / llm）。
G3	维护 意图记忆 （Intent Memory），用于上下文回溯与学习。
G4	支持 复合意图检测 与 Action Chain 拆分。
G5	为 CoreDispatcher 提供统一接口，无需感知内部实现。
3️⃣ Architecture Diagram
+------------------------------------------------------+
|                Intent Layer (V3.9)                   |
+------------------------------------------------------+
|                                                      |
|  ┌────────────────────────────┐                      |
|  |  IntentClassifier          |→ intent metadata     |
|  ├────────────────────────────┤                      |
|  |  IntentRouter              |→ route decision      |
|  ├────────────────────────────┤                      |
|  |  IntentMemory (new)        |↔ CognitiveGraph      |
|  ├────────────────────────────┤                      |
|  |  FallbackManager           |→ safe LLM fallback   |
|  └────────────────────────────┘                      |
|                                                      |
+------------------------------------------------------+
             ↓
       CoreDispatcher (V3.6)

4️⃣ Core Modules & Responsibilities
🧠 4.1 IntentClassifier

负责将自然语言输入转换为结构化 Intent 对象。

输入：

{
  "user_input": "帮我找一下 report 文件",
  "context": {...}
}


输出：

{
  "intent": "search_files",
  "confidence": 0.92,
  "complexity": "medium",
  "raw_text": "帮我找一下 report 文件"
}


关键策略：

使用轻量 embedding 匹配与规则相结合；

不再尝试提取参数，仅识别 意图类型；

若无法分类 → 返回 intent="unknown" 并标记 route="llm"。

🧭 4.2 IntentRouter

根据意图属性与复杂度决策路由。

判断逻辑	路由结果
intent ∈ {get_time, open_help}	direct_tool_execute
confidence ≥ 0.9 and complexity = low	direct
其他	llm

输出：

{
  "route": "llm",
  "reason": "complex_intent_or_low_confidence"
}

🧩 4.3 IntentMemory (V3.9 新增)

为认知连续性提供 “短期记忆” 机制。

职责：

记录最近 N 次用户意图；

支持 CoreDispatcher 的 context 注入；

参与 CognitiveGraph 更新。

结构：

{
  "history": [
    {"intent": "search_files", "timestamp": "..."},
    {"intent": "read_file_lines", "timestamp": "..."}
  ],
  "session_id": "halo-session-001"
}

⚙️ 4.4 FallbackManager

当 IntentClassifier 输出 unknown 或置信度 < 0.5 时，自动：

触发 LLM Tool Use 回退；

或提示 CoreDispatcher 进行 RecoveryPlan。

输出：

{
  "route": "llm_fallback",
  "reason": "low_confidence"
}

5️⃣ Data Structures
Intent Object
字段	类型	说明
intent	str	任务名称（如 search_files）
confidence	float	0 ~ 1 之间置信度
complexity	str	low / medium / high
route	str	direct / llm / llm_fallback
timestamp	str	UTC 时间戳
raw_text	str	原始用户输入
6️⃣ Interfaces with CoreDispatcher

函数接口定义：

def analyze_intent(user_input: str, context: dict) -> dict:
    """
    Intent Layer 入口函数
    返回 Intent metadata 供 CoreDispatcher 使用
    """


典型调用链：

intent_meta = IntentLayer.analyze_intent(user_input)
dispatch_result = CoreDispatcher.dispatch(intent_meta)

7️⃣ Decision Matrix（决策矩阵）
输入类型	分类结果	路由	示例
“现在几点”	get_time	direct	→ Tool Use: get_time
“帮我找 report 文件”	search_files	llm	→ LLM Tool Use
“打开 project 数据”	read_file_lines	llm	→ LLM Tool Use
“解释这个错误代码”	unknown	llm_fallback	→ LLM 补全推理
8️⃣ Integration Notes
项	说明
版本依赖	CoreDispatcher ≥ V3.6
输入要求	UTF-8 文本（支持中英文混合）
日志	所有分类决策写入 /logs/intent_layer.log
可视化	未来将与 HALO Dashboard 连接 (phase 4)
9️⃣ Extensibility Plan (Phase 4 Preview)

引入 IntentGraph → 多步意图与工具图谱；

支持 User Profile Learning → 个性化意图权重调整；

增加 Reasoning Feedback Loop → 执行结果反哺分类模型。

🔟 Version Control
字段	值
Spec Version	V3.9 Draft 1
Compatible Core Dispatcher	V3.6 +
Author	HALO Cognitive Team
Status	📘 Design Approved / Awaiting Prototype