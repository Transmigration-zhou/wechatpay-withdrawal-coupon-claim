# 微信支付提现笔笔省 - 每日领券脚本

自动领取微信小程序「提现笔笔省」的每日免费提现券。

## 流程

1. `GET /txbbs-mall/coupon/querydailygiftcoupons` —— 查询当日券信息，拿到 `coupon_id`、`face_value`、`exposure_token`、`is_claimed`
2. 若 `is_claimed: true` 直接退出
3. 否则用上一步返回的真实参数调 `POST /txbbs-mall/coupon/claimdailygiftcoupon` 领取

> **响应解析：** 服务端对成功响应使用了**双层压缩**（外层 zlib + 内层 raw deflate），`requests` 只自动解外层，因此脚本在 JSON 解析失败时会做一次 raw deflate 解压再解析。

## 快速开始

```bash
pip install -r requirements.txt
cp .env.example .env  # 然后填入 SESSION_TOKEN
python main.py
```

## 配置

`.env` 内容：

```
SESSION_TOKEN=<从微信小程序抓包获取>
```

### 如何获取 SESSION_TOKEN

1. 在 Mac 上用 [Stream](https://apps.apple.com/cn/app/stream/id1312141691) 或 Charles 等抓包工具开启抓包
2. 微信打开「提现笔笔省」小程序进入领券页
3. 找到任意一条向 `discount.wxpapp.wechatpay.cn` 发起的请求
4. 复制请求头里 `session-token` 的值

> ⚠️ `session-token` 寿命较短（一般几十分钟到一小时），过期需重新抓取。

## 定时执行

仓库内置 GitHub Actions 工作流 `.github/workflows/daily-claim.yml`，每天北京时间 09:00 自动运行。需要在仓库 Settings → Secrets 配置：

- `SESSION_TOKEN`

由于 token 短寿命问题，纯定时执行可能频繁失败；当前更适合**手动触发**或本地运行。

## 文件结构

```
.
├── main.py                       # 主脚本
├── requirements.txt              # 依赖：requests, python-dotenv
├── .env                          # 本地凭据（已 gitignore）
└── .github/workflows/
    └── daily-claim.yml           # 定时任务
```

## 错误码参考

| errcode | 含义 |
|---------|------|
| 0 | 成功 |
| 268566816 | 用户未登录/鉴权失败（session-token 失效） |
| 268592143 | "页面已过期"（实际多为今日已领或鉴权问题的通用错误） |
