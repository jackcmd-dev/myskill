# PyTorch 2.14 的 Triton Ascend 兼容性排查

本参考来自2026-10-26实测，针对triton_experimental准备环境。TritonMissing不一定表示未安装Triton；同为2.14的开发快照也可能位于不同接口边界。以下提交是已验证案例，不是适用于所有2.14或2.13/2.15的默认版本。

## 先取证再选择修复

在实际任务容器、激活同一CANN/Python环境后，记录sys.executable、torch/torch_npu完整版本与源码commit、triton.__version__/__file__及triton-ascend distribution版本。使用同一解释器的`python -m pip show torch torch-npu triton triton-ascend`辅助检查；包元数据存在不代表被导入的模块来自该安装。对照实际benchmark README安装要求，不直接运行可能替换目标torch的整份requirements。

| 症状/证据 | 应检查什么 | 处理方向 |
| --- | --- | --- |
| import triton失败，或triton-ascend无安装记录 | 解释器、激活入口、包路径、README要求 | 确认确实缺依赖后再按目标组合安装，保护torch版本 |
| CompiledKernel.launch_enter_hook属性缺失 | torch_npu使用的Triton接口与实际Triton源码 | 需要对应API适配；反复重装同版本不能解决 |
| 已能import但图编译报TritonMissing | 在导入torch_npu后的同一进程检查torch.utils._triton.has_triton实现、实际支持设备及插件兼容补丁 | 区分NPU未被识别与缺安装；检查真实源码，不能只按2.14版本号推断 |
| eager也不能枚举设备 | 宿主机设备健康、驱动挂载、容器权限和可见卡设置 | 返回远程容器/驱动排查，不能把它当成Triton安装问题 |

保留每次失败的报错、完整版本、导入路径和源码证据。has_triton可能有缓存，变更插件后用新进程复验。不要通过强制返回True、伪造版本字符串、运行时monkey patch或静默更换后端绕过兼容问题。

## 本次遇到的两个独立兼容问题

1. 旧torch_npu提交ee7bc39访问`CompiledKernel.launch_enter_hook`，实际Triton 3.6的对应接口已经迁移到`knobs.runtime.launch_enter_hook`，图编译失败。此时triton-ascend已经安装。
2. 改用当时官方main提交`14dc54e6f23cb882d675256fca2c1ae648819959`后，hook问题消失，但仍报TritonMissing。该插件对torch>=2.14假定上游已使用可注册的设备识别，跳过旧has_triton兼容补丁；固定的torch开发快照`69231fe37ab3b5d45ad5c4e6e81203be66be42cf`仍使用cuda/xpu/cpu/mtia固定列表，没有NPU。仅凭主版本匹配无法排除该问题。

用户批准后，固定官方历史main提交`85dbdb5fa1059aab0f537b7546649fac1b96ebbb`构建torch_npu。该提交同时具有Triton 3.6 hook适配和旧NPU识别补丁，未修改算子计算实现。若用户要求最新main，应先给出证据和候选版本方案供确认，不能静默固定历史提交。新主干可能已修复或改变接口，仍须按本次目标源码实测，不把本案例永久当成最新兼容结论。

## 已验证组合与验收

- ARM64、Ascend 910B4，驱动26.1.1。
- PyTorch `2.14.0a0+git69231fe`，完整commit见上。
- torch_npu `2.14.0a0+git85dbdb5`，完整commit见上；来源`https://gitcode.com/Ascend/pytorch`。
- CANN 9.2.0正式版；实际导入triton 3.6.0，triton-ascend `3.6.0+git0cfb1708`。
- Inductor + triton_experimental，ACLGraph关闭，不传动态shape参数。

构建和安装必须针对目标解释器及torch；已核实依赖后可用`python -m pip install --no-deps <已构建wheel>`保护固定框架，保存wheel SHA256与版本证据。这不是省略依赖检查的理由。

环境验收需包含：eager前后向、目标后端编译输出与梯度对齐、实际backend与ACLGraph配置、同轮前后向FX/生成代码/融合前后IR、debug+profiler同开的小型验证及非空kernel/task和可读数据库。仅import成功、has_triton=True或DVM成功不足以通过。

本组合已通过上述小型验证及DCGAN判别器训练的范围、效果、双关基线采集，精度均通过；不据此宣称其他模型或软件组合均已验证。复用者需重新执行自身环境的小型验收。环境报告应保留失败尝试、最终版本及授权的版本变更；性能数据由采集技能单独报告。
