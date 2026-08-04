# 货拉拉 SRC 信息收集笔记

> 目标：货拉拉（Huolala）SRC 联合活动（8/16-8/31）
> 起始日期：2026-08-03
> 测试原则：仅手工测试，不跑扫描器；不访问真实用户数据；最小验证

---

## 一、已发现子域名/资产

浏览 `https://www.huolala.cn` 顶部菜单（搬家/大货车/企业版等）后，Burp HTTP history 中捕获到以下域名：

| 域名 | 作用猜测 | 可疑程度 |
|------|---------|---------|
| `www.huolala.cn` | 主站官网 | 中 |
| `watch-dog.huolala.cn` | 数据收集/埋点接口 (`/api/v2/collect`) | 高 |
| `static.huolala.cn` | 静态资源/JSON Schema (`/schema/...`) | 高 |
| `mdap-app.huolala.cn` | APP 下载/分发 (`/website/latestApp?appId=...`) | 高 |
| `ltl.huolala.cn` | 零担货运业务站（LTL=Less Than Truckload） | 中高 |
| `wuliu.huolala.cn` | 物流业务门户（wuliu=物流） | 中高 |
| `api.map.huolala.cn` | 地图服务 API（地理编码/路线） | 高 |
| `mdap.huolala.cn` | APP 分发（与 mdap-app 同类，同站不同子域） | 高 |
| `eapi.huolala.cn` | 对外业务 API 网关（eapi=external API） | 高 |

## 二、已发现接口/路径

### 1. 官网页面类
- `GET /index.php?m=house_move&a=...`（PHP 入口，m=模块 a=动作，经典参数操控点）
- `GET /big_truck.html`
- `GET /house_move.html`

### 2. 数据收集类
- `OPTIONS /api/v2/collect` → `watch-dog.huolala.cn`
- `POST /api/v2/collect` → `watch-dog.huolala.cn`
  - POST 请求体待查看，可能包含设备/用户/行为数据

### 3. 静态配置类
- `GET /schema/8e5d32cc92de420893b51...` → `static.huolala.cn`
  - 返回 JSON，可能暴露业务配置、枚举值、内部字段名

### 4. APP 分发类
- `GET /website/latestApp?appId=com.la...` → `mdap-app.huolala.cn`
  - `appId` 参数可控，可能存在跳转/重定向/SSRF 风险

## 三、下一步待办

1. 继续点击剩余菜单：企业版、发物流、司机加入、租买货车、开放平台、关于我们
2. 对每个新出现的域名/接口，记录到上表
3. 重点检查请求参数（URL query / POST body）和 JSON 响应内容
4. 初步测试方向：
   - `index.php?m=xxx&a=yyy` 参数枚举
   - `watch-dog/api/v2/collect` POST 内容是否携带敏感字段
   - `static.huolala.cn/schema/...` 是否泄露配置/接口文档
   - `mdap-app?appId=` 是否存在 URL 重定向/SSRF

---

## 四、挖洞优先级（暂定）

高优先级：
- `watch-dog.huolala.cn/api/v2/collect`：数据收集接口，可能含越权/信息泄露
- `static.huolala.cn/schema/*`：配置泄露可直接变成低危报告
- `mdap-app.huolala.cn/website/latestApp`：参数可控，测重定向/SSRF

中优先级：
- `www.huolala.cn/index.php?m=&a=`：PHP 入口参数操控
- 登录/注册/下单流程（需注册账号后测）

## 五、访问验证（2026-08-04）

浏览器直连测试（代理 ON、拦截 OFF）：
- `eapi.huolala.cn` → 报错（API 域名，非 Web 页面，直连正常报错）
- `api.map.huolala.cn` → 报错（同上，地图 API 服务）
- `ltl.huolala.cn` → **正常加载**，是一个独立业务子站点（零担货运）

结论：
- `eapi` / `api.map` 这类 API 域名**不能靠浏览器直连测试**，正确打法是：正常使用货拉拉功能时，它们会被前端自动调用 → 在 Burp history 里抓它们的请求/响应 → 重放/改参测试
- `ltl.huolala.cn` 是可交互网站，按"点菜单→抓请求→看参数/响应"流程深挖
