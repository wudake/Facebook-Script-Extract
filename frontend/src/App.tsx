import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import SubmitPage from './pages/SubmitPage'
import TasksPage from './pages/TasksPage'
import TaskDetailPage from './pages/TaskDetailPage'
import SettingsPage from './pages/SettingsPage'
import CompletedScriptsPage from './pages/CompletedScriptsPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<SubmitPage />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="tasks/:taskId" element={<TaskDetailPage />} />
          <Route path="completed" element={<CompletedScriptsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
