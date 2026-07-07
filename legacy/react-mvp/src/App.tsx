import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { AdminPage } from './pages/admin/AdminPage';
import { SquadsPage } from './pages/directories/SquadsPage';
import { TeamDetailPage } from './pages/directories/TeamDetailPage';
import { TeamsPage } from './pages/directories/TeamsPage';
import { TemplateDetailPage } from './pages/directories/TemplateDetailPage';
import { TemplatesPage } from './pages/directories/TemplatesPage';
import { HomePage } from './pages/HomePage';
import { MatchSetupPage } from './pages/matches/MatchSetupPage';
import { MatchesPage } from './pages/matches/MatchesPage';
import { ControlPanelPage } from './pages/tagging/ControlPanelPage';
import { VideoPlayerPage } from './pages/tagging/VideoPlayerPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="directories/templates" element={<TemplatesPage />} />
          <Route path="directories/templates/:templateId" element={<TemplateDetailPage />} />
          <Route path="directories/teams" element={<TeamsPage />} />
          <Route path="directories/teams/:teamId" element={<TeamDetailPage />} />
          <Route path="directories/squads" element={<SquadsPage />} />
          <Route path="matches" element={<MatchesPage />} />
          <Route path="matches/:matchId/setup" element={<MatchSetupPage />} />
          <Route path="admin" element={<AdminPage />} />
        </Route>
        <Route path="tagging/:matchId/control" element={<ControlPanelPage />} />
        <Route path="tagging/:matchId/video" element={<VideoPlayerPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
