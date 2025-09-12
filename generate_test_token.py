#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 간단한 테스트 토큰으로 업무 완료 테스트
import hashlib
import hmac

# 테스트용 간단한 토큰 생성
secret_key = "your_secret_key_here"
test_data = "test_task:daily:bae.jae.kwon@seegene.com:1"
test_token = hmac.new(secret_key.encode(), test_data.encode(), hashlib.sha256).hexdigest()

print(f"생성된 테스트 토큰: {test_token}")
print(f"완료 테스트 URL: http://localhost:8000/complete?token={test_token}")
