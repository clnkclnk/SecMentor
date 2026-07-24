# Lab: http-observation

## 目的

观察 HTTP 请求/响应；练习改参数。对应 topic：`http-basics`、`burp-intro`。

## 启动（学员本机执行）

```bash
cd labs/http-observation
docker compose up -d
```

浏览器打开：`http://127.0.0.1:18080/`  
（若端口占用，改 `docker-compose.yml` 左侧端口后再起。）

## 任务

1. 访问 `/get?name=alice`，在 Network 或代理里找到该请求。  
2. 说明：方法、路径、查询参数、一个请求头、状态码。  
3. 把 `name` 改成别的值再请求，对照响应 JSON 变化。  
4. （可选）用 Yakit/Burp 拦截一次并修改后再放行。

## 验收时交给导师

粘贴或描述：你改的参数、看到的状态码/响应片段。导师据此写证据，**不要**只说「我看懂了」。

## 清理

```bash
docker compose down
```
