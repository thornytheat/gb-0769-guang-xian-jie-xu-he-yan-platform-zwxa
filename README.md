# 光纤接续核验台

验收员从 A、B 两端 OTDR 事件原件和设计清单复算接续损耗。首页比对双端轨迹帧与设计接头，按 `J`、`K` 或使用跳检按钮定位证据。左侧八个入口分别处理采信、校准、配对、判损、对账、留档、外检报告复核和签发。

`docker compose up --build` 后访问 `http://localhost:18468/`。本地先执行 `pip install -r requirements.txt`，再运行 `python -m flask --app app.main run --port=18468`，用 `pytest -q` 验收。`FIBER_DB` 设置 SQLite 文件，Compose 的命名卷保留运行记录。

各预览和留档 API 接收 `{"sample":"dirty"}`、`{"sample":"clean"}` 或 `{"traces":{"a":"CSV","b":"CSV","design":"CSV"},"settings":{...},"report":"CSV"}`。参数示例见 `sample_data/dirty/link.json` 与 `sample_data/dirty/report.csv`。从留档页提交，在「外检报告复核」页对已留档核验提交报告（同一报告重试不新增复核项），在签发页下载核验包。报告只保留三位小数；仅舍入差异判 `CONSISTENT` 采信，报告合格而现场超限判 `VERDICT_CONFLICT` 禁放行，缺现场证据判 `EVIDENCE_MISSING` 不直接采信报告结论。

- [模块与独立复算](docs/DEPTH.md)
- [字段与规则](docs/DATA-DICTIONARY.md)
