# Best practices for Claude Code


## On this page

- Give Claude a way to verify its work
- Explore first, then plan, then code
- Provide specific context in your promptsProvide rich content
- Provide rich content
- Configure your environmentWrite an effective CLAUDE.mdConfigure permissionsUse CLI toolsConnect MCP serversSet up hooksCreate skillsCreate custom subagentsInstall plugins
- Write an effective CLAUDE.md
- Configure permissions
- Use CLI tools
- Connect MCP servers
- Set up hooks
- Create skills
- Create custom subagents
- Install plugins
- Communicate effectivelyAsk codebase questionsLet Claude interview you
- Ask codebase questions
- Let Claude interview you
- Manage your sessionCourse-correct early and oftenManage context aggressivelyUse subagents for investigationRewind with checkpointsResume conversations
- Course-correct early and often
- Manage context aggressively
- Use subagents for investigation
- Rewind with checkpoints
- Resume conversations
- Automate and scaleRun non-interactive modeRun multiple Claude sessionsFan out across filesRun autonomously with auto modeAdd an adversarial review step
- Run non-interactive mode
- Run multiple Claude sessions
- Fan out across files
- Run autonomously with auto mode
- Add an adversarial review step
- Avoid common failure patterns
- Develop your intuition
- Related resources

# Best practices for Claude Code

Tips and patterns for getting the most out of Claude Code, from configuring your environment to scaling across parallel sessions.

## ​Give Claude a way to verify its work

- In one prompt: ask Claude to run the check and iterate in the same message, as in the table above.
- Across a session: set the check as a/goalcondition. A separate evaluator re-checks it after every turn and Claude keeps working until it holds.
/goal
- As a deterministic gate: aStop hookruns your check as a script and blocks the turn from ending until it passes. Claude Code overrides the hook and ends the turn after 8 consecutive blocks.
- By a second opinion: averification subagentor adynamic workflowthat checks its own findings has a fresh model try to refute the result, so the agent doing the work isn’t the one grading it.
/goal

## ​Explore first, then plan, then code

Explore

```
read /src/auth and understand how we handle sessions and login.also look at how we manage environment variables for secrets.
```

read /src/auth and understand how we handle sessions and login.also look at how we manage environment variables for secrets.
Plan

```
I want to add Google OAuth. What files need to change?What's the session flow? Create a plan.
```

I want to add Google OAuth. What files need to change?What's the session flow? Create a plan.
Ctrl+G
Implement

```
implement the OAuth flow from your plan. write tests for thecallback handler, run the test suite and fix any failures.
```

implement the OAuth flow from your plan. write tests for thecallback handler, run the test suite and fix any failures.
Commit

```
commit with a descriptive message and open a PR
```

commit with a descriptive message and open a PR

## ​Provide specific context in your prompts

"what would you improve in this file?"

### ​Provide rich content

@
- Reference files with@instead of describing where code lives. Claude reads the file before responding.
@
- Paste images directly. Copy/paste or drag and drop images into the prompt.
- Give URLsfor documentation and API references. Use/permissionsto allowlist frequently-used domains.
/permissions
- Pipe in databy runningcat error.log | claudeto send file contents directly.
cat error.log | claude
- Let Claude fetch what it needs. Tell Claude to pull context itself using Bash commands, MCP tools, or by reading files.

## ​Configure your environment


### ​Write an effective CLAUDE.md

/init
/init

```
# Code style-Use ES modules (import/export) syntax, not CommonJS (require)-Destructure imports when possible (eg. import { foo } from 'bar')# Workflow-Be sure to typecheck when you're done making a series of code changes-Prefer running single tests, and not the whole test suite, for performance
```

# Code style-Use ES modules (import/export) syntax, not CommonJS (require)-Destructure imports when possible (eg. import { foo } from 'bar')# Workflow-Be sure to typecheck when you're done making a series of code changes-Prefer running single tests, and not the whole test suite, for performance
@path/to/import

```
See @README.md for project overview and @package.json for available npm commands.# Additional Instructions-Git workflow: @docs/git-instructions.md-Personal overrides: @~/.claude/my-project-instructions.md
```

See @README.md for project overview and @package.json for available npm commands.# Additional Instructions-Git workflow: @docs/git-instructions.md-Personal overrides: @~/.claude/my-project-instructions.md
- Home folder (~/.claude/CLAUDE.md): applies to all Claude sessions
~/.claude/CLAUDE.md
- Project root (./CLAUDE.md): check into git to share with your team
./CLAUDE.md
- Project root (./CLAUDE.local.md): personal project-specific notes; add this file to your.gitignoreso it isn’t shared with your team
./CLAUDE.local.md
.gitignore
- Parent directories: useful for monorepos where bothroot/CLAUDE.mdandroot/foo/CLAUDE.mdare pulled in automatically
root/CLAUDE.md
root/foo/CLAUDE.md
- Child directories: Claude pulls in child CLAUDE.md files on demand when it reads a file in those directories

### ​Configure permissions

/permissions
/sandbox
- Auto mode: a separate classifier model reviews commands and blocks only what looks risky: scope escalation, unknown infrastructure, or hostile-content-driven actions. Best when you trust the general direction of a task but don’t want to click through every step
- Permission allowlists: permit specific tools you know are safe, likenpm run lintorgit commit
npm run lint
git commit
- Sandboxing: enable OS-level isolation that restricts filesystem and network access, allowing Claude to work more freely within defined boundaries

### ​Use CLI tools

gh
aws
gcloud
sentry-cli
gh
gh
Use 'foo-cli-tool --help' to learn about foo tool, then use it to solve A, B, C.

### ​Connect MCP servers

claude mcp add

### ​Set up hooks

.claude/settings.json
/hooks

### ​Create skills

SKILL.md
.claude/skills/
/skill-name
SKILL.md
.claude/skills/

```
---name:api-conventionsdescription:REST API design conventions for our services---# API Conventions-Use kebab-case for URL paths-Use camelCase for JSON properties-Always include pagination for list endpoints-Version APIs in the URL path (/v1/, /v2/)
```

---name:api-conventionsdescription:REST API design conventions for our services---# API Conventions-Use kebab-case for URL paths-Use camelCase for JSON properties-Always include pagination for list endpoints-Version APIs in the URL path (/v1/, /v2/)

```
---name:fix-issuedescription:Fix a GitHub issuedisable-model-invocation:true---Analyze and fix the GitHub issue: $ARGUMENTS.1.Use`gh issue view`to get the issue details2.Understand the problem described in the issue3.Search the codebase for relevant files4.Implement the necessary changes to fix the issue5.Write and run tests to verify the fix6.Ensure code passes linting and type checking7.Create a descriptive commit message8.Push and create a PR
```

---name:fix-issuedescription:Fix a GitHub issuedisable-model-invocation:true---Analyze and fix the GitHub issue: $ARGUMENTS.1.Use`gh issue view`to get the issue details2.Understand the problem described in the issue3.Search the codebase for relevant files4.Implement the necessary changes to fix the issue5.Write and run tests to verify the fix6.Ensure code passes linting and type checking7.Create a descriptive commit message8.Push and create a PR
/fix-issue 1234
disable-model-invocation: true

### ​Create custom subagents

.claude/agents/

```
---name:security-reviewerdescription:Reviews code for security vulnerabilitiestools:Read, Grep, Glob, Bashmodel:opus---You are a senior security engineer. Review code for:-Injection vulnerabilities (SQL, XSS, command injection)-Authentication and authorization flaws-Secrets or credentials in code-Insecure data handlingProvide specific line references and suggested fixes.
```

---name:security-reviewerdescription:Reviews code for security vulnerabilitiestools:Read, Grep, Glob, Bashmodel:opus---You are a senior security engineer. Review code for:-Injection vulnerabilities (SQL, XSS, command injection)-Authentication and authorization flaws-Secrets or credentials in code-Insecure data handlingProvide specific line references and suggested fixes.

### ​Install plugins

/plugin

## ​Communicate effectively


### ​Ask codebase questions

- How does logging work?
- How do I make a new API endpoint?
- What doesasync move { ... }do on line 134 offoo.rs?
async move { ... }
foo.rs
- What edge cases doesCustomerOnboardingFlowImplhandle?
CustomerOnboardingFlowImpl
- Why does this code callfoo()instead ofbar()on line 333?
foo()
bar()

### ​Let Claude interview you

AskUserQuestion

```
I want to build [brief description]. Interview me in detail using the AskUserQuestion tool.Ask about technical implementation, UI/UX, edge cases, concerns, and tradeoffs. Don't ask obvious questions, dig into the hard parts I might not have considered.Keep interviewing until we've covered everything, then write a complete spec to SPEC.md.
```

I want to build [brief description]. Interview me in detail using the AskUserQuestion tool.Ask about technical implementation, UI/UX, edge cases, concerns, and tradeoffs. Don't ask obvious questions, dig into the hard parts I might not have considered.Keep interviewing until we've covered everything, then write a complete spec to SPEC.md.

## ​Manage your session


### ​Course-correct early and often

- Esc: stop Claude mid-action with theEsckey. Context is preserved, so you can redirect.
Esc
Esc
- Esc + Escor/rewind: pressEsctwice or run/rewindto open the rewind menu and restore previous conversation and code state, or summarize from a selected message.
Esc + Esc
/rewind
Esc
/rewind
- "Undo that": have Claude revert its changes.
"Undo that"
- /clear: reset context between unrelated tasks. Long sessions with irrelevant context can reduce performance.
/clear
/clear

### ​Manage context aggressively

/clear
- Use/clearfrequently between tasks to reset the context window entirely
/clear
- When auto compaction triggers, Claude summarizes what matters most, including code patterns, file states, and key decisions
- For more control, run/compact <instructions>, like/compact Focus on the API changes
/compact <instructions>
/compact Focus on the API changes
- To compact only part of the conversation, useEsc + Escor/rewind, select a message checkpoint, and chooseSummarize from hereorSummarize up to here. The first condenses messages from that point forward while keeping earlier context intact; the second condenses earlier messages while keeping recent ones in full. SeeRestore vs. summarize.
Esc + Esc
/rewind
- Customize compaction behavior in CLAUDE.md with instructions like"When compacting, always preserve the full list of modified files and any test commands"to ensure critical context survives summarization
"When compacting, always preserve the full list of modified files and any test commands"
- For quick questions that don’t need to stay in context, use/btw. The answer appears in a dismissible overlay and never enters conversation history, so you can check a detail without growing context.
/btw

### ​Use subagents for investigation

"use subagents to investigate X"

```
Use subagents to investigate how our authentication system handles tokenrefresh, and whether we have any existing OAuth utilities I should reuse.
```

Use subagents to investigate how our authentication system handles tokenrefresh, and whether we have any existing OAuth utilities I should reuse.

```
use a subagent to review this code for edge cases
```

use a subagent to review this code for edge cases

### ​Rewind with checkpoints

Escape
/rewind

### ​Resume conversations

/rename
claude --continue
claude --resume
oauth-migration

## ​Automate and scale


### ​Run non-interactive mode

claude -p "prompt"
--output-format stream-json --verbose
claude -p "your prompt"

```
# One-off queriesclaude-p"Explain what this project does"# Structured output for scriptsclaude-p"List all API endpoints"--output-formatjson# Streaming for real-time processingclaude-p"Analyze this log file"--output-formatstream-json--verbose
```

# One-off queriesclaude-p"Explain what this project does"# Structured output for scriptsclaude-p"List all API endpoints"--output-formatjson# Streaming for real-time processingclaude-p"Analyze this log file"--output-formatstream-json--verbose

### ​Run multiple Claude sessions

- Worktrees: run separate CLI sessions in isolated git checkouts so edits don’t collide
- Desktop app: manage multiple local sessions visually, each in its own worktree
- Claude Code on the web: run sessions on Anthropic-managed cloud infrastructure in isolated VMs
- Agent teams: automated coordination of multiple sessions with shared tasks, messaging, and a team lead
Implement a rate limiter for our API endpoints
Review the rate limiter implementation in @src/middleware/rateLimiter.ts. Look for edge cases, race conditions, and consistency with our existing middleware patterns.
Here's the review feedback: [Session B output]. Address these issues.

### ​Fan out across files

claude -p
--allowedTools
Generate a task list
list all 2,000 Python files that need migrating
Write a script to loop through the list

```
forfilein$(catfiles.txt);doclaude-p"Migrate$filefrom React to Vue. Return OK or FAIL."\--allowedTools"Edit,Bash(git commit *)"done
```

forfilein$(catfiles.txt);doclaude-p"Migrate$filefrom React to Vue. Return OK or FAIL."\--allowedTools"Edit,Bash(git commit *)"done
Test on a few files, then run at scale
--allowedTools

```
claude-p"<your prompt>"--output-formatjson|your_command
```

claude-p"<your prompt>"--output-formatjson|your_command
--verbose

### ​Run autonomously with auto mode


```
claude--permission-modeauto-p"fix all lint errors"
```

claude--permission-modeauto-p"fix all lint errors"
-p

### ​Add an adversarial review step

/code-review

```
Use a subagent to review the rate limiter diff against PLAN.md. Check thatevery requirement is implemented, the listed edge cases have tests, andnothing outside the task's scope changed. Report gaps, not style preferences.
```

Use a subagent to review the rate limiter diff against PLAN.md. Check thatevery requirement is implemented, the listed edge cases have tests, andnothing outside the task's scope changed. Report gaps, not style preferences.

## ​Avoid common failure patterns

- The kitchen sink session.You start with one task, then ask Claude something unrelated, then go back to the first task. Context is full of irrelevant information.Fix:/clearbetween unrelated tasks.

> Fix:/clearbetween unrelated tasks.

/clear
- Correcting over and over.Claude does something wrong, you correct it, it’s still wrong, you correct again. Context is polluted with failed approaches.Fix: After two failed corrections,/clearand write a better initial prompt incorporating what you learned.

> Fix: After two failed corrections,/clearand write a better initial prompt incorporating what you learned.

/clear
- The over-specified CLAUDE.md.If your CLAUDE.md is too long, Claude ignores half of it because important rules get lost in the noise.Fix: Ruthlessly prune. If Claude already does something correctly without the instruction, delete it or convert it to a hook.

> Fix: Ruthlessly prune. If Claude already does something correctly without the instruction, delete it or convert it to a hook.

- The trust-then-verify gap.Claude produces a plausible-looking implementation that doesn’t handle edge cases.Fix: Always provide verification (tests, scripts, screenshots). If you can’t verify it, don’t ship it.

> Fix: Always provide verification (tests, scripts, screenshots). If you can’t verify it, don’t ship it.

- The infinite exploration.You ask Claude to “investigate” something without scoping it. Claude reads hundreds of files, filling the context.Fix: Scope investigations narrowly or use subagents so the exploration doesn’t consume your main context.

> Fix: Scope investigations narrowly or use subagents so the exploration doesn’t consume your main context.


## ​Develop your intuition


## ​Related resources

- How Claude Code works: the agentic loop, tools, and context management
- Extend Claude Code: skills, hooks, MCP, subagents, and plugins
- Common workflows: step-by-step recipes for debugging, testing, PRs, and more
- CLAUDE.md: store project conventions and persistent context
Was this page helpful?