# 通过 MCP 执行代码：构建更高效的智能体

模型上下文协议（Model Context Protocol，MCP）是一个将 AI 智能体（Agent）连接到外部系统的开放标准。传统上，将智能体与工具和数据连接需要为每一对组合进行自定义集成，这导致了碎片化和重复工作，使得真正互联的系统难以扩展。MCP 提供了一种通用协议——开发者只需在智能体中实现一次 MCP，即可解锁整个集成生态系统。

自 2024 年 11 月推出 MCP 以来，其采用速度非常快：社区已构建了数千个 MCP 服务器，所有主流编程语言都有可用的 SDK，业界已将 MCP 作为连接智能体与工具和数据的事实标准。

如今，开发者日常构建的智能体可以通过数十个 MCP 服务器访问数百甚至数千个工具。然而，随着连接工具数量的增加，预先加载所有工具定义并通过上下文窗口传递中间结果会减慢智能体的速度并增加成本。

在本文中，我们将探讨代码执行如何使智能体更高效地与 MCP 服务器交互，在使用更少 token 的同时处理更多工具。

## 工具消耗过多 token 会降低智能体效率

随着 MCP 使用规模的扩大，有两种常见模式会增加智能体的成本和延迟：
- 工具定义过载上下文窗口；
- 中间工具结果消耗额外的 token。

### 1. 工具定义过载上下文窗口

大多数 MCP 客户端会将所有工具定义预先直接加载到上下文中，使用直接的工具调用语法将其暴露给模型。这些工具定义可能如下所示：

```
gdrive.getDocument
     Description: Retrieves a document from Google Drive
     Parameters:
                documentId (required, string): The ID of the document to retrieve
                fields (optional, string): Specific fields to return
     Returns: Document object with title, body content, metadata, permissions, etc.
```

gdrive.getDocument
     Description: Retrieves a document from Google Drive
     Parameters:
                documentId (required, string): The ID of the document to retrieve
                fields (optional, string): Specific fields to return
     Returns: Document object with title, body content, metadata, permissions, etc.

```
salesforce.updateRecord
    Description: Updates a record in Salesforce
    Parameters:
               objectType (required, string): Type of Salesforce object (Lead, Contact,      Account, etc.)
               recordId (required, string): The ID of the record to update
               data (required, object): Fields to update with their new values
     Returns: Updated record object with confirmation
```

salesforce.updateRecord
    Description: Updates a record in Salesforce
    Parameters:
               objectType (required, string): Type of Salesforce object (Lead, Contact,      Account, etc.)
               recordId (required, string): The ID of the record to update
               data (required, object): Fields to update with their new values
     Returns: Updated record object with confirmation

工具描述占用更多的上下文窗口空间，增加响应时间和成本。在智能体连接到数千个工具的情况下，它们在读取请求之前就需要处理数十万个 token。

### 2. 中间工具结果消耗额外的 token

大多数 MCP 客户端允许模型直接调用 MCP 工具。例如，你可以问你的智能体："从 Google Drive 下载我的会议记录，并将其附加到 Salesforce 线索上。"

模型将进行如下调用：

```
TOOL CALL: gdrive.getDocument(documentId: "abc123")
        → returns "Discussed Q4 goals...\n[full transcript text]"
           (loaded into model context)

TOOL CALL: salesforce.updateRecord(
			objectType: "SalesMeeting",
			recordId: "00Q5f000001abcXYZ",
  			data: { "Notes": "Discussed Q4 goals...\n[full transcript text written out]" }
		)
		(model needs to write entire transcript into context again)
```

TOOL CALL: gdrive.getDocument(documentId: "abc123")
        → returns "Discussed Q4 goals...\n[full transcript text]"
           (loaded into model context)

TOOL CALL: salesforce.updateRecord(
			objectType: "SalesMeeting",
			recordId: "00Q5f000001abcXYZ",
  			data: { "Notes": "Discussed Q4 goals...\n[full transcript text written out]" }
		)
		(model needs to write entire transcript into context again)

每个中间结果都必须经过模型。在这个示例中，完整的通话记录流经了两次。对于一场 2 小时的销售会议，这可能意味着要额外处理 50,000 个 token。更大的文档甚至可能超出上下文窗口的限制，导致工作流程中断。

对于大型文档或复杂数据结构，模型在工具调用之间复制数据时更容易出错。

## 通过 MCP 执行代码提高上下文效率

随着代码执行环境在智能体中越来越普遍，一种解决方案是将 MCP 服务器呈现为代码 API 而非直接的工具调用。智能体随后可以编写代码与 MCP 服务器交互。这种方法解决了两个挑战：智能体可以仅加载所需的工具，并在执行环境中处理数据后再将结果返回给模型。

有多种方法可以实现这一点。一种方法是从连接的 MCP 服务器生成所有可用工具的文件树。以下是使用 TypeScript 的实现：

```
servers
├── google-drive
│   ├── getDocument.ts
│   ├── ... (other tools)
│   └── index.ts
├── salesforce
│   ├── updateRecord.ts
│   ├── ... (other tools)
│   └── index.ts
└── ... (other servers)
```

servers
├── google-drive
│   ├── getDocument.ts
│   ├── ... (other tools)
│   └── index.ts
├── salesforce
│   ├── updateRecord.ts
│   ├── ... (other tools)
│   └── index.ts
└── ... (other servers)

然后每个工具对应一个文件，类似这样：

```
// ./servers/google-drive/getDocument.ts
import { callMCPTool } from "../../../client.js";

interface GetDocumentInput {
  documentId: string;
}

interface GetDocumentResponse {
  content: string;
}

/* Read a document from Google Drive */
export async function getDocument(input: GetDocumentInput): Promise<GetDocumentResponse> {
  return callMCPTool<GetDocumentResponse>('google_drive__get_document', input);
}
```

// ./servers/google-drive/getDocument.ts
import { callMCPTool } from "../../../client.js";

interface GetDocumentInput {
  documentId: string;
}

interface GetDocumentResponse {
  content: string;
}

/* Read a document from Google Drive */
export async function getDocument(input: GetDocumentInput): Promise<GetDocumentResponse> {
  return callMCPTool<GetDocumentResponse>('google_drive__get_document', input);
}

上面从 Google Drive 到 Salesforce 的示例变成了以下代码：

```
// Read transcript from Google Docs and add to Salesforce prospect
import * as gdrive from './servers/google-drive';
import * as salesforce from './servers/salesforce';

const transcript = (await gdrive.getDocument({ documentId: 'abc123' })).content;
await salesforce.updateRecord({
  objectType: 'SalesMeeting',
  recordId: '00Q5f000001abcXYZ',
  data: { Notes: transcript }
});
```

// Read transcript from Google Docs and add to Salesforce prospect
import * as gdrive from './servers/google-drive';
import * as salesforce from './servers/salesforce';

const transcript = (await gdrive.getDocument({ documentId: 'abc123' })).content;
await salesforce.updateRecord({
  objectType: 'SalesMeeting',
  recordId: '00Q5f000001abcXYZ',
  data: { Notes: transcript }
});

智能体通过探索文件系统来发现工具：列出 `./servers/` 目录以找到可用的服务器（如 `google-drive` 和 `salesforce`），然后读取所需的特定工具文件（如 `getDocument.ts` 和 `updateRecord.ts`）来了解每个工具的接口。这使智能体可以仅加载当前任务所需的定义。这将 token 使用量从 150,000 个减少到 2,000 个——时间和成本节省了 98.7%。

Cloudflare 发布了类似的发现，将通过 MCP 执行代码称为"代码模式（Code Mode）"。核心洞察是一样的：LLM 擅长编写代码，开发者应该利用这一优势来构建更高效地与 MCP 服务器交互的智能体。

## 通过 MCP 执行代码的优势

通过 MCP 执行代码使智能体能够更高效地使用上下文，包括按需加载工具、在数据到达模型之前进行过滤，以及在单个步骤中执行复杂逻辑。使用这种方法还有安全性和状态管理方面的优势。

### 渐进式披露

模型擅长浏览文件系统。将工具以代码形式呈现在文件系统上，允许模型按需读取工具定义，而不是预先全部读取。

或者，可以在服务器上添加 `search_tools` 工具来查找相关定义。例如，当使用上面假设的 Salesforce 服务器时，智能体搜索 "salesforce" 并仅加载当前任务所需的那些工具。在 `search_tools` 工具中包含一个详细级别参数，允许智能体选择所需的详细程度（如仅名称、名称和描述，或包含 schema 的完整定义），这也有助于智能体节省上下文并高效地查找工具。

### 上下文高效的工具结果

在处理大型数据集时，智能体可以在代码中过滤和转换结果后再返回。以获取一个包含 10,000 行的电子表格为例：

```
// Without code execution - all rows flow through context
TOOL CALL: gdrive.getSheet(sheetId: 'abc123')
        → returns 10,000 rows in context to filter manually

// With code execution - filter in the execution environment
const allRows = await gdrive.getSheet({ sheetId: 'abc123' });
const pendingOrders = allRows.filter(row => 
  row["Status"] === 'pending'
);
console.log(`Found ${pendingOrders.length} pending orders`);
console.log(pendingOrders.slice(0, 5)); // Only log first 5 for review
```

// Without code execution - all rows flow through context
TOOL CALL: gdrive.getSheet(sheetId: 'abc123')
        → returns 10,000 rows in context to filter manually

// With code execution - filter in the execution environment
const allRows = await gdrive.getSheet({ sheetId: 'abc123' });
const pendingOrders = allRows.filter(row => 
  row["Status"] === 'pending'
);
console.log(`Found ${pendingOrders.length} pending orders`);
console.log(pendingOrders.slice(0, 5)); // Only log first 5 for review

智能体看到的是五行而不是 10,000 行。类似的模式适用于聚合、跨多个数据源的联接或提取特定字段——所有这些都不会使上下文窗口膨胀。

#### 更强大且上下文高效的控制流

循环、条件判断和错误处理可以用熟悉的代码模式完成，而不是链接单独的工具调用。例如，如果你需要在 Slack 中收到部署通知，智能体可以编写：

```
let found = false;
while (!found) {
  const messages = await slack.getChannelHistory({ channel: 'C123456' });
  found = messages.some(m => m.text.includes('deployment complete'));
  if (!found) await new Promise(r => setTimeout(r, 5000));
}
console.log('Deployment notification received');
```

let found = false;
while (!found) {
  const messages = await slack.getChannelHistory({ channel: 'C123456' });
  found = messages.some(m => m.text.includes('deployment complete'));
  if (!found) await new Promise(r => setTimeout(r, 5000));
}
console.log('Deployment notification received');

这种方法比通过智能体循环交替执行 MCP 工具调用和 sleep 命令更高效。

此外，能够编写被执行的条件树还节省了"首个 token 响应时间"的延迟：智能体可以让代码执行环境来评估 if 语句，而不必等待模型来评估。

### 隐私保护操作

当智能体使用 MCP 执行代码时，中间结果默认保留在执行环境中。这样，智能体只能看到你明确记录或返回的内容，这意味着你不想与模型共享的数据可以在工作流中流动而不会进入模型的上下文。

对于更敏感的工作负载，智能体框架可以自动对敏感数据进行标记化（tokenize）处理。例如，假设你需要将电子表格中的客户联系方式导入 Salesforce。智能体编写：

```
const sheet = await gdrive.getSheet({ sheetId: 'abc123' });
for (const row of sheet.rows) {
  await salesforce.updateRecord({
    objectType: 'Lead',
    recordId: row.salesforceId,
    data: { 
      Email: row.email,
      Phone: row.phone,
      Name: row.name
    }
  });
}
console.log(`Updated ${sheet.rows.length} leads`);
```

const sheet = await gdrive.getSheet({ sheetId: 'abc123' });
for (const row of sheet.rows) {
  await salesforce.updateRecord({
    objectType: 'Lead',
    recordId: row.salesforceId,
    data: { 
      Email: row.email,
      Phone: row.phone,
      Name: row.name
    }
  });
}
console.log(`Updated ${sheet.rows.length} leads`);

MCP 客户端在数据到达模型之前拦截数据并对 PII（个人身份信息）进行标记化处理：

```
// What the agent would see, if it logged the sheet.rows:
[
  { salesforceId: '00Q...', email: '[EMAIL_1]', phone: '[PHONE_1]', name: '[NAME_1]' },
  { salesforceId: '00Q...', email: '[EMAIL_2]', phone: '[PHONE_2]', name: '[NAME_2]' },
  ...
]
```

// What the agent would see, if it logged the sheet.rows:
[
  { salesforceId: '00Q...', email: '[EMAIL_1]', phone: '[PHONE_1]', name: '[NAME_1]' },
  { salesforceId: '00Q...', email: '[EMAIL_2]', phone: '[PHONE_2]', name: '[NAME_2]' },
  ...
]

然后，当数据在另一个 MCP 工具调用中共享时，通过 MCP 客户端的查找表进行反标记化（untokenize）处理。真实的电子邮件地址、电话号码和姓名从 Google Sheets 流向 Salesforce，但永远不会经过模型。这可以防止智能体意外记录或处理敏感数据。你还可以使用此方法定义确定性安全规则，选择数据可以流向何处以及从何处获取。

### 状态持久化与技能（Skills）

具有文件系统访问权限的代码执行允许智能体在操作之间维持状态。智能体可以将中间结果写入文件，使其能够恢复工作并跟踪进度：

```
const leads = await salesforce.query({ 
  query: 'SELECT Id, Email FROM Lead LIMIT 1000' 
});
const csvData = leads.map(l => `${l.Id},${l.Email}`).join('\n');
await fs.writeFile('./workspace/leads.csv', csvData);

// Later execution picks up where it left off
const saved = await fs.readFile('./workspace/leads.csv', 'utf-8');
```

const leads = await salesforce.query({ 
  query: 'SELECT Id, Email FROM Lead LIMIT 1000' 
});
const csvData = leads.map(l => `${l.Id},${l.Email}`).join('\n');
await fs.writeFile('./workspace/leads.csv', csvData);

// Later execution picks up where it left off
const saved = await fs.readFile('./workspace/leads.csv', 'utf-8');

智能体还可以将自己的代码持久化为可复用的函数。一旦智能体为某个任务开发了可运行的代码，它就可以保存该实现以供将来使用：

```
// In ./skills/save-sheet-as-csv.ts
import * as gdrive from './servers/google-drive';
export async function saveSheetAsCsv(sheetId: string) {
  const data = await gdrive.getSheet({ sheetId });
  const csv = data.map(row => row.join(',')).join('\n');
  await fs.writeFile(`./workspace/sheet-${sheetId}.csv`, csv);
  return `./workspace/sheet-${sheetId}.csv`;
}

// Later, in any agent execution:
import { saveSheetAsCsv } from './skills/save-sheet-as-csv';
const csvPath = await saveSheetAsCsv('abc123');
```

// In ./skills/save-sheet-as-csv.ts
import * as gdrive from './servers/google-drive';
export async function saveSheetAsCsv(sheetId: string) {
  const data = await gdrive.getSheet({ sheetId });
  const csv = data.map(row => row.join(',')).join('\n');
  await fs.writeFile(`./workspace/sheet-${sheetId}.csv`, csv);
  return `./workspace/sheet-${sheetId}.csv`;
}

// Later, in any agent execution:
import { saveSheetAsCsv } from './skills/save-sheet-as-csv';
const csvPath = await saveSheetAsCsv('abc123');

这与技能（Skills）的概念密切相关——技能是可复用的指令、脚本和资源的文件夹，用于提高模型在专门任务上的表现。在这些保存的函数中添加 SKILL.md 文件可以创建模型可以引用和使用的结构化技能。随着时间的推移，这允许你的智能体构建一个更高级别的能力工具箱，使其所需的脚手架不断演进，以最高效地工作。

请注意，代码执行本身也会引入复杂性。运行智能体生成的代码需要一个具有适当沙箱隔离、资源限制和监控的安全执行环境。这些基础设施需求带来了直接工具调用所没有的运营开销和安全考量。代码执行的优势——降低 token 成本、减少延迟和改进工具组合——应该与这些实现成本进行权衡。

## 总结

MCP 为智能体连接众多工具和系统提供了一个基础协议。然而，一旦连接了太多服务器，工具定义和结果可能会消耗过多的 token，降低智能体效率。

尽管这里涉及的许多问题看起来很新颖——上下文管理、工具组合、状态持久化——但软件工程中已有已知的解决方案。代码执行将这些成熟的模式应用于智能体，让它们使用熟悉的编程构造来更高效地与 MCP 服务器交互。如果你实现了这种方法，我们鼓励你与 MCP 社区分享你的发现。

### 致谢

本文由 Adam Jones 和 Conor Kelly 撰写。感谢 Jeremy Fox、Jerome Swannack、Stuart Ritchie、Molly Vorwerck、Matt Samuels 和 Maggie Vo 对本文草稿提供的反馈。