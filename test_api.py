#!/usr/bin/env python3
"""
Steam Game Recommender MCP Server 간단 검증 스크립트
Steam API 연결 및 기본 기능을 테스트합니다.
"""

import requests
import time

def test_steam_api_connection():
    """Steam API 연결 테스트"""
    print("🔗 Steam API 연결 테스트...")
    
    try:
        # Steam 게임 목록 API 테스트
        response = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2/")
        response.raise_for_status()
        data = response.json()
        
        apps = data.get("applist", {}).get("apps", [])
        print(f"✅ Steam API 연결 성공: {len(apps)}개 게임 발견")
        
        # Counter-Strike 검색 테스트
        cs_games = [app for app in apps if "counter-strike" in app.get("name", "").lower()]
        print(f"✅ Counter-Strike 게임 {len(cs_games)}개 발견")
        
        if cs_games:
            print(f"   예시: {cs_games[0]['name']} (ID: {cs_games[0]['appid']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Steam API 연결 실패: {e}")
        return False

def test_game_details_api():
    """게임 상세 정보 API 테스트"""
    print("\n📋 게임 상세 정보 API 테스트...")
    
    try:
        # Counter-Strike: Global Offensive (ID: 730) 테스트
        response = requests.get("https://store.steampowered.com/api/appdetails", params={"appids": 730})
        response.raise_for_status()
        data = response.json()
        
        if "730" in data and data["730"].get("success"):
            game_data = data["730"]["data"]
            print(f"✅ 게임 상세 정보 조회 성공: {game_data.get('name', 'Unknown')}")
            
            # 가격 정보 확인
            price_info = game_data.get("price_overview", {})
            if price_info:
                final_price = price_info.get("final", 0) / 100
                print(f"   가격: ${final_price:.2f}")
            
            # 장르 정보 확인
            genres = game_data.get("genres", [])
            if genres:
                genre_names = [g["description"] for g in genres]
                print(f"   장르: {', '.join(genre_names[:3])}")
            
            return True
        else:
            print("❌ 게임 상세 정보 조회 실패: 데이터 없음")
            return False
            
    except Exception as e:
        print(f"❌ 게임 상세 정보 API 테스트 실패: {e}")
        return False

def test_featured_games_api():
    """추천 게임 API 테스트"""
    print("\n⭐ 추천 게임 API 테스트...")
    
    try:
        response = requests.get("https://store.steampowered.com/api/featuredcategories")
        response.raise_for_status()
        data = response.json()
        
        if "specials" in data:
            specials = data["specials"]["items"]
            print(f"✅ 추천 게임 API 연결 성공: {len(specials)}개 할인 게임 발견")
            
            if specials:
                first_game = specials[0]
                print(f"   예시 할인 게임 ID: {first_game['id']}")
            
            return True
        else:
            print("❌ 추천 게임 API 테스트 실패: specials 섹션 없음")
            return False
            
    except Exception as e:
        print(f"❌ 추천 게임 API 테스트 실패: {e}")
        return False

def test_rate_limiting():
    """Rate limiting 테스트"""
    print("\n⏱️ Rate Limiting 테스트...")
    
    try:
        start_time = time.time()
        
        # 연속 3번 요청
        for i in range(3):
            response = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2/")
            response.raise_for_status()
            print(f"   요청 {i+1}/3 완료")
            time.sleep(1)  # 1초 대기
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"✅ Rate Limiting 테스트 완료: 총 {total_time:.1f}초 소요")
        return True
        
    except Exception as e:
        print(f"❌ Rate Limiting 테스트 실패: {e}")
        return False

def main():
    """메인 검증 함수"""
    print("🎮 Steam Game Recommender MCP Server API 검증 시작\n")
    
    tests = [
        test_steam_api_connection,
        test_game_details_api,
        test_featured_games_api,
        test_rate_limiting
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(1)  # 테스트 간 대기
    
    print(f"\n📊 검증 결과: {passed}/{total} 테스트 통과")
    
    if passed == total:
        print("🎉 모든 API 테스트가 성공적으로 완료되었습니다!")
        print("✅ Steam API 연동 준비 완료!")
        print("✅ FastMCP Cloud 배포 준비 완료!")
    else:
        print("⚠️ 일부 API 테스트가 실패했습니다.")
        print("   네트워크 연결이나 Steam API 상태를 확인해주세요.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
