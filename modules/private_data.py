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


# 코드 저장소에서 분리해 비공개 저장소로 이관한 민감 데이터 목록.
#   - 출입기자_리스트.csv : 기자 개인 연락처·이메일 (개인정보)
#   - 언론대응내역.csv    : 사내 언론대응 이력 (대외비성 업무 데이터)
# 앱 시작 시 로컬에 없으면 토큰 인증으로 내려받아 기존 경로에 복원하므로,
# 이를 읽는 코드(data_based_llm, journalist_db 등)는 수정 없이 그대로 동작한다.
#   - keywords.json     : 모니터링 키워드 설정(담당자가 앱에서 편집).
#                         모니터링 대상은 사내 관심사를 드러낼 수 있어 공개 저장소에 두지 않는다.
PRIVATE_DATA_FILES = (
    "data/master_data.json",
    "data/출입기자_리스트.csv",
    "data/언론대응내역.csv",
    "data/keywords.json",
)

# 없어도 앱이 정상 동작하는 파일 (기본값으로 대체됨) — 복원 실패를 경고하지 않는다.
#   keywords.json: 담당자가 한 번도 저장하지 않았으면 아예 존재하지 않는 게 정상이며,
#                  news_collector가 DEFAULT_KEYWORDS로 폴백한다.
OPTIONAL_DATA_FILES = frozenset({"data/keywords.json"})


def ensure_private_data(data_folder: str = "data") -> dict:
    """비공개 저장소의 민감 데이터를 로컬에 복원한다(이미 있으면 건너뜀).

    반환: {repo_path: True(존재/복원 성공) | False(복원 실패)}
    토큰이 없거나 네트워크가 막혀 실패해도 예외를 던지지 않는다
    (로컬에 파일이 이미 있는 개발 PC에서는 애초에 호출 자체가 no-op).
    """
    result = {}
    for repo_path in PRIVATE_DATA_FILES:
        local_path = os.path.join(data_folder, os.path.basename(repo_path))
        if os.path.exists(local_path):
            result[repo_path] = True
            continue
        result[repo_path] = fetch_private_file(repo_path, local_path)
    return result
