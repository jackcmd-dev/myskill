---
name: npu-graph-benchmark-collect
description: 在已准备好的NPU环境按Ascend TorchBench README采集融合范围、融合效果和性能基线；默认triton_experimental、关闭ACLGraph及动态shape，运行后报告实际命令、组合、完整产物及加速比。
---

# NPU 图模式 benchmark 数据收集

本技能只处理benchmark源码、审核后的运行、产物回收核验与耗时汇总。远程连接/创建容器用npu-remote-container；PyTorch2.14 + torch_npu + CANN9.2.0安装验证用pytorch214-npu-environment。已有可用会话或环境报告则直接复用，不重复要求安装其他技能。离线耗时汇总只需要日志。

## 输入与执行边界

先读 [采集输入与源码](references/configuration.md)，确认模型、版本、训练/推理、阶段和执行环境。新采集要求CANN9.2.0正式版，核实实际版本/路径；历史9.1.0数据保留真实标签。环境不匹配则返回缺口，不自行安装、换版本或创建容器。调用其他技能不扩大用户授权。

源码来源benchmark_source_mode默认remote_git，仓库https://gitcode.com/Ascend/pytorch，在运行端获取，PC无需下载；existing_checkout使用指定已有源码。复测固定原runner和模型commit，不自动更新HEAD。

benchmark前提交实际方案、完整命令、配置、统计口径和预期产物供审核；已批准同一方案不重复询问。只执行当前阶段，不自动跑GPU或实施优化。

## 新采集默认组合

用户未另行指定时，使用`--backend inductor --npu-backend triton_experimental --disable-aclgraph`；不传`--dynamic-shapes`、`--dynamic-batch-only`或`--aclgraph-mode`，按固定输入shape采集，不默认开启MFusion。用户口头说的`triton-ex`在本runner中对应`triton_experimental`，不要把缩写当CLI值。

该默认自2026-10-26更新。此前DVM+ACLGraph+reduce-overhead数据保留原标签，不能改称新组合已验证。已有环境的DVM验证也不能替代对triton_experimental的兼容检查；不支持时报告缺口，不静默回退DVM、普通triton或改变图回放/shape设置。复测历史组合只有用户明确指定时才覆盖当前默认。

## 采集流程

预检遇到TritonMissing或launch hook异常时，不能直接断定未安装triton-ascend。先记录实际解释器、导入路径和完整torch/torch_npu/triton版本，再交由对应环境技能排查接口及NPU识别兼容性；2.14案例见`pytorch214-npu-environment`的`references/triton-compatibility.md`。采集阶段不自行改依赖或静默回退DVM，通过目标后端的小型前后向及debug+profiler验证后再运行正式benchmark。

1. 每个新模型/版本读取实际README和runner，核实参数、模型入口、前后向/优化器范围、dtype/batch、后端和计时语义。检查目标triton_experimental是否可用及环境验证覆盖范围，核对实际后端、图捕获关闭和shape配置；不能凭安装成功认定可运行。细则见 [采集与核验](references/workflow.md)。
2. 请求远程技能按任务需求选空闲卡并持锁，初始化NPU前设置可见设备；同轮eager/compile固定同主机同卡。不共享忙卡、不终止其他任务，不在不同主机拼接一轮数据。
3. 按下表运行用户批准的阶段，使用版本/模型/阶段/时间隔离的目录和编译缓存：

   | 采集 | Debug | Profiler | 主要产物 |
   | --- | --- | --- | --- |
   | 融合范围 | 开 | 关 | 完整debug目录及前向/反向FX、生成代码、融合前后IR |
   | 融合效果 | 开 | 开 | 同轮完整debug目录、profiler原始数据与解析结果 |
   | 性能基线 | 关 | 关 | eager/compile逐步E2E耗时与正式加速比 |

4. 完整回收debug目录（存在时）、profile目录（存在时）、日志、精度、命令、真实环境和设备记录，生成SHA256清单；编译缓存默认留远端。额外提取并索引fx_graph_readable.py、output_code.py、ir_pre_fusion.txt、ir_post_fusion.txt。不能只收提取副本丢掉原始目录；某后端未生成目标文件时报告缺口，不伪造或拿其他轮产物补齐。
5. 核验退出码、实际迭代、精度、dump非空及前向/反向、profiler有效步/CSV/数据库，下载后核对SHA256。每次运行结束必须直接告诉用户实际运行命令（含调试环境变量及profiler参数）、实际组合、环境版本、结果/失败状态及产物路径；不能只给耗时而省略命令和组合。说明实际配置与请求是否一致，未能确认生效时写明未知。交付文件索引、采集记录和按请求生成的NPU耗时/加速比表格。技术案例见 [历史结果](references/project-history.md)，不要求原案例资产存在。

## 完成后的产物回报

每次采集结束，在最终回复中主动列出本轮实际收集的产物及保存目录，不能只说“已完成”或只给报告链接。按融合范围、融合效果、无调试基线分别用表格说明：实际文件/目录或证据包、宿主机及容器内绝对路径、本地回收绝对路径、回收与SHA256校验状态。路径使用本次实际值，不沿用历史案例目录；未下载时明确“仅远端保存”，不声称已回收。

范围/效果说明是否包含前向和反向的fx_graph_readable.py、output_code.py、ir_pre_fusion.txt、ir_post_fusion.txt及完整debug目录；效果另列eager/compile的profiler原始数据和解析结果。基线列逐步耗时、汇总/加速比表和精度结果，并列出共用的命令、环境/配置、日志和文件校验清单。只报告实际存在的内容，缺失项写明。完整目录若仅保存在归档中，给出归档完整路径和包内相对目录，区分完整归档与提取查阅副本；编译缓存等未回收项说明仍存于何处。失败或部分完成时也按实际状态回报。

## 计时与脚本

加速比使用同轮eager/compile原始单步均值之比，显示时四舍五入，不删慢步或用中位数替代。默认50步案例取原生第16～40步；实际区间从当前runner核实。debug/profiler轮仅为观测，正式基线必须双关；独立轮、不同卡/主机/软件栈的差异不直接归因于开关或框架。

Python3标准库脚本scripts/summarize_timings.py输出CSV、JSON、Markdown，不运行benchmark、不判定环境有效性；使用实际技能安装目录和日志路径：

```bash
python "$SKILL_DIR/scripts/summarize_timings.py" \
  --run "scope=$SCOPE_LOG" --run "effect=$EFFECT_LOG" \
  --run "baseline=$BASELINE_LOG" --output-dir "$REPORT_DIR"
```

本技能到数据收集与核验为止。后续取得GPU数据后，再单独定义并执行跨设备对比、融合映射、性能差距原因分析与最小复现；这些不属于当前技能能力，也不自动实施优化。
