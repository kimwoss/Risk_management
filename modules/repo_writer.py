# -*- coding: utf-8 -*-
"""
repo_writer.py
GitHub Contents API로 파일을 커밋(생성/갱신)한다. (GET sha → PUT, 409 재시도)

두 저장소를 분리 지원:
  - 공개 레포(Risk_management)      : 대응이력 CSV        → 토큰 GH_PAT
  - 비공개 레포(Risk_management_data): 기자리스트 JSON(PII) → 토큰 GH_DATA_TOKEN

토큰이 없으면 (False, "토큰 없음") 반환 → 호출부는 '미리보기만' 모드로 처리.
로컬 git 트리를 건드리지 않고 API만 사용하므로 배포 체크아웃에 안전.
"""
from __future__ import annotations

import base64
import os

import requests

_API = "https://api.github.com/repos/{repo}/contents/{path}"

PUBLIC_REPO = os.getenv("GH_REPO", "kimwoss/Risk_management")
PRIVATE_REPO = os.getenv("GH_DATA_REPO", "kimwoss/Risk_management_data")


def _token(kind: str) -> str | None:
    """kind: 'public' → GH_PAT, 'private' → GH_DATA_TOKEN (secrets 우선)."""
    def _secret(name):
        try:
            import streamlit as st  # 지연 임포트 (워크플로 환경 대비)
            v = st.secrets.get(name)
            return v.strip() if v else None
        except Exception:
            return None

    if kind == "private":
        return (_secret("GH_DATA_TOKEN") or os.getenv("GH_DATA_TOKEN")
                or _secret("GH_TOKEN") or os.getenv("GH_TOKEN") or os.getenv("GH_PAT"))
    return (_secret("GH_PAT") or os.getenv("GH_PAT")
            or _secret("GH_TOKEN") or os.getenv("GH_TOKEN"))


def can_commit(kind: str) -> bool:
    return bool(_token(kind))


def commit_file(kind: str, path: str, content: bytes, message: str,
                branch: str = "main") -> tuple[bool, str]:
    """
    kind='public'|'private' 레포의 path에 content를 커밋. 성공 시 (True, commit_url).
    실패 시 (False, 사유). 동시 커밋 충돌(409)은 최신 sha로 최대 3회 재시도.
    """
    token = _token(kind)
    if not token:
        return False, f"토큰 없음({'GH_DATA_TOKEN' if kind == 'private' else 'GH_PAT'})"

    repo = PRIVATE_REPO if kind == "private" else PUBLIC_REPO
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = _API.format(repo=repo, path=path)

    for _ in range(3):
        # 현재 sha 조회 (없으면 신규 생성)
        sha = None
        try:
            g = requests.get(url, headers=headers, params={"ref": branch}, timeout=20)
            if g.status_code == 200:
                sha = g.json().get("sha")
            elif g.status_code not in (404,):
                return False, f"GET {g.status_code}: {g.text[:120]}"
        except Exception as e:
            return False, f"GET 예외: {e}"

        payload = {
            "message": message,
            "branch": branch,
            "content": base64.b64encode(content).decode(),
        }
        if sha:
            payload["sha"] = sha
        try:
            p = requests.put(url, headers=headers, json=payload, timeout=25)
        except Exception as e:
            return False, f"PUT 예외: {e}"

        if p.status_code in (200, 201):
            try:
                return True, p.json().get("commit", {}).get("html_url", repo)
            except Exception:
                return True, repo
        if p.status_code == 409:
            continue  # sha 충돌 → 재조회 후 재시도
        return False, f"PUT {p.status_code}: {p.text[:150]}"

    return False, "충돌(409) 재시도 초과"
