import { useEffect, useState } from 'react';
import './App.css';

function App() {
  const [games, setGames] = useState([]);
  const [platform, setPlatform] = useState('');
  const [search, setSearch] = useState('');
  const [selectedGameId, setSelectedGameId] = useState(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState('');

  const fetchGames = async () => {
    let url = 'https://game-1muo.onrender.com';

    if (platform) {
      url += `?platform=${platform}`;
    }

    const response = await fetch(url);
    const data = await response.json();

    const sortedGames = data.games.sort(
      (a, b) => new Date(a.release_date) - new Date(b.release_date),
    );

    setGames(sortedGames);
  };

  useEffect(() => {
    fetchGames();
  }, [platform]);

  const syncGames = async () => {
    setIsSyncing(true);
    setSyncMessage('게임 데이터를 업데이트하는 중입니다...');

    try {
      const response = await fetch('https://game-1muo.onrender.com', {
        method: 'POST',
      });

      const data = await response.json();

      if (data.error) {
        setSyncMessage(`업데이트 실패: ${data.error}`);
      } else {
        setSyncMessage(
          `업데이트 완료! 새로 저장: ${data.saved_count}개, 갱신: ${data.updated_count}개`,
        );
        await fetchGames();
      }
    } catch (error) {
      setSyncMessage('업데이트 중 오류가 발생했습니다.');
    } finally {
      setIsSyncing(false);
    }
  };

  const getDday = (releaseDate) => {
    const today = new Date();
    const target = new Date(releaseDate);

    today.setHours(0, 0, 0, 0);
    target.setHours(0, 0, 0, 0);

    const diffTime = target - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays > 0) return `D-${diffDays}`;
    if (diffDays === 0) return 'D-Day';
    return '출시됨';
  };

  const toggleDetails = (gameId) => {
    if (selectedGameId === gameId) {
      setSelectedGameId(null);
    } else {
      setSelectedGameId(gameId);
    }
  };

  const filteredGames = games.filter((game) =>
    game.title.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="app">
      <header className="hero">
        <p className="badge">Game Release Calendar</p>
        <h1>다가오는 게임 출시일을 한눈에</h1>
        <p className="subtitle">
          PC, PlayStation, Xbox, Switch 출시 예정 게임을 빠르게 확인하세요.
        </p>

        <section className="ad-banner">
          <p>광고 영역</p>
          <span>AdSense 승인 후 이 위치에 광고가 표시됩니다.</span>
        </section>

        {/* <button
          className="sync-button"
          onClick={syncGames}
          disabled={isSyncing}
        >
          {isSyncing ? '업데이트 중...' : '최신 게임 데이터 업데이트'}
        </button>

        {syncMessage && <p className="sync-message">{syncMessage}</p>} */}
      </header>

      <section className="controls">
        <input
          type="text"
          placeholder="게임 검색..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        <select value={platform} onChange={(e) => setPlatform(e.target.value)}>
          <option value="">전체 플랫폼</option>
          <option value="PC">PC</option>
          <option value="PlayStation">PlayStation</option>
          <option value="Xbox">Xbox</option>
          <option value="Switch">Switch</option>
        </select>
      </section>

      <section className="game-grid">
        {filteredGames.length === 0 && (
          <p className="empty-message">검색 결과가 없습니다.</p>
        )}

        {filteredGames.map((game) => (
          <article className="game-card" key={game.id}>
            {game.image && (
              <img className="game-image" src={game.image} alt={game.title} />
            )}

            <div className="card-top">
              <span>{game.status}</span>
              <strong>{game.release_date}</strong>
            </div>

            <div className="dday">{getDday(game.release_date)}</div>

            <h2>{game.title}</h2>
            <p className="genre">{game.genre}</p>

            <div className="platforms">
              {game.platforms.map((item) => (
                <span key={item}>{item}</span>
              ))}
            </div>

            <button
              className="detail-button"
              onClick={() => toggleDetails(game.id)}
            >
              {selectedGameId === game.id ? '닫기' : '상세보기'}
            </button>

            {selectedGameId === game.id && (
              <div className="detail-box">
                <h3>게임 정보</h3>
                <p>{game.description}</p>

                <div className="detail-row">
                  <strong>출시일</strong>
                  <span>{game.release_date}</span>
                </div>

                <div className="detail-row">
                  <strong>장르</strong>
                  <span>{game.genre}</span>
                </div>

                <div className="premium-box">관심 게임 저장 기능 준비중</div>

                <div className="ad-box">광고 영역 준비중</div>
              </div>
            )}
          </article>
        ))}
      </section>
      <footer className="footer">
        Game data and images provided by{' '}
        <a href="https://rawg.io/" target="_blank" rel="noreferrer">
          RAWG
        </a>
        .
        <section className="ad-banner bottom-ad">
          <p>광고 영역</p>
          <span>게임 목록 하단 광고 자리입니다.</span>
        </section>
      </footer>
    </div>
  );
}

export default App;
