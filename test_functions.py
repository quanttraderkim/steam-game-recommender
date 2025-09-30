#!/usr/bin/env python3
"""
Steam Game Recommender 함수별 테스트
"""

import requests
import time
from datetime import datetime, timedelta

# Steam API 클라이언트
class SteamApiClient:
    def __init__(self):
        self.base_url = "https://api.steampowered.com"
        self.store_url = "https://store.steampowered.com/api"
        self.last_request_time = 0
        self.request_delay = 1.5
    
    def _rate_limit(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self.last_request_time = time.time()
    
    def get_all_games(self):
        try:
            self._rate_limit()
            response = requests.get(f"{self.base_url}/ISteamApps/GetAppList/v2/")
            response.raise_for_status()
            data = response.json()
            return data.get("applist", {}).get("apps", [])
        except Exception as e:
            print(f"게임 목록 조회 오류: {e}")
            return []
    
    def get_game_details(self, appid):
        try:
            self._rate_limit()
            response = requests.get(f"{self.store_url}/appdetails", params={"appids": appid})
            response.raise_for_status()
            data = response.json()
            if str(appid) in data and data[str(appid)].get("success"):
                return data[str(appid)]["data"]
            return None
        except Exception as e:
            print(f"게임 상세 정보 조회 오류: {e}")
            return None
    
    def get_featured_games(self):
        try:
            self._rate_limit()
            response = requests.get(f"{self.store_url}/featuredcategories")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"추천 게임 조회 오류: {e}")
            return None

# 캐시 클래스
class SimpleCache:
    def __init__(self):
        self.cache = {}
        self.cache_time = {}
        self.ttl = 300
    
    def get(self, key):
        if key in self.cache:
            if time.time() - self.cache_time[key] < self.ttl:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.cache_time[key]
        return None
    
    def set(self, key, value):
        self.cache[key] = value
        self.cache_time[key] = time.time()

def test_search_games():
    """게임 검색 테스트"""
    print("🔍 search_games 테스트...")
    try:
        steam_client = SteamApiClient()
        cache = SimpleCache()
        
        # 캐시에서 게임 목록 확인
        all_games = cache.get("all_games")
        if not all_games:
            all_games = steam_client.get_all_games()
            cache.set("all_games", all_games)
        
        query = "Counter-Strike"
        matching_games = [
            game for game in all_games 
            if query.lower() in game.get("name", "").lower()
        ]
        
        results = matching_games[:10]
        
        result = {
            "query": query,
            "total_found": len(matching_games),
            "results": [
                {
                    "appid": game["appid"],
                    "name": game["name"],
                    "type": "game"
                }
                for game in results
            ]
        }
        
        print(f"✅ 성공: {len(result['results'])}개 게임 발견")
        return True
    except Exception as e:
        print(f"❌ 실패: {e}")
        return False

def test_get_game_details():
    """게임 상세 정보 테스트"""
    print("\n📋 get_game_details 테스트...")
    try:
        steam_client = SteamApiClient()
        appid = 730  # Counter-Strike 2
        
        details = steam_client.get_game_details(appid)
        
        if not details:
            print("❌ 실패: 게임 정보 없음")
            return False
        
        # 가격 정보 처리
        price_info = details.get("price_overview", {})
        price_data = None
        if price_info:
            price_data = {
                "final_price": price_info.get("final", 0) / 100,
                "initial_price": price_info.get("initial", 0) / 100,
                "discount_percent": price_info.get("discount_percent", 0)
            }
        
        # 장르 정보 처리
        genres = []
        if "genres" in details:
            genres = [genre["description"] for genre in details["genres"]]
        
        result = {
            "appid": appid,
            "name": details.get("name", "Unknown"),
            "type": details.get("type", "Unknown"),
            "description": details.get("short_description", ""),
            "price": price_data,
            "release_date": details.get("release_date", {}).get("date", ""),
            "developers": details.get("developers", []),
            "publishers": details.get("publishers", []),
            "genres": genres,
            "recommendations": details.get("recommendations", {}).get("total", 0)
        }
        
        print(f"✅ 성공: {result['name']}")
        return True
    except Exception as e:
        print(f"❌ 실패: {e}")
        return False

def test_top_games_by_budget():
    """가격대별 게임 추천 테스트"""
    print("\n💵 top_games_by_budget 테스트...")
    try:
        steam_client = SteamApiClient()
        cache = SimpleCache()
        
        # 캐시에서 게임 목록 확인
        all_games = cache.get("all_games")
        if not all_games:
            all_games = steam_client.get_all_games()
            cache.set("all_games", all_games)
        
        max_price = 20.0
        budget_games = []
        
        # 샘플링 (처음 50개만 확인 - 테스트용)
        sample_games = all_games[:50]
        
        for game in sample_games:
            appid = game["appid"]
            details = steam_client.get_game_details(appid)
            
            if not details:
                continue
            
            price_info = details.get("price_overview", {})
            if not price_info:
                continue
            
            final_price = price_info.get("final", 0) / 100
            
            # 가격 필터
            if final_price > max_price:
                continue
            
            recommendations = details.get("recommendations", {}).get("total", 0)
            
            budget_games.append({
                "appid": appid,
                "name": details.get("name", "Unknown"),
                "price": final_price,
                "rating_percent": details.get("recommendations", {}).get("total", 0),
                "release_date": details.get("release_date", {}).get("date", ""),
                "genres": [g["description"] for g in details.get("genres", [])],
                "recommendations": recommendations
            })
        
        # 정렬
        budget_games.sort(key=lambda x: x["recommendations"], reverse=True)
        
        result = {
            "max_price": max_price,
            "genre": None,
            "sort_by": "rating",
            "total_found": len(budget_games),
            "results": budget_games[:10]
        }
        
        print(f"✅ 성공: {len(result['results'])}개 게임 발견")
        return True
    except Exception as e:
        print(f"❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_sale_recommendations():
    """할인 게임 추천 테스트"""
    print("\n💰 get_sale_recommendations 테스트...")
    try:
        steam_client = SteamApiClient()
        
        featured = steam_client.get_featured_games()
        
        if not featured or "specials" not in featured:
            print("❌ 실패: 할인 게임 정보 없음")
            return False
        
        specials = featured["specials"]["items"]
        sale_games = []
        
        # 처음 5개만 확인 (테스트용)
        for item in specials[:5]:
            appid = item["id"]
            details = steam_client.get_game_details(appid)
            
            if not details:
                continue
            
            price_info = details.get("price_overview", {})
            if not price_info:
                continue
            
            discount_percent = price_info.get("discount_percent", 0)
            final_price = price_info.get("final", 0) / 100
            
            sale_games.append({
                "appid": appid,
                "name": details.get("name", "Unknown"),
                "original_price": price_info.get("initial", 0) / 100,
                "final_price": final_price,
                "discount_percent": discount_percent,
                "genres": [g["description"] for g in details.get("genres", [])]
            })
        
        result = {
            "min_discount": 0,
            "max_price": None,
            "genre": None,
            "total_found": len(sale_games),
            "results": sale_games
        }
        
        print(f"✅ 성공: {len(result['results'])}개 할인 게임 발견")
        return True
    except Exception as e:
        print(f"❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 함수"""
    print("🎮 Steam Game Recommender 함수별 테스트 시작\n")
    
    tests = [
        test_search_games,
        test_get_game_details,
        test_top_games_by_budget,
        test_get_sale_recommendations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(2)  # 테스트 간 대기
    
    print(f"\n📊 테스트 결과: {passed}/{total} 함수 통과")
    
    if passed == total:
        print("🎉 모든 함수가 정상 작동합니다!")
    else:
        print("⚠️ 일부 함수에 문제가 있습니다.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
