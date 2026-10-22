# NPU Skills

## 首次使用需要配置什么

连接配置只需要每台宿主机的 **IP、用户名、密码**：

```json
{
  "hosts": [
    {"ip": "填写主机IP", "username": "填写用户名", "password": "填写密码"}
  ]
}
```

复制技能内 `assets/connection.example.json`，在自己的私有目录保存并填写，之后向执行代理提供**文件路径**即可，不在聊天中发送密码。多台主机继续添加到 `hosts`，填写顺序就是检查顺序。容器、Python/CANN 路径和空闲卡自动检查，不需要配置。

另外在任务中说明要处理的模型、PyTorch 版本和步骤（环境准备、融合范围、融合效果或性能基线）。默认从 GitCode 在运行端获取源码，无需 PC 仓库路径；仅切换已有仓库模式时提供仓库位置。离线分析只需提供日志位置，不需要连接配置。

本仓库包含 `npu-graph-benchmark-analysis/` 和 `pytorch213-npu-environment/` 两个技能目录，每个目录内直接包含 `SKILL.md`；不要只复制该文件，需保留 `references/`、`agents/`、`scripts/`（如有）。包中不含原项目的凭据、服务器连接配置、benchmark 日志、wheel 或编译缓存。

Codex 用户将两个文件夹放到**自己的** `$CODEX_HOME/skills/`；若未设置该变量，使用当前用户主目录下的 `.codex/skills/`。无需与发送方 PC 路径一致，也不要求 Windows 或 WSL。重新加载技能列表后使用技能名调用。

| 技能 | 用途 | 调用示例 |
| --- | --- | --- |
| `pytorch213-npu-environment` | 准备独立 PyTorch 2.13 NPU 环境，从指定官方仓库主干构建 torch_npu，完成小型设备及图编译验证 | 使用 $pytorch213-npu-environment，先检查我的现有环境，准备独立 2.13 容器，暂不跑模型 benchmark。 |
| `npu-graph-benchmark-analysis` | 按当前 README 收集融合范围、profiler 融合效果、无调试基线，输出加速比表、报告及最小复现 | 使用 $npu-graph-benchmark-analysis，分析我提供的 eager/compile 日志，生成三种配置加速比表。 |

首次使用时提供已有信息即可：执行在本机/容器还是远程、项目 README 和 runner 位置、实际 Python/CANN 环境、容器/镜像、可写输出目录。远程可提供已配置的 SSH 别名，不要把密码发到聊天。技能会检查实际路径和版本，缺失的必要信息再询问；不会连接原作者内网或读取其密码文件。

benchmark 源码默认使用 `benchmark_source_mode=remote_git`，从 `https://gitcode.com/Ascend/pytorch` 获取到运行主机/容器，PC 无需下载。已有源码时说“切换 `existing_checkout`，仓库在……（注明所在机器）”。这些是技能工作流配置，不是 benchmark CLI 参数。仅做离线日志汇总无需拉取代码；默认远程仓库也不意味着每轮复测都升级源码，复测沿用固定 commit。

两者独立可用，不要求另装 `pytorch-remote-validation`。环境准备依赖实际 NPU 驱动/CANN及对应构建工具；耗时汇总可在任意有 Python 3 的系统离线进行，只使用标准库。内置脚本解析原生 step/summary 格式，不保证适配所有自定义日志。

需要自动登录和多主机选卡时，复制任一技能的 `assets/connection.example.json` 到自己的私有目录，每台只填写 `ip`、`username`、`password`；多台按顺序添加。容器、环境路径和可用卡由执行代理自动检查，无需手填。仅把文件路径告知执行代理，不把真实文件放进分享包或仓库。按主机优先级检查环境与空闲卡，卡被占用时尝试下一台；全部不可用就报告并停止。两个技能均附有 `references/remote-pool.md`。这是供执行代理使用的配置与流程，并非独立安装后常驻运行的调度服务。

安装技能并不安装 torch/CANN，也不会自动创建容器或运行 benchmark。benchmark 先给出方案和完整命令供审核；当前会话已明确批准的同一方案无需重复批准。历史案例中的权限不传递给接收方。

文档中的变量必须按接收方实际环境填写。历史案例保留版本与性能数据用于理解方法，不是默认配置，也不需要取得原作者的镜像和产物。两个技能各自的 `references/configuration.md` 包含详细字段说明。
