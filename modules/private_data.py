# -*- coding: utf-8 -*-
"""비공개 데이터 저장소(Risk_management_data)에서 민감 데이터를 로컬로 부트스트랩.

공개 저장소에서 master_data.json(기자·담당자 연락처 포함)을 제거한 뒤에도
앱·워크플로가 기존처럼 로컬 파일을 읽을 수 있도록, 시작 시점에 파일이 없으면
비공개 저장소에서 내려받아 로컬 경로에 복원한다.

토큰 우선순위: st.secrets["GH_DATA_TOKEN"] → 환경변수 GH_DATA_TOKEN → GH_TOKEN
(streamlit 미설치 환경(워크플로)에서도 동작하도록 streamlit은 지연 임포트)
"""
import base64
import os

import requests

DATA_REPO = os.getenv("GH_DATA_REPO", "kimwoss/Risk_management_data")
_API = "https://api.github.com/repos/{repo}/contents/{path}"


def _get_token() -> str | None:
    try:
        import streamlit as st  # noqa: PLC0415

        tok = st.secrets.get("GH_DATA_TOKEN")
        if tok:
            return tok
    except Exception:
        pass
    return os.getenv("GH_DATA_TOKEN") or os.getenv("GH_TOKEN")


def fetch_private_file(repo_path: str, local_path: str, token: str | None = None) -> bool:
    """비공개 저장소의 repo_path 파일을 local_path로 내려받는다. 성공 시 True."""
    token = token or _get_token()
    if not token:
        print("[private_data] 토큰 없음 - 비공개 데이터 로드 생략")
        return False
    try:
        r = requests.get(
            _API.format(repo=DATA_REPO, path=repo_path),
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            params={"ref": "main"},
            timeout=20,
        )
        if r.status_code != 200:
            print(f"[private_data] GET {repo_path} -> {r.status_code}")
            return False
        content = base64.b64decode(r.json().get("content", ""))
        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(content)
        print(f"[private_data] ✅ {repo_path} → {local_path} ({len(content):,} bytes)")
        return True
    except Exception as e:
        print(f"[private_data] 로드 실패: {e}")
        return False


def ensure_master_data(local_path: str) -> bool:
    """master_data.json이 로컬에 없으면 비공개 저장소에서 복원한다."""
    if os.path.exists(local_path):
        return True
    return fetch_private_file("data/master_data.json", local_path)
