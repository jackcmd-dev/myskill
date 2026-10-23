---
name: npu-graph-benchmark-analysis
description: 在已准备好的NPU环境按Ascend TorchBench README收集融合范围、debug加profiler融合效果和无调试性能基线，汇总加速比、报告及最小复现；不安装环境或管理容器，支持离线日志分析。
---

# NPU 融合数据收集与分析

本技能只处理benchmark源码、审核后的运行、产物回收核验与分析。远程连接/创建容器用npu-remote-container；PyTorch2.14 + torch_npu + CANN9.2.0安装验证用pytorch214-npu-environment。已有可用会话或环境报告则直接复用，不重复要求安装其他技能。离线分析只需要日志。

## 输入与执行边界

先读 [采集输入与源码](references/configuration.md)，确认模型、版本、训练/推理、阶段和执行环境。新采集要求CANN9.2.0正式版，核实实际版本/路径；历史9.1.0数据保留真实标签。环境不匹配则返回缺口，不自行安装、换版本或创建容器。调用其他技能不扩大用户授权。

源码来源benchmark_source_mode默认remote_git，仓库https://gitcode.com/Ascend/pytorch，在运行端获取，PC无需下载；existing_checkout使用指定已有源码。复测固定原runner和模型commit，不自动更新HEAD。

benchmark前提交实际方案、完整命令、配置、统计口径和预期产物供审核；已批准同一方案不重复询问。只执行当前阶段，不自动跑GPU或实施优化。

## 采集流程

1. 每个新模型/版本读取实际README和runner，核实参数、模型入口、前后向/优化器范围、dtype/batch、后端和计时语义。细则见 [采集与分析](references/workflow.md)。
2. 请求远程技能按任务需求选空闲卡并持锁，初始化NPU前设置可见设备；同轮eager/compile固定同主机同卡。不共享忙卡、不终止其他任务，不在不同主机拼接一轮数据。
3. 按下表运行用户批准的阶段，使用版本/模型/阶段/时间隔离的目录和编译缓存：

   | 采集 | Debug | Profiler | 主要产物 |
   | --- | --- | --- | --- |
   | 融合范围 | 开 | 关 | 完整debug目录及前向/反向FX、生成代码、融合前后IR |
   | 融合效果 | 开 | 开 | 同轮完整debug目录、profiler原始数据与解析结果 |
   | 性能基线 | 关 | 关 | eager/compile逐步E2E耗时与正式加速比 |

4. 完整回收debug目录（存在时）、profile目录（存在时）、日志、精度、命令、真实环境和设备记录，生成SHA256清单；编译缓存默认留远端。额外提取并索引fx_graph_readable.py、output_code.py、ir_pre_fusion.txt、ir_post_fusion.txt。不能只收提取副本丢掉原始目录；某后端未生成目标文件时报告缺口，不伪造或拿其他轮产物补齐。
5. 核验退出码、实际迭代、精度、dump非空及前向/反向、profiler有效步/CSV/数据库，下载后核对SHA256。交付产物路径和按请求生成的表格、融合映射、原因报告/最小复现。技术案例见 [历史结果](references/project-history.md)，不要求原案例资产存在。

## 计时与脚本

加速比使用同轮eager/compile原始单步均值之比，显示时四舍五入，不删慢步或用中位数替代。默认50步案例取原生第16～40步；实际区间从当前runner核实。debug/profiler轮仅为观测，正式基线必须双关；独立轮、不同卡/主机/软件栈的差异不直接归因于开关或框架。

Python3标准库脚本scripts/summarize_timings.py输出CSV、JSON、Markdown，不运行benchmark、不判定环境有效性；使用实际技能安装目录和日志路径：

```bash
python "$SKILL_DIR/scripts/summarize_timings.py" \
  --run "scope=$SCOPE_LOG" --run "effect=$EFFECT_LOG" \
  --run "baseline=$BASELINE_LOG" --output-dir "$REPORT_DIR"
```

GPU数据到齐后先核对工作负载和计时口径，再比较设备内部加速比。数据收集不自动包含GPU运行或阶段2优化实施。
