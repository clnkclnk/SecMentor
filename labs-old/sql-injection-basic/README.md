# Lab: sql-injection-basic

## 目的

手工理解 SQL 注入。对应 `sqli-manual`。先手工，后工具。

## 启动

```bash
cd labs/sql-injection-basic
docker compose up -d
```

打开：`http://127.0.0.1:18082/`  
按页面初始化数据库；登录后将安全级别调到 Low。

## 任务

1. 进入 **SQL Injection** 练习页。  
2. 判断注入点类型，完成至少一种：联合查询 / 报错 / 盲注（能证明即可）。  
3. 记录：关键输入（可简化）、如何确认注入成立。  
4. 口述：若改成参数化查询，哪里会挡住你的输入。

若本机拉取镜像失败：可改用其他学习向 SQLi 靶场镜像，并在对话里告知导师你用的地址。

## 交给导师

关键步骤与现象（不要只贴终极 payload 列表）。导师检查是否达到 `apply`，必要时再给一个参数名不同的迁移题（`transfer`）。

## 清理

```bash
docker compose down
```
