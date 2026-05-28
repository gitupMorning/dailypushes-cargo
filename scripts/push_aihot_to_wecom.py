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
    "妯″瀷鍙戝竷/鏇存柊",
    "浜у搧鍙戝竷/鏇存柊",
    "琛屼笟鍔ㄦ€?,
    "璁烘枃鐮旂┒",
    "鎶€宸т笌瑙傜偣",
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
    return text[: limit - 1] + "鈥?


def fit_wecom_markdown(content, byte_limit=3900):
    encoded = content.encode("utf-8")
    if len(encoded) <= byte_limit:
        return content

    suffix = "\n\n> 鍐呭杈冮暱锛屽凡鑷姩鎴柇銆?
    suffix_bytes = suffix.encode("utf-8")
    keep = byte_limit - len(suffix_bytes)
    trimmed = encoded[:keep].decode("utf-8", errors="ignore").rstrip()
    return trimmed + suffix


def source_label(source_name):
    source_name = source_name or "鏉ユ簮"
    return source_name.replace("锛圧SS锛?, "").replace("锛堢綉椤碉級", "")


def build_markdown(daily):
    date = daily.get("date", "")
    sections = daily.get("sections") or []
    section_map = {section.get("label"): section for section in sections}

    lines = [
        f"## AI HOT 鏃ユ姤 路 {date}",
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
            title = item.get("title") or "鏈懡鍚嶆潯鐩?
            url = item.get("sourceUrl") or ""
            source = source_label(item.get("sourceName"))
            summary = shorten(item.get("summary"), 110)

            if url:
                lines.append(f"{number}. [{title}]({url}) 鈥?{source}")
            else:
                lines.append(f"{number}. {title} 鈥?{source}")
            if summary:
                lines.append(f"   {summary}")
            number += 1
        lines.append("")

    flashes = daily.get("flashes") or []
    if flashes:
        lines.append("### 蹇")
        for flash in flashes[:10]:
            title = flash.get("title") or "鏈懡鍚嶅揩璁?
            url = flash.get("sourceUrl") or ""
            source = source_label(flash.get("sourceName"))
            if url:
                lines.append(f"- [{title}]({url}) 鈥?{source}")
            else:
                lines.append(f"- {title} 鈥?{source}")

    lines.append("")
    lines.append("> 鏁版嵁鏉ヨ嚜 AI HOT銆俉ebhook 璇峰彧淇濆瓨鍦?GitHub Secrets銆?)

    content = "\n".join(lines).strip()

    # 浼佷笟寰俊 markdown 鍗曟潯娑堟伅鎸夊瓧鑺傞檺鍒堕暱搴︼紝涓枃闇€瑕佹寜 UTF-8 瀛楄妭鎴柇銆?    return fit_wecom_markdown(content)


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
