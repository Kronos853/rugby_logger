import { Link } from 'react-router-dom';

export function HomePage() {
  return (
    <div>
      <h1 className="page-title">Sports Video Logger</h1>
      <div className="card">
        <h3>Режимы</h3>
        <ul>
          <li>
            <Link to="/directories/templates">Справочники — шаблоны спорта</Link>
          </li>
          <li>
            <Link to="/directories/teams">Справочники — команды и игроки</Link>
          </li>
          <li>
            <Link to="/directories/squads">Справочники — сохранённые составы</Link>
          </li>
          <li>
            <Link to="/matches">Матчи — создание и подготовка</Link>
          </li>
          <li>
            <Link to="/admin">Администрирование — резервная копия БД</Link>
          </li>
        </ul>
      </div>
      <div className="card">
        <h3>Разметка (два монитора)</h3>
        <p className="muted">
          Откройте матч, затем запустите пульт на первом мониторе и видео на втором.
        </p>
        <p>
          <Link to="/matches">Перейти к матчам →</Link>
        </p>
      </div>
    </div>
  );
}
