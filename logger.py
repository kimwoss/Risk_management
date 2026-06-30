"""
중앙 집중식 로깅 시스템
뉴스 모니터링 시스템의 모든 이벤트를 추적하고 통계를 제공합니다.
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional


# 로그 파일 경로
LOG_FILE = os.path.join("data", "monitoring_log.jsonl")  # JSON Lines 형식
STATS_FILE = os.path.join("data", "daily_stats.json")  # 일일 통계

# 로그 로테이션 (무한 증가 방지)
# 하트비트가 3분마다 쓰므로 자동 트리밍 필수. 크기 초과 시 최근 KEEP_LINES만 보존.
MAX_LOG_BYTES = 3 * 1024 * 1024  # 3MB
KEEP_LINES = 10000               # 약 2~3일치 (일일 통계는 daily_stats.json에 별도 저장됨)


class MonitoringLogger:
    """모니터링 이벤트 로거"""

    def __init__(self):
        """로거 초기화"""
        os.makedirs("data", exist_ok=True)

    def _rotate_if_needed(self):
        """로그 파일이 임계 크기를 넘으면 최근 KEEP_LINES 줄만 남기고 트리밍."""
        try:
            if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_LOG_BYTES:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                if len(lines) > KEEP_LINES:
                    with open(LOG_FILE, 'w', encoding='utf-8') as f:
                        f.writelines(lines[-KEEP_LINES:])
        except Exception as e:
            print(f"[WARNING] 로그 로테이션 실패: {e}")

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """
        이벤트 로깅

        Args:
            event_type: 이벤트 타입 (collection, telegram, error 등)
            data: 이벤트 데이터
        """
        try:
            self._rotate_if_needed()

            entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "data": data
            }

            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        except Exception as e:
            print(f"[WARNING] 로그 저장 실패: {e}")

    def log_collection(self, keyword: str, count: int, api_calls: int = 1):
        """
        뉴스 수집 이벤트 로깅

        Args:
            keyword: 검색 키워드
            count: 수집된 기사 수
            api_calls: API 호출 횟수
        """
        self.log_event("collection", {
            "keyword": keyword,
            "articles_collected": count,
            "api_calls": api_calls
        })

    def log_telegram(self, success: int, failed: int, total: int):
        """
        텔레그램 전송 이벤트 로깅

        Args:
            success: 성공한 전송 수
            failed: 실패한 전송 수
            total: 전체 전송 시도 수
        """
        self.log_event("telegram", {
            "success": success,
            "failed": failed,
            "total": total,
            "success_rate": success / total if total > 0 else 0
        })

    def log_error(self, error_type: str, message: str, details: Optional[str] = None):
        """
        에러 로깅

        Args:
            error_type: 에러 타입 (api_quota, timeout, network 등)
            message: 에러 메시지
            details: 상세 정보 (선택)
        """
        error_data = {
            "error_type": error_type,
            "message": message
        }
        if details:
            error_data["details"] = details

        self.log_event("error", error_data)

    def log_run_summary(self, total_articles: int, new_articles: int,
                        telegram_sent: int, errors: int):
        """
        실행 요약 로깅

        Args:
            total_articles: 수집된 전체 기사 수
            new_articles: 신규 기사 수
            telegram_sent: 텔레그램 전송 수
            errors: 에러 발생 횟수
        """
        self.log_event("run_summary", {
            "total_articles": total_articles,
            "new_articles": new_articles,
            "telegram_sent": telegram_sent,
            "errors": errors
        })

    def get_daily_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        일일 통계 조회

        Args:
            date: 조회할 날짜 (YYYY-MM-DD), None이면 오늘

        Returns:
            일일 통계 딕셔너리
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        stats = {
            "date": date,
            "runs": 0,
            "total_collections": 0,
            "total_api_calls": 0,
            "total_articles": 0,
            "new_articles": 0,
            "telegram_sent": 0,
            "telegram_failed": 0,
            "errors": 0,
            "error_types": {}
        }

        if not os.path.exists(LOG_FILE):
            return stats

        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry["timestamp"].startswith(date):
                            event_type = entry["event_type"]
                            event_data = entry["data"]

                            if event_type == "collection":
                                stats["total_collections"] += 1
                                stats["total_api_calls"] += event_data.get("api_calls", 0)
                                stats["total_articles"] += event_data.get("articles_collected", 0)

                            elif event_type == "telegram":
                                stats["telegram_sent"] += event_data.get("success", 0)
                                stats["telegram_failed"] += event_data.get("failed", 0)

                            elif event_type == "error":
                                stats["errors"] += 1
                                error_type = event_data.get("error_type", "unknown")
                                stats["error_types"][error_type] = stats["error_types"].get(error_type, 0) + 1

                            elif event_type == "run_summary":
                                stats["runs"] += 1
                                stats["new_articles"] += event_data.get("new_articles", 0)

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"[WARNING] 통계 조회 실패: {e}")

        return stats

    def save_daily_stats(self):
        """오늘의 통계를 파일로 저장"""
        try:
            stats = self.get_daily_stats()
            with open(STATS_FILE, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            print(f"[DEBUG] 일일 통계 저장 완료: {STATS_FILE}")
        except Exception as e:
            print(f"[WARNING] 통계 저장 실패: {e}")

    def print_daily_summary(self):
        """오늘의 통계 출력"""
        stats = self.get_daily_stats()

        print("\n" + "=" * 80)
        print(f"[DAILY STATS] 일일 통계 ({stats['date']})")
        print("=" * 80)
        print(f"실행 횟수: {stats['runs']}")
        print(f"수집 작업: {stats['total_collections']}회")
        print(f"API 호출: {stats['total_api_calls']}회")
        print(f"수집 기사: {stats['total_articles']}건")
        print(f"신규 기사: {stats['new_articles']}건")
        print(f"텔레그램 전송: {stats['telegram_sent']}건 (실패: {stats['telegram_failed']}건)")
        print(f"에러 발생: {stats['errors']}건")

        if stats['error_types']:
            print("\n에러 유형:")
            for error_type, count in stats['error_types'].items():
                print(f"  - {error_type}: {count}건")

        print("=" * 80 + "\n")


# 전역 로거 인스턴스
logger = MonitoringLogger()
