A4 — Tool Routing Specification (Phase 4.0)

子标题：智能调度分层模型下的工具路由与执行策略
版本：Phase 4.0
目标：在不破坏 A1（IntentLayer）与 A3（Dispatcher Integration Plan）结构的前提下，实现智能判断 “云端任务” 与 “本地任务” 的动态调度机制。

1. 概要

A4 定义了 CoreDispatcher（Phase 3.9 已完成）的下一阶段扩展，使其具备“智能分层调度”能力：

判断用户意图是否应交由 Gemini 云端 AI 处理，或由本地 Tool Registry 执行。

该设计不引入新模块、不修改 A1/A2/A3 的职责边界，仅在现有 Dispatcher 中增加一个 Routing Policy Layer。

2. 架构总览
┌────────────────────────────────────────────┐
│                User Message                │
└────────────────────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────┐
│           A1. IntentLayer (识别意图)       │
│ 输出示例: {"intent": "get_weather", "route": "cloud"} │
└────────────────────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────┐
│       A3. Dispatcher (Phase 4.0 扩展)      │
│ ┌──────────────────────────────────────┐  │
│ │ RoutingPolicy.check_route(intent)    │  │
│ │ → 返回 "cloud" 或 "local"             │  │
│ └──────────────────────────────────────┘  │
└────────────────────────────────────────────┘
        │                       │
        │                       │
        ▼                       ▼
┌────────────────────┐   ┌──────────────────────┐
│ Gemini Cloud Path  │   │ Local Tool Registry  │
│ (联网型任务)        │   │ (操作型任务)          │
└────────────────────┘   └──────────────────────┘
        │                       │
        ▼                       ▼
┌────────────────────────────────────────────┐
│         A2. CognitiveGraph (记录记忆)       │
└────────────────────────────────────────────┘

3. Routing Policy 层设计
3.1 职责

RoutingPolicy 是一个轻量级策略层，用于在 Dispatcher 决策前判断执行路径。

它的输入为：

intent_data = {
    "intent": "get_weather",
    "route": "cloud"  # 可由 IntentLayer 提前给出，也可由策略判断
}


输出：

route = "cloud" or "local"

3.2 路由决策规则
任务类型	典型意图关键词	执行路径	示例
🌐 云端查询	weather, news, translate, stock, search, route	"cloud"	“东京天气怎样？”
💻 本地操作	open, read, delete, list, screenshot, run	"local"	“打开桌面文件夹”
🤖 未知任务	无匹配项	默认 "local"	保持向后兼容
3.3 配置文件示例（/config/routing_policy.yaml）
cloud_intents:
  - get_weather
  - get_news
  - translate_text
  - get_stock_price
  - web_search

local_intents:
  - search_files
  - open_file
  - delete_file
  - take_screenshot
  - run_command

4. Cloud Path 执行规范（Gemini API）
4.1 模块职责

当 route = "cloud" 时，Dispatcher 调用 Gemini 的信息检索能力。

Gemini 将执行：

搜索（Google Search / Web Info Retrieval）

实时知识问答（Facts, News, Translation）

不访问本地资源的推理

4.2 调用示例
if route == "cloud":
    response = gemini_api.query(user_input)
else:
    response = self._process_with_llm_tool_use(user_input)


返回的 response 会被封装为统一的结果对象：

{
  "source": "gemini_cloud",
  "intent": "get_weather",
  "data": "Tokyo's weather today is 18°C, partly cloudy."
}

5. Local Path 执行规范（Tool Registry）

当 route = "local" 时，保持 Phase 3.9 的流程不变：

调用 _process_with_llm_tool_use()。

LLM 根据工具 schema 生成 tool_call。

调用对应 plugin 的 execute()。

将结果写回 CognitiveGraph。

6. Dispatcher 路由流程 (Phase 4.0)
def dispatch(user_message):
    intent = A1.analyze_intent(user_message)
    route = RoutingPolicy.resolve(intent)

    if route == "cloud":
        result = gemini_api.query(user_message)
    elif route == "local":
        result = self._process_with_llm_tool_use(user_message)
    else:
        result = "Unable to determine route."

    A2.record_interaction(intent, route, result)
    return result

7. A2 回写逻辑

无论任务来源于 Cloud 或 Local，CognitiveGraph 都应更新：

CognitiveGraph.add_node({
    "intent": intent,
    "route": route,
    "result": result,
    "timestamp": now()
})


这保证未来可追踪与分析：

用户偏好（云/本地比例）

意图成功率

自动优化 routing policy

8. 安全与稳定性

云端调用安全：Gemini 端处理联网内容，无本地风险。

本地插件沙箱：维持 V28 的插件加载机制。

回退机制：若云端调用失败，Dispatcher 自动回退至 "local" 路径（若存在匹配插件）。

9. 演进路线图
版本	特性	状态
3.9	本地工具调用 (LLM Tool Use)	✅ 已实现
4.0	Cloud / Local 动态路由	🚀 当前文档
4.1	RoutePolicy 学习优化 (A2驱动)	⏳ 计划中
4.2	Multi-Agent 联合调度	🔮 研究方向
10. 示例

用户输入：

“东京今天的天气怎样？”

处理流程：

A1 → {"intent":"get_weather","route":"cloud"}

Dispatcher → RoutingPolicy 确认 route=cloud

Gemini → 调用联网接口返回天气信息

Dispatcher → 统一封装结果

A2 → 存储节点（intent: get_weather, route: cloud）

返回结果：

“东京今天多云，气温 18°C。”

结论

本修正版 A4 文档：

完全兼容 A1、A2、A3 的既有职责。

精准实现你提出的「云端可查 → 云执行、本地操作 → 插件执行」原则。

不引入 Coordinator 或 REST 服务，依旧保留 Phase 3.9 的稳定核心。