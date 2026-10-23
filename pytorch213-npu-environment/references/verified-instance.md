# 已验证的2.13 + torch_npu + CANN9.2.0实例

2026-10-23已在Ascend910B4、ARM64宿主机上完成独立验证，随后完成DCGAN训练三类采集及备份试恢复。

| 项目 | CANN9.2.0已验证值 |
| --- | --- |
| torch | 2.13.0+cpu |
| torch commit | cf30153c4c131c8164ee7798e5022d810682e2cb |
| torch_npu | 2.13.0+git7f86549 |
| torch_npu source commit | 7f8654960ab483a323770baa6f9362e7d7b246c9 |
| 独立Python环境 | /opt/npu-env/torch213，torch与torch_npu均从此环境导入 |
| 激活入口 | /opt/npu-env/cann-env.sh |
| CANN实际路径 | /usr/local/Ascend/cann-9.2.0，正式版 |
| 官方CANN镜像 | swr.cn-south-1.myhuaweicloud.com/ascendhub/cann:9.2.0-910b-ubuntu22.04-py3.12-devel |
| 官方镜像Digest | sha256:37ce44bba077e143ab2fa0818d0341aca702a146a6a0625ae627d692c8e62650 |

本次镜像在已经组合CANN9.2.0的2.14框架镜像基础上，复制本项目之前源码构建的2.13独立venv；沿用冻结torch_npu构建，并未重新拉取主干或在9.2.0下重新构建。该路径已实际验证运行兼容性。原框架基础镜像无已确认的公开下载地址，不能要求接收者提供原作者的镜像或容器。

NPU加法、eager反向、Inductor+DVM+reduce-overhead前后向及输出/梯度对比通过；实际加载CANN9.2.0，未混入旧9.1.0库。小型profiler有效步2，kernel/task各18行、TASK表20行。DCGAN训练的范围（debug）、效果（debug+profiler）、基线（双关）均通过精度检查；原生第16～40步均值基线eager7.701979168ms、compile4.734578421ms、1.626750786x。

之后已将容器快照和完整持久目录归档，校验SHA256；从导出镜像及备份目录副本创建独立临时容器，再次通过NPU运算、图模式前后向及profiler验证。此为当前宿主机上的恢复演练；重装后仍需兼容宿主机驱动及Docker，并重新执行验证。

全量pip check仍有CANN附带辅助工具依赖缺口，包括cannsim、schedule-search、mindstudio-kpp、ms-service-profiler、msboost相关项；核心计算、编译、profiler及本模型路径已实测通过，不能写成全依赖无缺口。技能包不包含原始镜像、wheel或采集数据，新使用者重新记录自己的来源和验证证据。

## CANN9.1.0历史实例：2026-10-22

以下只记录旧9.1.0环境的构建来源，不替代上面的9.2.0验证。不要混用两个实例的激活路径或依赖检查结论。

以下为历史证据，复用前核对当前容器、占用和运行时。新建任务不得覆盖该已完成环境或假定旧commit仍为最新主干。

| 项目 | 已验证值 |
| --- | --- |
| 基础镜像ID | sha256:57d673994d63274b4fb409c5b411cec67a70cf4bbcd1ba0c0ec4955e718cac5a |
| 容器工作目录 | /workspace |
| venv | /opt/npu-env/torch213 |
| 激活入口 | /opt/npu-env/activate-torch213.sh |
| Python | 3.12.13 |
| torch | 2.13.0+cpu |
| torch commit | cf30153c4c131c8164ee7798e5022d810682e2cb |
| torch_npu | 2.13.0+git7f86549 |
| source | https://gitcode.com/Ascend/pytorch.git，master |
| source commit | 7f8654960ab483a323770baa6f9362e7d7b246c9 |
| CANN | /opt/ascend/cann-9.1.0 |
| 编译器 | GCC12.3.1（本实例构建成功，不表示未来源码都支持） |
| Triton import / distribution | 3.5.0 / 3.6.0 |
| triton-ascend distribution | 3.6.0+git0cfb1708 |
| 最终设备验证 | 自动选物理2号卡，逻辑npu:0，Ascend910B4 |

构建入口 `bash ci/build.sh --python=3.12` 自动检测torch；默认功能开关未关闭。源码wheel为：

```text
/workspace/torch_npu_source/dist/torch_npu-2.13.0+git7f86549-cp312-cp312-linux_aarch64.whl
45644181 bytes
SHA256 79db172e98c326773c6eda9b6145d24b48f429fb12faa35c5a880fc9f1b2c01b
```

torch与torch_npu实际导入都在venv/lib/python3.12/site-packages。pip check、NPU加法、eager反向、DVM+reduce-overhead前后向与结果/梯度校验均通过。第一次图编译缺Triton，补装后通过；没有改框架/插件源码修复兼容性。

该实例交互 shell 默认激活2.13；使用者应换成自己的容器名和激活入口。直接 `docker exec ... python` 和基础镜像旧工具可能仍指向2.14，自动化显式source激活脚本。

该案例的原始构建日志和 wheel 不随技能分发；无需访问原作者 PC 或服务器。新用户应重新生成本环境的版本、构建和验证证据，不依赖外部项目脚本。表中镜像 ID 和容器路径仅为历史记录，不保证可在其他机器取得。

之后该实例已完成2.13 DCGAN融合范围、融合效果和双关基线采集。基线 eager 8.950306019 ms、compile 5.620081220 ms、1.592558127x，原生第16～40步均值，精度通过。它不证明新用户环境已就绪。2.14历史数据使用torch_npu旧commit ee7bc39，本实例使用7f86549，跨版本比较需记录此差异。
