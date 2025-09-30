"""
Steam Game Recommender MCP Server

Steam 게임 추천을 위한 FastMCP 서버입니다.
Claude Desktop과 연동하여 게임 추천 기능을 제공합니다.

주요 기능:
- 게임 검색 및 상세 정보 조회
- 할인 게임 추천
- 가격대별 최고 게임 추천
- 취향 기반 게임 추천
- 신작 게임 추천
"""

from fastmcp import FastMCP
import requests
import json
from typing import Dict, List, Optional, Any
import time
from datetime import datetime, timedelta

# FastMCP 서버 생성
mcp = FastMCP("steam-game-recommender")

# Steam API 클라이언트
class SteamApiClient:
    """Steam API 클라이언트"""
    
    def __init__(self):
        self.base_url = "https://api.steampowered.com"
        self.store_url = "https://store.steampowered.com/api"
        self.last_request_time = 0
        self.request_delay = 1.5  # Rate limit 고려
    
    def _rate_limit(self):
        """Rate limit 관리"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self.last_request_time = time.time()
    
    def get_all_games(self) -> List[Dict]:
        """전체 게임 목록 조회"""
        try:
            self._rate_limit()
            response = requests.get(f"{self.base_url}/ISteamApps/GetAppList/v2/")
            response.raise_for_status()
            data = response.json()
            return data.get("applist", {}).get("apps", [])
        except Exception as e:
            print(f"게임 목록 조회 오류: {e}")
            return []
    
    def get_game_details(self, appid: int) -> Optional[Dict]:
        """게임 상세 정보 조회"""
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
    
    def get_featured_games(self) -> Optional[Dict]:
        """추천/할인 게임 조회"""
        try:
            self._rate_limit()
            response = requests.get(f"{self.store_url}/featuredcategories")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"추천 게임 조회 오류: {e}")
            return None

# Steam API 클라이언트 인스턴스
steam_client = SteamApiClient()

# 간단한 캐시 (메모리 기반)
class SimpleCache:
    def __init__(self):
        self.cache = {}
        self.cache_time = {}
        self.ttl = 300  # 5분 TTL
    
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

cache = SimpleCache()

@mcp.tool
def search_games(query: str) -> Dict[str, Any]:
    """Steam 게임 검색
    
    Args:
        query: 검색할 게임 이름
    
    Returns:
        dict: 검색된 게임 목록과 기본 정보
    """
    try:
        # 캐시에서 게임 목록 확인
        all_games = cache.get("all_games")
        if not all_games:
            all_games = steam_client.get_all_games()
            cache.set("all_games", all_games)
        
        # 게임 이름으로 필터링 (대소문자 무시)
        matching_games = [
            game for game in all_games 
            if query.lower() in game.get("name", "").lower()
        ]
        
        # 최대 10개까지만 반환
        results = matching_games[:10]
        
        return {
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
    except Exception as e:
        return {
            "error": f"게임 검색 중 오류 발생: {str(e)}",
            "query": query,
            "results": []
        }

@mcp.tool
def get_game_details(appid: int) -> Dict[str, Any]:
    """게임 상세 정보 조회
    
    Args:
        appid: Steam 게임 ID
    
    Returns:
        dict: 게임의 상세 정보 (가격, 설명, 장르 등)
    """
    try:
        details = steam_client.get_game_details(appid)
        
        if not details:
            return {
                "error": f"게임 ID {appid}에 대한 정보를 찾을 수 없습니다.",
                "appid": appid
            }
        
        # 가격 정보 처리
        price_info = details.get("price_overview", {})
        price_data = None
        if price_info:
            price_data = {
                "final_price": price_info.get("final", 0) / 100,  # 센트를 달러로 변환
                "initial_price": price_info.get("initial", 0) / 100,
                "discount_percent": price_info.get("discount_percent", 0)
            }
        
        # 장르 정보 처리
        genres = []
        if "genres" in details:
            genres = [genre["description"] for genre in details["genres"]]
        
        # 개발사/퍼블리셔 정보
        developers = details.get("developers", [])
        publishers = details.get("publishers", [])
        
        return {
            "appid": appid,
            "name": details.get("name", "Unknown"),
            "type": details.get("type", "Unknown"),
            "description": details.get("short_description", ""),
            "price": price_data,
            "release_date": details.get("release_date", {}).get("date", ""),
            "developers": developers,
            "publishers": publishers,
            "genres": genres,
            "recommendations": details.get("recommendations", {}).get("total", 0)
        }
    except Exception as e:
        return {
            "error": f"게임 상세 정보 조회 중 오류 발생: {str(e)}",
            "appid": appid
        }

@mcp.tool
def get_sale_recommendations(min_discount: int = 50, max_price: Optional[float] = None, genre: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """할인 게임 추천
    
    Args:
        min_discount: 최소 할인율 (기본: 50%)
        max_price: 최대 가격 (달러, 선택)
        genre: 장르 필터 (선택)
        limit: 최대 결과 수 (기본: 10)
    
    Returns:
        dict: 할인 중인 게임 목록
    """
    try:
        featured = steam_client.get_featured_games()
        
        if not featured or "specials" not in featured:
            return {
                "error": "할인 게임 정보를 가져올 수 없습니다.",
                "results": []
            }
        
        specials = featured["specials"]["items"]
        sale_games = []
        
        for item in specials:
            appid = item["id"]
            details = steam_client.get_game_details(appid)
            
            if not details:
                continue
            
            price_info = details.get("price_overview", {})
            if not price_info:
                continue
            
            discount_percent = price_info.get("discount_percent", 0)
            final_price = price_info.get("final", 0) / 100
            
            # 할인율 필터
            if discount_percent < min_discount:
                continue
            
            # 가격 필터
            if max_price and final_price > max_price:
                continue
            
            # 장르 필터
            if genre:
                game_genres = [g["description"].lower() for g in details.get("genres", [])]
                if genre.lower() not in game_genres:
                    continue
            
            sale_games.append({
                "appid": appid,
                "name": details.get("name", "Unknown"),
                "original_price": price_info.get("initial", 0) / 100,
                "final_price": final_price,
                "discount_percent": discount_percent,
                "genres": [g["description"] for g in details.get("genres", [])]
            })
        
        # 할인율 높은 순으로 정렬
        sale_games.sort(key=lambda x: x["discount_percent"], reverse=True)
        
        return {
            "min_discount": min_discount,
            "max_price": max_price,
            "genre": genre,
            "total_found": len(sale_games),
            "results": sale_games[:limit]
        }
    except Exception as e:
        return {
            "error": f"할인 게임 추천 중 오류 발생: {str(e)}",
            "results": []
        }

@mcp.tool
def top_games_by_budget(max_price: float, genre: Optional[str] = None, sort_by: str = "rating", limit: int = 10) -> Dict[str, Any]:
    """가격대별 최고 게임 추천
    
    Args:
        max_price: 최대 예산 (달러)
        genre: 장르 필터 (선택)
        sort_by: 정렬 기준 (rating/release_date/popularity, 기본: rating)
        limit: 최대 결과 수 (기본: 10)
    
    Returns:
        dict: 가격대 내 최고 게임 목록
    """
    try:
        # 캐시에서 게임 목록 확인
        all_games = cache.get("all_games")
        if not all_games:
            all_games = steam_client.get_all_games()
            cache.set("all_games", all_games)
        
        budget_games = []
        
        # 샘플링 (전체 게임이 너무 많으므로 처음 1000개만 확인)
        sample_games = all_games[:1000]
        
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
            
            # 장르 필터
            if genre:
                game_genres = [g["description"].lower() for g in details.get("genres", [])]
                if genre.lower() not in game_genres:
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
        if sort_by == "rating":
            budget_games.sort(key=lambda x: x["recommendations"], reverse=True)
        elif sort_by == "release_date":
            budget_games.sort(key=lambda x: x["release_date"], reverse=True)
        elif sort_by == "popularity":
            budget_games.sort(key=lambda x: x["rating_percent"], reverse=True)
        
        return {
            "max_price": max_price,
            "genre": genre,
            "sort_by": sort_by,
            "total_found": len(budget_games),
            "results": budget_games[:limit]
        }
    except Exception as e:
        return {
            "error": f"가격대별 게임 추천 중 오류 발생: {str(e)}",
            "results": []
        }

@mcp.tool
def recommend_by_taste(liked_games: List[str], preferences: Optional[List[str]] = None, limit: int = 10) -> Dict[str, Any]:
    """취향 기반 게임 추천
    
    Args:
        liked_games: 좋아했던 게임 이름들
        preferences: 추가 선호 태그/장르 (선택)
        limit: 최대 결과 수 (기본: 10)
    
    Returns:
        dict: 취향에 맞는 게임 추천 목록
    """
    try:
        # 캐시에서 게임 목록 확인
        all_games = cache.get("all_games")
        if not all_games:
            all_games = steam_client.get_all_games()
            cache.set("all_games", all_games)
        
        # 좋아하는 게임들의 정보 수집
        liked_game_details = []
        
        for game_name in liked_games:
            # 직접 검색 로직 구현
            matching_games = [
                game for game in all_games 
                if game_name.lower() in game.get("name", "").lower()
            ]
            
            if matching_games:
                appid = matching_games[0]["appid"]
                details = steam_client.get_game_details(appid)
                if details:
                    liked_game_details.append(details)
        
        if not liked_game_details:
            return {
                "error": "좋아하는 게임에 대한 정보를 찾을 수 없습니다.",
                "results": []
            }
        
        # 공통 장르 추출
        all_genres = []
        for game in liked_game_details:
            genres = [g["description"] for g in game.get("genres", [])]
            all_genres.extend(genres)
        
        # 장르 빈도 계산
        genre_counts = {}
        for genre in all_genres:
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # 선호 장르 추가
        if preferences:
            for pref in preferences:
                genre_counts[pref] = genre_counts.get(pref, 0) + 2
        
        # 상위 장르 선택
        top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_genre_names = [genre for genre, count in top_genres]
        
        # 해당 장르의 게임들 찾기
        recommended_games = []
        
        # 샘플링 (처음 500개만 확인)
        sample_games = all_games[:500]
        
        for game in sample_games:
            appid = game["appid"]
            details = steam_client.get_game_details(appid)
            
            if not details:
                continue
            
            game_genres = [g["description"] for g in details.get("genres", [])]
            
            # 이미 좋아하는 게임은 제외
            if details["name"] in liked_games:
                continue
            
            # 장르 매칭 점수 계산
            match_score = 0
            for genre in game_genres:
                if genre in top_genre_names:
                    match_score += genre_counts.get(genre, 0)
            
            if match_score > 0:
                recommendations = details.get("recommendations", {}).get("total", 0)
                recommended_games.append({
                    "appid": appid,
                    "name": details.get("name", "Unknown"),
                    "match_score": match_score,
                    "genres": game_genres,
                    "recommendations": recommendations,
                    "price": details.get("price_overview", {}).get("final", 0) / 100
                })
        
        # 매칭 점수와 평점을 고려한 정렬
        recommended_games.sort(key=lambda x: (x["match_score"], x["recommendations"]), reverse=True)
        
        return {
            "liked_games": liked_games,
            "preferences": preferences,
            "top_genres": top_genre_names,
            "total_found": len(recommended_games),
            "results": recommended_games[:limit]
        }
    except Exception as e:
        return {
            "error": f"취향 기반 추천 중 오류 발생: {str(e)}",
            "results": []
        }

@mcp.tool
def get_recent_releases(days: int = 30, genre: Optional[str] = None, min_rating: Optional[int] = None, limit: int = 10) -> Dict[str, Any]:
    """신작 게임 추천
    
    Args:
        days: 최근 며칠 (기본: 30)
        genre: 장르 필터 (선택)
        min_rating: 최소 평점 (선택)
        limit: 최대 결과 수 (기본: 10)
    
    Returns:
        dict: 최신 출시 게임 목록
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 캐시에서 게임 목록 확인
        all_games = cache.get("all_games")
        if not all_games:
            all_games = steam_client.get_all_games()
            cache.set("all_games", all_games)
        
        recent_games = []
        
        # 샘플링 (처음 1000개만 확인)
        sample_games = all_games[:1000]
        
        for game in sample_games:
            appid = game["appid"]
            details = steam_client.get_game_details(appid)
            
            if not details:
                continue
            
            release_date_str = details.get("release_date", {}).get("date", "")
            if not release_date_str:
                continue
            
            try:
                # 날짜 파싱 (Steam 형식: "Dec 10, 2020")
                release_date = datetime.strptime(release_date_str, "%b %d, %Y")
                
                if release_date < cutoff_date:
                    continue
                
                # 장르 필터
                if genre:
                    game_genres = [g["description"].lower() for g in details.get("genres", [])]
                    if genre.lower() not in game_genres:
                        continue
                
                # 평점 필터
                recommendations = details.get("recommendations", {}).get("total", 0)
                if min_rating and recommendations < min_rating:
                    continue
                
                recent_games.append({
                    "appid": appid,
                    "name": details.get("name", "Unknown"),
                    "release_date": release_date_str,
                    "genres": [g["description"] for g in details.get("genres", [])],
                    "recommendations": recommendations,
                    "price": details.get("price_overview", {}).get("final", 0) / 100
                })
            except ValueError:
                # 날짜 파싱 실패 시 건너뛰기
                continue
        
        # 출시일 최신순으로 정렬
        recent_games.sort(key=lambda x: x["release_date"], reverse=True)
        
        return {
            "days": days,
            "genre": genre,
            "min_rating": min_rating,
            "total_found": len(recent_games),
            "results": recent_games[:limit]
        }
    except Exception as e:
        return {
            "error": f"신작 게임 추천 중 오류 발생: {str(e)}",
            "results": []
        }

@mcp.tool
def recommend_action_rpg_games(limit: int = 10) -> Dict[str, Any]:
    """액션 RPG 게임 추천
    
    Args:
        limit: 최대 결과 수 (기본: 10)
    
    Returns:
        dict: 액션 RPG 게임 추천 목록
    """
    try:
        # 캐시에서 게임 목록 확인
        all_games = cache.get("all_games")
        if not all_games:
            all_games = steam_client.get_all_games()
            cache.set("all_games", all_games)
        
        action_rpg_games = []
        
        # 샘플링 (처음 1000개만 확인)
        sample_games = all_games[:1000]
        
        for game in sample_games:
            appid = game["appid"]
            details = steam_client.get_game_details(appid)
            
            if not details:
                continue
            
            game_genres = [g["description"].lower() for g in details.get("genres", [])]
            
            # 액션 RPG 장르 확인
            is_action_rpg = (
                "action" in game_genres and 
                ("rpg" in game_genres or "role-playing" in game_genres)
            ) or (
                "action rpg" in " ".join(game_genres) or
                "action role-playing" in " ".join(game_genres)
            )
            
            if is_action_rpg:
                recommendations = details.get("recommendations", {}).get("total", 0)
                price_info = details.get("price_overview", {})
                final_price = price_info.get("final", 0) / 100 if price_info else 0
                
                action_rpg_games.append({
                    "appid": appid,
                    "name": details.get("name", "Unknown"),
                    "genres": [g["description"] for g in details.get("genres", [])],
                    "recommendations": recommendations,
                    "price": final_price,
                    "release_date": details.get("release_date", {}).get("date", "")
                })
        
        # 평점 높은 순으로 정렬
        action_rpg_games.sort(key=lambda x: x["recommendations"], reverse=True)
        
        return {
            "genre": "Action RPG",
            "total_found": len(action_rpg_games),
            "results": action_rpg_games[:limit]
        }
    except Exception as e:
        return {
            "error": f"액션 RPG 게임 추천 중 오류 발생: {str(e)}",
            "results": []
        }

if __name__ == "__main__":
    mcp.run()
