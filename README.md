# RemoteApp Tool 简体中文语言包 / zh-CN localization

给 [kimmknight/remoteapptool](https://github.com/kimmknight/remoteapptool) 的 **6.1.0.0** 官方原版做简体中文界面汉化。
**本仓库不含任何官方二进制文件**，只提供汉化脚本 + 语言映射表，你需要自己从官方 release 下载原版再跑一次脚本。

Simplified Chinese UI localization for RemoteApp Tool 6.1.0.0. This repo ships **scripts and a translation table only** — no upstream binaries. Download the official release, run `build.py`, get a Chinese build.

---

## 为什么不用反编译

上游是 VB.NET + WinForms，界面文字全部是硬编码的 `ldstr` 字符串，没有 satellite assembly / .resx 语言资源，所以传统"放个 zh-Hans 目录"的做法完全无效。

本项目的做法是**原位重写 .NET 元数据里的 `#US`（用户字符串）堆**：

- 每条替换后的字节长度不超过原槽位 → 字符串堆内偏移全部不变
- `ldstr` token 一个都不用改，IL 方法体零改动
- 不重编译、不签名、不碰资源表、不动任何逻辑

副作用可控：槽位剩余字节补 0，成为堆中的死区。运行时只按 token 偏移取值，不会顺序扫描 `#US`，因此不受影响。

## 快速开始

```bash
# 1. 从官方 release 下载 zip（约 440 KB）
#    https://github.com/kimmknight/remoteapptool/releases/download/v6.1.0.0/RemoteApp.Tool.6100.zip

# 2. 生成中文版（纯标准库，Python 3.8+，无需安装依赖）
python build.py --src RemoteApp.Tool.6100.zip --out ./dist
```

输出目录里就是可直接运行的免安装中文版，同时自动生成 `原始英文备份/` 便于还原。

脚本做的事：解压官方包 → 复制全部文件 → 备份原版 exe → 打补丁 → 打印替换条数与被跳过的超长条目。

## 汉化范围

覆盖 **279 条**界面字符串：

| 模块 | 内容 |
|---|---|
| 主窗口 | 菜单（文件/工具/帮助）、工具栏按钮、空列表引导语、右键菜单 |
| 远程应用属性 | 字段标签、校验提示、文件类型关联、图标选择 |
| 创建客户端连接 | 主机/选项/网关/文件类型/MSI/签名 六个选项卡全部控件与提示 |
| 附加 RDP 选项 | 选项名 + 全部 59 条技术说明（含多行排版） |
| 主机选项 | 会话超时、AppAllowList 开关、组策略说明 |
| 各类对话框 | 确认/警告/错误/文件占用/证书选择 |

### 有意保留英文（属功能标识，翻译即故障）

- 注册表值名：`Name` `Path` `VPath` `ShortName` `IconPath` `IconIndex` `SecurityDescriptor` `ShowInTSWA` `CommandLineSetting` `RequiredCommandLine`
- `.rdp` 参数键：`administrative_session` `allow_desktop_composition` 等全部下划线标识符
- 程序自身设置项名：`MainWindowWidth` `SavedServerAddress` 等
- 路径与命令：`mstsc.exe` `rdpinit.exe` `reg.exe` `shell` `open` `command`
- 字体名：`Segoe UI`、`Microsoft Sans Serif`
- 版权文本里的作者名、URL、许可证名称
- 组合框里的 `Optional` / `Enforced`（对应注册表 dword 取值语义）

## 校验

`src/verify.py` 会从成包里逐条回读 `#US` 条目并与映射表比对：

```
$ python src/verify.py
回读校验: 279 正确, 0 异常
```

另已在 Windows 11 上实测：程序正常启动、菜单与主界面中文渲染正常、字体回退到微软雅黑无缺字。

## 已知限制（与汉化无关，属原程序/RemoteApp 本身行为）

1. Windows 家庭版不能做被控端：工具能开、能建条目，但客户端连接会静默失败。
2. 客户端系统做被控端时只有 **1 个并发会话**；同一会话内可以开多个应用窗口。多个 `.rdp` 必须使用完全一致的地址写法（都用 IP 或都用主机名），否则第二个连接会新建会话并顶掉第一个。
3. Win11 24H2/25H2 若装过 KB5070311 及之后版本，RAIL 可能失效，需先执行：
   ```bat
   reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\WinLogon\ShellPrograms\RdpShell.exe" /v ShouldStartRailRPC /t REG_DWORD /d 1 /f
   ```
4. exe 文件名必须保持 `RemoteApp Tool.exe`，改名会导致启动报 .NET 错误。
5. 未汉化：`RDP2MSI.exe`（命令行辅助程序，无常规界面）以及 `LockChecker` / `IconLib` / `RDPSign` 等 DLL 内部的错误文案。

## 其他版本的适配

同主版本号内字符串基本稳定；版本变化后重跑 `build.py`，被跳过的条目会打印出来（槽位不足）。
映射表在 `src/lang/zh-CN.json`，键是英文原文，值是中文，换行风格会自动跟随原文（真换行 / 字面量 `\n` 两种都能匹配）。

## 免责与许可

- 本仓库代码：MIT（见 `LICENSE`）
- RemoteApp Tool 本体：MIT，版权归 kimmknight / MrBrianGale / wk6768 / danielb7390，见 `NOTICE.md`
- 本仓库不包含、也不再分发官方二进制；使用者需自行从官方渠道获取原版
- 汉化仅改动界面文本，不改变任何功能行为；因使用本汉化产生的任何问题由使用者自负

## 致谢

- [kimmknight/remoteapptool](https://github.com/kimmknight/remoteapptool) —— 原程序
- [woshub 的 RemoteApp 桌面版配置说明](https://woshub.com/run-remoteapps-desktop-windows/) —— 无 RDS 部署背景知识来源
