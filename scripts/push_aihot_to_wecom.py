import json
import os
import sys
import urllib.error
import urllib.request


AIHOT_DAILY_URL = "https://aihot.virxact.com/api/public/daily"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

SECTION_ORDER = [
    "模型发布/更新",
    "产品发布/更新",
    "行业动态",
    "论文研究",
    "技巧与观点",
]


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_json(url, payload):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def shorten(text, limit=120):
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def source_label(source_name):
    source_name = source_name or "来源"
    return source_name.replace("（RSS）", "").replace("（网页）", "")


def build_markdown(daily):
    date = daily.get("date", "")
    sections = daily.get("sections") or []
    section_map = {section.get("label"): section for section in sections}

    lines = [
        f"## AI HOT 日报 · {date}",
        "",
    ]

    number = 1
    for label in SECTION_ORDER:
        section = section_map.get(label)
        if not section:
            continue
        items = section.get("items") or []
        if not items:
            continue

        lines.append(f"### {label}")
        for item in items:
            title = item.get("title") or "未命名条目"
            url = item.get("sourceUrl") or ""
            source = source_label(item.get("sourceName"))
            summary = shorten(item.get("summary"), 110)

            if url:
                lines.append(f"{number}. [{title}]({url}) — {source}")
            else:
                lines.append(f"{number}. {title} — {source}")
            if summary:
                lines.append(f"   {summary}")
            number += 1
        lines.append("")

    flashes = daily.get("flashes") or []
    if flashes:
        lines.append("### 快讯")
        for flash in flashes[:10]:
            title = flash.get("title") or "未命名快讯"
            url = flash.get("sourceUrl") or ""
            source = source_label(flash.get("sourceName"))
            if url:
                lines.append(f"- [{title}]({url}) — {source}")
            else:
                lines.append(f"- {title} — {source}")

    lines.append("")
    lines.append("> 数据来自 AI HOT。Webhook 请只保存在 GitHub Secrets。")

    content = "\n".join(lines).strip()

    # 企业微信 markdown 单条消息有长度限制，超长时保留最重要部分。
    if len(content) > 3900:
        content = content[:3800].rstrip() + "\n\n> 内容较长，已自动截断。"
    return content


def main():
    webhook = os.environ.get("WECOM_WEBHOOK", "").strip()
    if not webhook:
        print("Missing WECOM_WEBHOOK environment variable.", file=sys.stderr)
        return 2

    try:
        daily = fetch_json(AIHOT_DAILY_URL)
        markdown = build_markdown(daily)
        result = post_json(
            webhook,
            {
                "msgtype": "markdown",
                "markdown": {"content": markdown},
            },
        )
    except urllib.error.HTTPError as exc:
        print(exc.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Push failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False))
    if result.get("errcode") != 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
