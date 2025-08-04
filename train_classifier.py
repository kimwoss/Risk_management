#!/usr/bin/env python3
"""
위기 단계 분류기 학습 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.services.classifier import CrisisStageClassifier
from src.utils.logger import Logger

def main():
    """위기 단계 분류기 학습 메인 함수"""
    logger = Logger.get_logger("train_classifier")
    
    try:
        print("🤖 위기 단계 분류기 학습 시작...")
        
        # 분류기 초기화
        classifier = CrisisStageClassifier()
        
        # 데이터 로드 및 전처리
        print("\n📊 데이터 로드 및 전처리...")
        df, info = classifier.load_and_prepare_data()
        
        # 데이터 정보 출력
        print(f"\n✅ 데이터 로드 완료:")
        print(f"   - 총 데이터: {df.shape[0]}행")
        print(f"   - 열 이름: {df.columns.tolist()}")
        
        if 'stage_clean' in df.columns:
            stage_counts = df['stage_clean'].value_counts()
            print(f"   - 단계 분포: {stage_counts.to_dict()}")
        
        # 샘플 데이터 출력
        print(f"\n📋 샘플 데이터:")
        if len(df) > 0:
            for i in range(min(3, len(df))):
                content = df.iloc[i]['content'][:100] + "..." if len(df.iloc[i]['content']) > 100 else df.iloc[i]['content']
                stage = df.iloc[i]['stage']
                print(f"   [{i+1}] 내용: {content}")
                print(f"       단계: {stage}")
        
        # 모델 학습
        print(f"\n🧠 모델 학습 시작...")
        
        # 여러 모델 타입으로 학습
        models_to_test = ['naive_bayes', 'svm', 'random_forest']
        results = {}
        
        for model_type in models_to_test:
            print(f"\n🔄 {model_type} 모델 학습...")
            try:
                result = classifier.train_model(df, model_type=model_type)
                results[model_type] = result
                
                print(f"   ✅ {model_type} 완료 - 정확도: {result['accuracy']:.3f}")
                print(f"      학습 데이터: {result['train_size']}개")
                print(f"      테스트 데이터: {result['test_size']}개")
                print(f"      클래스: {result['classes']}")
                
            except Exception as e:
                logger.error(f"{model_type} 학습 실패: {e}")
                print(f"   ❌ {model_type} 실패: {e}")
        
        # 최고 성능 모델 선택
        if results:
            best_model = max(results.keys(), key=lambda k: results[k]['accuracy'])
            best_accuracy = results[best_model]['accuracy']
            
            print(f"\n🏆 최고 성능 모델: {best_model} (정확도: {best_accuracy:.3f})")
            
            # 최고 모델로 재학습 및 저장
            classifier.train_model(df, model_type=best_model)
            classifier.save_model("best_crisis_classifier")
            
            print(f"✅ 모델 저장 완료: models/best_crisis_classifier")
        
        # 테스트 예측
        print(f"\n🔍 테스트 예측 (4단계 체계: 관심 → 주의 → 위기 → 비상):")
        test_samples = [
            "기자가 회사의 일반적인 사업 현황에 대해 문의했습니다",
            "언론에서 환경 문제에 대한 질문을 받았습니다", 
            "대규모 유출 사고에 대한 보도가 예정되어 있습니다",
            "전국적인 파업과 대규모 시위가 발생했습니다"
        ]
        
        stage_descriptions = {
            '관심': '(1단계) 잠재적 이슈 모니터링',
            '주의': '(2단계) 이슈 발생 및 초기 대응', 
            '위기': '(3단계) 심각한 이슈로 확산된 위기',
            '비상': '(4단계) 최고 수준의 비상 대응'
        }
        
        for i, sample in enumerate(test_samples, 1):
            pred = classifier.predict(sample)
            stage_desc = stage_descriptions.get(pred['stage'], pred['stage'])
            
            print(f"   [{i}] 텍스트: {sample}")
            print(f"       예측 단계: {pred['stage']} {stage_desc}")
            print(f"       신뢰도: {pred['confidence']:.3f}")
            
            if 'stage_info' in pred:
                info = pred['stage_info']
                print(f"       레벨: {info.get('level', 'N/A')}, 설명: {info.get('description', 'N/A')}")
            
            # 상위 2개 확률만 표시
            probs = pred['probabilities']
            sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:2]
            print(f"       상위 확률: {dict(sorted_probs)}")
            print()
        
        print(f"\n🎉 위기 단계 분류기 학습 완료!")
        
    except Exception as e:
        logger.error(f"분류기 학습 중 오류: {e}")
        print(f"❌ 오류 발생: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)