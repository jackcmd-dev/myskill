---
name: pytorch214-npu-environment
description: 负责PyTorch 2.14 + torch_npu + CANN 9.2.0正式版环境的创建和准备；该组合已经过NPU运算、图模式前后向、profiler及备份试恢复验证，适用于准备或核查2.14执行环境。
---

# PyTorch 2.14 + torch_npu + CANN 9.2.0 环境准备

本技能只准备软件环境，交付环境报告。不得把PyTorch 2.14省略torch_npu、误装2.4/2.13，或把9.2.0-beta当成9.2.0正式版。仅安装成功、import成功或镜像标签匹配不足以判定环境就绪。

2026-10-23已完成本组合的核心验证、DCGAN三类采集及备份试恢复，见[已验证实例](references/verified-instance.md)。环境创建由本技能确定镜像与软件需求，SSH和Docker操作交给npu-remote-container；宿主机需预先具备兼容NPU驱动和Docker，新使用者环境仍须实测。

## 输入与边界

- 已在目标容器中执行，或已有执行上下文时直接复用。需要远程连接/创建容器时调用 `npu-remote-container`，由它处理SSH密钥认证、IP/用户名配置、归属、Docker和选卡；本技能不维护第二份连接配置，不直接扫描或借用他人容器。
- 从用户请求确认目标版本与“复现原软件栈”或“新准备环境”。路径与镜像自动发现，不要求接收方PC有仓库。不要求用户填写能自动发现的路径；发现具体缺口再询问。
- 不运行DCGAN或其他模型benchmark、不收集性能加速比。可进行小型NPU计算、eager反向、图编译与profiler兼容性验证。完整数据收集由 `npu-graph-benchmark-collect` 单独负责，并按其约定审核命令。
- 不修改已有9.1.0环境和历史产物。需要独立容器时把明确镜像/挂载需求交给远程技能；特权模式、宿主机驱动变更按当前授权，不沿用历史权限。

## 准备流程

1. 读取 [安装与验证](references/build-and-verify.md)。记录CPU架构、NPU/驱动、镜像不可变ID、实际torch/torch_npu版本与import路径、CANN元数据和加载路径。
2. 优先使用当前任务已有且真实满足要求的环境；否则在独立环境安装或构建。CANN优先从官方正式版资源获取，不静默降级为beta或9.1.0。
3. PyTorch明确选择2.14目标的官方构建/源码产物；正式版、开发版、commit分别记录，不假定某个wheel永久可下载。复现旧结果时保持用户选定commit，不自动升级。
4. 新安装torch_npu默认使用 `https://gitcode.com/Ascend/pytorch` 当前主干，查询实际远端HEAD并固定commit，按已安装torch实际版本构建；不得改版本字符串伪装匹配。复现已验证栈且用户要求保持版本时可复用原构建，报告其来源与CANN验证结果，不谎称来自最新主干。
5. 安装必要依赖，保护目标torch/torch_npu版本；对照任务提供的模型/后端依赖清单补齐。记录pip check真实结果，核心路径和未使用的辅助工具缺口分别说明，不把有缺口说成全部通过。
6. 激活实际CANN9.2.0和对应Python环境。设备验证通过远程技能取得空闲卡/锁后执行，核查真实加载库未混入旧CANN。小型图模式检查输出及梯度，profiler检查有效步、非空kernel/task及可读数据库。
7. 输出不含凭据的 `environment_report.json` 和简洁文档：执行上下文、解释器与激活入口、各组件完整版本/commit/路径、来源SHA/镜像ID、验证结果、依赖缺口及是否满足指定核心路径。保留失败尝试；不把小型验证通过当作模型通过。

采集技能使用环境报告做只读复核，不依赖个人PC路径。参考 [已验证2.14实例](references/verified-instance.md) 理解实测路线；实例不提供默认主机、容器、个人镜像或已授权权限。
