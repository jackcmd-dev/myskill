# 已验证的2.14 + torch_npu + CANN9.2.0实例

2026-10-23，Ascend910B4 ARM64环境，torch2.14.0a0+git69231fe、torch_npu2.14.0+gitee7bc39、CANN9.2.0正式版。框架commit69231fe37ab3b5d45ad5c4e6e81203be66be42cf；runner与模型另由采集技能固定。

来源：官方CANN9.2.0-910b-ubuntu22.04-py3.12-devel镜像，Digest sha256:37ce44bba077e143ab2fa0818d0341aca702a146a6a0625ae627d692c8e62650；组合原已验证2.14软件栈，未重建torch_npu。此Digest是历史证据，不保证未来环境或架构可直接使用。

NPU加法、eager反向、Inductor+DVM+reduce-overhead前后向及梯度对比通过；实际CANN库为9.2.0、未加载旧9.1.0库。小型profiler有效步2，kernel/task各18行，TASK表有20行。完整DCGAN三轮随后也通过，不能将此历史结论当作新用户环境已验证。

全量pip check仍报告cannsim、schedule-search、mindstudio-kpp、ms-service-profiler、msboost等附属工具依赖缺口；所用核心计算、编译与profiler路径实际通过。历史基础镜像、源码、wheel和原始日志不随技能分发，不需要访问原作者PC、主机或容器。
