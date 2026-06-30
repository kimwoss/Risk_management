"""sent_articles_cache.json / pending_articles.json를 remote(origin/main)와 Union 병합.

여러 워크플로우(heartbeat, news_monitor 백업)가 동시에 data/를 수정·push해도
발송 이력(sent_cache)·재시도 큐(pending)가 유실되지 않도록, push 직전에
remote 값과 local 값을 합친다. local 우선 union이라 이번 실행에서 새로 발송/추가한
항목이 보존된다.

GitHub Actions의 push 단계에서 `git rebase origin/main` 직후 호출한다.
"""
import json
import os
import subprocess
import sys

DATA = "data"


def git_show(path):
    """origin/main의 해당 파일 내용을 JSON으로 반환. 실패 시 None."""
    r = subprocess.run(
        ["git", "show", f"origin/main:{path}"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except Exception:
        return None


def merge_dict_key(local_path, top_key):
    if not os.path.exists(local_path):
        return
    remote = git_show(local_path)
    if not remote:
        return
    try:
        with open(local_path, "r", encoding="utf-8") as f:
            local = json.load(f)
        remote_items = remote.get(top_key, {})
        local_items = local.get(top_key, {})
        merged = {**remote_items, **local_items}  # local 우선 union
        local[top_key] = merged
        if top_key == "url_timestamps":
            local["urls"] = list(merged.keys())
        local["count"] = len(merged)
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(local, f, ensure_ascii=False, indent=2)
        print(f"Merged {local_path}: remote={len(remote_items)}, "
              f"local={len(local_items)}, total={len(merged)}")
    except Exception as e:
        print(f"Merge skipped ({local_path}): {e}", file=sys.stderr)


def main():
    merge_dict_key(f"{DATA}/sent_articles_cache.json", "url_timestamps")
    merge_dict_key(f"{DATA}/pending_articles.json", "queue")


if __name__ == "__main__":
    main()
