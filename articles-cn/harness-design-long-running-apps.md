# 长时间运行应用开发的框架设计

作者：Prithvi Rajasekaran，Labsteam 团队成员。
在过去的几个月里，我一直在研究两个相互关联的问题：让 Claude 产出高质量的前端设计，以及让它无需人工干预就能构建完整的应用程序。这项工作源于我们团队此前在前端设计技能（frontend design skill）和长时间运行编码智能体（coding agent harness）方面的探索，我和同事们通过提示工程（prompt engineering）和框架设计大幅提升了 Claude 的表现——但两者最终都遇到了天花板。
为了突破瓶颈，我探索了跨越两个截然不同领域的新型 AI 工程方法——一个由主观品味定义，另一个由可验证的正确性和可用性定义。受生成对抗网络（Generative Adversarial Networks, GANs）的启发，我设计了一个包含生成器（generator）和评估器（evaluator）的多智能体（multi-agent）架构。要构建一个能可靠评判输出——并且具有品味——的评估器，首先需要制定一套标准，将"这个设计好不好？"这样的主观判断转化为具体的、可评分的术语。
随后，我将这些技术应用到长时间运行的自主编码中，并从此前的框架工作中继承了两条经验：将构建过程分解为可管理的块，以及使用结构化制品（structured artifacts）在会话之间传递上下文。最终成果是一个三智能体架构——规划器（planner）、生成器和评估器——能够在长达数小时的自主编码会话中产出丰富的全栈应用。

## 为什么朴素实现会失败

我们此前已经证明，框架设计对长时间运行的智能体编码效果有重大影响。在早期的一个实验中，我们使用初始化智能体（initializer agent）将产品规格分解为任务列表，然后由编码智能体逐个功能地实现任务，并通过传递制品来跨会话携带上下文。更广泛的开发者社区也得出了类似的洞察，比如"Ralph Wiggum"方法使用钩子（hooks）或脚本来让智能体保持持续的迭代循环。
但一些问题仍然持续存在。对于更复杂的任务，智能体往往会随着时间推移而偏离轨道。在分析这个问题时，我们观察到智能体执行此类任务时的两种常见失败模式。
第一种是，随着上下文窗口（context window）填满，模型倾向于在冗长的任务中失去连贯性（参见我们关于上下文工程的文章）。一些模型还会表现出"上下文焦虑"（context anxiety），即它们在接近自认为的上下文限制时会过早地结束工作。上下文重置（context reset）——完全清除上下文窗口并启动一个全新的智能体，结合结构化的交接以携带前一个智能体的状态和后续步骤——可以解决这两个问题。
这与压缩（compaction）不同，后者是将对话的早期部分原地摘要，以便同一个智能体可以在缩短的历史记录上继续工作。虽然压缩保留了连续性，但它没有给智能体一个全新的开始，这意味着上下文焦虑可能仍然存在。重置提供了一个全新的开始，代价是交接制品需要包含足够的状态，以便下一个智能体能够干净利落地接手工作。在我们早期的测试中，我们发现 Claude Sonnet 4.5 表现出的上下文焦虑非常强烈，仅靠压缩不足以支撑出色的任务表现，因此上下文重置成为框架设计中必不可少的环节。这解决了核心问题，但增加了编排复杂性、token 开销和每次框架运行的延迟。
第二个问题我们此前没有涉及，那就是自我评估（self-evaluation）。当被要求评估自己产出的工作时，智能体倾向于自信地赞扬这些工作——即使对人类观察者来说，质量明显平庸。这个问题在设计等主观任务中尤为突出，因为没有等同于可验证软件测试的二元检查。一个布局是精致还是平庸，这是一个判断性问题，而智能体在给自己的工作打分时总是偏向正面。
然而，即使在有可验证结果的任务上，智能体有时也会表现出糟糕的判断力，妨碍其完成任务。将执行工作的智能体与评判工作的智能体分开，被证明是解决这个问题的有力杠杆。这种分离本身并不能立即消除那种宽容倾向；评估器仍然是一个倾向于对 LLM 生成的输出持宽容态度的大语言模型。但将独立的评估器调校得更具怀疑精神，远比让生成器对自己的工作持批判态度要容易得多。而且一旦存在外部反馈，生成器就有了具体的迭代目标。

## 前端设计：让主观质量可评分

我从前端设计开始实验，这是自我评估问题最显而易见的领域。在没有任何干预的情况下，Claude 通常倾向于安全、可预测的布局——技术上可用，但视觉上平淡无奇。
两个洞察塑造了我为前端设计构建的框架。首先，虽然美学不能完全简化为一个分数——个人品味也总是各异——但可以通过编码设计原则和偏好的评分标准来提升美学质量。"这个设计美不美？"很难一致地回答，但"这是否遵循了我们好的设计原则？"给了 Claude 具体的评分依据。其次，通过将前端生成与前端评分分离，我们可以创建一个反馈循环，驱动生成器产出更强的输出。
基于此，我编写了四条评分标准，同时提供给提示中的生成器和评估器智能体：
- 设计质量：设计是否感觉是一个连贯的整体，而不是各部分的拼凑？这里的优秀表现意味着颜色、排版、布局、图像和其他细节组合在一起，营造出独特的氛围和身份感。
- 原创性：是否有自定义决策的证据，还是仅仅是模板布局、库默认值和 AI 生成的模式？人类设计师应该能识别出刻意的创意选择。未经修改的通用组件——或典型的 AI 生成痕迹，如白色卡片上的紫色渐变——在此项会失分。
- 工艺：技术执行：排版层次、间距一致性、色彩和谐、对比度。这是一项能力检查而非创意检查。大多数合理的实现在此项默认就能表现良好；失败意味着基本功出了问题。
- 功能性：独立于美学的可用性。用户能否理解界面的功能、找到主要操作，并在不猜测的情况下完成任务？
我强调设计质量和原创性，甚于工艺和功能性。Claude 在工艺和功能性上默认就能取得不错的分数，因为所需的技术能力对模型来说往往是自然而然的。但在设计和原创性方面，Claude 的输出往往充其量是平淡的。这些标准明确惩罚了高度通用的"AI 垃圾"模式，通过加大设计和原创性的权重，推动模型进行更多美学上的冒险。
我使用带有详细评分分解的少样本示例（few-shot examples）来校准评估器。这确保了评估器的判断与我的偏好一致，并减少了跨迭代的分数漂移。
我在 Claude Agent SDK 上构建了这个循环，使编排保持简单。生成器智能体首先根据用户提示创建一个 HTML/CSS/JS 前端。我给评估器提供了 Playwright MCP，让它可以直接与实时页面交互，然后对每个标准进行评分并撰写详细的评价。在实践中，评估器会自行导航页面，截图并仔细研究实现，然后才产出评估。这些反馈作为下一次迭代的输入回流给生成器。每次生成运行 5 到 15 次迭代，每次迭代通常将生成器推向更具特色的方向，以回应评估器的评价。由于评估器是在主动导航页面而非对静态截图评分，每个循环都需要真实的挂钟时间。完整运行最长可达四个小时。我还指示生成器在每次评估后做出战略决策：如果分数趋势良好，就改进当前方向；如果方法不奏效，则转向完全不同的美学风格。
跨运行来看，评估器的评估在迭代过程中有所改善，然后趋于平稳，但仍有提升空间。一些生成是渐进式改进。另一些则在迭代之间发生了急剧的美学转向。
标准的措辞以我未完全预料到的方式引导了生成器。包含"最好的设计是博物馆级别的"这样的短语，推动设计向特定的视觉方向收敛，表明与标准相关的提示词直接塑造了输出的特性。
虽然分数在迭代中总体有所改善，但模式并不总是干净的线性关系。后期的实现整体上往往更好，但我经常看到我更喜欢中间某次迭代而非最后一次的情况。实现的复杂度也倾向于在各轮次中增加，生成器在回应评估器的反馈时会追求更有野心的解决方案。即使在第一次迭代中，输出也明显好于完全没有提示的基线，表明标准和相关语言本身就在任何评估器反馈导致进一步改进之前，就引导模型远离了通用默认值。
在一个值得注意的例子中，我提示模型为一家荷兰艺术博物馆创建网站。到第九次迭代时，它已经为一个虚构的博物馆制作了一个简洁的暗色主题着陆页。页面视觉上很精致，但基本符合我的预期。然后，在第十次循环中，它完全抛弃了原有方案，将网站重新想象为一种空间体验：一个带有棋盘格地板的 3D 房间，使用 CSS 透视渲染，艺术品以自由形式的位置悬挂在墙上，通过门廊式导航在展厅之间切换，而不是滚动或点击。这是我此前在单次生成中从未见过的那种创意飞跃。

## 扩展到全栈编码

基于这些发现，我将这种 GAN 启发的模式应用到全栈开发中。生成器-评估器循环自然映射到软件开发生命周期，其中代码审查和 QA 与设计评估器扮演着相同的结构角色。

### 架构

在我们此前的长时间运行框架中，我们通过初始化智能体、逐个功能工作的编码智能体以及会话之间的上下文重置，解决了连贯的多会话编码问题。上下文重置是一个关键突破：该框架使用 Sonnet 4.5，它表现出了前面提到的"上下文焦虑"倾向。构建一个在上下文重置中运行良好的框架，是让模型保持任务的关键。Opus 4.5 大体上自行消除了这种行为，因此我得以完全从该框架中去除上下文重置。智能体作为单个连续会话贯穿整个构建过程，Claude Agent SDK 的自动压缩功能在过程中处理上下文增长。
在这项工作中，我在原有框架的基础上构建了一个三智能体系统，每个智能体解决我在先前运行中观察到的一个特定缺口。系统包含以下智能体角色：
规划器（Planner）：我们此前的长时间运行框架要求用户预先提供详细的规格说明。我希望自动化这一步骤，因此创建了一个规划器智能体，它接收简单的 1-4 句话提示，并将其扩展为完整的产品规格。我提示它在范围上要有野心，并专注于产品上下文和高层技术设计，而非详细的技术实现。这样强调是因为担心，如果规划器试图预先指定精细的技术细节并出错，规格中的错误会级联到下游实现中。更明智的做法是约束智能体的产出物，让它们在工作过程中自行摸索路径。我还要求规划器寻找将 AI 功能融入产品规格的机会。（参见底部附录中的示例。）
生成器（Generator）：此前框架中逐个功能推进的方法在范围管理上效果很好。我在这里应用了类似的模型，指示生成器以冲刺（sprint）方式工作，从规格中一次提取一个功能。每次冲刺使用 React、Vite、FastAPI 和 SQLite（后来改为 PostgreSQL）技术栈实现应用，并且生成器被指示在每次冲刺结束时进行自我评估，然后再交给 QA。它还使用 git 进行版本控制。
评估器（Evaluator）：此前框架产出的应用看起来往往令人印象深刻，但实际使用时仍有真实的 bug。为了捕捉这些问题，评估器使用 Playwright MCP 像用户一样点击正在运行的应用，测试 UI 功能、API 端点和数据库状态。然后根据发现的 bug 和一套以前端实验为模型的标准对每次冲刺进行评分，这里调整为涵盖产品深度、功能性、视觉设计和代码质量。每项标准都有硬性阈值，如果任何一项低于阈值，冲刺就会失败，生成器会收到关于问题所在的详细反馈。在每次冲刺之前，生成器和评估器会协商冲刺合同（sprint contract）：在编写任何代码之前就该工作块的"完成"定义达成一致。这之所以存在，是因为产品规格是故意保持高层级的，我需要一个步骤来弥合用户故事与可测试实现之间的差距。生成器提议它将构建什么以及如何验证成功，评估器审查该提案以确保生成器在构建正确的东西。两者迭代直到达成一致。
通信通过文件处理：一个智能体写入文件，另一个智能体读取该文件并在该文件中回复，或者写一个新文件让前一个智能体读取。然后生成器按照约定的合同构建，再将工作交给 QA。这使工作忠实于规格，同时不会过早地过度规定实现细节。

### 运行框架

在该框架的第一个版本中，我使用 Claude Opus 4.5，将用户提示同时运行完整框架和单智能体系统进行对比。我使用 Opus 4.5，因为这是我开始这些实验时我们最好的编码模型。
我编写了以下提示来生成一个复古视频游戏制作工具：

> Create a 2D retro game maker with features including a level editor, sprite editor, entity behaviors, and a playable test mode.

下表展示了框架类型、运行时长和总成本。
框架的开销贵了 20 多倍，但输出质量的差异立即显而易见。
我期望的是一个可以构建关卡及其组成部分（精灵、实体、图块布局）然后点击播放来实际游玩的界面。我首先打开了单独运行的输出，初始应用似乎符合这些预期。
然而，随着我点击操作，问题开始浮现。布局浪费空间，固定高度的面板让大部分视口都是空的。工作流程很僵硬。尝试填充关卡时提示我先创建精灵和实体，但 UI 中没有任何引导我走向这个顺序的内容。更关键的是，实际的游戏是坏的。我的实体出现在屏幕上但没有对输入做出任何响应。深入代码后发现，实体定义和游戏运行时之间的连接是断开的，且表面没有任何提示问题出在哪里。
在评估完单独运行后，我将注意力转向框架运行。这次运行从相同的一句话提示开始，但规划器步骤将该提示扩展为跨十个冲刺的 16 个功能规格。它远远超出了单独运行所尝试的范围。除了核心编辑器和游玩模式外，规格还要求精灵动画系统、行为模板、音效和音乐、AI 辅助的精灵生成器和关卡设计师，以及可分享链接的游戏导出功能。我让规划器访问了我们的前端设计技能，它阅读了该技能并将其用于创建应用的视觉设计语言作为规格的一部分。对于每个冲刺，生成器和评估器协商一份合同，定义冲刺的具体实现细节，以及用于验证完成情况的可测试行为。
该应用立即展现出比单独运行更多的精致感和流畅度。画布使用了完整的视口，面板尺寸合理，界面具有一致的视觉身份，与规格中的设计方向保持一致。我在单独运行中看到的一些笨拙确实仍然存在——工作流程仍然没有清楚地表明你应该在尝试填充关卡之前先构建精灵和实体，我不得不自己摸索出来。这被理解为基础模型的产品直觉的缺口，而非框架设计要解决的问题，尽管它确实暗示了在框架内进行针对性迭代可以进一步提高输出质量的地方。
在使用编辑器的过程中，新运行相比单独运行的优势变得更加明显。精灵编辑器更丰富、功能更完善，拥有更整洁的工具面板、更好的颜色选择器和更实用的缩放控制。
因为我要求规划器将 AI 功能融入其规格，应用还内置了 Claude 集成，让我可以通过提示来生成游戏的不同部分。这显著加快了工作流程。
最大的差异在游玩模式。我实际上能够移动我的实体并玩游戏。物理引擎有一些粗糙之处——我的角色跳上平台但最终与平台重叠了，直觉上感觉不对——但核心功能是可以工作的，而单独运行没有做到这一点。四处移动后，我确实遇到了一些 AI 游戏关卡构建的局限性。有一面大墙我无法跳过去，所以我被卡住了。这表明有一些常识性改进和边缘情况，框架可以处理以进一步完善应用。
通读日志后，很明显评估器使实现与规格保持一致。每次冲刺，它都会走一遍冲刺合同的测试标准，并通过 Playwright 操作正在运行的应用，对任何偏离预期行为的地方提交 bug 报告。合同非常细致——仅第 3 次冲刺就有关卡编辑器的 27 项标准——评估器的发现足够具体，无需额外调查就能采取行动。下表展示了我们评估器识别出的几个问题示例：
fillRectangle
LevelEditor.tsx:892
selection
selectedEntityId
selectedEntityId
selection || (selectedEntityId && activeLayer === 'entity')
PUT /frames/reorder
/{frame_id}
eorder
让评估器达到这个水平需要下功夫。开箱即用时，Claude 是一个糟糕的 QA 智能体。在早期运行中，我看到它识别出合法问题，然后说服自己认为这些问题无关紧要，最终批准了工作。它还倾向于浅层测试，而不是深入探索边缘情况，因此更隐蔽的 bug 经常溜走。调校的循环是阅读评估器的日志，找到其判断与我的判断不一致的示例，然后更新 QA 的提示来解决这些问题。经过几轮这样的开发循环后，评估器的评分方式才让我觉得合理。即便如此，框架输出仍展示了模型 QA 能力的局限：小的布局问题、在某些地方感觉不直观的交互，以及评估器未深入测试的更深层嵌套功能中的未发现 bug。显然通过进一步调校还有更多的验证空间可以挖掘。但与单独运行相比——其中应用的核心功能根本无法工作——提升是显而易见的。

### 迭代框架

第一组框架结果令人鼓舞，但它也很笨重、缓慢且昂贵。合乎逻辑的下一步是在不降低性能的前提下寻找简化框架的方法。这部分是常识，部分源于一个更普遍的原则：框架中的每个组件都编码了一个关于模型自身无法完成的事情的假设，而这些假设值得压力测试，既因为它们可能是不正确的，也因为随着模型改进它们可能很快过时。我们的博文《构建有效的智能体》将底层理念表述为"找到尽可能简单的解决方案，只在需要时才增加复杂性"，这是任何维护智能体框架的人身上都能看到的模式。
在我的第一次简化尝试中，我大幅削减了框架并尝试了一些有创意的新想法，但我无法复制原始框架的性能。而且很难辨别框架设计中的哪些部分实际上是承重的，以及以什么方式承重。基于那次经验，我转向了更有条理的方法，一次移除一个组件，并审查其对最终结果的影响。
当我进行这些迭代循环时，我们还发布了 Opus 4.6，这进一步激发了减少框架复杂性的动力。有充分理由预期 4.6 比 4.5 需要更少的脚手架。从我们的发布博文来看："[Opus 4.6] 计划更仔细，维持智能体任务的时间更长，能在更大的代码库中更可靠地运行，并且拥有更好的代码审查和调试技能来捕捉自己的错误。"它在长上下文检索方面也有显著提升。这些都是框架原本要补充的能力。

### 移除冲刺结构

我首先完全移除了冲刺结构。冲刺结构曾帮助将工作分解为模型可以连贯处理的块。鉴于 Opus 4.6 的改进，有充分理由相信模型可以原生处理这项工作，无需这种分解。
我保留了规划器和评估器，因为它们各自持续带来明显价值。没有规划器，生成器的范围就会缩小：给定原始提示，它会不经规划就开始构建，最终创建的功能不如规划器参与时丰富。
移除冲刺结构后，我将评估器移到运行结束时的单次通过，而不是每个冲刺都评分。由于模型能力更强，这改变了评估器在某些运行中的承重程度，其有用性取决于任务相对于模型自身可靠完成能力的位置。在 4.5 上，这个边界很近：我们的构建处于生成器独自能做好的边缘，评估器在整个构建过程中捕捉到了有意义的问题。在 4.6 上，模型的原始能力增强了，所以边界向外移动了。曾经需要评估器检查才能连贯实现的任务，现在通常在生成器独自能处理好的范围内；对于在这个边界内的任务，评估器变成了不必要的开销。但对于仍然处于生成器能力边缘的构建部分，评估器继续带来真实的提升。
实际意义是，评估器不是一个固定的"是或否"决策。当任务超出了当前模型独自可靠完成的范围时，它是值得投入的。
在结构简化的同时，我还增加了提示来改善框架如何将 AI 功能构建到每个应用中，特别是让生成器构建一个可以通过工具驱动应用自身功能的正式智能体（agent）。这需要真正的迭代，因为相关知识足够新，Claude 的训练数据对此覆盖有限。但经过足够的调校，生成器能够正确地构建智能体了。

### 更新框架的结果

为了测试更新后的框架，我使用以下提示生成了一个数字音频工作站（DAW），一个用于作曲、录制和混音的音乐制作程序：

> Build a fully featured DAW in the browser using the Web Audio API.

运行仍然漫长且昂贵，大约 4 小时，token 成本约 124 美元。
大部分时间花在了构建器上，它在没有 Opus 4.5 所需的冲刺分解的情况下连贯运行了两个多小时。
与之前的框架一样，规划器将一行提示扩展为完整的规格。从日志中，我可以看到生成器模型在规划应用和智能体设计、连接智能体以及在交给 QA 之前测试方面做得很好。
尽管如此，QA 智能体仍然发现了真实的缺口。在第一轮反馈中，它指出：

> This is a strong app with excellent design fidelity, solid AI agent, and good backend. The main failure point is Feature Completeness — while the app looks impressive and the AI integration works well, several core DAW features are display-only without interactive depth: clips can't be dragged/moved on the timeline, there are no instrument UI panels (synth knobs, drum pads), and no visual effect editors (EQ curves, compressor meters). These aren't edge cases — they're the core interactions that make a DAW usable, and the spec explicitly calls for them.

在第二轮反馈中，它又发现了几个功能性缺口：

> Remaining gaps:- Audio recording is still stub-only (button toggles but no mic capture)- Clip resize by edge drag and clip split not implemented- Effect visualizations are numeric sliders, not graphical (no EQ curve)

生成器在自行工作时仍然容易遗漏细节或用存根替代功能，而 QA 在捕捉这些最后一步的问题上仍然有价值，供生成器修复。
基于提示，我期望的是一个可以创建旋律、和声和鼓点模式，将它们编排成一首歌，并在过程中获得集成智能体帮助的程序。下面的视频展示了结果。
这个应用远非专业的音乐制作程序，智能体的歌曲创作能力显然还有很多需要改进的地方。此外，Claude 实际上听不到声音，这使得 QA 反馈循环在音乐品味方面的效果打了折扣。
但最终的应用具备了一个可用音乐制作程序的所有核心部件：在浏览器中运行的编曲视图、混音器和传输控制。除此之外，我能够完全通过提示拼凑出一段简短的歌曲片段：智能体设定了速度和调性，铺下旋律，构建了鼓轨，调整了混音器电平，并添加了混响。歌曲创作的核心原语是存在的，智能体可以自主驱动它们，使用工具端到端地创建一个简单的作品。你可能会说它还不完美——但它正在接近。

## 未来展望

随着模型持续改进，我们可以大致预期它们能够在更长时间内、更复杂的任务上工作。在某些情况下，这意味着围绕模型的脚手架随时间推移变得不那么重要，开发者可以等待下一个模型，看某些问题自行解决。另一方面，模型越好，就越有空间开发能够实现超出模型基线能力的复杂任务的框架。
考虑到这一点，这项工作中有几个值得传承的经验。对你正在构建的模型进行实验，在真实问题上阅读其追踪记录，并调校其性能以实现你期望的结果，这始终是良好实践。在处理更复杂的任务时，将任务分解并将专门的智能体应用于问题的各个方面，有时能带来提升空间。当新模型发布时，重新审视框架通常是良好实践——剥离不再承重的部分，添加新部分以实现之前可能无法实现的更大能力。
从这项工作中，我的信念是：随着模型改进，有趣的框架组合空间不会缩小。相反，它在移动，而 AI 工程师的有趣工作就是持续寻找下一个新颖的组合。

## 致谢

特别感谢 Mike Krieger、Michael Agaby、Justin Young、Jeremy Hadfield、David Hershey、Julius Tarng、Xiaoyi Zhang、Barry Zhang、Orowa Sidker、Michael Tingley、Ibrahim Madha、Martina Long 和 Canyon Robbins 对这项工作的贡献。
同时也感谢 Jake Eaton、Alyssa Leonard 和 Stef Sequeira 在塑造本文方面的帮助。

## 附录

规划器智能体生成的示例计划。

```
RetroForge - 2D Retro Game Maker

Overview
RetroForge is a web-based creative studio for designing and building 2D retro-style video games. It combines the nostalgic charm of classic 8-bit and 16-bit game aesthetics with modern, intuitive editing tools—enabling anyone from hobbyist creators to indie developers to bring their game ideas to life without writing traditional code.

The platform provides four integrated creative modules: a tile-based Level Editor for designing game worlds, a pixel-art Sprite Editor for crafting visual assets, a visual Entity Behavior system for defining game logic, and an instant Playable Test Mode for real-time gameplay testing. By weaving AI assistance throughout (powered by Claude), RetroForge accelerates the creative process—helping users generate sprites, design levels, and configure behaviors through natural language interaction.

RetroForge targets creators who love retro gaming aesthetics but want modern conveniences. Whether recreating the platformers, RPGs, or action games of their childhood, or inventing entirely new experiences within retro constraints, users can prototype rapidly, iterate visually, and share their creations with others.

Features
1. Project Dashboard & Management
The Project Dashboard is the home base for all creative work in RetroForge. Users need a clear, organized way to manage their game projects—creating new ones, returning to works-in-progress, and understanding what each project contains at a glance.

User Stories: As a user, I want to:

- Create a new game project with a name and description, so that I can begin designing my game
- See all my existing projects displayed as visual cards showing the project name, last modified date, and a thumbnail preview, so that I can quickly find and continue my work
- Open any project to enter the full game editor workspace, so that I can work on my game
- Delete projects I no longer need, with a confirmation dialog to prevent accidents, so that I can keep my workspace organized
- Duplicate an existing project as a starting point for a new game, so that I can reuse my previous work

Project Data Model: Each project contains:

Project metadata (name, description, created/modified timestamps)
Canvas settings (resolution: e.g., 256x224, 320x240, or 160x144)
Tile size configuration (8x8, 16x16, or 32x32 pixels)
Color palette selection 
All associated sprites, tilesets, levels, and entity definitions

...
```