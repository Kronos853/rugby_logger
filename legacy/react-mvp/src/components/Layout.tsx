import { NavLink, Outlet } from 'react-router-dom';

export function Layout() {
  return (
    <div className="app-shell">
      <nav className="app-nav">
        <NavLink to="/" end>
          Главная
        </NavLink>
        <NavLink to="/directories/templates">Шаблоны</NavLink>
        <NavLink to="/directories/teams">Команды</NavLink>
        <NavLink to="/directories/squads">Составы</NavLink>
        <NavLink to="/matches">Матчи</NavLink>
        <NavLink to="/admin">Администрирование</NavLink>
      </nav>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
