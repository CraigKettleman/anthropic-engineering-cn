# "思考"工具：让Claude在复杂工具使用场景中停下来思考

- 扩展思维更新  2025年12月15日  自首次发布以来，扩展思维（Extended Thinking）功能已得到显著改进，因此在大多数情况下，我们建议使用该功能而非专门的思考工具。扩展思维提供了类似的好处——给予Claude空间来推理复杂问题——同时具有更好的集成性和性能。有关实现细节，请参阅我们的扩展思维文档。
扩展思维更新
2025年15日
自首次发布以来，扩展思维功能已得到显著改进，因此在大多数情况下，我们建议使用该功能而非专门的思考工具。扩展思维提供了类似的好处——给予Claude空间来推理复杂问题——同时具有更好的集成性和性能。有关实现细节，请参阅我们的扩展思维文档。

在我们持续增强Claude复杂问题解决能力的过程中，我们发现了一种特别有效的方法：一个"思考"工具，它能在复杂任务期间为结构化思考创建专用空间。

这种简单而强大的技术——正如我们将在下文解释的，它与Claude的新"扩展思维"功能不同（有关扩展思维实现细节，请参阅此处）——在Claude的智能体（Agentic）工具使用能力方面取得了显著改进。这包括遵循策略、做出一致决策以及处理多步骤问题，且只需最少的实现开销。

在本文中，我们将探讨如何在不同应用中实现"思考"工具，基于经过验证的基准测试结果为开发者提供实用指导。

### 什么是"思考"工具？

通过"思考"工具，我们赋予Claude在得出最终答案的过程中，加入一个额外思考步骤的能力——该步骤拥有自己专用的空间。

虽然它听起来与扩展思维类似，但这是一个不同的概念。扩展思维关注的是Claude在开始生成响应之前所做的事情。通过扩展思维，Claude在采取行动之前会深入考虑并迭代其计划。而"思考"工具是让Claude在开始生成响应后，增加一个步骤来停下来思考是否已获得推进所需的所有信息。这在执行长链工具调用或与用户进行长多步骤对话时尤其有用。

这使得"思考"工具更适合Claude无法仅从用户查询中获得制定响应所需的全部信息，且需要处理外部信息（例如工具调用结果中的信息）的场景。Claude使用"思考"工具进行的推理不如扩展思维全面，更侧重于模型发现的新信息。

对于较简单的工具使用场景，如非顺序工具调用或直接指令遵循，我们建议使用扩展思维。当您不需要Claude调用工具时，扩展思维也适用于编码、数学和物理等用例。"思考"工具更适合Claude需要调用复杂工具、在长链工具调用中仔细分析工具输出、在具有详细指南的策略密集环境中导航，或在每一步都建立在前一步基础上且错误代价高昂的场景中做出顺序决策。

以下是来自τ-Bench的标准工具规范格式的示例实现：

```
{
  "name": "think",
  "description": "Use the tool to think about something. It will not obtain new information or change the database, but just append the thought to the log. Use it when complex reasoning or some cache memory is needed.",
  "input_schema": {
    "type": "object",
    "properties": {
      "thought": {
        "type": "string",
        "description": "A thought to think about."
      }
    },
    "required": ["thought"]
  }
}
```

### τ-Bench上的性能表现

我们使用τ-bench（tau-bench）评估了"思考"工具，这是一个综合性基准测试，旨在测试模型在真实客户服务场景中使用工具的能力，其中"思考"工具是评估标准环境的一部分。

τ-bench评估Claude的以下能力：
- 与模拟用户进行真实对话
- 始终遵循复杂的客服智能体策略指南
- 使用各种工具访问和操作环境数据库

τ-bench中使用的主要评估指标是pass^k，它衡量给定任务中所有k次独立试验都成功的概率，在所有任务上取平均值。与其他LLM评估中常见的pass@k指标（衡量k次试验中至少有一次成功）不同，pass^k评估的是一致性和可靠性——这对于需要一致遵循策略的客户服务应用来说是至关重要的品质。

#### 性能分析

我们的评估比较了几种不同的配置：
- 基线（无"思考"工具，无扩展思维模式）
- 仅扩展思维模式
- 仅"思考"工具
- "思考"工具加优化提示（针对航空领域）

结果表明，当Claude 3.7在基准测试的"航空"和"零售"客户服务领域中有效使用"思考"工具时，取得了显著的改进：
- 航空领域："思考"工具配合优化提示在pass^1指标上达到了0.570，而基线仅为0.370——相对改进54%；
- 零售领域：仅"思考"工具就达到了0.812，而基线为0.783。

Claude 3.7 Sonnet在Tau-Bench评估"航空"领域的表现

航空领域的最佳性能是通过将"思考"工具与优化提示配对实现的，该提示提供了在分析客户请求时应使用的推理方法示例。以下是优化提示的示例：

```
## Using the think tool

Before taking any action or responding to the user after receiving tool results, use the think tool as a scratchpad to:
- List the specific rules that apply to the current request
- Check if all required information is collected
- Verify that the planned action complies with all policies
- Iterate over tool results for correctness 

Here are some examples of what to iterate over inside the think tool:
<think_tool_example_1>
User wants to cancel flight ABC123
- Need to verify: user ID, reservation ID, reason
- Check cancellation rules:
  * Is it within 24h of booking?
  * If not, check ticket class and insurance
- Verify no segments flown or are in the past
- Plan: collect missing info, verify rules, get confirmation
</think_tool_example_1>

<think_tool_example_2>
User wants to book 3 tickets to NYC with 2 checked bags each
- Need user ID to check:
  * Membership tier for baggage allowance
  * Which payments methods exist in profile
- Baggage calculation:
  * Economy class × 3 passengers
  * If regular member: 1 free bag each → 3 extra bags = $150
  * If silver member: 2 free bags each → 0 extra bags = $0
  * If gold member: 3 free bags each → 0 extra bags = $0
- Payment rules to verify:
  * Max 1 travel certificate, 1 credit card, 3 gift cards
  * All payment methods must be in profile
  * Travel certificate remainder goes to waste
- Plan:
1. Get user ID
2. Verify membership level for bag fees
3. Check which payment methods in profile and if their combination is allowed
4. Calculate total: ticket price + any bag fees
5. Get explicit confirmation for booking
</think_tool_example_2>
```

特别有趣的是不同方法之间的比较。使用"思考"工具配合优化提示，相比扩展思维模式（其表现与未提示的"思考"工具相似）取得了明显更好的结果。单独使用"思考"工具（无提示）相比基线提高了性能，但仍不及优化方法。

"思考"工具与优化提示的组合以显著优势提供了最强的性能，这可能是由于基准测试中航空策略部分的高复杂度，模型从获得如何"思考"的示例中获益最多。

在零售领域，我们也测试了各种配置以了解每种方法的具体影响。

Claude 3.7 Sonnet在Tau-Bench评估"零售"领域的表现

"思考"工具即使在没有额外提示的情况下也取得了最高的pass^1分数0.812。零售策略相比航空领域明显更容易处理，Claude仅通过拥有一个思考空间就能在没有进一步指导的情况下有所改进。

#### τ-Bench分析的关键发现

我们的详细分析揭示了几种模式，可以帮助您有效实现"思考"工具：
- 提示在困难领域中至关重要。仅仅让"思考"工具可用可能会稍微提高性能，但将其与优化提示配对，在困难领域中会产生显著更好的结果。然而，较简单的领域可能仅从能够使用"思考"中获益。
- 跨试验的一致性提升。使用"思考"带来的改进在k达到5的pass^k中得以保持，表明该工具帮助Claude更有效地处理边缘情况和异常场景。

### SWE-Bench上的性能表现

在评估Claude 3.7 Sonnet时，我们向SWE-bench设置中添加了类似的"思考"工具，为达到0.623的最先进分数做出了贡献。以下是改编后的"思考"工具定义：

```
{
  "name": "think",
  "description": "Use the tool to think about something. It will not obtain new information or make any changes to the repository, but just log the thought. Use it when complex reasoning or brainstorming is needed. For example, if you explore the repo and discover the source of a bug, call this tool to brainstorm several unique ways of fixing the bug, and assess which change(s) are likely to be simplest and most effective. Alternatively, if you receive some test results, call this tool to brainstorm ways to fix the failing tests.",
  "input_schema": {
    "type": "object",
    "properties": {
      "thought": {
        "type": "string",
        "description": "Your thoughts."
      }
    },
    "required": ["thought"]
  }
}
```

我们的实验（使用"思考"工具n=30个样本，不使用n=144个样本）表明，包含该工具的单独效果使性能平均提高了1.6%（Welch's t检验：t(38.89) = 6.71，p < .001，d = 1.47）。

### 何时使用"思考"工具

根据这些评估结果，我们确定了Claude从"思考"工具中获益最多的特定场景：
- 工具输出分析。当Claude在行动前需要仔细处理先前工具调用的输出，且可能需要回溯其方法时；
- 策略密集环境。当Claude需要遵循详细指南并验证合规性时；以及
- 顺序决策。当每个行动都建立在前一步基础上，且错误代价高昂时（常见于多步骤领域）。

## 实现最佳实践

为了充分利用Claude的"思考"工具，我们基于τ-bench实验推荐以下实现实践。

#### 1. 使用领域特定示例进行策略性提示

最有效的方法是提供关于何时以及如何使用"思考"工具的清晰说明，例如τ-bench航空领域所使用的。提供针对您特定用例的示例可以显著提高模型使用"思考"工具的效果：
- 推理过程中期望的详细程度；
- 如何将复杂指令分解为可执行的步骤；
- 处理常见场景的决策树；以及
- 如何检查是否已收集所有必要信息。

#### 2. 将复杂指导放在系统提示中

我们发现，当说明较长和/或较复杂时，将关于"思考"工具的说明放在系统提示中比放在工具描述本身中更有效。这种方法提供了更广泛的上下文，并帮助模型更好地将思考过程整合到其整体行为中。

### 何时*不*使用"思考"工具

虽然"思考"工具可以提供实质性改进，但它并非适用于所有工具使用用例，而且确实会以增加提示长度和输出token为代价。具体而言，我们发现"思考"工具在以下用例中不会提供任何改进：
- 非顺序工具调用。如果Claude只需进行单次工具调用或多次并行调用即可完成任务，添加"思考"不太可能带来任何改进。
- 简单指令遵循。当Claude需要遵守的约束不多，且其默认行为已足够好时，额外的"思考"不太可能带来收益。

### 入门指南

"思考"工具是对Claude实现的简单添加，只需几个步骤即可产生有意义的改进：
- 在智能体工具使用场景中进行测试。从具有挑战性的用例开始——即Claude目前在策略合规性或长工具调用链中的复杂推理方面存在困难的场景。
- 添加工具定义。实现一个针对您领域定制的"思考"工具。它只需最少的代码，但能实现更结构化的推理。同时考虑在系统提示中包含关于何时以及如何使用该工具的说明，以及与您领域相关的示例。
- 监控和改进。观察Claude在实践中如何使用该工具，并调整您的提示以鼓励更有效的思考模式。

最棒的是，添加此工具在性能结果方面的负面影响极小。除非Claude决定使用它，否则它不会改变外部行为，也不会干扰您现有的工具或工作流程。

### 结论

我们的研究表明，"思考"工具可以显著提升Claude 3.7 Sonnet在需要策略遵循和长工具调用链推理的复杂任务中的性能。"思考"并非万能解决方案，但它为正确的用例提供了实质性收益，且实现复杂度极低。

我们期待看到您如何使用"思考"工具与Claude一起构建更强大、更可靠、更透明的AI系统。

1. 虽然我们的τ-Bench结果聚焦于Claude 3.7 Sonnet使用"思考"工具的改进，但我们的实验表明，Claude 3.5 Sonnet（新版本）在与3.7 Sonnet相同的配置下也能获得性能提升，表明这种改进可以推广到其他Claude模型。