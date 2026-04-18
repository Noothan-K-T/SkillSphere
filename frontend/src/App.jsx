import React, { useState, useEffect } from 'react';
import './App.css';
import * as pdfjsLib from 'pdfjs-dist/legacy/build/pdf';
import pdfjsWorker from 'pdfjs-dist/legacy/build/pdf.worker.min.mjs?url';

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker;

// --- Animated SVG Icons ---
const RoadmapIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="mr-2 h-5 w-5"
  >
    <path d="M6 3v18" />
    <path d="M18 3v18" />
    <path d="M12 3v18" />
    <path d="M9 6l-3-3l-3 3" />
    <path d="M15 18l3 3l3-3" />
  </svg>
);

const ResumeIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="mr-2 h-5 w-5"
  >
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
  </svg>
);

const SavedIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="mr-2 h-5 w-5"
  >
    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
  </svg>
);

const LogoutIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="mr-2 h-5 w-5"
  >
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    <polyline points="16 17 21 12 16 7" />
    <line x1="21" y1="12" x2="9" y2="12" />
  </svg>
);

const DeleteIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-5 w-5"
  >
    <polyline points="3 6 5 6 21 6" />
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    <line x1="10" y1="11" x2="10" y2="17" />
    <line x1="14" y1="11" x2="14" y2="17" />
  </svg>
);

// --- Styles & Animations ---
const styles = `
  body { background-color: #0d1117; }
  .aurora-bg {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: -1;
    background-color: #0d1117;
    overflow: hidden;
  }
  .aurora-bg::before,
  .aurora-bg::after {
    content: '';
    position: absolute;
    width: 600px;
    height: 600px;
    border-radius: 50%;
    filter: blur(100px);
    opacity: 0.3;
  }
  .aurora-bg::before {
    background: radial-gradient(circle, #007cf0, transparent 60%);
    top: -200px;
    left: -200px;
    animation: move-aurora-1 20s infinite alternate;
  }
  .aurora-bg::after {
    background: radial-gradient(circle, #ff3366, transparent 60%);
    bottom: -200px;
    right: -200px;
    animation: move-aurora-2 25s infinite alternate;
  }
  @keyframes move-aurora-1 {
    from { transform: translate(0, 0) rotate(0deg); }
    to { transform: translate(200px, 100px) rotate(90deg); }
  }
  @keyframes move-aurora-2 {
    from { transform: translate(0, 0) rotate(0deg); }
    to { transform: translate(-200px, -100px) rotate(-90deg); }
  }
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  .loader { animation: spin 1s linear infinite; border-top-color: #2dd4bf; }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .fade-in { animation: fadeIn 0.6s ease-out forwards; }
`;

// --- Helper Components ---
const Loader = () => (
  <div className="loader ease-linear rounded-full border-4 border-t-4 border-gray-600 h-6 w-6 ml-3"></div>
);

const MessageBox = ({ message, type }) => {
  if (!message) return null;

  const cls =
    type === 'error'
      ? 'bg-red-900/50 text-red-300 border-red-500/50'
      : 'bg-green-900/50 text-green-300 border-green-500/50';

  return (
    <div className={`mt-4 p-4 rounded-lg text-center font-semibold text-sm fade-in border ${cls}`}>
      {message}
    </div>
  );
};

const AuthCard = ({ title, children }) => (
  <div className="bg-gray-900/60 backdrop-blur-sm p-8 sm:p-10 rounded-2xl shadow-2xl shadow-black/30 border border-white/10 max-w-md mx-auto fade-in">
    <h2 className="text-3xl font-bold text-center text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-fuchsia-500 mb-2">
      {title}
    </h2>
    <p className="text-center text-gray-400 mb-8">Your AI-Powered Career Co-Pilot</p>
    {children}
  </div>
);

const Card = ({ children }) => (
  <div className="bg-gray-900/60 backdrop-blur-sm p-6 md:p-8 rounded-2xl shadow-2xl shadow-black/30 border border-white/10 fade-in">
    {children}
  </div>
);

// --- Navigation Bar ---
const Navbar = ({ page, setPage, token, setToken }) => {
  const handleLogout = () => {
    setToken(null);
    localStorage.removeItem('skillSphereToken');
    setPage('login');
  };

  return (
    <nav className="bg-gray-900/50 backdrop-blur-xl rounded-xl shadow-2xl shadow-black/20 p-4 mb-8 flex justify-between items-center sticky top-4 z-50 border border-white/10">
      <div
        className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-fuchsia-500 cursor-pointer"
        onClick={() => (token ? setPage('home') : setPage('login'))}
      >
        SkillSphere
      </div>
      <div>
        {token ? (
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage('home')}
              className={`flex items-center font-semibold p-2 rounded-lg transition-all ${
                page === 'home'
                  ? 'bg-cyan-900/50 text-cyan-300'
                  : 'text-gray-300 hover:bg-gray-800/50'
              }`}
            >
              <RoadmapIcon /> Home
            </button>
            <button
              onClick={() => setPage('my-roadmaps')}
              className={`flex items-center font-semibold p-2 rounded-lg transition-all ${
                page === 'my-roadmaps'
                  ? 'bg-cyan-900/50 text-cyan-300'
                  : 'text-gray-300 hover:bg-gray-800/50'
              }`}
            >
              <SavedIcon /> My Roadmaps
            </button>
            <button
              onClick={handleLogout}
              className="flex items-center bg-gray-800 text-gray-300 font-bold py-2 px-4 rounded-lg transition-colors hover:bg-red-500 hover:text-white shadow-md"
            >
              <LogoutIcon /> Logout
            </button>
          </div>
        ) : (
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage('login')}
              className="font-semibold px-4 py-2 rounded-lg text-gray-300 hover:bg-gray-800/50"
            >
              Login
            </button>
            <button
              onClick={() => setPage('register')}
              className="bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold py-2 px-4 rounded-lg transition-all transform hover:scale-105 hover:shadow-lg hover:shadow-cyan-500/30"
            >
              Register for Free
            </button>
          </div>
        )}
      </div>
    </nav>
  );
};

// --- Roadmap Generator (Unified Dashboard) ---
const RoadmapGenerator = ({ token, setPage }) => {
  const [currentRole, setCurrentRole] = useState('');
  const [desiredRole, setDesiredRole] = useState('');
  const [roadmap, setRoadmap] = useState(null);
  const [skillGap, setSkillGap] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [saveButtonText, setSaveButtonText] = useState('Save Roadmap');
  
  // Parser specific state
  const [resumeText, setResumeText] = useState('');
  const [file, setFile] = useState(null);
  const [isParsing, setIsParsing] = useState(false);
  const [parsedData, setParsedData] = useState(null);

  const handleUnauthorized = () => {
    localStorage.removeItem('skillSphereToken');
    window.location.reload();
  };

  const handleFileUpload = async () => {
    if (!file) { setError('Please select a file first.'); return; }
    setIsParsing(true);
    setError('');
    try {
      let text = '';
      const extension = file.name.toLowerCase();
      if (extension.endsWith('.pdf')) {
        const arrayBuffer = await file.arrayBuffer();
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i);
          const content = await page.getTextContent();
          let lastY = -1;
          for (const item of content.items) {
            if (lastY !== -1 && Math.abs(item.transform[5] - lastY) > 5) {
              text += '\n';
            }
            text += (item.str || '') + ' ';
            lastY = item.transform[5];
          }
          text += '\n';
        }
      } else {
        text = await file.text();
      }

      const res = await fetch('http://127.0.0.1:8001/api/parse-resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ resume_text: text })
      });

      if (res.status === 401) { handleUnauthorized(); return; }
      const data = await res.json();
      if (!res.ok) {
        const errorDetail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
        throw new Error(errorDetail || 'Failed to parse resume');
      }
      
      setParsedData(data);
      if (data.experience?.length > 0) setCurrentRole(data.experience[0].role);
    } catch (err) {
      setError(err.message || 'An unknown error occurred during parsing.');
    } finally {
      setIsParsing(false);
    }
  };

  const handleTextParse = async () => {
    if (!resumeText.trim()) { setError('Please paste some text.'); return; }
    setIsParsing(true);
    setError('');
    try {
      const res = await fetch('http://127.0.0.1:8001/api/parse-resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ resume_text: resumeText })
      });
      if (res.status === 401) { handleUnauthorized(); return; }
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to parse');
      setParsedData(data);
      if (data.experience?.length > 0) setCurrentRole(data.experience[0].role);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsParsing(false);
    }
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    setError('');
    setRoadmap(null);
    setSkillGap(null);
    setIsLoading(true);
    setSaveButtonText('Save Roadmap');

    const currentSkills = parsedData?.skills ? Object.values(parsedData.skills).flat() : [];

    try {
      const res = await fetch('http://127.0.0.1:8001/api/generate-roadmap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          current_role: currentRole,
          desired_role: desiredRole,
          current_skills: currentSkills
        })
      });

      const data = await res.json();
      if (!res.ok) {
        const errorDetail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
        throw new Error(errorDetail || 'Failed to generate roadmap');
      }
      setSkillGap(data.skill_gap);
      setRoadmap(data.roadmap);
    } catch (err) {
      setError(err.message || 'An unknown error occurred during roadmap generation.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveRoadmap = async () => {
    setSaveButtonText('Saving...');
    const currentSkills = parsedData?.skills ? Object.values(parsedData.skills).flat() : [];
    try {
      const res = await fetch('http://127.0.0.1:8001/api/roadmaps', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          roadmap_data: { current_role: currentRole, desired_role: desiredRole, current_skills: currentSkills },
          roadmap_response: { skill_gap: skillGap, roadmap: roadmap }
        })
      });
      
      const data = await res.json();
      if (res.status === 401) { handleUnauthorized(); return; }
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to save roadmap');
      }
      
      setSaveButtonText('Saved!');
    } catch (err) {
      setError(err.message);
      setSaveButtonText('Save Roadmap');
    }
  };

  return (
    <Card>
      <div className="mb-10 text-center">
        <h2 className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-fuchsia-600 mb-4">
          SkillSphere Dashboard
        </h2>
        <p className="text-gray-400 text-lg">Analyze your career path and bridge the gap with AI.</p>
      </div>

      {/* Step 1: Parser */}
      {!parsedData && (
        <div className="fade-in mb-10 overflow-hidden">
          <div className="flex items-center mb-6">
            <div className="bg-cyan-500 text-white rounded-full w-10 h-10 flex items-center justify-center font-bold mr-4 shadow-lg shadow-cyan-500/20">1</div>
            <h3 className="text-2xl font-bold text-gray-200">Step 1: Analyze Your Background</h3>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div className="p-6 bg-gray-900/40 rounded-2xl border border-white/5 hover:border-cyan-500/30 transition-all group">
               <h4 className="font-semibold text-gray-300 mb-4 flex items-center">
                 <span className="mr-2">📁</span> Upload Resume (PDF/TXT)
               </h4>
               <input
                 type="file"
                 accept=".pdf,.txt"
                 onChange={(e) => setFile(e.target.files[0])}
                 className="w-full p-2 text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-cyan-500/10 file:text-cyan-400 hover:file:bg-cyan-500/20 cursor-pointer"
               />
               <button
                 onClick={handleFileUpload}
                 disabled={isParsing || !file}
                 className="mt-6 w-full bg-gray-800 hover:bg-cyan-600 text-white font-bold py-2 rounded-xl transition-all disabled:opacity-50"
               >
                 {isParsing ? 'Processing...' : 'Upload & Analyze'}
               </button>
            </div>

            <div className="p-6 bg-gray-900/40 rounded-2xl border border-white/5 hover:border-fuchsia-500/30 transition-all">
               <h4 className="font-semibold text-gray-300 mb-4 flex items-center">
                 <span className="mr-2">📝</span> Paste Resume Text
               </h4>
               <textarea
                 rows="3"
                 className="w-full p-3 bg-gray-800/50 border border-white/10 rounded-xl text-white text-sm focus:ring-1 focus:ring-fuchsia-500 transition"
                 placeholder="Paste your resume content here..."
                 value={resumeText}
                 onChange={(e) => setResumeText(e.target.value)}
               />
               <button
                 onClick={handleTextParse}
                 disabled={isParsing || !resumeText.trim()}
                 className="mt-4 w-full bg-gray-800 hover:bg-fuchsia-600 text-white font-bold py-2 rounded-xl transition-all disabled:opacity-50"
               >
                 Parse Text
               </button>
            </div>
          </div>
          <div className="mt-6 text-center">
             <button onClick={() => setParsedData({})} className="text-gray-500 hover:text-cyan-400 text-sm font-medium transition-colors underline decoration-dotted">
               Or skip parsing and enter manually
             </button>
          </div>
        </div>
      )}

      {/* Step 2: Generation */}
      {parsedData && (
        <div className="fade-in">
          <div className="flex items-center mb-6">
            <div className="bg-green-500 text-white rounded-full w-10 h-10 flex items-center justify-center font-bold mr-4 shadow-lg shadow-green-500/20">2</div>
            <h3 className="text-2xl font-bold text-gray-200">Step 2: Generate Your Roadmap</h3>
            <button 
              onClick={() => {setParsedData(null); setRoadmap(null);}} 
              className="ml-auto text-xs text-gray-500 hover:text-red-400"
            >
              Reset All
            </button>
          </div>

          {/* Profile Snapshot Section */}
          <div className="mb-10 p-6 bg-gray-900/60 rounded-2xl border border-white/10 shadow-inner">
            <h4 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400 mb-6 flex items-center">
              <span className="mr-2">🔍</span> Profile Snapshot
            </h4>
            
            <div className="space-y-8">
              {/* Skills Area */}
              {parsedData.skills && Object.keys(parsedData.skills).length > 0 && (
                <div className="space-y-4">
                  <h5 className="text-sm font-semibold text-gray-400 uppercase tracking-widest">Extracted Background</h5>
                  {Object.entries(parsedData.skills).map(([category, skillsList]) => (
                    <div key={category}>
                      <p className="text-[10px] text-gray-500 font-bold uppercase mb-1.5 ml-1">{category}</p>
                      <div className="flex flex-wrap gap-2">
                        {skillsList.map((skill, i) => (
                          <span key={i} className="bg-blue-900/30 text-blue-300 text-xs px-3 py-1.5 rounded-lg border border-blue-500/20">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="grid md:grid-cols-2 gap-8">
                {/* Experience Area */}
                {parsedData.experience?.length > 0 && (
                  <div>
                    <h5 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-3">Recent Experience</h5>
                    <div className="space-y-4">
                      {parsedData.experience.slice(0, 3).map((exp, i) => (
                        <div key={i} className="group">
                          <p className="font-bold text-gray-100 text-sm group-hover:text-cyan-400 transition-colors">{exp.role}</p>
                          <div className="flex justify-between items-center mt-0.5">
                            <p className="text-gray-400 text-[11px] italic">{exp.company}</p>
                            <p className="text-cyan-500/80 text-[10px] font-medium bg-cyan-500/5 px-2 py-0.5 rounded-md border border-cyan-500/10">{exp.dates}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Education Area */}
                {parsedData.education?.length > 0 && (
                  <div>
                    <h5 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-3">Education</h5>
                    <div className="space-y-4">
                      {parsedData.education.slice(0, 2).map((edu, i) => (
                        <div key={i} className="group">
                          <p className="font-bold text-gray-100 text-sm group-hover:text-fuchsia-400 transition-colors">{edu.degree}</p>
                          <div className="flex justify-between items-center mt-0.5">
                            <p className="text-gray-400 text-[11px] italic">{edu.university}</p>
                            <p className="text-fuchsia-400/80 text-[10px] font-medium bg-fuchsia-500/5 px-2 py-0.5 rounded-md border border-fuchsia-500/10">{edu.dates || edu.graduation_year}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          <form onSubmit={handleGenerate} className="p-6 bg-gray-900/40 rounded-2xl border border-white/10 mb-8">
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-gray-400 text-sm font-semibold mb-2 ml-1">Current Role</label>
                <input
                  type="text"
                  value={currentRole}
                  onChange={(e) => setCurrentRole(e.target.value)}
                  className="w-full p-3 bg-gray-800/50 border border-white/10 rounded-xl text-white focus:ring-2 focus:ring-cyan-500 transition"
                  placeholder="Your current title"
                  required
                />
              </div>
              <div>
                <label className="block text-gray-400 text-sm font-semibold mb-2 ml-1">Target Career Role</label>
                <input
                  type="text"
                  value={desiredRole}
                  onChange={(e) => setDesiredRole(e.target.value)}
                  className="w-full p-3 bg-gray-800/50 border border-white/10 rounded-xl text-white focus:ring-2 focus:ring-cyan-500 transition"
                  placeholder="e.g. Senior Backend Architect"
                  required
                />
              </div>
            </div>
            
            <button
              type="submit"
              disabled={isLoading}
              className="mt-8 w-full bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold py-4 rounded-xl shadow-lg shadow-cyan-500/20 active:scale-95 transition-all text-lg flex items-center justify-center disabled:opacity-50"
            >
              {isLoading ? 'Processing Skills...' : 'Create Roadmap'}
              {isLoading && <Loader />}
            </button>
          </form>
        </div>
      )}

      {error && <MessageBox message={error} type="error" />}

      {roadmap && (
        <div className="mt-12 fade-in border-t border-white/10 pt-10">
          <div className="flex items-center justify-between mb-8">
             <h3 className="text-3xl font-bold text-gray-100">AI Learning Strategy</h3>
             <button
               onClick={handleSaveRoadmap}
               className="bg-green-600 hover:bg-green-500 text-white font-bold py-2 px-6 rounded-xl transition-all hover:shadow-lg hover:shadow-green-500/20"
             >
               {saveButtonText}
             </button>
          </div>

          {skillGap && (
            <div className="mb-10 grid md:grid-cols-2 gap-4">
              <div className="p-5 bg-green-900/10 border border-green-500/20 rounded-2xl">
                <span className="text-green-400 text-xs font-bold uppercase tracking-widest block mb-2">Strengths Found</span>
                <div className="flex flex-wrap gap-2">
                   {skillGap.matching_skills?.map((s,i) => <span key={i} className="text-xs bg-green-500/20 text-green-300 px-3 py-1 rounded-full">{s}</span>)}
                </div>
              </div>
              <div className="p-5 bg-orange-900/10 border border-orange-500/20 rounded-2xl">
                <span className="text-orange-400 text-xs font-bold uppercase tracking-widest block mb-2">Skill Gaps to Fill</span>
                <div className="flex flex-wrap gap-2">
                   {skillGap.missing_skills?.map((s,i) => <span key={i} className="text-xs bg-orange-500/20 text-orange-300 px-3 py-1 rounded-full">{s}</span>)}
                </div>
              </div>
            </div>
          )}

          <div className="space-y-8 relative before:absolute before:inset-0 before:left-5 before:w-0.5 before:bg-gradient-to-b before:from-cyan-500/50 before:to-transparent before:z-0">
             {roadmap.map((step, idx) => (
               <div key={idx} className="relative z-10 pl-14">
                  <div className="absolute left-0 top-0 w-10 h-10 rounded-full bg-gray-900 border-2 border-cyan-500 flex items-center justify-center font-bold text-cyan-400">{step.step}</div>
                   <div className="p-6 bg-gray-900/40 backdrop-blur-md rounded-2xl border border-white/5 shadow-2xl transition-all hover:border-cyan-500/30 group/step">
                    <div className="flex justify-between items-start mb-3">
                      <h4 className="text-xl font-bold text-gray-100 group-hover/step:text-cyan-400 transition-colors">{step.title}</h4>
                      <span className="text-[10px] font-bold text-cyan-500/40 uppercase tracking-widest mt-1.5">Module {step.step}</span>
                    </div>
                    <p className="text-gray-400 text-sm leading-relaxed mb-5">{step.description}</p>
                    <div className="flex flex-wrap gap-2.5">
                       {step.resources.map((r,i) => (
                         <span key={i} className="group/tag inline-flex items-center text-[10px] font-medium bg-cyan-500/5 text-cyan-400/70 px-3 py-1.5 rounded-lg border border-cyan-500/10 hover:bg-cyan-500/10 hover:text-cyan-300 hover:border-cyan-500/30 transition-all cursor-default">
                           <span className="mr-2 opacity-40 group-hover/tag:opacity-100 transition-opacity">🚀</span>
                           {r}
                         </span>
                       ))}
                    </div>
                  </div>
               </div>
             ))}
          </div>
        </div>
      )}
    </Card>
  );
};

// --- My Roadmaps Page ---
const MyRoadmapsPage = ({ token }) => {
  const [savedRoadmaps, setSavedRoadmaps] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [openRoadmapId, setOpenRoadmapId] = useState(null);

  useEffect(() => {
    const fetchRoadmaps = async () => {
      if (!token) {
        setSavedRoadmaps([]);
        setIsLoading(false);
        return;
      }

      try {
        const res = await fetch('http://127.0.0.1:8001/api/my-roadmaps', {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Failed to fetch roadmaps');
        }

        setSavedRoadmaps(data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchRoadmaps();
  }, [token]);

  const handleDelete = async (roadmapId) => {
    if (!roadmapId) return;

    setSavedRoadmaps((current) => current.filter((r) => (r.id || r._id) !== roadmapId));

    try {
      const res = await fetch(`http://127.0.0.1:8001/api/roadmaps/${roadmapId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!res.ok) {
        throw new Error('Failed to delete roadmap');
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const toggleRoadmap = (id) => {
    setOpenRoadmapId(openRoadmapId === id ? null : id);
  };

  if (isLoading) {
    return (
      <div className="text-center p-10">
        <Loader />
      </div>
    );
  }

  return (
    <Card>
      <h2 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-fuchsia-500 mb-6">
        My Saved Roadmaps
      </h2>

      {error && <MessageBox message={error} type="error" />}

      {savedRoadmaps.length === 0 && !isLoading ? (
        <p className="text-gray-400 text-center py-10">You haven't saved any roadmaps yet.</p>
      ) : (
        <div className="space-y-4">
          {savedRoadmaps.map((doc) => (
            <div key={doc.id || doc._id} className="border rounded-lg shadow-sm bg-gray-900/50 border-white/10">
              <div className="w-full text-left p-4 flex justify-between items-center">
                <button
                  onClick={() => toggleRoadmap(doc.id || doc._id)}
                  className="flex-grow text-left"
                >
                  <span className="font-semibold text-lg text-gray-200">
                    {doc.current_role} → {doc.desired_role}
                  </span>
                  <p className="text-sm text-gray-500">
                    Saved on: {new Date(doc.created_at).toLocaleDateString()}
                  </p>
                </button>
                <div className="flex items-center">
                  <button
                    onClick={() => toggleRoadmap(doc.id || doc._id)}
                    className="p-2"
                  >
                    <span
                      className={`transform transition-transform text-cyan-400 ${
                        openRoadmapId === (doc.id || doc._id) ? 'rotate-180' : ''
                      }`}
                    >
                      ▼
                    </span>
                  </button>
                  <button
                    onClick={() => handleDelete(doc.id || doc._id)}
                    className="p-2 text-gray-500 hover:text-red-500 transition-colors"
                  >
                    <DeleteIcon />
                  </button>
                </div>
              </div>

              {openRoadmapId === (doc.id || doc._id) && (
                <div className="p-4 border-t border-white/10 fade-in">
                  
                  {doc.skill_gap && (
                    <div className="mb-8 p-6 bg-gray-900/60 rounded-xl shadow-lg border border-white/10">
                      <h4 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-300 mb-4">
                        📊 Skill Gap Analysis
                      </h4>
                      <div className="grid md:grid-cols-2 gap-6">
                        <div>
                          <h5 className="font-semibold text-gray-300 mb-3 flex items-center">
                            ✅ Matching Skills
                          </h5>
                          <div className="flex flex-wrap gap-2">
                            {doc.skill_gap.matching_skills?.length > 0 ? (
                              doc.skill_gap.matching_skills.map((skill, idx) => (
                                <span key={idx} className="bg-green-900/50 text-green-300 text-sm font-medium px-3 py-1 rounded-full border border-green-500/30">
                                  {skill}
                                </span>
                              ))
                            ) : (
                              <span className="text-gray-500 text-sm italic">No significant matching skills found.</span>
                            )}
                          </div>
                        </div>
                        <div>
                          <h5 className="font-semibold text-gray-300 mb-3 flex items-center">
                            🎯 Missing Skills to Learn
                          </h5>
                          <div className="flex flex-wrap gap-2">
                            {doc.skill_gap.missing_skills?.length > 0 ? (
                              doc.skill_gap.missing_skills.map((skill, idx) => (
                                <span key={idx} className="bg-orange-900/50 text-orange-300 text-sm font-medium px-3 py-1 rounded-full border border-orange-500/30">
                                  {skill}
                                </span>
                              ))
                            ) : (
                              <span className="text-gray-500 text-sm italic">You have all the required skills theoretically!</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="space-y-6">
                    {doc.roadmap.map((step) => (
                      <div
                        key={step.step}
                        className="p-5 border-l-4 border-cyan-500 rounded-r-lg bg-gray-800/50"
                      >
                        <h4 className="font-bold text-lg text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-fuchsia-500">
                          Step {step.step}: {step.title}
                        </h4>
                        <p className="text-gray-300 my-2">{step.description}</p>
                        <div className="mt-3">
                          <h5 className="font-semibold text-sm text-gray-200">Suggested Resources:</h5>
                          <ul className="list-disc list-inside text-sm text-cyan-400 mt-1 space-y-1">
                            {step.resources.map((res, i) => (
                              <li key={i}>
                                <span className="text-gray-400">{res}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};

// --- Login Page ---
const LoginPage = ({ setPage, setToken }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const res = await fetch('http://127.0.0.1:8001/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to login');
      }

      setToken(data.access_token);
      localStorage.setItem('skillSphereToken', data.access_token);
      setPage('home');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthCard title="Welcome Back!">
      <form onSubmit={handleLogin}>
        <div className="mb-4">
          <label className="block text-gray-300 font-semibold mb-2">Email Address</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full p-3 bg-gray-800/50 border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 transition"
            required
          />
        </div>

        <div className="mb-6">
          <label className="block text-gray-300 font-semibold mb-2">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-3 bg-gray-800/50 border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 transition"
            required
          />
        </div>

        <MessageBox message={error} type="error" />

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold py-3 rounded-lg flex items-center justify-center transition-all hover:shadow-xl hover:shadow-cyan-500/30 transform hover:scale-105 disabled:opacity-50"
        >
          {isLoading ? 'Logging In...' : 'Login'}
          {isLoading && <Loader />}
        </button>
      </form>

      <p className="text-center text-gray-400 mt-6">
        Don't have an account?{' '}
        <span
          onClick={() => setPage('register')}
          className="text-cyan-400 font-semibold cursor-pointer hover:underline"
        >
          Register here
        </span>
      </p>
    </AuthCard>
  );
};

// --- Register Page ---
const RegisterPage = ({ setPage }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setIsLoading(true);

    try {
      const res = await fetch('http://127.0.0.1:8001/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to register');
      }

      setMessage('Registration successful! Please log in.');
      setEmail('');
      setPassword('');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthCard title="Create Your Account">
      <form onSubmit={handleRegister}>
        <div className="mb-4">
          <label className="block text-gray-300 font-semibold mb-2">Email Address</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full p-3 bg-gray-800/50 border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 transition"
            required
          />
        </div>

        <div className="mb-6">
          <label className="block text-gray-300 font-semibold mb-2">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-3 bg-gray-800/50 border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 transition"
            minLength="8"
            maxLength="72"
            required
          />
        </div>

        <MessageBox message={error} type="error" />
        <MessageBox message={message} type="success" />

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold py-3 rounded-lg flex items-center justify-center transition-all hover:shadow-xl hover:shadow-cyan-500/30 transform hover:scale-105 disabled:opacity-50"
        >
          {isLoading ? 'Creating Account...' : 'Register'}
          {isLoading && <Loader />}
        </button>
      </form>

      <p className="text-center text-gray-400 mt-6">
        Already have an account?{' '}
        <span
          onClick={() => setPage('login')}
          className="text-cyan-400 font-semibold cursor-pointer hover:underline"
        >
          Login here
        </span>
      </p>
    </AuthCard>
  );
};

// --- Main App Component ---
export default function App() {
  const [page, setPage] = useState('login');
  const [token, setToken] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem('skillSphereToken');
    if (stored) {
      setToken(stored);
      setPage('home');
    }
  }, []);

  const renderPage = () => {
    if (!token) {
      switch (page) {
        case 'login':
          return <LoginPage setPage={setPage} setToken={setToken} />;
        case 'register':
          return <RegisterPage setPage={setPage} />;
        default:
          return <LoginPage setPage={setPage} setToken={setToken} />;
      }
    }

    switch (page) {
      case 'my-roadmaps':
        return <MyRoadmapsPage token={token} />;
      case 'home':
      default:
        return <RoadmapGenerator token={token} setPage={setPage} />;
    }
  };

  return (
    <>
      <style>{styles}</style>
      <div className="relative text-white min-h-screen font-sans">
        <div className="aurora-bg"></div>
        <div className="relative container mx-auto p-4 md:p-8 max-w-5xl">
          <Navbar page={page} setPage={setPage} token={token} setToken={setToken} />
          <main>{renderPage()}</main>
          <footer className="text-center mt-12 text-white/50">
            <p>&copy; 2025 SkillSphere. Your AI-Powered Career Co-Pilot.</p>
          </footer>
        </div>
      </div>
    </>
  );
}

