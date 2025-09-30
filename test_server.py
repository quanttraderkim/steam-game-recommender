#!/usr/bin/env python3
"""
Steam Game Recommender MCP Server 검증 스크립트
각 도구의 기본 기능을 테스트합니다.
"""

import sys
import json
from main import (
    search_games, 
    get_game_details, 
    get_sale_recommendations, 
    top_games_by_budget, 
    recommend_by_taste, 
    get_recent_releases
)

def test_search_games():
    """게임 검색 테스트"""
    print("🔍 게임 검색 테스트...")
    try:
        result = search_games("Counter-Strike")
        print(f"✅ 검색 결과: {len(result.get('results', []))}개 게임 발견")
        if result.get('results'):
            print(f"   첫 번째 게임: {result['results'][0]['name']} (ID: {result['results'][0]['appid']})")
        return True
    except Exception as e:
        print(f"❌ 게임 검색 실패: {e}")
        return False

def test_get_game_details():
    """게임 상세 정보 테스트"""
    print("\n📋 게임 상세 정보 테스트...")
    try:
        # Counter-Strike: Global Offensive의 Steam ID
        result = get_game_details(730)
        if result.get('error'):
            print(f"❌ 게임 상세 정보 실패: {result['error']}")
            return False
        print(f"✅ 게임 정보: {result.get('name', 'Unknown')}")
        print(f"   장르: {', '.join(result.get('genres', []))}")
        print(f"   가격: ${result.get('price', {}).get('final_price', 0):.2f}")
        return True
    except Exception as e:
        print(f"❌ 게임 상세 정보 실패: {e}")
        return False

def test_sale_recommendations():
    """할인 게임 추천 테스트"""
    print("\n💰 할인 게임 추천 테스트...")
    try:
        result = get_sale_recommendations(min_discount=30, limit=3)
        if result.get('error'):
            print(f"❌ 할인 게임 추천 실패: {result['error']}")
            return False
        print(f"✅ 할인 게임 {len(result.get('results', []))}개 발견")
        for game in result.get('results', [])[:2]:
            print(f"   {game['name']}: {game['discount_percent']}% 할인 (${game['final_price']:.2f})")
        return True
    except Exception as e:
        print(f"❌ 할인 게임 추천 실패: {e}")
        return False

def test_budget_games():
    """가격대별 게임 추천 테스트"""
    print("\n💵 가격대별 게임 추천 테스트...")
    try:
        result = top_games_by_budget(max_price=20.0, limit=3)
        if result.get('error'):
            print(f"❌ 가격대별 게임 추천 실패: {result['error']}")
            return False
        print(f"✅ 가격대 내 게임 {len(result.get('results', []))}개 발견")
        for game in result.get('results', [])[:2]:
            print(f"   {game['name']}: ${game['price']:.2f} (평점: {game['recommendations']})")
        return True
    except Exception as e:
        print(f"❌ 가격대별 게임 추천 실패: {e}")
        return False

def test_taste_recommendation():
    """취향 기반 추천 테스트"""
    print("\n🎯 취향 기반 추천 테스트...")
    try:
        result = recommend_by_taste(["Portal", "Half-Life"], limit=3)
        if result.get('error'):
            print(f"❌ 취향 기반 추천 실패: {result['error']}")
            return False
        print(f"✅ 추천 게임 {len(result.get('results', []))}개 발견")
        print(f"   상위 장르: {', '.join(result.get('top_genres', [])[:3])}")
        for game in result.get('results', [])[:2]:
            print(f"   {game['name']}: 매칭 점수 {game['match_score']}")
        return True
    except Exception as e:
        print(f"❌ 취향 기반 추천 실패: {e}")
        return False

def test_recent_releases():
    """신작 게임 추천 테스트"""
    print("\n🆕 신작 게임 추천 테스트...")
    try:
        result = get_recent_releases(days=90, limit=3)
        if result.get('error'):
            print(f"❌ 신작 게임 추천 실패: {result['error']}")
            return False
        print(f"✅ 최근 출시 게임 {len(result.get('results', []))}개 발견")
        for game in result.get('results', [])[:2]:
            print(f"   {game['name']}: {game['release_date']}")
        return True
    except Exception as e:
        print(f"❌ 신작 게임 추천 실패: {e}")
        return False

def main():
    """메인 검증 함수"""
    print("🎮 Steam Game Recommender MCP Server 검증 시작\n")
    
    tests = [
        test_search_games,
        test_get_game_details,
        test_sale_recommendations,
        test_budget_games,
        test_taste_recommendation,
        test_recent_releases
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 검증 결과: {passed}/{total} 테스트 통과")
    
    if passed == total:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("✅ FastMCP Cloud 배포 준비 완료!")
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 로그를 확인해주세요.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
