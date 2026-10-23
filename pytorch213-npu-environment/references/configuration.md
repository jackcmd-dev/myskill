# PyTorch2.13环境输入与交接

目标明确为PyTorch2.13 + torch_npu + CANN9.2.0正式版。实际路径从当前容器发现，不依赖作者PC或内网。

已有执行上下文则直接复用；需要连接或创建容器时使用npu-remote-container，由它处理仅IP、用户名、密码的连接文件、容器归属、设备选择和文件传输。本技能不维护第二份凭据模板，不直接执行SSH或选择他人容器。

检查与安装在目标容器内进行；已有正式2.13 wheel可按实际Python/架构核实来源及SHA，其他2.13开发构建须记录完整版本/commit。源码torch_npu默认固定官方当前主干HEAD，实际根据已安装PyTorch版本构建。历史构建机制变化时按当前源码处理。

交付environment_report.json，记录实际解释器/激活入口、组件版本/路径/来源、设备/编译/profiler小型验证、依赖缺口及核心路径是否就绪。环境技能不跑模型benchmark；模型数据交给npu-graph-benchmark-analysis在用户批准后收集。
