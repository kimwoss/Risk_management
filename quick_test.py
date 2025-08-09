#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Quick Test Starting...")

try:
    from data_based_llm import DataBasedLLM
    print("DataBasedLLM imported successfully")
    
    llm = DataBasedLLM()
    print("DataBasedLLM initialized successfully")
    
    # 간단한 기존 메소드 테스트
    result = llm.generate_issue_report(
        "조선일보", 
        "김철수", 
        "포스코 이슈 테스트"
    )
    
    print(f"Report generated successfully!")
    print(f"Length: {len(result)} characters")
    print(f"Preview: {result[:100]}...")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()