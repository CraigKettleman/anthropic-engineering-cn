# 通过 Claude 3.5 Sonnet 在 SWE-bench Verified 上刷新纪录

我们的最新模型——升级版 Claude 3.5 Sonnet，在 SWE-bench Verified 这一软件工程评估中取得了 49% 的成绩，超越了此前最优模型 45% 的记录。本文将介绍我们围绕该模型构建的"智能体（Agent）"系统，旨在帮助开发者从 Claude 3.5 Sonnet 中获得最佳性能表现。

SWE-bench 是一个 AI 评估基准，用于衡量模型完成真实世界软件工程任务的能力。具体而言，它测试模型如何解决来自热门开源 Python 仓库的 GitHub Issue。对于基准中的每个任务，AI 模型会被提供一个已配置好的 Python 环境，以及该 Issue 被解决之前某个时间点的仓库检出副本（checkout，即本地工作副本）。模型需要理解、修改并测试代码，然后提交其提出的解决方案。

每个解决方案都会依据关闭原始 GitHub Issue 的 Pull Request 中的真实单元测试来评分。这检验了 AI 模型是否能够实现与 PR 原始作者相同的功能。

SWE-bench 并非孤立地评估 AI 模型，而是评估整个"智能体"系统。在这里，"智能体"指的是 AI 模型与其周围软件脚手架（Scaffolding）的组合。这个脚手架负责生成输入模型的提示词（Prompt）、解析模型输出以执行操作，以及管理交互循环——将模型上一步操作的结果纳入下一步的提示词中。即使使用相同的底层 AI 模型，智能体在 SWE-bench 上的表现也会因脚手架的不同而产生显著差异。

针对大语言模型编码能力的基准测试还有很多，但 SWE-bench 之所以日益受到关注，主要有以下几个原因：

- 它使用来自真实项目的实际工程任务，而非竞赛或面试类题目；
- 它尚未饱和——仍有很大的改进空间。目前还没有模型在 SWE-bench Verified 上突破 50% 的完成率（尽管更新后的 Claude 3.5 Sonnet 在撰写本文时已达到 49%）；
- 它评估的是整个"智能体"，而非孤立的模型。开源开发者和初创公司已在优化脚手架方面取得了巨大成功，在相同模型基础上大幅提升了性能。

需要注意的是，原始 SWE-bench 数据集中包含一些任务，如果不借助 GitHub Issue 之外的额外上下文信息（例如关于应返回的特定错误消息），这些任务是无法解决的。SWE-bench Verified 是 SWE-bench 的一个包含 500 道题的子集，经过人工审核确认其可解性，因此能够最清晰地衡量编码智能体的表现。本文将主要引用这一基准。

## 达到业界最优水平

### 使用工具的智能体（Tool Using Agent）

在为升级版 Claude 3.5 Sonnet 优化的智能体脚手架设计中，我们的设计哲学是尽可能将控制权交给语言模型本身，同时保持脚手架的精简。该智能体拥有一个提示词、一个用于执行 Bash 命令的 Bash 工具，以及一个用于查看和编辑文件和目录的编辑工具（Edit Tool）。我们持续采样，直到模型自行决定完成任务，或超过其 200k 的上下文长度限制。这种脚手架允许模型运用自身判断来解决问题，而非被硬编码为特定的模式或工作流。

提示词为模型概述了一种建议的方法，但对于此任务来说不会过长或过于详细。模型可以自由选择如何从一个步骤推进到下一步，而非遵循严格的离散式转换。如果您对 Token 消耗不太敏感，可以明确鼓励模型生成较长的响应。

以下代码展示了我们智能体脚手架中的提示词：

```
<uploaded_files>
{location}
</uploaded_files>
I've uploaded a python code repository in the directory {location} (not in /tmp/inputs). Consider the following PR description:

<pr_description>
{pr_description}
</pr_description>

Can you help me implement the necessary changes to the repository so that the requirements specified in the <pr_description> are met?
I've already taken care of all changes to any of the test files described in the <pr_description>. This means you DON'T have to modify the testing logic or any of the tests in any way!

Your task is to make the minimal changes to non-tests files in the {location} directory to ensure the <pr_description> is satisfied.

Follow these steps to resolve the issue:
1. As a first step, it might be a good idea to explore the repo to familiarize yourself with its structure.
2. Create a script to reproduce the error and execute it with `python <filename.py>` using the BashTool, to confirm the error
3. Edit the sourcecode of the repo to resolve the issue
4. Rerun your reproduce script and confirm that the error is fixed!
5. Think about edgecases and make sure your fix handles them as well

Your thinking should be thorough and so it's fine if it's very long.
```

模型的第一个工具用于执行 Bash 命令。其 Schema 很简单，只需要传入要在环境中运行的命令。然而，工具的描述承载了更多的信息量。它包含更详细的使用说明，包括转义输入、无网络访问权限以及如何在后台运行命令等内容。

接下来展示的是 Bash 工具的规格说明：

```
{
   "name": "bash",
   "description": "Run commands in a bash shell\n
* When invoking this tool, the contents of the \"command\" parameter does NOT need to be XML-escaped.\n
* You don't have access to the internet via this tool.\n
* You do have access to a mirror of common linux and python packages via apt and pip.\n
* State is persistent across command calls and discussions with the user.\n
* To inspect a particular line range of a file, e.g. lines 10-25, try 'sed -n 10,25p /path/to/the/file'.\n
* Please avoid commands that may produce a very large amount of output.\n
* Please run long lived commands in the background, e.g. 'sleep 10 &' or start a server in the background.",
   "input_schema": {
       "type": "object",
       "properties": {
           "command": {
               "type": "string",
               "description": "The bash command to run."
           }
       },
       "required": ["command"]
   }
}
```

模型的第二个工具（编辑工具）要复杂得多，包含了模型查看、创建和编辑文件所需的全部功能。同样，我们的工具描述中包含了模型使用该工具的详细信息。

我们在工具描述和规格的设计上投入了大量精力，覆盖了各种智能体任务场景。我们进行了测试，以发现模型可能误解规格说明或使用工具时可能出现的各种陷阱，然后编辑描述来预先解决这些问题。我们认为，应该像为人类设计工具界面那样投入大量精力来为模型设计工具接口。

以下代码展示了编辑工具的描述：

```
{
   "name": "str_replace_editor",
   "description": "Custom editing tool for viewing, creating and editing files\n
* State is persistent across command calls and discussions with the user\n
* If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep\n
* The `create` command cannot be used if the specified `path` already exists as a file\n
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>` \n
* The `undo_edit` command will revert the last edit made to the file at `path`\n
\n
Notes for using the `str_replace` command:\n
* The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!\n
* If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique\n
* The `new_str` parameter should contain the edited lines that should replace the `old_str`",
...
```

我们提升性能的一个方法是让工具具备"防错性"。例如，有时在智能体离开根目录后，模型可能会搞错相对文件路径。为了防止这种情况，我们直接要求工具始终使用绝对路径。

我们试验了几种不同的文件编辑策略，最终发现字符串替换（String Replacement）的可靠性最高——模型指定要替换的 `old_str` 和替换后的 `new_str`。只有在 `old_str` 恰好匹配一处时才会执行替换。如果匹配多于一处或无匹配，模型会收到相应的错误提示以供重试。

编辑工具的规格说明如下：

```
...
   "input_schema": {
       "type": "object",
       "properties": {
           "command": {
               "type": "string",
               "enum": ["view", "create", "str_replace", "insert", "undo_edit"],
               "description": "The commands to run. Allowed options are: `view`, `create`, `str_replace`, `insert`, `undo_edit`."
           },
           "file_text": {
               "description": "Required parameter of `create` command, with the content of the file to be created.",
               "type": "string"
           },
           "insert_line": {
               "description": "Required parameter of `insert` command. The `new_str` will be inserted AFTER the line `insert_line` of `path`.",
               "type": "integer"
           },
           "new_str": {
               "description": "Required parameter of `str_replace` command containing the new string. Required parameter of `insert` command containing the string to insert.",
               "type": "string"
           },
           "old_str": {
               "description": "Required parameter of `str_replace` command containing the string in `path` to replace.",
               "type": "string"
           },
           "path": {
               "description": "Absolute path to file or directory, e.g. `/repo/file.py` or `/repo`.",
               "type": "string"
           },
           "view_range": {
               "description": "Optional parameter of `view` command when `path` points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, -1]` shows all lines from `start_line` to the end of the file.",
               "items": {
                   "type": "integer"
               },
               "type": "array"
           }
       },
       "required": ["command", "path"]
   }
}
```

## 结果

总体而言，升级版 Claude 3.5 Sonnet 在推理、编码和数学能力上都优于我们此前的模型以及此前的业界最优模型。它还展示了更强的智能体能力：工具和脚手架帮助将这些提升的能力发挥到了最佳水平。

## 智能体行为示例

在运行基准测试时，我们使用 SWE-Agent 框架作为智能体代码的基础。在下方的日志中，我们将智能体的文本输出、工具调用和工具响应分别渲染为 THOUGHT（思考）、ACTION（动作）和 OBSERVATION（观察），尽管我们并未将模型限制为固定的输出顺序。

以下代码块将展示 Sonnet 3.5 解决一个 SWE-bench 问题的典型过程。

在第一个代码块中，您可以看到提供给模型的初始提示词的一部分，其中 `{pr_description}` 已填充为 SWE-bench 任务中的真实值。重要的是，该任务包含了重现问题的步骤，这将为模型提供一个有价值的调查起点。

```
<uploaded_files>
/repo
</uploaded_files>
I've uploaded a python code repository in the directory /repo (not in /tmp/inputs). Consider the following PR description:

<pr_description>
linear_model.RidgeClassifierCV's Parameter store_cv_values issue
#### Description
Parameter store_cv_values error on sklearn.linear_model.RidgeClassifierCV

#### Steps/Code to Reproduce
import numpy as np
from sklearn import linear_model as lm

#test database
n = 100
x = np.random.randn(n, 30)
y = np.random.normal(size = n)

rr = lm.RidgeClassifierCV(alphas = np.arange(0.1, 1000, 0.1), normalize = True, 
                                         store_cv_values = True).fit(x, y)

#### Expected Results
Expected to get the usual ridge regression model output, keeping the cross validation predictions as attribute.

#### Actual Results
TypeError: __init__() got an unexpected keyword argument 'store_cv_values'

lm.RidgeClassifierCV actually has no parameter store_cv_values, even though some attributes depends on it.
```

模型作出响应，首先使用编辑工具查看仓库结构。您可以在 THOUGHT 和 ACTION 下看到模型的文本输出和工具调用参数，在 OBSERVATION 下看到工具输出的一部分：

```
THOUGHT:
I'll help you implement the changes to satisfy the PR description. Let's follow the steps you outlined.

1. First, let's explore the repo structure:
ACTION (str_replace_editor):
command:
view

path:
/repo

OBSERVATION:
Here's the files and directories up to 2 levels deep in /repo, excluding hidden items:
/repo
/repo/PULL_REQUEST_TEMPLATE.md
/repo/ISSUE_TEMPLATE.md
/repo/sklearn
/repo/sklearn/decomposition
/repo/sklearn/kernel_ridge.py
/repo/sklearn/model_selection
/repo/sklearn/covariance
/repo/sklearn/cluster
/repo/sklearn/base.py
/repo/sklearn/dummy.py
/repo/sklearn/naive_bayes.py
...
```

模型对仓库结构有了更好的了解后，使用编辑工具创建一个新脚本，用于重现问题并测试修复：

```
THOUGHT:
Based on the repository structure, we'll need to modify the Ridge Classifier in the `sklearn/linear_model` directory.

Let's create a script to reproduce the error:
ACTION (str_replace_editor):
command:
create

path:
/repo/reproduce_error.py

file_text:
import numpy as np
from sklearn import linear_model as lm

#test database
n = 100
x = np.random.randn(n, 30)
y = np.random.normal(size = n)

rr = lm.RidgeClassifierCV(alphas=np.arange(0.1, 1000, 0.1), normalize=True, 
                         store_cv_values=True).fit(x, y)

OBSERVATION:
File created successfully at: /repo/reproduce_error.py
```

然后模型使用 Bash 工具执行它编写的脚本，成功重现了任务中的问题：

```
THOUGHT:
Let's verify that we can reproduce the error:
ACTION (bash):
command:
python3 /repo/reproduce_error.py

OBSERVATION:
Traceback (most recent call last):
  File "/repo/reproduce_error.py", line 10, in <module>
    store_cv_values=True).fit(x, y)
TypeError: __init__() got an unexpected keyword argument 'store_cv_values'
```

从这里开始，模型使用编辑工具修改仓库中的源代码，并重新运行脚本验证修改是否解决了问题：

```
THOUGHT:
The error is reproducible. Looking at the code, I can see that the issue is that while the `RidgeClassifierCV` class inherits from `_BaseRidgeCV`, it fails to pass the `store_cv_values` parameter from its constructor through to the base class constructor.

Let's fix this:
ACTION (str_replace_editor):
command:
str_replace

path:
/repo/sklearn/linear_model/ridge.py

old_str:
    def __init__(self, alphas=(0.1, 1.0, 10.0), fit_intercept=True,
                 normalize=False, scoring=None, cv=None, class_weight=None):
        super(RidgeClassifierCV, self).__init__(
            alphas=alphas, fit_intercept=fit_intercept, normalize=normalize,
            scoring=scoring, cv=cv)
        self.class_weight = class_weight

new_str:
    def __init__(self, alphas=(0.1, 1.0, 10.0), fit_intercept=True,
                 normalize=False, scoring=None, cv=None, class_weight=None,
                 store_cv_values=False):
        super(RidgeClassifierCV, self).__init__(
            alphas=alphas, fit_intercept=fit_intercept, normalize=normalize,
            scoring=scoring, cv=cv, store_cv_values=store_cv_values)
        self.class_weight = class_weight
```

在这个特定示例中，模型工作了 12 步后决定提交解决方案。任务的测试随后成功运行，验证了模型的方案确实解决了问题。有些任务中模型需要超过 100 轮才能提交解决方案；而在另一些任务中，模型一直尝试直到用尽上下文长度。

通过对比升级版 Claude 3.5 Sonnet 与旧模型的尝试记录，我们发现升级版 3.5 Sonnet 更善于自我纠正。它还展示了一种尝试多种不同解决方案的能力，而不是反复卡在同一个错误上。

## 挑战

SWE-bench Verified 是一个强大的评估基准，但运行起来也比简单的单轮评估更为复杂。以下是我们使用它时面临的一些挑战——其他 AI 开发者可能也会遇到类似的问题。

- **运行时间长且 Token 成本高。** 上面的示例来自一个在 12 步内成功完成的案例。然而，许多成功的运行需要数百轮模型才能解决，消耗超过 10 万 Token。升级版 Claude 3.5 Sonnet 非常执着：只要给它足够的时间，它通常能够找到解决问题的方法，但这可能代价不菲；

- **评分问题。** 在检查失败的任务时，我们发现有些情况下模型的行为是正确的，但存在环境配置问题，或安装补丁被重复应用的问题。解决这些系统层面的问题对于准确评估 AI 智能体的性能至关重要。

- **隐藏测试。** 由于模型无法看到用于评分的测试用例，它常常在任务实际失败时"认为"自己已经成功了。其中一些失败是因为模型在错误的抽象层次上解决了问题（施加了创可贴式的修复，而非进行更深层的重构）。另一些失败则不那么公平：模型确实解决了问题，但其方案与原始任务的单元测试不匹配。

- **多模态。** 尽管升级版 Claude 3.5 Sonnet 具备出色的视觉和多模态能力，我们并未实现让它查看保存到文件系统或以 URL 引用的文件的功能。这使得调试某些任务（特别是来自 Matplotlib 的任务）尤为困难，也容易导致模型产生幻觉。这里肯定有唾手可得的改进机会——SWE-bench 已经推出了一个新的专注于多模态任务的评估。我们期待看到开发者在不久的将来使用 Claude 在该评估中取得更高的分数。

升级版 Claude 3.5 Sonnet 在 SWE-bench Verified 上取得了 49% 的成绩，超越了此前的业界最优水平（45%），而这一切仅凭一个简洁的提示词和两个通用工具实现。我们有信心，使用新版 Claude 3.5 Sonnet 的开发者将很快找到更新、更好的方法，在我们初步展示的基础上进一步提升 SWE-bench 的成绩。

## 致谢

Erik Schluntz 优化了 SWE-bench 智能体并撰写了本博文。Simon Biggs、Dawn Drain 和 Eric Christiansen 协助实现了基准测试。Shauna Kravec、Dawn Drain、Felipe Rosso、Nova DasSarma、Ven Chandrasekaran 以及众多其他人为训练 Claude 3.5 Sonnet 成为出色的智能体编码能手做出了贡献。