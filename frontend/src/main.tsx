import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Navigate, RouterProvider, createBrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { FixedRateView } from './pages/FixedRateView'
import { IsaView } from './pages/IsaView'

// main.tsx — frontend entrypoint that mounts React and sets up routes
// This is where the browser app starts.

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      // Default route: send users to the Fixed Rate page.
      { index: true, element: <Navigate to="/fixed" replace /> },
      { path: 'fixed', element: <FixedRateView /> },
      { path: 'isa', element: <IsaView /> },
    ],
  },
])

// Attach React to the <div id="root"> element in index.html.
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
