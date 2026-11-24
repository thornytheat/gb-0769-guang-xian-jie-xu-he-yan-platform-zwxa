# 深度登记 光纤接续核验台

- 规模：中型
- 核心规则：校准双向链程后做单调一对一最优配对，按带符号均值验设计接头。

## 功能模块

| 模块 | 使用者动作 | 入口 | 核心文件 | 测试 |
|---|---|---|---|---|
| M1 轨迹文件采信 | 检查原行与隔离原因 | POST /api/trace | `app/modules/trace/service.py` | `tests/test_trace.py` |
| M2 距离与方向校准 | 核对双端坐标与起偏 | POST /api/calibration | `app/modules/calibration/service.py` | `tests/test_calibration.py` `tests/test_settings.py` |
| M3 双端事件最优配对 | 核查相邻冲突及孤测 | POST /api/pairs | `app/modules/pairs/optimal.py` | `tests/test_pairs.py` `tests/test_pair_oracle.py` |
| M4 接续净损耗判定 | 对照带符号读数和均值 | POST /api/loss | `app/modules/loss/service.py` | `tests/test_loss.py` |
| M5 设计与实测对账 | 核对逐接头是否缺证 | POST /api/design | `app/modules/design/service.py` | `tests/test_design.py` |
| M6 批次留档复跑 | 留档和重跑同一轨迹组 | POST /api/inspections | `app/modules/archive/storage.py` | `tests/test_archive.py` |
| M7 光纤证据签发 | 复核签发条件并下载 | GET /api/certificate/<id> | `app/modules/certificate/service.py` | `tests/test_certificate.py` |
| M8 外检报告复核 | 逐条对账报告结论与现场复算 | POST /api/inspections/<id>/reviews | `app/modules/report/reconcile.py` `app/modules/review/service.py` | `tests/test_report.py` `tests/test_report_reconcile.py` `tests/test_review.py` |

## 陷阱登记

| TRAP | 现象 | 朴素错误 | 处理 | 位置 | 测试 |
|---|---|---|---|---|---|
| TRAP-02 | A 端首列 BOM | 事件列读不到 | 清理首 BOM | `app/modules/trace/reader.py` | `tests/test_trace.py::test_bom_and_repeated_header` |
| TRAP-04 | A 端续行表头 | 当配对记录 | 按分段另计 | `app/modules/trace/reader.py` | `tests/test_trace.py::test_bom_and_repeated_header` |
| TRAP-05 | A-Y 列尾多字段 | 错配字段值 | 原行隔离 | `app/modules/trace/reader.py` | `tests/test_trace.py::test_extra_fields_keep_raw_location` |
| TRAP-07 | A-N 哨兵、B-G 空值 | 当成零损耗 | 两种原因分别留档 | `app/reasons.py` | `tests/test_trace.py::test_missing_sentinel_and_blank_are_isolated` |
| TRAP-10 | 0.2005 dB 半毫精度 | 先舍入误过限 | 用两倍毫 dB 判界 | `app/modules/loss/verdict.py` | `tests/test_loss.py::test_double_mdb_preserves_half_increment` |
| TRAP-14 | A-C 同键异距 | 后写覆盖 | 整组隔离 | `app/modules/trace/service.py` | `tests/test_trace.py::test_conflicting_records_both_withdrawn` |
| TRAP-15 | A-02 米和千米并存 | 两条虚假轨迹 | 归一毫米后比对 | `app/modules/trace/units.py` | `tests/test_trace.py::test_equivalent_units_dedupe` |
| TRAP-19 | A100 可匹配 B97 或 B101 | 最近优先导致 A105 无法配对 | 先最大配对数再最小间差 | `app/modules/pairs/optimal.py` | `tests/test_pairs.py::test_global_pairing_beats_greedy_and_keeps_competition` |
| TRAP-21 | A700 和 B820 均无对侧 | 只报一端孤测 | 分别记录缺 A 或缺 B | `app/modules/pairs/service.py` | `tests/test_pairs.py::test_opposite_ends_missing_in_both_directions` |
| TRAP-22 | 报告只留三位小数 | 拿四位现场值直接比报告值，全部对不上 | 现场净损耗折回毫 dB 后按半进到三位再比 | `app/modules/report/reader.py` | `tests/test_report.py::test_field_value_rounds_half_up_to_report_precision` |
| TRAP-23 | 报告判合格、现场超限 | 只比数值忽略结论，超限接头被放行 | 结论冲突单独成类并阻塞签发 | `app/modules/report/reconcile.py` | `tests/test_report_reconcile.py::test_report_pass_but_field_over_limit_blocks_release` |
| TRAP-24 | 报告有接头、现场无双端证据 | 直接采信报告合格结论 | 标记缺现场证据，报告结论不可直接采信 | `app/modules/report/reconcile.py` | `tests/test_report_reconcile.py::test_missing_field_evidence_cannot_trust_report_conclusion` |
| TRAP-25 | 同一报告反复提交 | 每次重试新增一条复核项 | 复核身份含报告 SHA-256，命中即复用 | `app/modules/review/service.py` | `tests/test_review.py::test_review_api_idempotent_for_same_report` |

## 对账规则

- 6 个设计接头 = 3 通过 + 1 超限 + 2 缺证。
- 12 条窗内端点 = 2×(4 已挂接 + 1 孤配) + 2 单端。窗外测量另计 1 条。
- F-01 双向均值 (−0.100+0.300)/2=0.1000 dB，F-03 为 (0.33+0.31)/2=0.3200 dB，超出 0.200 dB。

输入为设备导出的事件表。二进制曲线解码、坡度自校与电子签章未纳入该工作台。

## 外检报告复核规则

- 报告 CSV 必填 `joint,loss_db,verdict`，损耗只保留三位小数；超过三位、坏数值、未知结论、同键冲突均按原行隔离，不进入对账。
- 现场净损耗（两倍毫 dB）折成毫 dB 后按 ROUND_HALF_UP 回到三位小数，再与报告值比较。
- 逐条对账六类结论：
  - `CONSISTENT` 舍入一致：报告值等于现场三位舍入且结论一致，差异仅舍入，报告结论采信，不算造假。
  - `VALUE_MISMATCH` 数值不符：三位舍入后损耗仍对不上，报告数据不可采信。
  - `VERDICT_CONFLICT` 结论冲突：报告与现场合格性相反（典型为报告合格、现场超限），不得按报告放行。
  - `EVIDENCE_MISSING` 缺现场证据：报告列示但现场无双端耦合证据（单端/缺证/越界），报告结论不可直接采信，须补证。
  - `REPORT_MISSING` 报告漏列：现场有复算结论而报告未列该接头。
  - `REPORT_ROW_INVALID` 报告坏行：该接头报告原行已隔离，无法对账。
- 除 `CONSISTENT` 外五类均为阻塞项，任一存在则整批 `handover_ready=false`，签发件追加 `REPORT_*` 阻塞码。
- 复核身份 `sha256(规则, 链路核验编号, 报告 SHA-256)`；同一报告重试命中同一编号，复用首次复核，不新增复核项。
