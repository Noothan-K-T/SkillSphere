import React, { useState, useEffect } from 'react';
import './App.css';
// --- Animated SVG Icons ---
const RoadmapIcon = () => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2 h-5 w-5"><path d="M6 3v18"/><path d="M18 3v18"/><path d="M12 3v18"/><path d="M9 6l-3-3l-3 3"/><path d="M15 18l3 3l3-3"/></svg> );
const ResumeIcon = () => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2 h-5 w-5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg> );
const SavedIcon = () => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2 h-5 w-5"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg> );
const LogoutIcon = () => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2 h-5 w-5"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg> );
const DeleteIcon = () => ( <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg> );


// --- Style & Animation ---
const styles = `
    body { background-color: #0d1117; }
    .aurora-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; background-color: #0d1117; overflow: hidden; }
    .aurora-bg::before, .aurora-bg::after { content: ''; position: absolute; width: 600px; height: 600px; border-radius: 50%; filter: blur(100px); opacity: 0.3; }
    .aurora-bg::before { background: radial-gradient(circle, #007cf0, transparent 60%); top: -200px; left: -200px; animation: move-aurora-1 20s infinite alternate; }
    .aurora-bg::after { background: radial-gradient(circle, #ff3366, transparent 60%); bottom: -200px; right: -200px; animation: move-aurora-2 25s infinite alternate; }
    @keyframes move-aurora-1 { from { transform: translate(0, 0) rotate(0deg); } to { transform: translate(200px, 100px) rotate(90deg); } }
    @keyframes move-aurora-2 { from { transform: translate(0, 0) rotate(0deg); } to { transform: translate(-200px, -100px) rotate(-90deg); } }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .loader { animation: spin 1s linear infinite; border-top-color: #2dd4bf; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    .fade-in { animation: fadeIn 0.6s ease-out forwards; }
`;

// --- Helper Components ---
const Loader = () => <div className="loader ease-linear rounded-full border-4 border-t-4 border-gray-600 h-6 w-6 ml-3"></div>;

const MessageBox = ({ message, type }) => {
    if (!message) return null;
    const typeClasses = type === 'error' ? 'bg-red-900/50 text-red-300 border-red-500/50' : 'bg-green-900/50 text-green-300 border-green-500/50';
    return <div className={`mt-4 p-4 rounded-lg text-center font-semibold text-sm fade-in border ${typeClasses}`}>{message}</div>;
};

// --- Page & Feature Components ---
const Navbar = ({ page, setPage, token, setToken }) => {
    const handleLogout = () => {
        setToken(null);
        localStorage.removeItem('skillSphereToken');
        setPage('login');
    };

    return (
        <nav className="bg-gray-900/50 backdrop-blur-xl rounded-xl shadow-2xl shadow-black/20 p-4 mb-8 flex justify-between items-center sticky top-4 z-50 border border-white/10">
            <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-fuchsia-500 cursor-pointer" onClick={() => token ? setPage('home') : setPage('login')}>
                SkillSphere
            </div>
            <div>
                {token ? (
                    <div className="flex items-center space-x-2">
                        <button onClick={() => setPage('home')} className={`flex items-center font-semibold p-2 rounded-lg transition-all ${page === 'home' ? 'bg-cyan-900/50 text-cyan-300' : 'text-gray-300 hover:bg-gray-800/50'}`}><RoadmapIcon /> Roadmap</button>
                        <button onClick={() => setPage('parser')} className={`flex items-center font-semibold p-2 rounded-lg transition-all ${page === 'parser' ? 'bg-cyan-900/50 text-cyan-300' : 'text-gray-300 hover:bg-gray-800/50'}`}><ResumeIcon /> Parser</button>
                        <button onClick={() => setPage('my-roadmaps')} className={`flex items-center font-semibold p-2 rounded-lg transition-all ${page === 'my-roadmaps' ? 'bg-cyan-900/50 text-cyan-300' : 'text-gray-300 hover:bg-gray-800/50'}`}><SavedIcon /> Saved</button>
                        <button onClick={handleLogout} className="flex items-center bg-gray-800 text-gray-300 font-bold py-2 px-4 rounded-lg transition-colors hover:bg-red-500 hover:text-white shadow-md">
                            <LogoutIcon /> Logout
                        </button>
                    </div>
                ) : (
                    <div className="flex items-center space-x-2">
                        <button onClick={() => setPage('login')} className="font-semibold px-4 py-2 rounded-lg text-gray-300 hover:bg-gray-800/50">Login</button>
                        <button onClick={() => setPage('register')} className="bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold py-2 px-4 rounded-lg transition-all transform hover:scale-105 hover:shadow-lg hover:shadow-cyan-500/30">
                            Register for Free
                        </button>
                    </div>
                )}
            </div>
        </nav>
    );
};
const AuthCard = ({ title, children }) => ( <div className="bg-gray-900/60 backdrop-blur-sm p-8 sm:p-10 rounded-2xl shadow-2xl shadow-black/30 border border-white/10 max-w-md mx-auto fade-in"> <h2 className="text-3xl font-bold text-center text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-fuchsia-500 mb-2">{title}</h2> <p className="text-center text-gray-400 mb-8">Your AI-Powered Career Co-Pilot</p> {children} </div> );
const Card = ({ children }) => ( <div className="bg-gray-900/60 backdrop-blur-sm p-6 md:p-8 rounded-2xl shadow-2xl shadow-black/30 border border-white/10 fade-in"> {children} </div> );

const RoadmapGenerator = ({ token, parsedData }) => {
    const [currentRole, setCurrentRole] = useState('');
    const [desiredRole, setDesiredRole] = useState('');
    const [roadmap, setRoadmap] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [saveButtonText, setSaveButtonText] = useState('Save Roadmap');

    useEffect(() => {
        if (parsedData?.experience?.length > 0) {
            setCurrentRole(parsedData.experience[0].role);
        }
    }, [parsedData]);

    const handleGenerate = async (e) => { e.preventDefault(); setError(''); setRoadmap(null); setIsLoading(true); setSaveButtonText('Save Roadmap'); const currentSkills = parsedData?.skills ? Object.values(parsedData.skills).flat() : []; try { const response = await fetch('http://127.0.0.1:8001/api/generate-roadmap', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify({ current_role: currentRole, desired_role: desiredRole, current_skills: currentSkills }) }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || 'Failed to generate roadmap.'); setRoadmap(data.roadmap); } catch (err) { setError(err.message); } finally { setIsLoading(false); } };
    const handleSaveRoadmap = async () => { if (!roadmap) return; setSaveButtonText('Saving...'); const currentSkills = parsedData?.skills ? Object.values(parsedData.skills).flat() : []; const roadmapData = { current_role: currentRole, desired_role: desiredRole, current_skills: currentSkills }; const roadmapResponse = { roadmap: roadmap }; try { const response = await fetch('http://127.0.0.1:8001/api/roadmaps', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify({ roadmap_data: roadmapData, roadmap_response: roadmapResponse }) }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || 'Failed to save roadmap.'); setSaveButtonText('Saved!'); } catch (err) { setError(err.message); setSaveButtonText('Save Roadmap'); } };

    return (
        <Card>
            <h2 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-fuchsia-500 mb-2">AI Career Roadmap</h2>
            <p className="text-gray-400 mb-8">Chart your course from where you are to where you want to be.</p>
            <form onSubmit={handleGenerate}>
                <div className="grid md:grid-cols-2 gap-6 mb-6 p-6 bg-gray-900/50 rounded-xl border border-white/10">
                    <div>
                        <label className="block text-gray-300 font-semibold mb-2">Your Current Role</label>
                        <input type="text" value={currentRole} onChange={e => setCurrentRole(e.target.value)} placeholder="Parse a resume or enter manually" className="w-full p-3 bg-gray-800/50 border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 transition" required />
                    </div>
                    <div>
                        <label className="block text-gray-300 font-semibold mb-2">Your Desired Role</label>
                        <input type="text" value={desiredRole} onChange={e => setDesiredRole(e.target.value)} placeholder="e.g., AI Product Manager" className="w-full p-3 bg-gray-800/50 border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 transition" required />
                    </div>
                </div>
                <MessageBox message={error} type="error" />
                <button type="submit" disabled={isLoading} className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold py-3 rounded-lg flex items-center justify-center transition-all hover:shadow-xl hover:shadow-cyan-500/30 transform hover:scale-105 disabled:opacity-50">
                    {isLoading ? 'Generating...' : 'Generate My Roadmap'}
                    {isLoading && <Loader />}
                </button>
            </form>
            {roadmap && (
                <div className="mt-10 pt-6 border-t border-white/10 fade-in">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-2xl font-bold text-gray-200">Your Personalized Roadmap</h3>
                        <button onClick={handleSaveRoadmap} disabled={saveButtonText !== 'Save Roadmap'} className="bg-gradient-to-r from-green-500 to-teal-500 text-white font-bold py-2 px-4 rounded-lg transition-all hover:shadow-lg hover:shadow-green-500/30 transform hover:scale-105 disabled:from-gray-500 disabled:to-gray-600 disabled:scale-100 disabled:shadow-none">
                            {saveButtonText}
                        </button>
                    </div>
                    <div className="space-y-6">
                        {roadmap.map(step => (
                            <div key={step.step} className="p-5 border-l-4 border-cyan-500 rounded-r-lg bg-gray-900/50 shadow-lg">
                                <h4 className="font-bold text-lg text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-fuchsia-500">Step {step.step}: {step.title}</h4>
                                <p className="text-gray-300 my-2">{step.description}</p>
                                <div className="mt-3">
                                    <h5 className="font-semibold text-sm text-gray-200">Suggested Resources:</h5>
                                    <ul className="list-disc list-inside text-sm text-cyan-400 mt-1 space-y-1">
                                        {step.resources.map((res, i) => <li key={i}><span className="text-gray-400">{res}</span></li>)}
                                    </ul>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </Card>
    );
};

const MyRoadmapsPage = ({ token }) => {
    const [savedRoadmaps, setSavedRoadmaps] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const [openRoadmapId, setOpenRoadmapId] = useState(null);

    useEffect(() => {
        const fetchRoadmaps = async () => {
            try {
                const response = await fetch('http://127.0.0.1:8001/api/my-roadmaps', { headers: { 'Authorization': `Bearer ${token}` } });
                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || 'Failed to fetch roadmaps.');
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
        if (!roadmapId) return; // Prevent sending 'undefined'
        setSavedRoadmaps(currentRoadmaps => currentRoadmaps.filter(r => (r.id || r._id) !== roadmapId));
        try {
            const response = await fetch(`http://127.0.0.1:8001/api/roadmaps/${roadmapId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) {
                throw new Error('Failed to delete roadmap.');
            }
        } catch (err) {
            setError(err.message);
            // In a real app, you might re-fetch or add the item back to the list here
        }
    };
    
    const toggleRoadmap = (id) => setOpenRoadmapId(openRoadmapId === id ? null : id);

    if (isLoading) return <div className="text-center p-10"><Loader /></div>;
    
    return (
        <Card>
            <h2 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-fuchsia-500 mb-6">My Saved Roadmaps</h2>
            {error && <MessageBox message={error} type="error" />}
            {savedRoadmaps.length === 0 && !isLoading ? (
                <p className="text-gray-400 text-center py-10">You haven't saved any roadmaps yet.</p>
            ) : (
                <div className="space-y-4">
                    {savedRoadmaps.map(doc => (
                        <div key={doc.id || doc._id} className="border rounded-lg shadow-sm bg-gray-900/50 border-white/10">
                            <div className="w-full text-left p-4 flex justify-between items-center">
                                <button onClick={() => toggleRoadmap(doc.id || doc._id)} className="flex-grow text-left">
                                    <span className="font-semibold text-lg text-gray-200">{doc.current_role} → {doc.desired_role}</span>
                                    <p className="text-sm text-gray-500">Saved on: {new Date(doc.created_at).toLocaleDateString()}</p>
                                </button>
                                <div className="flex items-center">
                                    <button onClick={() => toggleRoadmap(doc.id || doc._id)} className="p-2">
                                        <span className={`transform transition-transform text-cyan-400 ${openRoadmapId === (doc.id || doc._id) ? 'rotate-180' : ''}`}>▼</span>
                                    </button>
                                    <button onClick={() => handleDelete(doc.id || doc._id)} className="p-2 text-gray-500 hover:text-red-500 transition-colors">
                                        <DeleteIcon />
                                    </button>
                                </div>
                            </div>
                            {openRoadmapId === (doc.id || doc._id) && (
                                <div className="p-4 border-t border-white/10 fade-in">
                                    <div className="space-y-6">
                                        {doc.roadmap.map(step => (
                                           <div key={step.step} className="p-5 border-l-4 border-cyan-500 rounded-r-lg bg-gray-800/50">
                                                <h4 className="font-bold text-lg text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-fuchsia-500">Step {step.step}: {step.title}</h4>
                                                <p className="text-gray-300 my-2">{step.description}</p>
                                                <div className="mt-3">
                                                    <h5 className="font-semibold text-sm text-gray-200">Suggested Resources:</h5>
                                                    <ul className="list-disc list-inside text-sm text-cyan-400 mt-1 space-y-1">
                                                        {step.resources.map((res, i) => <li key={i}><span className="text-gray-400">{res}</span></li>)}
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

const ResumeParser = ({ token, setParsedData, setPage }) => {
    const [resumeText, setResumeText] = useState('');
    const [localParsedData, setLocalParsedData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const handleParse = async () => {
        if (!resumeText.trim()) {
            setError("Please paste some resume text first.");
            return;
        }
        setIsLoading(true);
        setError('');
        setLocalParsedData(null);
        try {
            const response = await fetch('http://127.0.0.1:8001/api/parse-resume', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ resume_text: resumeText })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to parse resume.');
            setLocalParsedData(data);
            setParsedData(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Card>
            <h2 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-fuchsia-500 mb-2">AI Resume Parser</h2>
            <p className="text-gray-400 mb-6">Let our AI analyze your resume to find your current role and skills.</p>
            <textarea rows="15" className="w-full p-4 border bg-gray-800/50 border-white/10 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 transition" placeholder="Paste the full text of a resume here..." value={resumeText} onChange={(e) => setResumeText(e.target.value)} />
            <MessageBox message={error} type="error" />
            <button onClick={handleParse} disabled={isLoading} className="mt-4 w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold py-3 rounded-lg flex items-center justify-center transition-all hover:shadow-xl hover:shadow-cyan-500/30 transform hover:scale-105 disabled:opacity-50">
                {isLoading ? 'Analyzing...' : 'Analyze Resume'}
                {isLoading && <Loader />}
            </button>

            {localParsedData && (
                <div className="mt-10 pt-6 border-t border-white/10 fade-in">
                    <button onClick={() => setPage('home')} className="w-full mb-6 bg-gradient-to-r from-green-500 to-teal-500 text-white font-bold py-3 rounded-lg flex items-center justify-center transition-all hover:shadow-xl hover:shadow-green-500/30 transform hover:scale-105">
                        Use this data to generate a roadmap →
                    </button>
                    <h3 className="text-2xl font-bold text-gray-200 mb-4">Analysis Results</h3>
                    <div className="space-y-6">
                        <div>
                            <h4 className="font-semibold text-lg text-gray-300 mb-3">🛠️ Skills</h4>
                            <div className="p-4 bg-gray-900/50 rounded-lg border border-white/10">
                                {Object.entries(localParsedData.skills).map(([category, skillsList]) => (
                                    <div key={category} className="mb-3 last:mb-0">
                                        <h5 className="font-semibold text-md text-gray-400 capitalize">{category.replace(/_/g, ' ')}</h5>
                                        <div className="flex flex-wrap gap-2 mt-2">
                                            {skillsList.map((skill, i) => <span key={i} className="bg-cyan-900/50 text-cyan-300 text-sm font-medium px-3 py-1 rounded-full">{skill}</span>)}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div>
                           <h4 className="font-semibold text-lg text-gray-300 mb-3">👔 Work Experience</h4>
                            <ul className="space-y-4 text-gray-300">
                                {localParsedData.experience.map((exp, i) => (
                                    <li key={i} className="p-4 border rounded-lg bg-gray-900/50 border-white/10">
                                        <p className="font-semibold text-gray-100">{exp.role}</p>
                                        <p className="text-gray-400">{exp.company}</p>
                                        <p className="text-sm text-gray-500 mt-2">{exp.summary}</p>
                                    </li>
                                ))}
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-semibold text-lg text-gray-300 mb-3">🎓 Education</h4>
                            <ul className="list-disc list-inside space-y-2 text-gray-400 pl-4">
                                {localParsedData.education.map((edu, i) => <li key={i}>{edu.degree} at {edu.university} {edu.graduation_year && `(${edu.graduation_year})`}</li>)}
                            </ul>
                        </div>
                    </div>
                </div>
            )}
        </Card>
    );
};

const LoginPage = ({ setPage, setToken }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleLogin = async (e) => { e.preventDefault(); setError(''); setIsLoading(true); try { const response = await fetch('http://127.0.0.1:8001/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || 'Failed to login'); setToken(data.access_token); localStorage.setItem('skillSphereToken', data.access_token); setPage('home'); } catch (err) { setError(err.message); } finally { setIsLoading(false); } };

    return (
        <AuthCard title="Welcome Back!">
            <form onSubmit={handleLogin}>
                <div className="mb-4">
                    <label className="block text-gray-300 font-semibold mb-2">Email Address</label>
                    <input type="email" value={email} onChange={e => setEmail(e.target.value)} className="w-full p-3 bg-gray-800/50 border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 transition" required />
                </div>
                <div className="mb-6">
                    <label className="block text-gray-300 font-semibold mb-2">Password</label>
                    <input type="password" value={password} onChange={e => setPassword(e.target.value)} className="w-full p-3 bg-gray-800/50 border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 transition" required />
                </div>
                <MessageBox message={error} type="error" />
                <button type="submit" disabled={isLoading} className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold py-3 rounded-lg flex items-center justify-center transition-all hover:shadow-xl hover:shadow-cyan-500/30 transform hover:scale-105 disabled:opacity-50">
                    {isLoading ? 'Logging In...' : 'Login'}
                    {isLoading && <Loader />}
                </button>
            </form>
            <p className="text-center text-gray-400 mt-6">
                Don't have an account? <span onClick={() => setPage('register')} className="text-cyan-400 font-semibold cursor-pointer hover:underline">Register here</span>
            </p>
        </AuthCard>
    );
};

const RegisterPage = ({ setPage }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleRegister = async (e) => { e.preventDefault(); setError(''); setMessage(''); setIsLoading(true); try { const response = await fetch('http://127.0.0.1:8001/api/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || 'Failed to register'); setMessage('Registration successful! Please log in.'); setEmail(''); setPassword(''); } catch (err) { setError(err.message); } finally { setIsLoading(false); } };

    return (
        <AuthCard title="Create Your Account">
            <form onSubmit={handleRegister}>
                <div className="mb-4">
                    <label className="block text-gray-300 font-semibold mb-2">Email Address</label>
                    <input type="email" value={email} onChange={e => setEmail(e.target.value)} className="w-full p-3 bg-gray-800/50 border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 transition" required />
                </div>
                <div className="mb-6">
                    <label className="block text-gray-300 font-semibold mb-2">Password</label>
                    <input type="password" value={password} onChange={e => setPassword(e.target.value)} className="w-full p-3 bg-gray-800/50 border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-cyan-500 transition" minLength="8" maxLength="72" required />
                </div>
                <MessageBox message={error} type="error" />
                <MessageBox message={message} type="success" />
                <button type="submit" disabled={isLoading} className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold py-3 rounded-lg flex items-center justify-center transition-all hover:shadow-xl hover:shadow-cyan-500/30 transform hover:scale-105 disabled:opacity-50">
                    {isLoading ? 'Creating Account...' : 'Register'}
                    {isLoading && <Loader />}
                </button>
            </form>
            <p className="text-center text-gray-400 mt-6">
                Already have an account? <span onClick={() => setPage('login')} className="text-cyan-400 font-semibold cursor-pointer hover:underline">Login here</span>
            </p>
        </AuthCard>
    );
};

// --- Main App Component ---
export default function App() {
    const [page, setPage] = useState('login');
    const [token, setToken] = useState(null);
    const [parsedResumeData, setParsedResumeData] = useState(null);

    useEffect(() => {
        const storedToken = localStorage.getItem('skillSphereToken');
        if (storedToken) {
            setToken(storedToken);
            setPage('home');
        } else {
            setPage('login');
        }
    }, []);

    const renderPage = () => {
        if (!token) {
            switch (page) {
                case 'login': return <LoginPage setPage={setPage} setToken={setToken} />;
                case 'register': return <RegisterPage setPage={setPage} />;
                default: return <LoginPage setPage={setPage} setToken={setToken} />;
            }
        }

        switch (page) {
            case 'parser': return <ResumeParser token={token} setParsedData={setParsedResumeData} setPage={setPage} />;
            case 'my-roadmaps': return <MyRoadmapsPage token={token} />;
            case 'home': default: return <RoadmapGenerator token={token} parsedData={parsedResumeData} />;
        }
    };

    return (
        <>
            <style>{styles}</style>
            <div className="relative text-white min-h-screen font-sans">
                <div className="aurora-bg"></div>
                <div className="relative container mx-auto p-4 md:p-8 max-w-5xl">
                    <Navbar page={page} setPage={setPage} token={token} setToken={setToken} />
                    <main>
                        {renderPage()}
                    </main>
                    <footer className="text-center mt-12 text-white/50">
                        <p>&copy; 2025 SkillSphere. Your AI-Powered Career Co-Pilot.</p>
                    </footer>
                </div>
            </div>
        </>
    );
}

