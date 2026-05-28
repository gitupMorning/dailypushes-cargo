# AI HOT 企业微信每日推送

这个目录是一套 GitHub Actions 定时任务模板：每天拉取 AI HOT 日报，并推送到企业微信群机器人。

## 使用步骤

1. 在 GitHub 新建一个仓库，例如 `aihot-wecom-daily`。
2. 把本目录里的文件提交到仓库根目录：
   - `.github/workflows/aihot-wecom.yml`
   - `scripts/push_aihot_to_wecom.py`
3. 打开仓库 `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`。
4. 新增 secret：
   - Name: `WECOM_WEBHOOK`
   - Secret: 你的企业微信群机器人 Webhook 完整地址
5. 进入仓库 `Actions` 页面，启用 workflows。
6. 点开 `AI HOT to WeCom`，可以先手动点 `Run workflow` 测试。

## 默认推送时间

默认每天北京时间 08:10 推送，也就是 UTC 00:10。

如果要改时间，编辑 `.github/workflows/aihot-wecom.yml`：

```yaml
- cron: "10 0 * * *"
```

GitHub Actions 的定时任务使用 UTC 时间。

## 安全提醒

不要把 Webhook 写进代码或提交到 GitHub。Webhook 只放在 GitHub Actions Secret 里。
