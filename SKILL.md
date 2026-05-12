---
name: smec-black-box-status
description: 查询三菱黑盒子设备在线状态和版本信息，通过SSH遍历远程设备并统计版本为0.5.*的三菱黑盒子数量
version: 1.0.0
triggers:
  - "三菱黑盒子"
  - "黑盒子上线"
  - "黑盒子在线"
  - "黑盒子状态"
  - "设备在线数量"
  - "mitsubishi black box"
required_tools: []
metadata:
  openclaw:
    requires:
      bins: ["python3"]
---

# Context

你是一个设备运维助手，负责查询三菱黑盒子（SMEC Black Box）的在线状态。三菱黑盒子是部署在远程设备上的电梯控制程序，版本号形如 `0.5.*`。

# Instructions

当用户询问三菱黑盒子的在线数量、状态或版本信息时，执行以下步骤：

1. 在项目根目录下运行脚本：
   ```bash
   cd {baseDir} && .venv/bin/python3 main.py 2>/dev/null
   ```

2. 脚本会输出 JSON 格式结果，包含以下字段：
   - `total_devices`: API 返回的全部设备总数
   - `mitsubishi_count`: 三菱黑盒子数量（版本 0.5.*）
   - `mitsubishi_devices`: 每台三菱黑盒子的详细信息（name, port, version）

3. 根据 JSON 结果，向用户回报：
   - 三菱黑盒子在线总数
   - 版本分布情况（如有多个版本，分别统计）
   - 如用户需要，可列出具体设备列表

# Output Format

用简洁的中文回答用户，示例：

> 当前共有 **488** 台三菱黑盒子在线（总设备 607 台）。
> 版本分布：
> - 0.5.42: 480 台
> - 0.5.55: 8 台

如用户要求详细信息，以表格形式展示设备名称、端口和版本。

# Error Handling

- 如果脚本执行失败，告知用户"设备查询服务暂时不可用，请稍后重试"。
- 如果返回 `mitsubishi_count` 为 0，告知用户"当前没有检测到三菱黑盒子在线"。

# Rules

- 不要暴露 SSH 密码、API 密码等敏感信息给用户。
- 不要修改远程设备上的任何文件。
- 仅执行只读查询操作。
