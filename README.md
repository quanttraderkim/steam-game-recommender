# Steam Game Recommender MCP Server

Steam 게임 추천을 위한 FastMCP 서버입니다. Claude Desktop과 연동하여 게임 추천 기능을 제공합니다.

## 🎮 주요 기능

- **게임 검색**: Steam 게임 검색 및 상세 정보 조회
- **할인 게임 추천**: 할인 중인 게임 추천
- **가격대별 추천**: 예산에 맞는 최고 게임 추천
- **취향 기반 추천**: 좋아하는 게임 기반 유사 게임 추천
- **신작 게임**: 최신 출시 게임 추천

## 🛠️ 사용 가능한 도구

### 1. `search_games`
게임 이름으로 Steam 게임을 검색합니다.
- **입력**: `query` (검색할 게임 이름)
- **출력**: 매칭되는 게임 목록

### 2. `get_game_details`
특정 게임의 상세 정보를 조회합니다.
- **입력**: `appid` (Steam 게임 ID)
- **출력**: 가격, 설명, 장르, 개발사 등 상세 정보

### 3. `get_sale_recommendations`
할인 중인 게임을 추천합니다.
- **입력**: 
  - `min_discount` (최소 할인율, 기본: 50%)
  - `max_price` (최대 가격, 선택)
  - `genre` (장르 필터, 선택)
  - `limit` (최대 결과 수, 기본: 10)
- **출력**: 할인 게임 목록

### 4. `top_games_by_budget`
가격대별 최고 게임을 추천합니다.
- **입력**:
  - `max_price` (최대 예산, 달러)
  - `genre` (장르 필터, 선택)
  - `sort_by` (정렬 기준: rating/release_date/popularity)
  - `limit` (최대 결과 수, 기본: 10)
- **출력**: 가격대 내 최고 게임 목록

### 5. `recommend_by_taste`
좋아하는 게임을 기반으로 유사한 게임을 추천합니다.
- **입력**:
  - `liked_games` (좋아한 게임 이름들)
  - `preferences` (추가 선호 태그/장르, 선택)
  - `limit` (최대 결과 수, 기본: 10)
- **출력**: 취향에 맞는 게임 추천

### 6. `get_recent_releases`
최신 출시 게임을 추천합니다.
- **입력**:
  - `days` (최근 며칠, 기본: 30)
  - `genre` (장르 필터, 선택)
  - `min_rating` (최소 평점, 선택)
  - `limit` (최대 결과 수, 기본: 10)
- **출력**: 최신 게임 목록

## 📦 설치 및 실행

### 로컬 개발 환경

```bash
# 1. 프로젝트 클론
git clone https://github.com/사용자명/steam-game-recommender.git
cd steam-game-recommender

# 2. Python 가상환경 설정
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 로컬 테스트
fastmcp dev main.py
```

### FastMCP Cloud 배포

1. **GitHub에 푸시**
```bash
git add .
git commit -m "Initial commit: Steam Game Recommender MCP Server"
git push origin main
```

2. **FastMCP Cloud에서 배포**
   - https://fastmcp.cloud 접속
   - GitHub 레포지토리 연결
   - Server Name: `steam-game-recommender`
   - Entry Point: `main.py`

## 🔧 Claude Desktop 설정

배포 후 Claude Desktop 설정 파일에 추가:

```json
{
  "mcpServers": {
    "steam-game-recommender": {
      "command": "npx",
      "args": ["@modelcontextprotocol/inspector", "https://steam-game-recommender.fastmcp.app/mcp"]
    }
  }
}
```

## 📋 사용 예시

### 게임 검색
```
"Counter-Strike" 게임을 검색해주세요.
```

### 할인 게임 추천
```
50% 이상 할인된 액션 게임을 추천해주세요.
```

### 가격대별 추천
```
20달러 이하의 최고 평점 게임을 추천해주세요.
```

### 취향 기반 추천
```
"Portal", "Half-Life"를 좋아하는데 비슷한 게임을 추천해주세요.
```

### 신작 게임
```
최근 30일 내에 출시된 인디 게임을 추천해주세요.
```

## ⚠️ 주의사항

- Steam API는 Rate limit이 있으므로 요청 간격을 조절합니다.
- 일부 게임 정보는 Steam에서 제공하지 않을 수 있습니다.
- 가격은 달러 기준으로 표시됩니다.

## 📝 라이선스

MIT License

## 🤝 기여

이슈나 풀 리퀘스트를 환영합니다!