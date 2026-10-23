# 已验证实例：2026-10-22

本页记录的是 **CANN 9.1.0** 的历史实例。技能当前目标已改为 **9.2.0**，该目标尚不能由此历史验证证明；不可直接套用表中的镜像与CANN路径宣称符合新要求。

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
