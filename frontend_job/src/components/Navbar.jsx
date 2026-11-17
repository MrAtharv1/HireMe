// import React from 'react';
// import { Link, useLocation } from 'react-router-dom';
// import { Briefcase, FileText, User, UploadCloud } from 'lucide-react';
// import { useApp } from '../context/AppContext';

// const Navbar = () => {
//   const location = useLocation();
//   const { profileId } = useApp();

//   // Helper to highlight the active tab
//   const isActive = (path) => location.pathname === path || location.pathname.startsWith(`${path}/`);

//   return (
//     <nav className="bg-brand-card/50 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50">
//       <div className="container mx-auto px-4">
//         <div className="flex items-center justify-between h-16">
          
//           {/* Logo */}
//           <Link to="/" className="flex items-center text-xl font-bold text-slate-100 hover:text-brand-accent transition-colors">
//             <span className="bg-brand-accent text-white p-1.5 rounded-lg mr-2">
//               <Briefcase size={20} />
//             </span>
//             Naukri AI
//           </Link>

//           {/* Navigation Links (Only show if a profile exists) */}
//           {profileId && (
//             <div className="flex space-x-1">
//               <Link
//                 to="/jobs"
//                 className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
//                   isActive('/jobs') ? 'bg-brand-accent/10 text-brand-accent' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
//                 }`}
//               >
//                 <Briefcase size={16} className="mr-2" />
//                 Jobs
//               </Link>
              
//               <Link
//                 to="/applications"
//                 className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
//                   isActive('/applications') ? 'bg-brand-accent/10 text-brand-accent' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
//                 }`}
//               >
//                 <FileText size={16} className="mr-2" />
//                 Tracker
//               </Link>

//               <Link
//                 to="/profile"
//                 className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
//                   isActive('/profile') ? 'bg-brand-accent/10 text-brand-accent' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
//                 }`}
//               >
//                 <User size={16} className="mr-2" />
//                 Profile
//               </Link>
//             </div>
//           )}

//           {/* Upload New Resume Button */}
//           <div>
//             <Link
//               to="/"
//               className="flex items-center px-4 py-2 border border-slate-700 hover:border-brand-accent text-slate-300 hover:text-brand-accent rounded-lg text-sm font-medium transition-colors"
//             >
//               <UploadCloud size={16} className="mr-2" />
//               New Upload
//             </Link>
//           </div>

//         </div>
//       </div>
//     </nav>
//   );
// };

// export default Navbar;

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Briefcase, FileText, User, UploadCloud, LogIn, LogOut } from 'lucide-react';
import { useApp } from '../context/AppContext';

const Navbar = () => {
  const location = useLocation();
  const { profileId, user, isAuthenticated, logout, setIsAuthModalOpen } = useApp();

  // Highlight the active tab
  const isActive = (path) => location.pathname === path || location.pathname.startsWith(`${path}/`);

  // --- THE FIX: Hide this global navbar on the landing/upload page ---
  if (location.pathname === '/') {
    return null; 
  }

  return (
    <nav className="bg-brand-card/50 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 text-xl font-bold text-slate-100 hover:opacity-95 transition-opacity">
            <svg className="w-8 h-8 drop-shadow-sm shrink-0" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="navLogoBg" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#0f172a" />
                  <stop offset="60%" stopColor="#064e3b" />
                  <stop offset="100%" stopColor="#059669" />
                </linearGradient>
                <linearGradient id="navLogoEmerald" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#34d399" />
                  <stop offset="100%" stopColor="#10b981" />
                </linearGradient>
                <linearGradient id="navSparkGold" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#fef08a" />
                  <stop offset="100%" stopColor="#eab308" />
                </linearGradient>
              </defs>
              <rect x="3" y="3" width="58" height="58" rx="16" fill="url(#navLogoBg)" stroke="#34d399" strokeOpacity="0.4" strokeWidth="2" />
              <rect x="17" y="16" width="6.5" height="32" rx="3.25" fill="#ffffff" />
              <rect x="40.5" y="16" width="6.5" height="32" rx="3.25" fill="#ffffff" />
              <path d="M21 32h22" stroke="url(#navLogoEmerald)" strokeWidth="6" strokeLinecap="round" />
              <path d="M46 10 C46 14.5 43.5 17 39 17 C43.5 17 46 19.5 46 24 C46 19.5 48.5 17 53 17 C48.5 17 46 14.5 46 10 Z" fill="url(#navSparkGold)" />
            </svg>
            <div className="flex items-center gap-1.5 font-extrabold tracking-tight">
              <span>HireMe</span>
              <span className="text-xs bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-1.5 py-0.5 rounded-md font-bold">AI</span>
            </div>
          </Link>

          {/* Navigation Links (Only show if a profile exists) */}
          {profileId && (
            <div className="flex space-x-1">
              <Link
                to="/jobs"
                className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive('/jobs') ? 'bg-brand-accent/10 text-brand-accent' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <Briefcase size={16} className="mr-2" />
                Jobs
              </Link>
              
              <Link
                to="/applications"
                className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive('/applications') ? 'bg-brand-accent/10 text-brand-accent' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <FileText size={16} className="mr-2" />
                Tracker
              </Link>

              <Link
                to="/profile"
                className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive('/profile') ? 'bg-brand-accent/10 text-brand-accent' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <User size={16} className="mr-2" />
                Profile
              </Link>
            </div>
          )}

          {/* Right-hand Controls (Upload & User Account) */}
          <div className="flex items-center gap-3">
            <Link
              to="/"
              className="flex items-center px-3.5 py-1.5 border border-slate-700 hover:border-brand-accent text-slate-300 hover:text-brand-accent rounded-xl text-xs font-semibold transition-colors"
            >
              <UploadCloud size={15} className="mr-1.5" />
              New Upload
            </Link>

            {isAuthenticated ? (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-900 border border-slate-750 rounded-xl text-xs text-slate-200">
                  {user?.avatar_url ? (
                    <img src={user.avatar_url} alt="" className="w-5 h-5 rounded-full object-cover" />
                  ) : (
                    <div className="w-5 h-5 rounded-full bg-brand-accent/20 text-brand-accent font-bold flex items-center justify-center text-[10px]">
                      {(user?.full_name || user?.email || 'U')[0].toUpperCase()}
                    </div>
                  )}
                  <span className="max-w-[130px] truncate font-medium">{user?.full_name || user?.email}</span>
                </div>
                <button
                  type="button"
                  onClick={logout}
                  className="text-xs text-slate-400 hover:text-red-400 p-2 rounded-xl border border-slate-800 hover:border-red-500/30 transition-colors"
                  title="Sign out"
                >
                  <LogOut size={14} />
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setIsAuthModalOpen(true)}
                className="flex items-center gap-1.5 px-3.5 py-1.5 bg-brand-accent hover:bg-brand-accent/90 text-slate-950 font-bold rounded-xl text-xs transition-all shadow-sm cursor-pointer"
              >
                <LogIn size={14} />
                Sign In
              </button>
            )}
          </div>

        </div>
      </div>
    </nav>
  );
};

export default Navbar;