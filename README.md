<img src="docs/assets/overview.svg" alt="EvidenceBound Planner — Evidence, constraints, reviewable decisions" width="100%" />

# EvidenceBound Planner

**把研究目标、科学依据和资源约束连接成一份可审查的实验方案。**

EvidenceBound Planner 提供一套供 Agent 阅读执行的实验规划工作流，以及可独立运行的 Python 校验工具。它帮助研究者比较候选方案、明确参数来源、核对采购预算和设备排期，并保留每一次方案修订的原因。

项目由两个相互配合的部分组成：[`SKILL.md`](SKILL.md) 引导 Agent 处理科学问题、证据和方案结构；[`verify_plan.py`](scripts/verify_plan.py) 对已经明确声明的数值模型和排期进行确定性检查。研究判断与计算结果各有边界，输出便于复核。

[![Tests](https://github.com/ssstry2635/evidence-bounded-experiment-planner/actions/workflows/tests.yml/badge.svg)](https://github.com/ssstry2635/evidence-bounded-experiment-planner/actions/workflows/tests.yml)

Python 3.10+ · 运行时仅使用标准库 · 无需 API Key

## 能解决什么问题

当一个研究目标需要落到实验执行层面，常见困难是参数没有依据、对照与终点不匹配、技术重复被当成独立样本，或预算和设备预约无法同时满足。这个项目把这些问题组织到同一条可追溯的工作流中。

你可以用它审阅多个版本的候选方案，在明确的有限参数集合内比较预算与时间；也可以单独审核已经拟好的设备排期，检查并发容量、预约窗口、前后依赖和截止时间。方案修改会保留原始版本、变更项、证据与后续影响。

它适合需要保留证据和资源计算的实验规划、方法讨论、方案评审与研究准备。科学推理部分需要由支持读取本地文件和执行工具的 Agent 或研究者完成；命令行工具自身不会阅读论文并自动生成实验设计。

## 工作方式

```mermaid
flowchart LR
    A[研究目标与实际材料] --> B[假设、终点与对照]
    B --> C[参数证据与资源模型]
    C --> D[有限参数搜索]
    C --> E[显式排期审核]
    D --> F[方案比较与修订]
    E --> F
    F --> G[方案、计算输入与变更记录]
```

**科学设计。** 明确可检验假设、自变量和因变量、混杂因素、相关对照、独立样本单位、质量门槛与异常响应。

**证据约束。** 参数关联到实际文献、方法、设备信息或资源情景。已知事实、计算结果、设计假设和需要确认的事项分别表达。

**数值核对。** 计算样本需求、库存缺口、整包采购和总成本。在有限域内穷举，先判断硬约束，再按声明的目标优先级比较方案。

**排期核对。** 对每个步骤检查预约覆盖、资源需求、容量、依赖和截止时间，输出具体违反项。

## 快速开始

只需安装 Python 3.10 或更新版本。核心工具不需要 `pip install`。

```bash
git clone https://github.com/ssstry2635/evidence-bounded-experiment-planner.git
cd evidence-bounded-experiment-planner

python scripts/verify_plan.py solve examples/model.json --out output/search
python scripts/verify_plan.py schedule examples/schedule.json --out output/schedule-audit.json
```

搜索会生成 `output/search/report.json` 和 `output/search/evaluations.csv`。前者记录每个候选方案的可行数量、最优点、目标值、约束检查和并列情况，后者保留逐点计算结果。排期命令生成单独的审核 JSON。

`examples/` 中的数值均为**假设接口示例**，用于理解工具，并非论文事实、实验测量或设备安全参数。

## 读懂搜索示例

[`examples/model.json`](examples/model.json) 定义了三组候选参数、四个实验组、库存、采购包规格、预算和时间上限。参数 `n` 表示每组独立样本数，`dwell` 表示示例中的批次时长。

工具从原始数量重新计算，而不是信任某个候选方案自报的总价：

```text
samples  = groups × n
packs    = ceil(max(0, samples - stock) / pack_size)
cost     = packs × pack_size × unit_cost
duration = ceil(samples / 8) × dwell
```

示例一共枚举 8 个点，其中 5 个满足声明的硬约束。按“先成本、后时间”的目标顺序，选中 B 的 `n=3`、`dwell=2`，采购成本为 120，示例时长为 4。

报告中的对应字段如下，完整计算仍以实际生成的 JSON 和 CSV 为准：

```json
{
  "status": "completed",
  "complete_enumeration": true,
  "evaluated": 8,
  "feasible_count": 5,
  "best": {
    "candidate_id": "B",
    "parameters": {"dwell": "2", "n": "3"},
    "objectives": ["120", "4"]
  }
}
```

十进制数量以字符串输出，以保留计算精度。`completed` 指枚举过程完成，不代表实验已经执行或获得了某种科学效果。

## 接入自己的数值模型

输入包含来源索引 `sources`、常量 `constants`、按依赖顺序定义的 `derived`、硬约束 `constraints`、排序目标 `objectives` 和带版本的 `candidates`。

每个候选方案声明实际允许的有限参数值。硬约束使用明确的左右表达式和关系符；目标按照给定顺序进行词典序比较。需要审计候选方案原稿时，把其参数域固定为单值；需要搜索修订空间时，使用经过科学与资源约束确认的实际允许域。两种结果应分开解释。

```json
{
  "id": "budget",
  "lhs": "cost",
  "op": "<=",
  "rhs": "budget",
  "evidence": ["resource-contract"]
}
```

表达式支持数值、变量、`+ - * /`、一元正负号，以及 `ceil`、`floor`、`abs`、`min`、`max`。实现使用受限 AST 遍历，不执行任意 Python 表达式。默认最多枚举 100,000 个点，可显式提高到 1,000,000；超出范围会报告失败，不会假装完成搜索。

CLI 使用 50 位有效十进制数字。无限循环小数在该精度下舍入，因此不声称是任意表达式的精确有理数计算。单位需由建模者统一并记录转换依据。

完整字段和规则见 [数值与排期接口](references/verification.md)。

## 审核设备排期

[`examples/schedule.json`](examples/schedule.json) 安排两批任务顺序使用一台容量为 1 的设备。第一批在 0–4 小时，第二批在 4–8 小时，预约窗口为 0–8 小时。

时间区间使用半开区间 `[start, end)`，因此第一批结束时第二批可以开始。把第二批开始时间改为 3 后，工具会同时指出设备容量冲突和前置任务未完成。

排期审核验证的是你给出的这一份排期。它没有搜索所有可能的任务顺序；某份排期不通过，不等于不存在任何可行排期。

## 让 Agent 使用规划工作流

让能够读取本地文件的 Agent 先阅读 [`SKILL.md`](SKILL.md)，再提供研究目标、实际资料、资源限制和期望输出。可以使用如下请求：

```text
阅读本仓库的 SKILL.md。
根据 data/ 下的研究目标、文献和候选方案，比较各方案的证据与资源约束。
给出可审查的修订方案，保留来源、计算输入、排期和逐项变更记录。
将结果写入 output/；未确认的参数和材料请明确标出。
```

建议交付实验方案、证据参数表、候选对比、样本与采购计算、显式排期、异常响应、确认项和变更记录。若调用方提供固定输出格式，保留其字段和标识。

## 目录与进一步阅读

```text
SKILL.md                     Agent 工作流入口
scripts/verify_plan.py       搜索与排期命令行工具
examples/model.json         有限参数搜索示例
examples/schedule.json      设备排期示例
references/                 证据、设计、接口与交付说明
tests/                      算术、边界与排期回归测试
docs/                       项目概览与设计说明
```

[证据与实验设计](references/evidence-and-design.md) 说明参数和对照如何落地；[数值与排期接口](references/verification.md) 解释输入结构、精度和搜索范围；[交付复核](references/output-and-review.md) 提供科学、算术和输出三层检查；[架构说明](docs/architecture.md) 区分 Agent 与程序各自承担的工作。

## 验证与开发

```bash
python -B -m unittest discover -s tests -v
```

当前有 15 项回归测试，覆盖库存与整包采购边界、十进制与受限表达式、全部不可行、并列与最大化目标、重复/空参数域、搜索上限、过期报告替换、设备容量、预约缺口、依赖与截止时间。其中有限网格搜索还通过固定随机种子与独立整数算术进行交叉核验。

仓库提供 GitHub Actions 工作流，在 Python 3.10、3.11、3.12 和 3.13 环境运行测试与示例。贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 能力边界

该工具验证的是声明模型的计算与显式排期。它不会自动判断证据是否真实、单位是否具有相同物理意义、对照是否足以回答科学问题，也不会预测未经测量的实验响应。条件性最优点仅在给定参数域和目标顺序内成立。

示例展示工程逻辑。真实实验中的关键参数、设备兼容性、安全与伦理条件仍须由具备相应职责的人员确认。项目会保留这些不确定性，避免把形式完整的报告误当成已经验证的实验结论。
