# NOTICE

## 上游项目

本仓库产出的中文版基于以下开源项目，仅修改其界面字符串：

- **RemoteApp Tool** — https://github.com/kimmknight/remoteapptool
- 版权：kimmknight, MrBrianGale, wk6768, danielb7390
- 许可：MIT License（全文见上游仓库 LICENSE）

## 本仓库与上游的关系

- 本仓库与上游作者**无关**，未获其背书，也未向上游提交代码
- 本仓库**不包含、不再分发**上游的任何二进制文件（exe / dll / ico）
- `build.py` 需要使用者自行从上游 releases 页面下载原版 zip
- 本仓库代码采用 MIT 许可，与上游许可兼容

## 第三方组件

上游程序内嵌 [IconLib](https://github.com/CastorTiu/IconLib)（作者 CastorTiu，
CC BY-SA 3.0），汉化未改动该组件，其许可不受影响。

## 汉化改动声明

汉化只重写 .NET 元数据 `#US` 字符串堆中的界面文本：

- 不修改 IL 指令、方法体、元数据表结构
- 不修改注册表写入逻辑、生成的 `.rdp` / `.msi` 内容、文件布局
- 程序集本身无强名称签名，改动不影响加载

如上游作者认为本汉化存在不妥，可在本仓库开 issue，会立即调整或下架。
