# 采集输入与源码来源

使用已有容器/已附着会话，或远程技能提供的execution_context.json，以及环境准备技能提供的environment_report.json。没有固定PC/WSL路径。凭据和容器生命周期由npu-remote-container负责，本技能不读取密码文件、不创建容器、不安装或升级torch/torch_npu/CANN。

首次只确认模型、PyTorch版本、训练/推理及本次阶段；已提供的信息不重复询问。默认CANN9.2.0正式版，模型软件与数据依赖应在环境阶段准备；只读检查缺口后返回环境技能处理。当前请求仅采集时，不自动执行安装。

记录实际解释器与激活路径、源码/runner/README位置、输入shape/dtype/batch、后端、ACLGraph和独立输出目录。路径由运行端发现，执行上下文里区分宿主机和容器目录。报告与回收目录由当前工作区或用户要求确定；可以全程留在远端。

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


## 与其他技能的交接

需要SSH或Docker操作时使用npu-remote-container；已有可用执行上下文则不重复连接。软件版本/依赖不满足时说明差异，只有当前用户授权准备环境时才转交pytorch214-npu-environment；否则交付缺口并等待，不扩大“只采集”的范围。设备分配由远程技能执行，采集保持同轮固定主机/卡。

技能脚本路径以实际安装位置解析；scripts/summarize_timings.py仅依赖Python3标准库。离线汇总只要已有日志，不依赖另两个技能或NPU连接。分享时保持技能目录相对结构，安装到接收者自己的技能目录。
