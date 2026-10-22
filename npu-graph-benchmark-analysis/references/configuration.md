# 首次使用：路径、连接与配置

技能不依赖 Windows、WSL、个人 PC 目录或原作者的服务器。可在 Linux NPU 主机直接执行、在已有容器执行，或从任意系统通过 SSH 操作。离线分析只需要日志和本技能内的 Python 脚本，不需要连接 NPU。

首次使用先从用户请求和当前工作区识别配置；只询问无法从已有信息确定且影响下一步的字段。不扫描个人凭据文件，不探测示例主机。路径未确定时不执行带占位符的命令。

| 配置 | 含义及要求 |
| --- | --- |
| 执行方式 | 直接在容器/主机，或 SSH 到已授权主机后 docker exec；不要求 WSL |
| 连接与容器 | 远程时提供 SSH 别名/用户/端口/跳板机及容器名；支持已配置的 SSH config/agent。未提供就不要假定 root、22 端口或某个 IP |
| 项目目录 | 默认在实际运行主机/容器获取源码；已有仓库模式使用用户提供的 checkout 或解压目录，不要求 PC 上有源码 |
| 容器工作目录 | 运行/构建产物所在目录；与宿主机挂载目录分别记录，不能相互混用 |
| 输出目录 | 用户指定的可写目录，按版本、模型、模式和时间隔离；可全程存远端，PC 回收目录可选 |
| Python / 激活入口 | 容器内实际解释器、venv 和 CANN 环境入口；逐项验证路径，不猜测 /opt 下的布局 |
| README / runner | benchmark 任务需要实际 README、torchbench.py 位置与源码版本；两者可能不在同一机器 |
| 镜像 / 设备 / 构建工具 | 创建环境时提供可获得的兼容开发镜像与 NPU 运行时，按实际架构、驱动和 CANN 核实 |

可在当前项目保存一份不含秘密的运行配置/任务记录。推荐字段：`execution_mode`、`ssh_target`、`container`、`host_workspace`、`container_workspace`、`project_root`、`readme_path`、`runner_dir`、`python_bin`、`cann_env`、`venv_dir`、`source_dir`、`output_root`、`artifact_destination`。这是记录约定，不是程序会自动加载的配置文件；命令须从已核实值生成。

## benchmark 源码来源开关

| 字段 | 默认 / 说明 |
| --- | --- |
| `benchmark_source_mode` | `remote_git`（默认）或 `existing_checkout` |
| `benchmark_repo_url` | `https://gitcode.com/Ascend/pytorch`；指包含 Ascend benchmark runner 的仓库，不是预先假定的 PC 路径 |
| `benchmark_ref` | 优先使用用户指定的分支/tag/commit；未指定时查询远端默认分支 HEAD 并固定本次实际 commit，不永久写死主干名 |
| `benchmark_checkout_dir` | 实际执行主机/容器中的独立目录，按当前可写工作目录确定；不能指向未授权覆盖的既有目录 |
| `benchmark_existing_path` | 仅 `existing_checkout` 必需，为已有仓库/解压目录在所在机器的实际路径 |
| `benchmark_readme_relative` | 候选 `benchmarks/torchbench/README.md`，先核实仓库内容；路径变动时查找并确认，不能假定永久存在 |

这是供技能生成命令时使用的工作流开关，不是 `torchbench.py` 的 CLI 参数，也不代表现有启动脚本自动读取配置。用户可直接说“默认远程仓库”或“切换已有仓库，路径为……”。不得把上述字段传给 runner。

### remote_git（默认）

1. 在实际运行主机或容器查询仓库、ref 和 README；PC 仅作为控制端，无需本地 clone。根据连接和挂载关系确定独立 checkout 目录，记录命令在哪台机器执行。
2. 在该目录不存在时 clone；固定指定 ref 或已查询的默认 HEAD。若目录已存在，先检查远端 URL、commit、未提交修改，不自动 reset/clean/pull；改用新目录或按当前用户授权复用。
3. checkout 后读取真实 README 和 runner，记录 remote URL、请求 ref、实际 commit；如果尚无本地 checkout，可先用可用的代码浏览/API 阅读指定 ref 的 README。不能只用网页 URL 当作可执行代码目录。
4. 按 README 获取其要求的 TorchBench 模型仓库、依赖和子模块，同样放在运行端并固定版本。Ascend runner 仓库与模型仓库不是同一资产，不能漏掉后者。
5. 对照复测应复用此前已记录的 runner/模型 commit，避免每轮追踪新 HEAD 引入变量。只有用户要求升级源码时才更新。
6. 运行端 GitCode 无法访问时报告具体缺口，可在授权范围使用用户提供的源或源码包，不悄悄退回 PC 的私有目录，不擅自换仓库。

### existing_checkout

使用用户明确提供的路径和所在机器，不要求其一定是 PC/WSL。读取当前 README，记录实际 commit 与工作区修改；不自动同步远端。源码包则记录来源与 SHA256。如果需传到运行容器，仅同步本任务必要源码和版本证据，不传个人凭据。

仅分析已有日志时，两种源码获取流程均跳过；若需要解释 runner 计时语义而源码证据不足，明确该缺口。

## 凭据和远程执行

- 使用用户现有的 SSH key、agent、SSH config 或授权连接工具；不得要求把密码发到聊天，不内置密码文件位置或读取个人文件的逻辑。无认证方式时请用户在其环境配置。
- 校验主机身份，不关闭 host key 检查来绕过变化。任何凭据、token、私钥均不写入脚本、日志、技能或产物包。
- SSH 连接信息与容器内路径分开处理。检查版本、运行 NPU 或构建依赖时在目标容器内执行，不能拿宿主机的 import 结果替代。
- 传输只使用当前连接实际可用的 scp、sftp、rsync 或文件工具；若大文件传输卡住，排查并降低并发/缓冲，不无限重试。
- 收集已有授权内的证据，保留旧环境和产物；不终止其他人的任务。特权容器需要当前用户/环境的授权，历史实例的授权不可沿用。

## 携带与安装

分享整个技能目录，保留 `SKILL.md`、`references/`、`agents/` 及存在的 `scripts/` 相对结构。Codex 用户将文件夹放到自己的 `$CODEX_HOME/skills/`；未设置时使用其用户目录下的 `.codex/skills/`，不使用原作者的安装路径。其他技能运行器按其目录约定加载 `SKILL.md`。

技能中的相对引用以该技能目录为基准，不是当前 shell 目录；使用附带脚本时先解析技能实际安装位置。除 Python 3 标准库外，耗时汇总脚本不需要额外依赖；环境构建仍需远端 NPU 驱动、CANN、Docker（使用容器时）及官方源码要求的工具。
