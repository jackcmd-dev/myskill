# 安装、源码构建与验证

这些命令是已验证流程的模式，执行前按实际镜像、Python版本、目录和当前主干源码检查；不要对已有环境直接运行创建、覆盖或清理操作。

## 基础容器与隔离环境

本技能目标为 **CANN 9.2.0**。选择或准备含该版本的独立环境，按官方要求核对硬件/驱动及当前 torch_npu 源码兼容性；记录实际版本元数据、安装/激活路径和包来源。不能把历史基础镜像中的9.1.0直接视为满足条件，不能通过改目录名或版本文件代替安装。此文后续命令仍是历史流程模板，使用9.2.0后必须重新通过依赖、小型NPU计算及编译前后向验证；不得擅自改宿主机驱动或覆盖旧结果环境。

将明确的目标镜像、工作目录和只读驱动挂载要求交给npu-remote-container创建本任务容器；本技能只负责容器内软件准备，不直接管理Docker或主机连接。不要在创建时绑定某张正在使用的NPU。

基础镜像可以含2.14，但目标2.13必须位于不继承系统site-packages的venv：

命令变量来自 [配置与连接](configuration.md)；执行前核实 `CANN_ENV`（CANN 激活脚本）、`BASE_PYTHON`（基础解释器）、`VENV_DIR`（隔离环境目录）、`SOURCE_DIR`（源码目录）、`SOURCE_BRANCH`（已查询的主干名）、`PYTHON_MINOR`（如 3.12）和 `MAX_JOBS`（构建并发）已赋值。路径均指目标容器内部，它们不是预设环境变量。

```bash
source "$CANN_ENV"
unset PYTHONPATH
export PYTHONNOUSERSITE=1
# 仅当目标不存在时创建；不要覆盖已有venv
"$BASE_PYTHON" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
```

CANN的set_env脚本曾在shell `set -u` 下产生未定义变量提示，加载时避免使用nounset；可使用 `set -eo pipefail`。不要因此声称CANN已不可用或直接修改厂商脚本。

官方PyTorch CPU wheel索引：`https://download.pytorch.org/whl/cpu`。安装 `torch==2.13.0+cpu`，匹配Python/架构/glibc。若官方依赖下载慢，可保留官方torch包，用已批准可信索引安装其声明依赖；使用 `--no-deps` 后必须补齐真实依赖并执行pip check，不能忽略依赖缺失。

```bash
python -m pip install --no-deps --index-url https://download.pytorch.org/whl/cpu 'torch==2.13.0+cpu'
```

从wheel元数据确定依赖，当前实例涉及filelock、typing-extensions、setuptools、sympy、networkx、jinja2、fsspec及传递依赖。目标环境不安装预编译torch_npu；如果任务中途从预编译改为源码，应先确认旧安装进程是否仍在运行，停止仅属于本任务的旧流程后再继续。

## 固定主干并检查构建需求

```bash
git ls-remote --symref https://gitcode.com/Ascend/pytorch.git HEAD refs/heads/main refs/heads/master
# 将已查询确认的主干分支填入 SOURCE_BRANCH；不把历史 master 当作永久默认
git clone --depth 1 --branch "$SOURCE_BRANCH" https://gitcode.com/Ascend/pytorch.git "$SOURCE_DIR"
cd "$SOURCE_DIR"
git rev-parse HEAD
```

读取适用AGENTS.md、version.txt、requirements-build.txt、requirements.txt、ci/build.sh、setup.py和.gitmodules。主干支持多个torch版本，requirements仍可能固定2.15 nightly；不要直接pip install整份requirements覆盖2.13。基于当前源码准备所需工具，记录任何选择性安装差异。

已验证主干的工具需求涉及PyYAML、typing-extensions、setuptools>=81、wheel>=0.45.1、CMake、NumPy、Ninja、nanobind>=2.9及auditwheel。实例中使用wheel0.45.1；这些为历史需求，不对未来源码盲目锁死。

```bash
git submodule update --init --recursive --jobs 4
git submodule status --recursive
```

让.gitmodules决定固定子模块及update=none规则，不擅自把每个子模块切到最新分支。初始化可能包含op-plugin、DVM、TorchAir、Tensorpipe、ACL头文件等组件，保持上游默认配置，除非用户明确要求精简。

## 按已安装torch自动构建

```bash
source "$CANN_ENV"
source "$VENV_DIR/bin/activate"
unset TORCH_VERSION PYTHONPATH
export PYTHONNOUSERSITE=1
cd "$SOURCE_DIR"
# MAX_JOBS 已按当前资源选择
export MAX_JOBS
export CMAKE_BUILD_PARALLEL_LEVEL="$MAX_JOBS"
bash ci/build.sh --python="$PYTHON_MINOR"
```

当前入口不传--torch时读取实际已安装的PyTorch并生成对应版本包；本项目日志为 `Using PyTorch 2.13.0+cpu`。检查构建输出是否确为2.13，不能仅凭version.txt含2.13就认定产物正确。源码若变更此机制，应按新的官方入口处理并解释差异。

先核查nproc、共享负载、内存/磁盘再设置并发，不直接使用全部CPU。本次256 CPU先8路、资源核实后32路增量完成。需要调整时，先停止本项目构建树并确认退出，再增量恢复，保存前次日志；不要并发运行两个构建器写同一build目录，也不要kill其他人的编译进程。

生成wheel后校验名称、Python/架构、版本、SHA256，再在独立venv安装。已补齐依赖时可 `pip install --no-deps <精确wheel路径>`，防止重新解析覆盖torch版本；之后pip check和pip freeze。

## 默认shell与自动化入口

激活脚本应先加载CANN、清除外部PYTHONPATH、设置PYTHONNOUSERSITE，再source 实际 venv/bin/activate。新容器的交互/登录shell在旧基础镜像的激活逻辑之后加载此脚本，并实测最终解释器。

Docker容器环境变量不会因修改.bashrc自动更新；`docker exec ... python` 不加载shell配置。因此自动化使用 `bash -lc` 加载正确激活入口，或显式调用venv/bin/python并准备CANN环境。旧npu-mode/npu-run-suite可能硬编码旧解释器，不能以其名称推断版本。

## 运行时选卡与验证

由npu-remote-container在宿主机根据npu-smi查询候选卡，要求健康正常、无运行进程、计算利用率0、显存满足验证需求；实例使用至少16 GiB，可按模型/验证需求调整。取得协作锁后复查，在任务的docker exec上设置ASCEND_RT_VISIBLE_DEVICES和必要的NPU_ASSIGNED_DEVICES。设置之后才启动Python导入NPU；不要在无卡选择的常驻Python进程里初始化全部卡再尝试切换。

保存选卡快照、物理/逻辑映射；无空闲卡则退出或按用户要求等待。锁只约束遵守该协议的任务。容器提供候选卡访问不代表这些卡全部被任务占用。

验证清单：

1. PyTorch2.13与源码构建torch_npu2.13的实际版本、commit、导入路径都正确，来自隔离venv。
2. 记录pip check真实状态；模型/后端核心依赖必须满足，未使用辅助工具的缺口单独列明，不能说成全量依赖通过。实际import Triton与发行包版本分别记录。
3. 任务内只见1张卡，记录型号。
4. NPU加法结果正确；小型eager计算的反向结果正确。
5. 显式DVM后端，使用 `torch.compile(..., backend='inductor', mode='reduce-overhead')` 对小型算子序列前向和反向，核对eager输出与梯度并同步。不是跑benchmark，也不输出性能加速比。
6. 编译完成后独立对小型算子验证profiler采集和解析，检查有效步、非空kernel/task、时间线及可读数据库。不能用历史9.1.0结果替代2.13 + CANN9.2.0验证，也不运行完整模型。

本次最初出现TritonMissing，补装同2.14来源的triton-ascend3.6.0+git0cfb1708及其依赖后通过；不要泛化为所有2.13都必须使用此版本。包的Requires-Dist含triton==3.6.0，禁止忽略它仅靠改版本号或复制旧site-packages解决。记录import3.5.0与distribution3.6.0的真实差异，保留失败报告及最终报告。

环境问题若需要安装其他编译器/CANN或修改上游源码，应先评估其是否超出当前环境授权；小型验证通过不保证特定模型完整可运行。

## 交付

保存container creation记录、真实版本/路径、repo URL/主干commit、子模块版本、构建命令和退出码、wheel路径/大小/SHA256、pip freeze/check、依赖安装来源、验证结果和失败尝试。下载并校验manifest，默认不回收大型源码、缓存或wheel本体，除非用户需要。不得归档凭据、代理令牌或无关文件。

交付容器名、主机、进入命令、激活入口、已通过项及尚未执行的模型任务。不要在“准备环境”请求中顺便运行DCGAN benchmark或做优化。
