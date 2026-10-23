# 安装与验证流程

目标是PyTorch2.14 + torch_npu + CANN9.2.0正式版，目录全部从当前执行上下文发现。远程SSH/容器由 `npu-remote-container` 处理；本文件不提供固定主机或密码位置。

## CANN与框架来源

先核对CANN元数据及实际激活/库路径。官方镜像清单：https://github.com/Ascend/cann-container-image/blob/main/OVERVIEW.zh.md 。本实例采用其中9.2.0-910b-ubuntu22.04-py3.12-devel的ARM64版本；其他硬件必须按实际芯片选型，不能把910B镜像用于所有设备。查询当前官方兼容要求，不能凭版本大小保证驱动兼容；不得顺便升级共享宿主机驱动。

可选两条安装路线，均需验证：

- 在官方CANN开发镜像中安装目标PyTorch2.14与源码构建torch_npu，使用隔离Python环境，避免通用requirements替换目标torch。
- 复现既有2.14软件栈时，在新镜像组合官方CANN9.2.0组件与原框架/插件，明确来源、复制边界与激活入口；即使保留旧CANN文件，实际加载必须为目标版本。未经验证不能认定旧插件必然兼容新CANN。

没有现成2.14构建时核实官方产物或源码来源、目标ref、Python/架构，保留wheel或构建日志与SHA256；不能改用2.13或最新其他版本继续并标成2.14。

## torch_npu源码构建

新安装默认从GitCode Ascend/pytorch主干查询并固定HEAD，不把历史master当永久分支名。读取源码构建说明、AGENTS.md、requirements、ci/build.sh、setup.py及.gitmodules，固定子模块；通用requirements可能要求其他torch版本，不直接全量覆盖目标环境。

以下变量都来自已核实的容器内路径/配置；未设置不得运行：

```bash
source "$CANN_ENV"
source "$VENV_DIR/bin/activate"
unset TORCH_VERSION PYTHONPATH
export PYTHONNOUSERSITE=1
cd "$TORCH_NPU_SOURCE_DIR"
export MAX_JOBS
export CMAKE_BUILD_PARALLEL_LEVEL="$MAX_JOBS"
bash ci/build.sh --python="$PYTHON_MINOR"
```

先确认当前入口不传--torch时会读取实际已安装torch；机制变化按官方说明调整。设置资源允许的构建并发，保存commit、子模块、命令、日志、退出码和产物SHA256。安装后从真实解释器检查torch_npu版本、路径及依赖。已有环境不一定使用venv；明确当前解释器即可，不为形式统一重装已验证框架。

## 激活与验证

CANN set_env可能不兼容shell nounset；不要因此修改厂商脚本，可用set -eo pipefail加载。自动化显式激活或调用准确解释器，docker exec python不会自动读取.bashrc。清除旧CANN路径污染时保留框架必要路径，不破坏NPU可见设备变量。

记录torch.__version__/__file__/git commit、torch_npu.__version__/__file__、Python、Triton import与distribution版本、CANN完整版本和安装元数据、驱动、激活环境及/proc/self/maps中的实际CANN库。不能把CPU wheel后缀解释为未使用NPU。

使用远程技能分配的单卡，验证NPU加法、eager反向、目标后端（本项目Inductor+DVM+默认ACLGraph）的前后向正确性与同步。随后在编译完成后对小算子做独立profiler验证，避免嵌套profiler。检查CSV、时间线、有效步与数据库TASK记录，保留失败与成功报告。这些是小型环境检查，不运行模型benchmark或报告加速比。

环境报告必须区分核心路径通过、pip check完整状态、辅助工具缺口及尚未测试的模型需求。若核心路径不兼容，报告阻塞，不擅自关闭后端或改源码宣称就绪。交付后停止；只有用户另行请求的数据采集才交接采集技能。
