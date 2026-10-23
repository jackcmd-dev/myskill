# 采集与分析细则

## 环境和工作负载

新采集要求 **CANN 9.2.0**。记录实际版本元数据、激活入口和动态库路径，并核实硬件/驱动/torch_npu兼容要求及小型验证结果；版本不符不启动benchmark，不把已完成的9.1.0数据改标为9.2.0。更换CANN后是新软件栈，应新建结果目录并注明与历史基线的差异。

先按 [配置文档](configuration.md) 解析源码来源开关：默认 `remote_git`，在运行主机/容器获取 `https://gitcode.com/Ascend/pytorch` 并固定 commit；`existing_checkout` 使用用户现有路径。接收方 PC 不需要 checkout。每次对照复测沿用已记录源码版本，不自动更新 HEAD。

在容器中检查真正被导入的框架及插件，不把宿主机 Python 或容器标签当作证据。记录 Python、torch、torch_npu、triton/triton-ascend、CANN、驱动、镜像 ID、runner/TorchBench 提交、依赖来源、输入 shape、batch、dtype、训练/推理、后端及 ACLGraph 设置。版本不符就停止该版本采集；不要回退旧版本并标成新版本。

README的通用requirements覆盖多种模型；本技能只检查实际模型所需依赖，缺口交给环境准备技能按当前授权处理，不直接pip安装或覆盖框架。新版本依赖与实际import需独立核实。

检查 `Model.get_module()` 和 runner 的执行路径。DCGAN 本项目返回判别器，accuracy 流程编译模型并执行训练步骤，不能描述为完整 GAN 交替训练；`--training` 也不自动保证模块处于 `model.train()`，实际 train/eval 规则必须查 runner。

远程凭据、SSH、容器生命周期与传输由npu-remote-container负责，本技能只消费脱敏执行上下文，不读取密码文件。按实际本地或远程执行方式生成命令；复杂多层 shell 转义优先使用脚本，SSH 使用已校验的主机密钥。不要求 Windows 或 WSL。若二进制/较长标准输入传输停滞，改用已验证的 `scp -X buffer=1024 -X nrequests=1` 上传脚本再执行，记录失败而不是无限重试。

## 运行时选卡（交给npu-remote-container执行）

容器支持候选设备访问，不在创建时固定某个任务的卡。任务启动器读取 `npu-smi info`，要求健康正常、无进程、计算利用率为 0、空闲显存足够。DCGAN FP32 batch64 曾使用 16384 MB 门槛；其他模型应按需求调整，不泛化为所有模型的需求。

从符合条件的卡中选择，取得协作文件锁后再次检查。通过任务的 `docker exec -e ASCEND_RT_VISIBLE_DEVICES=<物理卡>` 设置单卡可见性，必要时同步项目工具的 NPU_ASSIGNED_DEVICES；在 Python 导入/初始化 NPU 前生效。记录物理卡和逻辑 npu:0 的映射，同一轮 eager/compile、推理/训练不换卡。任务退出释放锁。

这些变量不是特权容器的安全隔离。锁只约束遵守同一机制的任务，不能阻止其他使用方中途抢卡；需要独占保证时协调使用方或调度系统。不能停止其他人的进程。设备占用时不无休止重建容器。

## README 命令模式

路径与连接先按 [配置文档](configuration.md) 核实。以下为已用于 2.14/2.13 DCGAN 的模板，应用于其他版本前检查 README、`--help` 及源码参数。环境初始化、PYTHONPATH、目录应按实际容器设置。可复用 shell 启动器做日志/选卡，但不要修改测量函数或模型。

基础参数：

```bash
python -u torchbench.py --accuracy --cold-start-latency \
  --training --float32 --backend inductor --npu-backend dvm \
  --only dcgan --batch-size 64 --iterations 50 \
  --output "$root/accuracy.csv"
```

推理改为 `--inference`。DVM 是本项目 DCGAN 已确认配置，不是所有模型都必须采用的后端。`--backend inductor` 选择编译路径；accuracy 原生流程分别执行 eager/compile 并校验结果。当前 performance 的 `--execution-mode both` 与 accuracy 的编译覆盖范围不完全相同，不能随意混用。

### 融合范围

```bash
export TORCH_COMPILE_DEBUG=1
export TORCH_COMPILE_DEBUG_DIR="$root/debug"
export TORCHINDUCTOR_CACHE_DIR="$root/inductor_cache"
export TORCH_LOGS=graph_breaks,recompiles
```

完整回收本轮debug目录，包括ir_pre_fusion.txt与ir_post_fusion.txt，不只收提取的目标文件。每轮使用隔离缓存，防止命中旧缓存导致缺少目标 dump。运行后遍历全部图，配对同目录 `fx_graph_readable.py` 与 `output_code.py`，保留原始路径并提取副本、计算 SHA256。训练寻找 forward/backward，也保留其他片段；不要求一定各一个。目录名 inference 可能表示不带反向的参数更新片段，需看内容而非按名字误判。

FX 反映该编译阶段图（可能已分解/变换），检查 `torch.ops.aten` 和 `torch.ops.npu`；生成代码检查外部库调用、DVM/Triton kernel、图片段和编译边界。不要假设所有 output_code 都有 Triton，或一个 kernel 对应一个原始算子。训练图、优化器是否被编译取决于具体入口。

### 融合效果

同时开启 debug 和 profiler，使性能记录可与同轮 FX/生成代码对应；不能只开 profiler 就认定该阶段收集完整。

```bash
export TORCH_COMPILE_DEBUG=1
export TORCH_COMPILE_DEBUG_DIR="$root/debug"
export TORCHINDUCTOR_CACHE_DIR="$root/inductor_cache"
export TORCH_LOGS=graph_breaks,recompiles
```

在基础命令增加：

```bash
--enable-profiler=0 --prof-output-path "$root/profile"
```

当前 2.14 runner 的此开关接在 accuracy 的 run_n_iterations 路径；不能只加到 performance 命令便声称完成采集。原生 schedule 为 wait=0、warmup=10、active=max(1,iterations-10)、repeat=1，50 次迭代得到 40 个有效 step；以当前源码和 profiler_info.json 为证据。编译在外层 profiler 启动前完成，防止编译/autotune profiler 嵌套破坏任务数据。

除以下 profiler 文件外，还需按融合范围流程回收本轮实际生成的全部 `fx_graph_readable.py` / `output_code.py`，保留 forward/backward 等图片段、路径、图中断日志和 SHA256。使用独立缓存并核验 dump 非空；两类产物必须来自同一轮，早先仅 profiler 的数据应标注缺少同轮 dump，不用其他轮次的文件冒充配对。该阶段耗时受 debug/profiler 影响，正式 E2E 加速比仍使用独立双关基线。

检查 `profile/<模型>/{eager,compile}/<run>_ascend_pt/ASCEND_PROFILER_OUTPUT/`。本项目实际包含 step_trace_time.csv、kernel_details.csv、operator_details.csv、task_time.csv、trace_view.json、SQLite db 及原始数据。字段和文件名随版本变化；本次实际没有 op_statistic.csv，不能写死其存在。验证非空 CSV、实际 step 数、时间线和数据库可读性，而非仅看退出码。数据库缺少关键任务数据时报告采集缺口。

README 默认 with_stack/record_shapes 为 false，不能声称已获取调用栈和 shape。若后续映射需要它们，先提交补采方案，不偷偷修改原生 profiler。未启用 profiler 的 runner 仍可能构造对象并产生未初始化清理警告，结合参数及产物判断，不能仅凭警告认定任务失败或 profiler 已开启。

将 kernel 与 FX/生成代码建立对应，再比较融合 kernel 与 eager 对应算子组；核查 ACLGraph 回放内部任务可见性、同步、CPU 下发及设备空闲时间。kernel_details 与 task_time 的行数可能不同，不直接当成融合数量或执行次数等价。kernel 耗时直接相加可能重复计算并行重叠，必须声明求和与时间线并集的区别。

### 性能基线

debug=0，删除 `--enable-profiler`（`=0` 表示 Level0 开启，不是关闭）及 profile 输出参数；保留同一 workload 和 README accuracy 基础参数。独立运行并保留每步日志，不混用 profiler 时间。

当前 runner 在 50 步中汇总第 16～40 步算术均值；不同迭代数需从源码或实际 summary 确认区间。加速比取相同口径的 eager/compile 均值之比；耗时下降为 (1-compile/eager)*100%。该值为整步 E2E，不是算子总时间。记录慢步但不擅自删去，单次测试可提供本轮数据，多轮统计需另行授权。

## 证据和交付

按版本/模型/模式/时间隔离目录；至少保存命令、退出码、实际环境、输入配置、log、accuracy、设备选择记录、debug/profiler 状态及产物 manifest。远端保留缓存，本地回收一般排除缓存、凭据及无关文件；下载后校验 SHA256。

三情况对比表列出 debug/profiler 开关、eager/compile E2E 均值、加速比、耗时下降及数据用途，并附原始记录。基线、范围、效果是互补证据，不把 profiler 放大的比值当真实优化收益。

有 GPU 同配置数据后，先核对模型入口、batch/dtype、train/eval、设备型号、计时范围、精度、ACLGraph/图执行与预热口径，再比较各设备内部加速比；不要仅比较 NPU/GPU 绝对时延或不同配置的比值。

原因报告应区分证据、推断和待验证假设，覆盖融合覆盖范围、分图/回退、kernel 效率、CPU 下发和回放/同步。复现应尽量缩小算子序列，保留真实 shape/dtype/布局、参数及梯度需求，给出 eager/compile、正确性及同步计时。不能为了简化改变导致问题的条件；未实际验证的复现注明未验证。不在阶段 1 实施优化。
