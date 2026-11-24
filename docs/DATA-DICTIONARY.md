# 轨迹、接头与判损字段

A、B 的 CSV 必填 `event,distance,unit,loss_db`，设计清单必填 `joint,distance,unit,limit_db`。字段可换列序，UTF-8 首行 BOM 会清理。ID 为原形字符串，按来源和 ID 分键。同键比较归一距离与损耗，完全相同保留首行，冲突整组隔离。记录保留起始物理行和原值。空白单元格、哨兵及 JSON null 分别校验。空文件、全空行、仅表头分别为 `EMPTY_FILE`、`BLANK_FILE`、`HEADER_ONLY`。每源最多 350 个正文记录、250,000 字符。

距离单位可为 mm、m 或 km，归一成整数毫米。采集损耗 dB 支持有符号值，精确到毫 dB。配置 `length_m` 为光路总长，`zero_a_m/zero_b_m` 为两向测量偏置。统一链程 A = A 原读数减 A 起偏，B = 全长减去 B 原读数扣掉 B 起偏的结果。校准有效范围是闭区间 `[0,L]`。出界测量归隔离，出界设计仍在清单中并标缺证。设计本来就在 A 端坐标系。

双端事件按链程和 ID 排序。一对一单调配对先最大化数量，再最小化距离差总和，最后依照同状态优先配对、保留较早 A 端、再保留较早 B 端的固定遍历作稳定裁决。容差 `pair_tol_m` 含等号。配对中点的分辨率为半毫米。配对双方的读数取带符号平均作为净损耗，保留单向负值和原行。通过阈值含等号，净值为负记录无效净增益。

设计点与配对中点再次按相同优化目标一对一对齐，使用 `design_tol_m`。每接头以自己的 `limit_db` 判定，损耗模块的 `reference_limit_db` 用于单独预览。单端或孤配均保留。运行清单含源 SHA-256、校准参数、时间 UTC、耗时、版本、证据。快照摘要可用排序键、紧凑 JSON 和 UTF-8 重算。

## 外检报告与复核字段

外检报告 CSV（`report.csv`）必填 `joint,loss_db,verdict`，列序可换、首行 BOM 会清理。`loss_db` 为带符号小数，仅接受至多三位小数，解析为整数毫 dB（`loss_mdb`）；超过三位报 `REPORT_PRECISION_OVER_3`，坏数值报 `BAD_REPORT_NUMERIC`，越界报 `REPORT_OUT_OF_SCALE`。`verdict` 接受 `合格/PASS` 与 `超限/不合格/OVER_LIMIT`，其他值报 `BAD_REPORT_VERDICT`。同键完全相同保留首行（`DUPLICATE_REPORT_JOINT`），同键异值整组隔离（`CONFLICTING_REPORT_JOINT`）。

复核以设计接头与报告接头的并集逐条对账。现场侧取设计对账行：缺证类（`SINGLE_SIDE_ONLY`/`NO_COUPLED_EVIDENCE`/`DESIGN_OUTSIDE_LINK`）无复算值；有效行取损耗判定的 `net_double_mdb`，除以 2 折成毫 dB 后按半进舍入到三位（`field_net_mdb`），并把现场结论映射为 `PASS`/`OVER_LIMIT`（`INVALID_NET_GAIN` 按不可签认的不合格处理）。对账输出每条含 `joint`、报告行号与报告值/结论、现场 `field_code`/`field_net_db`/`field_net_mdb`、`reconcile_code` 与 `note`；汇总给出六类计数、`blockers` 与整批 `handover_ready`。复核留档表 `reviews` 以 `review_id` 唯一去重，含 `inspection_id`、`report_sha256`、`handover_ready`、时间与完整对账文档。签发件在现场阻塞码之外追加 `REPORT_VALUE_MISMATCH`、`REPORT_VERDICT_CONFLICT`、`REPORT_EVIDENCE_MISSING`、`REPORT_JOINT_MISSING`、`REPORT_ROW_INVALID`。
