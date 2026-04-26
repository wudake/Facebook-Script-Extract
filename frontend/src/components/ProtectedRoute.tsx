import { Navigate, useLocation } from 'react-router-dom'
import { isAuthenticated } from '../utils/auth'

interface Props {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: Props) {
  const location = useLocation()
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  return <>{children}</>
}
