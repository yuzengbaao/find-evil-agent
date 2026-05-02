# FIND EVIL! 45天开发计划

**注册日期**: 2026-05-02
**截止日期**: 2026-06-16 11:45 GMT+8
**参赛者**: yuzengbaao (Solo)
**仓库**: https://github.com/yuzengbaao/find-evil-agent

---

## Week 1 (5/2-5/8): 基线搭建

| 天 | 日期 | 任务 | 验收标准 |
|----|------|------|---------|
| D1 | 5/2 | ✅ 注册+仓库+骨架 | repo + audit_logger + self_correct |
| D2 | 5/3 | 安装SIFT工具链 | Volatility3/Plaso/SleuthKit/YARA可运行 |
| D3 | 5/4 | 下载测试样本+构建案例 | 至少1个E01内存样本可挂载分析 |
| D4 | 5/5 | 跑Protocol SIFT原始基线 | 基线findings导出+日志记录 |
| D5 | 5/6 | 分析基线弱点 | 误报/漏报/日志缺口/幻觉清单 |
| D6 | 5/7 | 设计增强架构文档 | architecture.md完成 |
| D7 | 5/8 | 基线报告+Rapid Agent规则检查 | baseline-report.md + 规则确认 |

---

## Week 2 (5/9-5/15): 核心开发

| 天 | 日期 | 任务 | 验收标准 |
|----|------|------|---------|
| D8 | 5/9 | audit_logger集成到agent | 每个tool调用自动记录JSONL |
| D9 | 5/10 | evidence-integrity层 | 只读挂载+write sandbox+hash校验 |
| D10 | 5/11 | self_correct引擎v1 | 跨工具矛盾检测+自动重跑 |
| D11 | 5/12 | confidence评分系统 | 每个finding有corroboration-based分数 |
| D12 | 5/13 | 决策日志 | agent推理链完整记录 |
| D13 | 5/14 | 端到端测试 | 基线 vs 增强 版对比 |
| D14 | 5/15 | 修复+迭代 | Week2 bug fix + 性能优化 |

---

## Week 3 (5/16-5/22): 增强迭代

| 天 | 日期 | 任务 | 验收标准 |
|----|------|------|---------|
| D15 | 5/16 | 第二测试案例 | 不同类型证据(disk vs memory vs network) |
| D16 | 5/17 | 多证据类型支持 | Volatility+Plaso+SleuthKit联合分析 |
| D17 | 5/18 | 准确率benchmark框架 | accuracy_report.py输出量化对比 |
| D18 | 5/19 | 第三测试案例(边界情况) | 对抗性样本(空证据/损坏镜像) |
| D19 | 5/20 | MeDo截止检查(如适用) | — |
| D20 | 5/21 | 幻觉检测强化 | 事实vs推理严格区分 |
| D21 | 5/22 | Week3 review | 全指标对比表 |

---

## Week 4 (5/23-5/29): 文档+打磨

| 天 | 日期 | 任务 | 验收标准 |
|----|------|------|---------|
| D22 | 5/23 | README最终版 | 安装/运行/架构/创新点完整 |
| D23 | 5/24 | 架构图(diagrams/) | 系统架构+数据流+安全边界 |
| D24 | 5/25 | Dataset文档 | 数据来源+ground truth+处理方式 |
| D25 | 5/26 | Accuracy Report | 基线vs增强版完整对比数据 |
| D26 | 5/27 | Demo视频脚本 | 5分钟脚本+分镜 |
| D27 | 5/28 | 代码清理+测试 | 所有test pass + lint clean |
| D28 | 5/29 | 内部review | 自检6项评分标准 |

---

## Week 5 (5/30-6/5): Demo+提交准备

| 天 | 日期 | 任务 | 验收标准 |
|----|------|------|---------|
| D29 | 5/30 | 录制demo视频 | ≤5分钟,含语音+真实终端+self-correction演示 |
| D30 | 5/31 | 视频编辑+字幕 | 可上传到YouTube/Vimeo |
| D31 | 6/1 | hosted project URL | Cloud Run或类似平台部署 |
| D32 | 6/2 | Devpost提交表草稿 | 填写所有必填项 |
| D33 | 6/3 | 代码仓库最终整理 | MIT license + clean history |
| D34 | 6/4 | 提交材料交叉检查 | 8项必交成果逐项确认 |
| D35 | 6/5 | 缓冲日 | 处理意外问题 |

---

## Week 6 (6/6-6/15): 提交+收尾

| 天 | 日期 | 任务 | 验收标准 |
|----|------|------|---------|
| D36 | 6/6 | 提交前终检 | 6项评分标准自评 |
| D37 | 6/7 | 正式提交Devpost | 所有材料上传完成 |
| D38 | 6/8 | 提交确认 | 确认提交成功+截图 |
| D39-45 | 6/9-6/15 | 缓冲+改进 | 根据需要更新提交 |

---

## 8项必交成果检查表

| # | 成果 | 负责天 | 状态 |
|---|------|--------|------|
| 1 | 公开代码仓库(MIT) | D2 | ✅ 已创建 |
| 2 | README(安装/运行) | D22 | ⬜ |
| 3 | Live deployment URL | D31 | ⬜ |
| 4 | ≤5分钟demo视频 | D29-30 | ⬜ |
| 5 | 架构图 | D23 | ⬜ |
| 6 | Dataset文档 | D24 | ⬜ |
| 7 | Accuracy Report | D25 | ⬜ |
| 8 | Agent Execution Logs | D13+ | ⬜ |

---

## 6项评分标准自评模板

| # | 标准 | 权重 | 我们的优势 |
|---|------|------|-----------|
| 1 | 自主执行质量 | tiebreaker | self-correction loop |
| 2 | IR准确性 | 核心 | 跨工具corroboration+幻觉检测 |
| 3 | 分析广度深度 | 核心 | 多证据类型联合分析 |
| 4 | 约束实现 | 核心 | OS级只读+write sandbox(非prompt级) |
| 5 | 审计追踪质量 | 核心 | JSONL全链路+hash+token |
| 6 | 可用性文档 | 加分 | 清晰README+部署指南 |

---

_更新时间: 2026-05-02 | 状态: Day 1 完成 ✅_
