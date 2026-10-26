# 技术案例：DCGAN 2.14 / 2.13（2026-10-22）

2026-10-26默认采集策略更新：新任务使用triton_experimental、关闭ACLGraph、不启用动态shape，具体命令见[采集流程](workflow.md)。同日已在ARM64/910B4、驱动26.1.1、torch2.14.0a0+git69231fe、torch_npu2.14.0a0+git85dbdb5、CANN9.2.0、triton3.6.0及triton-ascend3.6.0+git0cfb1708上完成DCGAN判别器训练三类采集，精度均通过。双关基线复测eager7.824547598 / compile4.801735200 ms，1.629525010×；首次高波动基线独立保留，不混用数据。插件兼容问题及完整提交见2.14环境技能的references/triton-compatibility.md。下述DVM等历史实测记录不改标，不是当前新采集默认值。

本页记录的既有测量使用 **CANN 9.1.0**。技能当前新采集目标为 **9.2.0**，历史数据及其版本保持不变，不视为9.2.0基线。

这些是历史结果，不是默认运行配置。原始日志、镜像和项目脚本不随技能分发，不要求访问原作者的 PC 或内网；新任务须独立核实环境并生成证据。

2026-10-23 采集要求修正：融合效果必须同时开启 debug 和 profiler。以下 2.14/2.13 历史 profiler 轮实际均未开启 debug，保留其真实性能记录，但缺少同轮编译 dump，尚不满足修正后的完整融合效果采集要求；不能标为已经补采完成。历史开关和数值不改写。

## 路径和版本

- 镜像：sha256:57d673994d63274b4fb409c5b411cec67a70cf4bbcd1ba0c0ec4955e718cac5a。
- torch 2.14.0a0+git69231fe，commit 69231fe37ab3b5d45ad5c4e6e81203be66be42cf，导入 /opt/npu-env/pytorch/torch/__init__.py。
- torch_npu 2.14.0+gitee7bc39；Python 3.12.13；CANN 9.1.0；驱动工具 26.0.rc1；Ascend910B4 32GB。
- Triton import 3.5.0 与 triton-ascend distribution 3.6.0+git0cfb1708 曾存在差异，报告时分别记录。
- runner commit 2c8682df9271e545e7f50f8c45e2395563a05483；TorchBench fb14629994956c16d27c7a9940c5f081afbf68dc。
- 源码包 SHA256：ascend_torchbench_runner_2c8682d.tar.gz 为 8153932cda25ec87ef1d849e635611c0b3e87a1db5f19bdf20f4912476cdf13e；torchbenchmark_fb146299.tar.gz 为 6caca9b6b742a6a6795f01fa2abffaf79ca9a6b27ac3cfd3a1b88f825a85598d。
- 新目录只额外安装 tqdm==4.67.1 到 /workspace/deps，没有直接安装整套通用 requirements 或复制旧二进制依赖。

## 案例启动方式（不随包分发）

案例使用项目启动器做自动选卡、日志保存和容器执行；启动器不是本技能的依赖。新用户按自己的配置生成命令，不能假定旧项目脚本可用。

## 已完成的正式 README 数据

以下目录位于项目 artifacts/dcgan/，对应容器 /workspace/results/ 下同名目录。三轮均物理卡 5、FP32、batch64、DVM、训练精度 pass_accuracy。均值为原始日志第16～40步。

| 数据目录 | Debug | Profiler | eager ms | compile ms | 加速比 |
| --- | --- | --- | ---: | ---: | ---: |
| dcgan_fusion_scope_readme_20261022_070459 | 开 | 关 | 7.686688798 | 4.666181980 | 1.647318692x |
| dcgan_fusion_effect_readme_20261022_072106 | 关 | Level0 | 16.729846410 | 5.001448421 | 3.345000288x |
| dcgan_baseline_readme_20261022_074214 | 关 | 关 | 7.708662758 | 4.589032028 | 1.679801472x |

基线耗时降低 40.4692%；eager 选取区间含约14ms慢步，未剔除。1.68x 是本轮训练 E2E 基线，不是 GPU 比值或多轮稳定结论。

scope 同时采集推理：1 个 inference 图；训练：1 个 forward 图、1 个 backward 图，共6个目标文件，各有 fx_graph_readable.py/output_code.py。README accuracy 流程未生成单独 SGD 更新图。

profile 只采集训练，50次迭代、40 active steps，每种模式均有 step_trace_time、kernel_details、operator_details、task_time、trace_view 和 db。kernel_details 行数 eager3440/compile3160，task_time 行数不同，不能解释成融合数量。199个文件回收校验通过。

本地报告：DCGAN_README_scope_collection.md、DCGAN_README_effect_collection.md、DCGAN_README_training_baseline.md、DCGAN训练模式_三种采集配置耗时与加速比对比.md。完整归档分别为 dcgan_scope_readme_evidence.tar.gz、dcgan_effect_readme_evidence.tar.gz、dcgan_baseline_readme_evidence.tar.gz。

## 历史尝试的边界

更早的 performance 包装脚本数据、图中断及 SGD 更新图与上述 accuracy 路径不同，只保留为历史，不能混入同配置对照。DLRM 已由用户暂停，不继续诊断。GPU dump/profiler 未提供，因此尚未完成 NPU/GPU 差距分析；还未实施优化。

## 2.13 已完成数据

相同 runner/TorchBench 提交，torch 2.13.0+cpu，torch_npu 2.13.0+git7f86549。三轮 FP32、batch64、DVM、训练精度通过，原生第16～40步均值：

| 配置 | 物理卡 | eager ms | compile ms | 加速比 |
| --- | ---: | ---: | ---: | ---: |
| debug 开、profiler 关 | 2 | 19.658041615 | 4.646768775 | 4.230475534x |
| debug 关、profiler Level0 | 2 | 7.721860800 | 4.804286808 | 1.607285557x |
| debug 关、profiler 关 | 5 | 8.950306019 | 5.620081220 | 1.592558127x |

双关基线耗时降低37.2079%。存在单步波动且卡不同，不能将三轮差异全部归因于开关；debug轮4.230x不是正式基线。2.13与2.14的torch_npu commit不同，不是仅变PyTorch的单变量实验。

## CANN9.2.0正式版2.14三轮（2026-10-23）

torch2.14.0a0+git69231fe，torch_npu2.14.0+gitee7bc39；FP32 batch64 DVM训练。scope debug开/profiler关，17.749383580 / 4.607701600 ms，3.852112207x；effect双开，约7.734 / 4.877 ms，观测1.585738845x；baseline双关8.305478375 / 4.884313224 ms，正式1.700439344x，耗时下降41.1917%。三轮精度通过，物理卡分别5/1/3，不把轮间变化直接归因于开关。记录精度数值以原日志为准。

scope/effect完整debug已回收，各有前向/反向FX、output_code和融合前后IR；effect两模式各40个有效profiler步，原始/解析profile已回收。42/222/18个清单文件分别SHA校验通过。这是实际历史案例，不提供默认个人容器或主机。
