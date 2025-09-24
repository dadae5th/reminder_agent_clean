#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
빠른 이메일 전송 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from send_digest_supabase import run_daily_digest
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("📧 이메일 전송 시작...")
    try:
        result = run_daily_digest()
        print("✅ 이메일 전송 완료!")
    except Exception as e:
        print(f"💥 오류 발생: {e}")

if __name__ == "__main__":
    main()
