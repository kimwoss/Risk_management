"""
데이터 버전 관리 및 업데이트 추적 시스템
"""
import json
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import hashlib

class DataVersionManager:
    """데이터 파일의 버전 관리 및 변경 추적 클래스"""
    
    def __init__(self, data_folder: str = "data"):
        self.data_folder = data_folder
        self.version_file = os.path.join(data_folder, "version_history.json")
        self.backup_folder = os.path.join(data_folder, "backups")
        
        # 백업 폴더 생성
        os.makedirs(self.backup_folder, exist_ok=True)
        
        # 버전 히스토리 초기화
        self.version_history = self._load_version_history()
    
    def _load_version_history(self) -> Dict:
        """버전 히스토리 로드"""
        if os.path.exists(self.version_file):
            with open(self.version_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "master_data.json": {"versions": [], "current_version": "1.0.0"},
                "언론대응내역.csv": {"versions": [], "current_version": "1.0.0"}
            }
    
    def _save_version_history(self):
        """버전 히스토리 저장"""
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(self.version_history, f, ensure_ascii=False, indent=2)
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """파일 해시 계산"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _increment_version(self, current_version: str, change_type: str = "minor") -> str:
        """버전 번호 증가"""
        try:
            major, minor, patch = map(int, current_version.split('.'))
            
            if change_type == "major":
                major += 1
                minor = 0
                patch = 0
            elif change_type == "minor":
                minor += 1
                patch = 0
            else:  # patch
                patch += 1
            
            return f"{major}.{minor}.{patch}"
        except:
            return "1.0.1"
    
    def create_backup(self, file_name: str, change_description: str = "", change_type: str = "minor") -> bool:
        """파일 백업 생성"""
        try:
            source_path = os.path.join(self.data_folder, file_name)
            if not os.path.exists(source_path):
                print(f"⚠️ 파일을 찾을 수 없습니다: {file_name}")
                return False
            
            # 현재 파일 해시 계산
            current_hash = self._calculate_file_hash(source_path)
            
            # 이전 해시와 비교하여 변경 여부 확인
            if file_name in self.version_history:
                versions = self.version_history[file_name]["versions"]
                if versions and versions[-1].get("hash") == current_hash:
                    print(f"📝 {file_name}: 변경사항 없음 (백업 스킵)")
                    return True
            
            # 새 버전 번호 생성
            current_version = self.version_history[file_name]["current_version"]
            new_version = self._increment_version(current_version, change_type)
            
            # 백업 파일명 생성 (타임스탬프 포함)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_name.split('.')[0]}_v{new_version}_{timestamp}.{file_name.split('.')[-1]}"
            backup_path = os.path.join(self.backup_folder, backup_name)
            
            # 파일 복사
            if file_name.endswith('.csv'):
                df = pd.read_csv(source_path, encoding='utf-8')
                df.to_csv(backup_path, index=False, encoding='utf-8')
            else:
                with open(source_path, 'r', encoding='utf-8') as src:
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            
            # 버전 정보 업데이트
            version_info = {
                "version": new_version,
                "timestamp": datetime.now().isoformat(),
                "backup_file": backup_name,
                "hash": current_hash,
                "change_description": change_description,
                "change_type": change_type,
                "file_size": os.path.getsize(source_path)
            }
            
            self.version_history[file_name]["versions"].append(version_info)
            self.version_history[file_name]["current_version"] = new_version
            
            # 최근 10개 버전만 유지
            if len(self.version_history[file_name]["versions"]) > 10:
                old_versions = self.version_history[file_name]["versions"][:-10]
                for old_version in old_versions:
                    old_backup_path = os.path.join(self.backup_folder, old_version["backup_file"])
                    if os.path.exists(old_backup_path):
                        os.remove(old_backup_path)
                
                self.version_history[file_name]["versions"] = self.version_history[file_name]["versions"][-10:]
            
            self._save_version_history()
            
            print(f"✅ {file_name} 백업 완료: v{new_version}")
            if change_description:
                print(f"   📝 변경 내용: {change_description}")
            
            return True
            
        except Exception as e:
            print(f"❌ 백업 실패 ({file_name}): {str(e)}")
            return False
    
    def get_version_info(self, file_name: str) -> Dict:
        """파일 버전 정보 조회"""
        if file_name in self.version_history:
            return self.version_history[file_name]
        return {"versions": [], "current_version": "1.0.0"}
    
    def list_all_versions(self) -> str:
        """모든 파일의 버전 정보 출력"""
        result = ["=== 데이터 파일 버전 현황 ===\n"]
        
        for file_name, info in self.version_history.items():
            result.append(f"📁 {file_name}")
            result.append(f"   현재 버전: v{info['current_version']}")
            result.append(f"   총 버전 수: {len(info['versions'])}")
            
            if info['versions']:
                latest = info['versions'][-1]
                result.append(f"   최근 업데이트: {latest['timestamp'][:19]}")
                if latest.get('change_description'):
                    result.append(f"   변경 내용: {latest['change_description']}")
            
            result.append("")
        
        return "\n".join(result)
    
    def restore_version(self, file_name: str, version: str) -> bool:
        """특정 버전으로 복원"""
        try:
            if file_name not in self.version_history:
                print(f"❌ 파일 이력을 찾을 수 없습니다: {file_name}")
                return False
            
            # 해당 버전 찾기
            target_version = None
            for ver_info in self.version_history[file_name]["versions"]:
                if ver_info["version"] == version:
                    target_version = ver_info
                    break
            
            if not target_version:
                print(f"❌ 버전을 찾을 수 없습니다: v{version}")
                return False
            
            # 백업 파일 경로
            backup_path = os.path.join(self.backup_folder, target_version["backup_file"])
            if not os.path.exists(backup_path):
                print(f"❌ 백업 파일을 찾을 수 없습니다: {target_version['backup_file']}")
                return False
            
            # 현재 파일 백업 (복원 전)
            self.create_backup(file_name, f"복원 전 백업 (v{version}으로 복원)", "patch")
            
            # 파일 복원
            target_path = os.path.join(self.data_folder, file_name)
            if file_name.endswith('.csv'):
                df = pd.read_csv(backup_path, encoding='utf-8')
                df.to_csv(target_path, index=False, encoding='utf-8')
            else:
                with open(backup_path, 'r', encoding='utf-8') as src:
                    with open(target_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            
            print(f"✅ {file_name}을 v{version}으로 복원했습니다")
            return True
            
        except Exception as e:
            print(f"❌ 복원 실패: {str(e)}")
            return False
    
    def check_data_integrity(self) -> Dict[str, bool]:
        """데이터 무결성 검사"""
        results = {}
        
        # master_data.json 검사
        try:
            master_path = os.path.join(self.data_folder, "master_data.json")
            with open(master_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 필수 필드 검사
            required_sections = ["departments", "media_contacts", "crisis_levels", "system_config"]
            missing_sections = [s for s in required_sections if s not in data]
            
            if missing_sections:
                results["master_data.json"] = False
                print(f"❌ master_data.json: 누락된 섹션 - {missing_sections}")
            else:
                results["master_data.json"] = True
                print("✅ master_data.json: 구조 검증 통과")
                
        except Exception as e:
            results["master_data.json"] = False
            print(f"❌ master_data.json: 검증 실패 - {str(e)}")
        
        # 언론대응내역.csv 검사
        try:
            csv_path = os.path.join(self.data_folder, "언론대응내역.csv")
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            required_columns = ["순번", "발생 일시", "발생 유형", "단계", "이슈 발생 보고", "대응 결과"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                results["언론대응내역.csv"] = False
                print(f"❌ 언론대응내역.csv: 누락된 컬럼 - {missing_columns}")
            else:
                results["언론대응내역.csv"] = True
                print(f"✅ 언론대응내역.csv: 구조 검증 통과 ({len(df)}건)")
                
        except Exception as e:
            results["언론대응내역.csv"] = False
            print(f"❌ 언론대응내역.csv: 검증 실패 - {str(e)}")
        
        return results

def main():
    """데이터 버전 관리 시스템 테스트"""
    print("=== 데이터 버전 관리 시스템 ===\n")
    
    # 버전 관리자 초기화
    version_manager = DataVersionManager()
    
    # 1. 현재 버전 정보 출력
    print("1. 현재 버전 정보")
    print(version_manager.list_all_versions())
    
    # 2. 데이터 무결성 검사
    print("2. 데이터 무결성 검사")
    integrity_results = version_manager.check_data_integrity()
    
    # 3. 백업 생성 (변경사항이 있는 경우만)
    print("\n3. 백업 생성")
    version_manager.create_backup("master_data.json", "시스템 초기 설정", "minor")
    version_manager.create_backup("언론대응내역.csv", "데이터 정리 및 검증", "minor")
    
    # 4. 업데이트된 버전 정보
    print("\n4. 업데이트된 버전 정보")
    print(version_manager.list_all_versions())

if __name__ == "__main__":
    main()
