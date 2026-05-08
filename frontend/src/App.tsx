import { NavLink, Outlet } from 'react-router-dom'

function App() {
  // Top-level layout: header navigation + the current page (Outlet).
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-indigo-500 to-fuchsia-500" />
            <div>
              <div className="text-sm font-semibold leading-4">
                UK Savings & ISA Rate Tracker
              </div>
              <div className="text-xs text-slate-400">
                Local-first • SQLite • React
              </div>
            </div>
          </div>
          <nav className="flex items-center gap-2 text-sm">
            <NavLink
              to="/fixed"
              className={({ isActive }) =>
                [
                  'rounded-md px-3 py-1.5',
                  isActive
                    ? 'bg-slate-100 text-slate-900'
                    : 'text-slate-200 hover:bg-slate-900 hover:text-slate-50',
                ].join(' ')
              }
            >
              Fixed Rate
            </NavLink>
            <NavLink
              to="/isa"
              className={({ isActive }) =>
                [
                  'rounded-md px-3 py-1.5',
                  isActive
                    ? 'bg-slate-100 text-slate-900'
                    : 'text-slate-200 hover:bg-slate-900 hover:text-slate-50',
                ].join(' ')
              }
            >
              ISA
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-10">
        <Outlet />
      </main>
    </div>
  )
}

export default App
