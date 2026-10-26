# SSH密钥登录、自动连接与多宿主机选卡

此流程用于用户授权的远程 NPU 任务，远程基础能力独立使用，不安装框架或运行模型。读取技能不自动建立连接；在用户要求检查环境或运行已批准任务时执行。技能包不包含现成的通用登录器/调度器；执行代理根据此配置生成适合当前 SSH、Docker 和设备工具的命令或任务启动器，不假定原作者项目脚本存在。

## 用户自己的连接配置文件

可复制技能内 `assets/connection.example.json` 到用户选择的私有目录，填写后只提供文件路径。文件可位于任何实际控制端，不要求PC或WSL固定目录；真实主机名单不进入源码仓库、分享包或容器。

用户只需填写`ip`和`username`，多台主机按`hosts`顺序尝试。默认SSH22端口、公钥认证；复用实际运行ssh/scp的客户端已有默认密钥、ssh-agent和SSH配置。自定义私钥可选填`identity_file`，其路径必须属于实际控制端（Windows和WSL各自的SSH环境不自动互通），不是需要分享的文件。不要要求填写password，也不新增容器名、卡号等必填项。端口和跳板机有特殊要求时优先复用SSH配置，再补充实际缺口。

用户要求使用此名单执行任务时，执行代理自动完成以下发现工作：

- 查询 Docker 可访问性、已有容器及挂载；结合当前任务记录和容器内版本检查选择匹配环境。容器名不能代替真实版本检查。
- 在归属已确认的候选容器中发现路径，并按调用方提供的只读环境检查核实目标；不要求用户手填这些路径。只读检查其他容器，不修改或占用他人环境。无法判断容器归属时新建本任务容器（在当前授权内）或询问具体缺口。
- 读取 npu-smi 并结合模型/验证需求确定显存门槛；只在健康、无进程、利用率为0且显存足够的卡上运行。默认允许在此用户提供的主机名单内按顺序回退，当前主机无空闲卡就检查下一台。
- 没有匹配容器时，按调用方指定的镜像和当前授权创建独立容器；登录能力不代表授权特权容器、覆盖旧环境或停止其他任务。

这些是技能代理执行时使用的配置和发现规则，不是runner参数或常驻调度器。执行前校验IP有效、用户名非空，使用结构化子进程参数，拒绝以选项前缀或控制字符注入SSH参数。不读取私钥内容；`identity_file`只传给SSH客户端。旧配置若仍有password，默认忽略且不打印，建议用户自行从私有配置移除；不要因为看到旧字段就恢复密码自动登录。

## 容器命名与归属

新建名称使用 `npu-<当前使用者标识>-torch<版本>-<时间戳>-<随机短串>`，使用合法 Docker 名称字符并在创建前检查重名；宿主机持久工作目录使用同一唯一标识。使用者标识优先从当前任务的使用者身份获取，不把共享 SSH 账户 root 当作唯一归属；无法获得唯一身份时生成本地实例标识并保存到当前任务配置，之后复用。不增加IP和用户名之外的必填连接字段。

创建时添加项目命名空间标签（例如 `io.npu-skills.owner` 和 `io.npu-skills.task`），记录实例标识、容器 ID、宿主机及独立目录。不得从历史案例复制原作者的个人前缀、容器名或目录。

只自动进入运行任务、修改、停止或复用归属标签及任务记录均匹配的容器。容器名或版本匹配不足以证明归属；无标签的已有容器只有当前用户明确指定并授权复用时才可使用。发现阶段可读取容器列表、标签和挂载元数据，不得未经授权进入不明归属容器执行探测命令。没有本任务容器时在授权范围创建独立容器，不自动借用他人的环境。由用户主动指定他人/共享容器的情形单独按其明确授权处理。

## SSH认证和主机身份

主机已被可信known_hosts记录时，自动连接使用如下选项，scp同步采用相同认证选项：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 \
  -o PreferredAuthentications=publickey \
  -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no \
  -o StrictHostKeyChecking=yes -o ForwardAgent=no \
  "$SSH_USER@$SSH_HOST" true
```

`SSH_USER`与`SSH_HOST`取自已校验配置。自定义密钥增加`-i "$IDENTITY_FILE" -o IdentitiesOnly=yes`，否则保留客户端和agent既有发现方式。私钥有口令时由用户在本机解锁并加载ssh-agent；无人值守阶段不读取口令，也不以空口令密钥作为必要条件。不要开启agent转发。

新主机先通过管理员或可信控制台核对SSH主机密钥指纹，再建立known_hosts记录；ssh-keyscan只能取得待核对公钥，不能独立证明身份。重装造成主机密钥变化时先重新核实，不自动删除旧记录或关闭校验。

## 首次配置免密登录

用户首次要求建立连接、换服务器或遇到 `Permission denied (publickey,...)` 时，主动引导以下流程。已有公钥登录成功就直接复用。不要把网络不可达、主机身份未核实或主机密钥变化误判为需要重新安装用户公钥。

以下均为通用模板。代理应按当前用户的操作系统、SSH用户和实际路径生成本次可执行命令；真实IP、用户名、公钥、邮箱及个人路径只用于该用户的私有配置和本次操作，不写入skill、示例、共享脚本或发布包。私钥始终留在本机，只读取公钥文件。

### 1. 确认本机密钥

先确认实际运行SSH的是Windows、Linux还是WSL，并检查该控制端的SSH配置、agent和已有公钥；Windows和WSL的密钥、agent及known_hosts不自动共享。优先复用已有密钥，不默认重新生成或覆盖。PowerShell中的默认公钥查看方式：

```powershell
Get-ChildItem "$env:USERPROFILE\.ssh" -Filter '*.pub'
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub"
```

Linux/WSL对应使用 `ls ~/.ssh/*.pub` 与 `cat ~/.ssh/id_ed25519.pub`；实际选中了其他密钥时替换文件名。不要读取不带`.pub`的私钥文件内容。

没有合适密钥且用户授权配置免密时，选择未占用的文件名后创建：

```powershell
# PowerShell；先确认这个文件名尚未使用。
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\id_ed25519" -C npu-automation
```

Linux/WSL使用 `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -C npu-automation`。建议用户交互设置私钥口令；不要把口令写入参数或配置，也不要求空口令。已有私钥但缺少公钥文件时，由用户在本机用 `ssh-keygen -y -f <私钥路径>` 恢复公钥，不读取私钥正文。

带口令密钥通过实际控制端的ssh-agent解锁：Linux/WSL在需要时执行 `eval "$(ssh-agent -s)"`，再执行 `ssh-add ~/.ssh/id_ed25519`；Windows先检查 `Get-Service ssh-agent`，服务未启动时由用户在管理员PowerShell按需执行 `Set-Service ssh-agent -StartupType Manual` 和 `Start-Service ssh-agent`，然后在本机执行 `ssh-add "$env:USERPROFILE\.ssh\id_ed25519"`。由用户交互输入私钥口令。

### 2. 将公钥添加到服务器

先按上一节核对SSH主机指纹。用户不希望通过SSH密码登录时，直接选择云平台网页终端、物理控制台或管理员渠道安装公钥；公钥不会因本机已经生成而自动出现在新服务器。

让用户在服务器控制台以**目标SSH用户**执行以下Linux命令。将占位符替换为上一步选定公钥的完整单行内容，不使用本skill作者或其他用户的公钥。先验证内容是合法单行公钥，再执行；命令中只放公钥，不放私钥或密码。

```bash
# 在服务器端执行；当前用户必须是将要通过SSH登录的用户。
# 占位符必须先替换为完整的单行公钥。
key='<PUBLIC_KEY_LINE>'
install -d -m 700 "$HOME/.ssh"
touch "$HOME/.ssh/authorized_keys"
if ! grep -qxF -- "$key" "$HOME/.ssh/authorized_keys"; then
  printf '\n%s\n' "$key" >> "$HOME/.ssh/authorized_keys"
fi
chmod 600 "$HOME/.ssh/authorized_keys"
```

保留已有authorized_keys；追加前去重，前置换行兼容已有文件末尾无换行的情况。管理员代装时必须定位目标用户的真实home并核对文件属主，不把公钥误装到管理员自己的账户。不要对整个`.ssh`目录递归更改属主。Windows服务器按其OpenSSH配置和ACL选择公钥位置，不套用Linux命令。

用户愿意在本机交互输入一次服务器密码且Linux/WSL具备ssh-copy-id时，可改用：

```bash
ssh-copy-id -i "$KEY_FILE.pub" -o StrictHostKeyChecking=yes "$SSH_USER@$SSH_HOST"
```

服务器密码仅由用户在本机SSH认证提示中输入，不索要到聊天，不写入JSON或脚本。代理无法交互时，应交付可执行命令、说明在哪台机器执行并等待完成；不要用明文密码自动化替代。

### 3. 验证与保存连接

用户完成服务器端配置后，代理主动复验。以下PowerShell模板需替换主机、用户名和实际密钥路径；Linux/WSL使用其本机路径及shell语法：

```powershell
ssh -i "$env:USERPROFILE\.ssh\id_ed25519" -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=10 -o PreferredAuthentications=publickey -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no -o StrictHostKeyChecking=yes -o ForwardAgent=no <SSH_USER>@<SERVER_IP> "whoami"
```

只有退出码为0且返回目标用户，才报告免密登录成功，随后检查Docker。失败时区分公钥未装到目标用户、选错本机密钥、agent未解锁、权限或服务器策略，不循环重试、不关闭主机校验，也不修改共享sshd_config、禁用服务器密码登录或调整root登录策略。

成功后将`assets/connection.example.json`保存到用户选择的私有配置目录，写入`ip`、`username`；显式选择密钥时可增加`identity_file`，只存该控制端的私钥路径。保留其他已有主机配置，后续优先复用，不重复要求用户提供密码或重新配置。报告配置位置和验证结果；不要把私有连接配置复制到skill或分享包。

参考：[OpenSSH ssh](https://man.openbsd.org/ssh)、[SSH客户端配置](https://man.openbsd.org/ssh_config)、[ssh-keygen](https://man.openbsd.org/ssh-keygen)。

## 多主机回退流程

1. 校验配置，明确任务所需 torch/torch_npu/CANN/后端、runner/模型 commit、模式、dtype、batch 和设备要求。已批准方案允许名单内同配置主机回退，无需因仅换主机重复审核 benchmark；软件版本、后端或参数变化仍需审核。
2. 按列表顺序连接；失败时记录脱敏原因，继续下一项。每台主机每轮最多尝试一次连接，建议连接超时 10 秒、单次认证；不循环试密码。整轮名单用尽后停止并报告，不无限轮询，除非用户要求等待。
3. 自动发现匹配容器及环境路径，在目标容器内检查实际解释器、import 路径、软件版本、源码 commit 和设备可访问性。容器不存在或配置不兼容时记为不合格，不能回退到另一个 torch 版本冒充同配置任务。本技能只返回目标环境不匹配的状态；由调用方决定是否转交环境准备技能，不自行安装或切换框架版本。
4. 查询该主机设备，候选卡需健康正常、无运行进程、计算利用率为 0、显存满足任务需求且在允许列表。无合格卡就继续下一台主机，不占用忙卡、不重建容器来解决卡占用。
5. 对候选卡取得主机上的协作锁后重新查询占用；被抢占则尝试下一卡/主机。锁持有至该轮子进程结束，正常退出或失败均释放；锁只能约束遵守协议的任务，不声称提供系统级独占。
6. 在导入或初始化 torch_npu 前，使用该次 docker exec 的设备可见性变量设置物理卡到逻辑 npu:0 的映射。容器不永久绑定该卡。同一轮 eager/compile（及同轮约定的采集）固定主机、容器和卡。
7. 一旦 benchmark 已启动，不因中途报错自动在其他主机重跑或拼接两台机器的 eager/compile 数据。保留失败日志并报告；重新运行应明确为新的完整轮次，并按当前授权决定。
8. 保存脱敏的尝试记录、选中主机/容器/物理卡、软件和源码版本、开始/结束设备快照与锁范围，不归档原始连接文件。不同轮使用不同主机/卡时在表格注明；不能把跨轮差异全部归因于 debug/profiler 或 PyTorch。

无合格主机时报告“未启动”，列出不可达、认证失败、环境不兼容或设备忙等具体原因；不展示密码、认证原文或秘密参数。
