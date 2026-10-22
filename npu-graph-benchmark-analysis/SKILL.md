---
name: npu-graph-benchmark-analysis
description: 按 Ascend TorchBench README 收集并分析 NPU eager/图模式融合范围、profiler 融合效果和无调试性能基线，输出加速比表、报告与最小复现；支持跨模型、版本及用户自定义本地或远程环境。
---

# NPU 图模式 benchmark 分析

## 首次使用必须告知用户的配置

开始远程任务前，先用简短说明告知用户需要填写的内容，不只让用户自行阅读参考文档：复制 `assets/connection.example.json` 到自己的私有目录，每台主机只填写 `ip`、`username`、`password`，多台按优先级添加到 `hosts`；填好后提供文件路径，不在聊天中提供密码。容器、Python/CANN 路径及空闲卡自动检查，无需用户手填。已提供连接文件时直接复用，不重复要求配置。

从用户请求确认模型、PyTorch 版本及本次采集阶段；这些是任务信息，不是连接文件字段。默认远端 Git 源码无需配置；只有用户选择已有仓库时才需要其路径及所在机器。仅做离线日志分析时跳过连接配置，请用户提供日志位置和输出要求。

比较同设备 eager E2E / compile E2E 加速比。GPU 数据未提供时完成 NPU 工作，明确缺口，不编造差距结论。默认只处理数据收集、分析及最小复现；实施优化或运行 GPU 须在用户请求范围内。

## 首次使用与执行边界

先读 [配置与连接](references/configuration.md)，确定本次 README、runner、Python、设备与产物目录。所有路径由当前用户环境解析，不依赖原作者 PC、WSL 或内网。可只做已有日志的离线分析。远程安全流程已包含在本技能，无需安装其他技能。

源码来源开关 `benchmark_source_mode` 默认为 `remote_git`：从 `https://gitcode.com/Ascend/pytorch` 获取源码到实际运行主机或容器，不要求接收方 PC 下载代码。设为 `existing_checkout` 时使用用户已有仓库（可在 WSL、本机、远程主机或容器），不自动拉取或覆盖；离线分析不获取源码。详细配置和版本固定规则见配置文档。

需要自动连接或多主机选卡时，读 [连接池与凭据文件](references/remote-pool.md)，请用户指定其私有配置文件路径，模板为 `assets/connection.example.json`。可以从该文件读取用户名/密码，通过正常 SSH 认证连接；禁止回显秘密。当前主机无空闲卡时按授权名单尝试下一台，校验同配置环境后再运行，单轮不跨主机拼接数据。

benchmark 启动前提交实际方案、完整命令、配置、统计口径及产物，等待审核；已经批准的同一方案不重复询问。遵守当前用户已有授权，不把历史项目的容器特权或环境变更许可带给新用户。

## 工作流程

1. 明确仅收集、已有数据分析、跨版本对比或最小复现；只推进本次要求的阶段。
2. 每个新模型/版本读取当前项目 README 和 runner，核实参数、源码版本、真实 import 路径、依赖与模型入口。不要直接套用历史命令。详细步骤见 [采集与分析细则](references/workflow.md)。
3. 记录版本、模式、dtype、batch、输入、train/eval、编译后端、ACLGraph、设备和同步计时范围，建立独立输出目录；生成完整命令审核后执行。
4. 区分三类采集：

   | 采集 | Debug | Profiler | 目的 |
   | --- | --- | --- | --- |
   | 融合范围 | 开 | 关 | FX、生成代码、图中断与编译边界 |
   | 融合效果 | 关 | 开 | kernel、算子、设备任务与时间线 |
   | 性能基线 | 关 | 关 | 同设备 eager/compile E2E 加速比 |

5. 在启动 Python/NPU 初始化之前选择空闲设备并复查；单轮 eager/compile 固定同一卡。记录物理卡和逻辑设备映射，不共享被占用的卡、不停止其他任务。协作锁不能约束其他使用方。
6. 核验退出码、实际迭代、精度结果、非空产物及统计区间；保存命令、运行时、设备快照和 SHA256 清单。需要回收时使用用户指定目录，避免输出链接指向他人的 PC。
7. 按请求交付三情况表、融合映射、差距报告和最小复现。可选阅读 [DCGAN 历史案例](references/project-history.md) 理解已验证行为；不依赖案例产物存在。

## 计时与汇总脚本

同轮比值使用 eager/compile 原始单步算术均值计算，显示时再四舍五入，不用中位数替换均值、不擅自删慢步。预热、同步和聚合区间从实际 runner 确认，不能将 profiler active 步数等同总迭代。

`scripts/summarize_timings.py` 使用 Python 3 标准库，从原生日志输出 CSV、JSON 和 Markdown。解析脚本路径时以本技能实际安装目录为准；以下变量需替换为已存在的技能、日志和可写输出目录，不能原样运行：

```bash
python "$SKILL_DIR/scripts/summarize_timings.py" \
  --run "debug=$DEBUG_LOG" \
  --run "profiler=$PROFILER_LOG" \
  --run "baseline=$BASELINE_LOG" \
  --output-dir "$REPORT_DIR"
```

脚本不运行 benchmark，不验证标签/环境；当前支持本案例原生 step/summary 日志格式，格式变化时先检查适配。只有双关轮次作为对应基线；debug/profiler 比值为观测值。独立运行的差异不能直接归因于开关。单轮不等于多轮稳定结论。

## 版本和 GPU 对照

2.14、2.13、2.4 分别记录，核实实际版本、commit、torch_npu、Triton、CANN、驱动与后端。跨版本软件栈变化不能全部归因于 PyTorch。GPU 数据到齐后先核对配置和计时范围，再比较各设备内部加速比。
