// // import React, { useState, useRef } from 'react';
// // import { useNavigate } from 'react-router-dom';
// // import { UploadCloud, FileText, Loader2, AlertCircle } from 'lucide-react';
// // import { useApp } from '../context/AppContext';
// // import api from '../api/client';

// // const UploadPage = () => {
// //   const [file, setFile] = useState(null);
// //   const [isDragging, setIsDragging] = useState(false);
// //   const [isUploading, setIsUploading] = useState(false);
// //   const [error, setError] = useState(null);
  
// //   const { setProfileId, user, isAuthenticated, setIsAuthModalOpen, logout } = useApp();
// //   const navigate = useNavigate();
// //   const fileInputRef = useRef(null);

// //   // Drag and Drop Handlers
// //   const handleDragOver = (e) => {
// //     e.preventDefault();
// //     setIsDragging(true);
// //   };

// //   const handleDragLeave = (e) => {
// //     e.preventDefault();
// //     setIsDragging(false);
// //   };

// //   const handleDrop = (e) => {
// //     e.preventDefault();
// //     setIsDragging(false);
// //     const droppedFile = e.dataTransfer.files[0];
// //     if (droppedFile) validateAndSetFile(droppedFile);
// //   };

// //   const handleFileChange = (e) => {
// //     const selectedFile = e.target.files[0];
// //     if (selectedFile) validateAndSetFile(selectedFile);
// //   };

// //   const validateAndSetFile = (selectedFile) => {
// //     setError(null);
// //     const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
// //     if (!validTypes.includes(selectedFile.type)) {
// //       setError('Please upload a PDF or DOCX file.');
// //       return;
// //     }
// //     if (selectedFile.size > 10 * 1024 * 1024) {
// //       setError('File is too large. Maximum size is 10MB.');
// //       return;
// //     }
// //     setFile(selectedFile);
// //   };

// //   // Upload to FastAPI Backend
// //   const handleUpload = async () => {
// //     if (!file) return;
    
// //     setIsUploading(true);
// //     setError(null);

// //     const formData = new FormData();
// //     formData.append('file', file);

// //     // Generate a temporary user ID for testing since we don't have Auth yet
// //     // const tempUserId = crypto.randomUUID();
// //     const tempUserId = "123e4567-e89b-12d3-a456-426614174004"

// //     try {
// //       // Calls: POST /resume/upload?user_id=...
// //       const response = await api.post(`/resume/upload?user_id=${tempUserId}`, formData, {
// //         headers: {
// //           'Content-Type': 'multipart/form-data',
// //         },
// //       });

// //       // Save the profile ID globally
// //       setProfileId(response.data.profile_id);
      
// //       // Redirect to the Jobs Dashboard
// //       navigate('/jobs');
      
// //     } catch (err) {
// //       console.error(err);
// //       setError(err.response?.data?.detail || 'Failed to parse resume. Please try again.');
// //     } finally {
// //       setIsUploading(false);
// //     }
// //   };

// //   return (
// //     <div className="flex flex-col items-center justify-center min-h-[80vh] px-4">
      
// //       <div className="text-center mb-10">
// //         <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-brand-accent to-blue-400 bg-clip-text text-transparent">
// //           The Interview Generation System
// //         </h1>
// //         <p className="text-slate-400 text-lg max-w-xl mx-auto">
// //           Drop your resume below. Our AI will parse your skills, find matching jobs, and tailor your profile to beat the ATS.
// //         </p>
// //       </div>

// //       <div className="w-full max-w-xl">
// //         {/* Drag & Drop Zone */}
// //         <div
// //           className={`relative border-2 border-dashed rounded-xl p-12 flex flex-col items-center justify-center transition-all duration-200 cursor-pointer
// //             ${isDragging ? 'border-brand-accent bg-brand-accent/10' : 'border-slate-700 bg-brand-card hover:border-slate-500'}`}
// //           onDragOver={handleDragOver}
// //           onDragLeave={handleDragLeave}
// //           onDrop={handleDrop}
// //           onClick={() => fileInputRef.current?.click()}
// //         >
// //           <input
// //             type="file"
// //             ref={fileInputRef}
// //             className="hidden"
// //             accept=".pdf,.docx"
// //             onChange={handleFileChange}
// //           />
          
// //           {file ? (
// //             <div className="flex flex-col items-center text-center">
// //               <div className="w-16 h-16 bg-brand-accent/20 text-brand-accent rounded-full flex items-center justify-center mb-4">
// //                 <FileText size={32} />
// //               </div>
// //               <p className="text-lg font-medium text-slate-200">{file.name}</p>
// //               <p className="text-sm text-slate-400 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
// //             </div>
// //           ) : (
// //             <div className="flex flex-col items-center text-center">
// //               <div className="w-16 h-16 bg-slate-800 text-slate-400 rounded-full flex items-center justify-center mb-4 shadow-inner">
// //                 <UploadCloud size={32} />
// //               </div>
// //               <p className="text-lg font-medium text-slate-200 mb-1">Click to upload or drag and drop</p>
// //               <p className="text-sm text-slate-500">PDF or DOCX (Max 10MB)</p>
// //             </div>
// //           )}
// //         </div>

// //         {/* Error Message */}
// //         {error && (
// //           <div className="mt-4 p-4 bg-red-500/10 border border-red-500/50 rounded-lg flex items-center text-red-400">
// //             <AlertCircle size={20} className="mr-3 flex-shrink-0" />
// //             <p className="text-sm">{error}</p>
// //           </div>
// //         )}

// //         {/* Action Button */}
// //         <button
// //           onClick={handleUpload}
// //           disabled={!file || isUploading}
// //           className={`w-full mt-6 py-4 rounded-xl font-bold text-lg flex items-center justify-center transition-all duration-200
// //             ${!file ? 'bg-slate-800 text-slate-500 cursor-not-allowed' : 
// //               'bg-brand-accent text-white hover:bg-blue-500 hover:shadow-lg hover:shadow-brand-accent/20'}`}
// //         >
// //           {isUploading ? (
// //             <>
// //               <Loader2 className="animate-spin mr-3" size={24} />
// //               AI is analyzing your profile...
// //             </>
// //           ) : (
// //             'Parse Resume & Find Jobs ✨'
// //           )}
// //         </button>
// //       </div>
// //     </div>
// //   );
// // };

// // export default UploadPage;

// // import React, { useState, useRef } from 'react';
// // import { useNavigate } from 'react-router-dom';
// // import { useApp } from '../context/AppContext';
// // import api from '../api/client';

// // const UploadPage = () => {
// //   // --- UPLOAD STATE & LOGIC ---
// //   const [file, setFile] = useState(null);
// //   const [isDragging, setIsDragging] = useState(false);
// //   const [isUploading, setIsUploading] = useState(false);
// //   const [error, setError] = useState(null);
  
// //   const { setProfileId, user, isAuthenticated, setIsAuthModalOpen, logout } = useApp();
// //   const navigate = useNavigate();
// //   const fileInputRef = useRef(null);

// //   const handleDragOver = (e) => {
// //     e.preventDefault();
// //     setIsDragging(true);
// //   };

// //   const handleDragLeave = (e) => {
// //     e.preventDefault();
// //     setIsDragging(false);
// //   };

// //   const handleDrop = (e) => {
// //     e.preventDefault();
// //     setIsDragging(false);
// //     const droppedFile = e.dataTransfer.files[0];
// //     if (droppedFile) validateAndSetFile(droppedFile);
// //   };

// //   const handleFileChange = (e) => {
// //     const selectedFile = e.target.files[0];
// //     if (selectedFile) validateAndSetFile(selectedFile);
// //   };

// //   const validateAndSetFile = (selectedFile) => {
// //     setError(null);
// //     const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
// //     if (!validTypes.includes(selectedFile.type)) {
// //       setError('Please upload a PDF or DOCX file.');
// //       return;
// //     }
// //     if (selectedFile.size > 10 * 1024 * 1024) {
// //       setError('File is too large. Maximum size is 10MB.');
// //       return;
// //     }
// //     setFile(selectedFile);
// //   };

// //   const handleUpload = async () => {
// //     if (!file || isUploading) return;
    
// //     setIsUploading(true);
// //     setError(null);

// //     const formData = new FormData();
// //     formData.append('file', file);

// //     const tempUserId = "123e4567-e89b-12d3-a456-426614174004";

// //     try {
// //       const response = await api.post(`/resume/upload?user_id=${tempUserId}`, formData, {
// //         headers: {
// //           'Content-Type': 'multipart/form-data',
// //         },
// //       });

// //       setProfileId(response.data.profile_id);
// //       navigate('/jobs');
      
// //     } catch (err) {
// //       console.error(err);
// //       setError(err.response?.data?.detail || 'Failed to parse resume. Please try again.');
// //     } finally {
// //       setIsUploading(false);
// //     }
// //   };

// //   const scrollToSection = (id) => {
// //     document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
// //   };

// //   return (
// //     <>
// //       {/* Inline styles for fonts and custom keyframes to avoid touching tailwind.config.js */}
// //       <style>{`
// //         @import url('https://fonts.googleapis.com/css2?family=Anton&family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');
// //         @keyframes fadeUp { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }
// //         @keyframes marquee { from { transform: translateX(0); } to { transform: translateX(-50%); } }
// //         .animate-fadeUp-1 { animation: fadeUp 0.7s ease both; }
// //         .animate-fadeUp-2 { animation: fadeUp 0.7s 0.2s ease both; }
// //         .animate-fadeUp-3 { animation: fadeUp 0.6s 0.35s ease both; }
// //         .animate-marquee { animation: marquee 18s linear infinite; }
// //       `}</style>

// //       {/* Breakout Wrapper */}
// //       <div className="absolute top-0 left-0 w-screen min-h-screen z-[100] overflow-x-hidden font-['DM_Sans',sans-serif] bg-[#f5f0d8] text-[#2a1a1a]">
        
// //         {/* ─── NAV ─── */}
// //         <nav className="sticky top-0 z-[200] bg-white flex items-center justify-between px-12 h-[72px] border-b border-black/5">
// //           <div className="w-[46px] h-[46px] bg-[#5c1a1a] rounded-full flex items-center justify-center font-['Anton',sans-serif] text-white text-[1.3rem] cursor-pointer shrink-0">
// //             H
// //           </div>
// //           <ul className="flex gap-10 list-none absolute left-1/2 -translate-x-1/2">
// //             <li><a href="#" className="text-base font-normal text-[#2a1a1a] no-underline hover:text-[#5c1a1a] transition-colors underline" onClick={(e) => e.preventDefault()}>Home</a></li>
// //             <li><a href="#upload" className="text-base font-normal text-[#2a1a1a] no-underline hover:text-[#5c1a1a] transition-colors" onClick={(e) => { e.preventDefault(); scrollToSection('upload'); }}>Upload</a></li>
// //             <li><a href="#jobs" className="text-base font-normal text-[#2a1a1a] no-underline hover:text-[#5c1a1a] transition-colors" onClick={(e) => { e.preventDefault(); scrollToSection('jobs'); }}>Jobs</a></li>
// //             <li><a href="#contact" className="text-base font-normal text-[#2a1a1a] no-underline hover:text-[#5c1a1a] transition-colors" onClick={(e) => { e.preventDefault(); scrollToSection('contact'); }}>Contact</a></li>
// //           </ul>
// //           <button className="bg-[#d4be6a] border-2 border-[#5c1a1a] rounded-full py-[0.6rem] px-[1.8rem] font-['DM_Sans',sans-serif] text-[0.95rem] font-medium text-[#2a1a1a] cursor-pointer hover:bg-[#c8b05e] hover:-translate-y-[1px] transition-all" onClick={() => scrollToSection('upload')}>
// //             Start Exploring
// //           </button>
// //         </nav>

// //         {/* ─── HERO (Section 1) ─── */}
// //         <section className="bg-[#b8dede] min-h-[88vh] relative overflow-hidden flex flex-col before:content-[''] before:absolute before:inset-0 before:bg-[linear-gradient(rgba(90,130,130,0.18)_1px,transparent_1px),linear-gradient(90deg,rgba(90,130,130,0.18)_1px,transparent_1px)] before:bg-[size:40px_40px] before:pointer-events-none">
// //           <svg className="absolute left-[-10px] top-[60px] w-[260px] opacity-50 pointer-events-none" viewBox="0 0 260 300" fill="none" xmlns="http://www.w3.org/2000/svg">
// //             <rect x="20" y="90" width="220" height="160" rx="12" stroke="#3d6060" strokeWidth="1.5" fill="none" />
// //             <path d="M85 90 L85 65 Q85 50 100 50 L160 50 Q175 50 175 65 L175 90" stroke="#3d6060" strokeWidth="1.5" fill="none" />
// //             <line x1="20" y1="155" x2="240" y2="155" stroke="#3d6060" strokeWidth="1.5" />
// //             <rect x="110" y="140" width="40" height="30" rx="5" stroke="#3d6060" strokeWidth="1.5" fill="none" />
// //             <rect x="55" y="30" width="70" height="90" rx="4" stroke="#3d6060" strokeWidth="1" fill="none" transform="rotate(-12 90 75)" />
// //             <line x1="65" y1="55" x2="108" y2="48" stroke="#3d6060" strokeWidth="0.8" transform="rotate(-12 90 75)" />
// //             <line x1="65" y1="65" x2="108" y2="58" stroke="#3d6060" strokeWidth="0.8" transform="rotate(-12 90 75)" />
// //             <line x1="65" y1="75" x2="108" y2="68" stroke="#3d6060" strokeWidth="0.8" transform="rotate(-12 90 75)" />
// //             <circle cx="210" cy="50" r="3" fill="#3d6060" opacity="0.5" />
// //             <circle cx="230" cy="70" r="2" fill="#3d6060" opacity="0.4" />
// //             <line x1="195" y1="35" x2="195" y2="25" stroke="#3d6060" strokeWidth="1" opacity="0.5" />
// //             <line x1="190" y1="30" x2="200" y2="30" stroke="#3d6060" strokeWidth="1" opacity="0.5" />
// //           </svg>

// //           <svg className="absolute right-[-20px] top-[50px] w-[300px] opacity-50 pointer-events-none" viewBox="0 0 300 360" fill="none" xmlns="http://www.w3.org/2000/svg">
// //             <rect x="30" y="20" width="200" height="270" rx="6" stroke="#3d6060" strokeWidth="1.5" fill="none" />
// //             <rect x="35" y="25" width="190" height="260" rx="5" stroke="#3d6060" strokeWidth="0.5" fill="none" opacity="0.4" />
// //             <rect x="50" y="40" width="60" height="60" rx="30" stroke="#3d6060" strokeWidth="1" fill="none" />
// //             <rect x="125" y="50" width="85" height="8" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" />
// //             <rect x="125" y="65" width="65" height="6" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" />
// //             <rect x="125" y="78" width="75" height="5" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" opacity="0.6" />
// //             <line x1="50" y1="115" x2="210" y2="115" stroke="#3d6060" strokeWidth="1" />
// //             <rect x="50" y="128" width="50" height="7" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" />
// //             <rect x="50" y="143" width="150" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
// //             <rect x="50" y="153" width="140" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
// //             <rect x="50" y="163" width="130" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
// //             <rect x="50" y="180" width="55" height="7" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" />
// //             <rect x="50" y="195" width="145" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
// //             <rect x="50" y="205" width="155" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
// //             <rect x="50" y="215" width="120" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
// //             <rect x="50" y="232" width="45" height="7" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" />
// //             <rect x="50" y="247" width="130" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
// //             <rect x="50" y="257" width="110" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
// //             <rect x="50" y="35" width="200" height="270" rx="6" stroke="#3d6060" strokeWidth="1" fill="none" opacity="0.25" transform="rotate(6 150 170)" />
// //             <circle cx="250" cy="40" r="3" fill="#3d6060" opacity="0.4" />
// //             <line x1="265" y1="60" x2="265" y2="50" stroke="#3d6060" strokeWidth="1" opacity="0.5" />
// //             <line x1="260" y1="55" x2="270" y2="55" stroke="#3d6060" strokeWidth="1" opacity="0.5" />
// //           </svg>

// //           <div className="relative z-10 pt-14 pb-10 px-14 flex-1 flex flex-col justify-between">
// //             <div>
// //               <div className="font-['Anton',sans-serif] text-[clamp(4.5rem,11vw,10rem)] text-[#5c1a1a] leading-[0.92] tracking-[-0.01em] uppercase max-w-[85%] animate-fadeUp-1">Let's get<br />hired!</div>
// //             </div>
// //             <p className="font-['DM_Sans',sans-serif] text-[clamp(1.1rem,2.2vw,1.45rem)] font-normal text-[#6b2020] pt-6 max-w-[560px] leading-[1.4] animate-fadeUp-2">Shit that works — AI parses your resume, matches real jobs, and tailors your profile to beat the ATS.</p>
// //           </div>

// //           <div className="absolute z-20 bottom-[190px] left-[360px]">
// //             <div className="inline-flex items-center gap-[0.6rem] bg-[#d4be6a] border-[1.5px] border-black/10 rounded-full py-[0.55rem] px-[1.4rem] text-[0.95rem] font-medium text-[#2a1a1a] cursor-pointer hover:scale-[1.03] transition-transform animate-fadeUp-3">
// //               <span className="w-2.5 h-2.5 bg-[#5c1a1a] rounded-full shrink-0"></span> ATS Optimization
// //             </div>
// //           </div>
// //           <div className="absolute z-20 bottom-[255px] right-[120px]">
// //             <div className="inline-flex items-center gap-[0.6rem] bg-[#d4be6a] border-[1.5px] border-black/10 rounded-full py-[0.55rem] px-[1.4rem] text-[0.95rem] font-medium text-[#2a1a1a] cursor-pointer hover:scale-[1.03] transition-transform animate-fadeUp-3">
// //               <span className="w-2.5 h-2.5 bg-[#5c1a1a] rounded-full shrink-0"></span> Smart Job Match
// //             </div>
// //           </div>

// //           <div className="absolute bottom-8 right-10 z-10 w-[52px] h-[52px] bg-[#d4be6a] border-2 border-[#5c1a1a] rounded-full flex items-center justify-center cursor-pointer hover:translate-y-[2px] transition-transform" onClick={() => scrollToSection('marquee')}>
// //             <svg viewBox="0 0 24 24" fill="none" stroke="#5c1a1a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
// //               <line x1="12" y1="5" x2="12" y2="19" /><polyline points="19 12 12 19 5 12" />
// //             </svg>
// //           </div>
// //         </section>

// //         {/* ─── MARQUEE ─── */}
// //         <div className="bg-white border-y-2 border-[#5c1a1a] overflow-hidden py-[0.65rem] whitespace-nowrap" id="marquee">
// //           <div className="inline-flex gap-0 animate-marquee">
// //             {[...Array(10)].map((_, i) => (
// //               <span key={i} className="font-['DM_Sans',sans-serif] text-base font-medium text-[#5c1a1a] px-8 inline-flex items-center gap-6">
// //                 Upload. Parse. Get Hired. <span className="text-[#6b2020]">→</span>
// //               </span>
// //             ))}
// //           </div>
// //         </div>

// //         {/* ─── UPLOAD SECTION ─── */}
// //         <section className="grid grid-cols-1 md:grid-cols-2 min-h-[75vh] relative" id="upload">
// //           {/* LEFT PANEL */}
// //           <div className="bg-[#d9c76e] py-16 px-[3.5rem] pl-[4rem] flex flex-col justify-center relative before:content-[''] before:absolute before:inset-0 before:bg-[linear-gradient(rgba(140,110,0,0.12)_1px,transparent_1px),linear-gradient(90deg,rgba(140,110,0,0.12)_1px,transparent_1px)] before:bg-[size:40px_40px] before:pointer-events-none">
// //             <div className="relative z-10">
// //               <span className="inline-block border-[1.5px] border-[#5c1a1a] rounded-full py-[0.4rem] px-[1.2rem] text-[0.9rem] font-medium text-[#5c1a1a] mb-[1.8rem] w-fit">Resume Upload</span>
// //               <h2 className="font-['Anton',sans-serif] text-[clamp(2.8rem,5vw,5rem)] text-[#5c1a1a] leading-[0.95] uppercase mb-6">Drop your<br />resume<br />here</h2>
// //               <p className="text-[1.1rem] font-normal text-[#6b2020] leading-[1.5] max-w-[380px] mb-10">Our AI will parse your skills, find matching jobs, and tailor your profile to beat the ATS.</p>

// //               <button className="inline-flex items-center gap-3 bg-[#5c1a1a] border-2 border-[#5c1a1a] rounded-full py-[0.85rem] px-8 font-['DM_Sans',sans-serif] text-base font-semibold text-white cursor-pointer hover:bg-[#4a1414] hover:-translate-y-[2px] transition-all w-fit" id="leftUploadBtn" onClick={handleInitiateUpload}>
// //                 <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
// //                   <polyline points="16 16 12 12 8 16" /><line x1="12" y1="12" x2="12" y2="21" />
// //                   <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
// //                 </svg>
// //                 Upload Resume
// //               </button>
// //             </div>
// //           </div>

// //           {/* ARROW CIRCLE (Centered between panels) */}
// //           <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 w-[120px] h-[120px] bg-white border-[2.5px] border-[#5c1a1a] rounded-full flex items-center justify-center cursor-pointer hover:bg-[#f5f0d8] hover:scale-105 transition-all duration-200" onClick={() => scrollToSection('upload')}>
// //             <svg viewBox="0 0 24 24" fill="none" stroke="#5c1a1a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-[38px] h-[38px]">
// //               <line x1="5" y1="12" x2="19" y2="12" />
// //               <polyline points="12 5 19 12 12 19" />
// //             </svg>
// //           </div>

// //           {/* RIGHT PANEL */}
// //           <div className="bg-[#ede6c3] relative flex items-center justify-center py-12 px-14 before:content-[''] before:absolute before:inset-0 before:bg-[linear-gradient(rgba(0,0,0,0.07)_1px,transparent_1px),linear-gradient(90deg,rgba(0,0,0,0.07)_1px,transparent_1px)] before:bg-[size:40px_40px] before:pointer-events-none">
// //             <div className="relative z-10 bg-white border-2 border-[#5c1a1a] rounded-2xl p-10 w-full max-w-[440px] shadow-[6px_6px_0_#5c1a1a]">
// //               {/* Hidden file input */}
// //               <input 
// //                 type="file" 
// //                 id="fileInput" 
// //                 accept=".pdf,.docx" 
// //                 className="hidden" 
// //                 ref={fileInputRef}
// //                 onChange={handleFileChange}
// //               />

// //               {/* Drop zone */}
// //               <div 
// //                 className={`border-2 border-dashed rounded-xl py-10 px-6 flex flex-col items-center justify-center text-center cursor-pointer transition-all bg-[#f5f0d8] min-h-[200px] ${isDragging || file ? 'border-[#5c1a1a] bg-[#5c1a1a]/[0.06]' : 'border-[#c0a060] hover:border-[#5c1a1a] hover:bg-[#5c1a1a]/[0.04]'}`}
// //                 id="dropZone"
// //                 onDragOver={handleDragOver}
// //                 onDragLeave={handleDragLeave}
// //                 onDrop={handleDrop}
// //                 onClick={() => fileInputRef.current?.click()}
// //               >
// //                 <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 transition-colors ${file ? 'bg-[#5c1a1a]/15' : 'bg-[#5c1a1a]/10'}`} id="dropIcon">
// //                   {file ? (
// //                     <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#5c1a1a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
// //                       <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
// //                       <polyline points="14 2 14 8 20 8" />
// //                       <line x1="16" y1="13" x2="8" y2="13" />
// //                       <line x1="16" y1="17" x2="8" y2="17" />
// //                       <polyline points="10 9 9 9 8 9" />
// //                     </svg>
// //                   ) : (
// //                     <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#5c1a1a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
// //                       <polyline points="16 16 12 12 8 16" /><line x1="12" y1="12" x2="12" y2="21" />
// //                       <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
// //                     </svg>
// //                   )}
// //                 </div>
// //                 <div id="dropContent">
// //                   {file ? (
// //                     <>
// //                       <p className="text-base font-semibold text-[#5c1a1a] mb-1">{file.name}</p>
// //                       <p className="text-[0.82rem] text-[#888]">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
// //                     </>
// //                   ) : (
// //                     <>
// //                       <p className="text-base font-semibold text-[#2a1a1a] mb-1">Click to upload or drag and drop</p>
// //                       <p className="text-[0.82rem] text-[#888]">PDF or DOCX (Max 10MB)</p>
// //                     </>
// //                   )}
// //                 </div>
// //               </div>

// //               {/* Error */}
// //               {error && (
// //                 <div className="mt-4 py-3 px-4 bg-red-600/[0.08] border border-red-600/35 rounded-lg flex items-center gap-2.5 text-[0.85rem] text-[#b91c1c]" id="errorBox">
// //                   <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
// //                     <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
// //                   </svg>
// //                   <span id="errorMsg">{error}</span>
// //                 </div>
// //               )}

// //               {/* Submit */}
// //               <button 
// //                 className={`w-full mt-6 p-4 rounded-full font-['DM_Sans',sans-serif] text-base font-semibold border-none flex items-center justify-center gap-2 transition-all ${!file ? 'bg-[#e8e0c8] text-[#a0907a] cursor-not-allowed' : 'bg-[#5c1a1a] text-white cursor-pointer hover:bg-[#4a1414] hover:-translate-y-[2px] hover:shadow-[0_6px_20px_rgba(92,26,26,0.25)]'} ${isUploading ? '!bg-[#7a3030] !text-white !cursor-not-allowed' : ''}`} 
// //                 id="parseBtn" 
// //                 disabled={!file || isUploading}
// //                 onClick={handleUpload}
// //               >
// //                 {isUploading ? (
// //                   <>
// //                     <div className="w-5 h-5 border-[2.5px] border-white/30 border-t-white rounded-full animate-spin"></div> AI is analyzing your profile...
// //                   </>
// //                 ) : (
// //                   'Parse Resume & Find Jobs ✨'
// //                 )}
// //               </button>
// //             </div>
// //           </div>
// //         </section>

// //         {/* ─── BLOG / FEATURES ─── */}
// //         <section className="bg-[#f5f0d8] py-20 px-16 text-center" id="jobs">
// //           <span className="inline-block border-[1.5px] border-[#5c1a1a] rounded-full py-[0.4rem] px-[1.2rem] text-[0.9rem] font-medium text-[#5c1a1a] mb-[1.8rem] bg-transparent">How It Works</span>
// //           <h2 className="font-['Anton',sans-serif] text-[clamp(2.8rem,7vw,6rem)] text-[#5c1a1a] uppercase leading-[0.95] mb-[1.2rem]">From the Dashboard</h2>
// //           <p className="text-[1.1rem] font-medium text-[#6b2020] mb-12 leading-[1.5]">Dive into our latest job matches and career discoveries</p>

// //           <div className="grid grid-cols-1 md:grid-cols-3 gap-0 text-left mb-12">
// //             <div className="bg-white border border-black/5 cursor-pointer overflow-hidden transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)]">
// //               <div className="w-full aspect-[4/3] flex items-center justify-center text-5xl bg-[#acd8d8]">
// //                 <svg width="100" height="100" viewBox="0 0 100 100" fill="none">
// //                   <rect x="15" y="25" width="70" height="55" rx="5" stroke="#3d6060" strokeWidth="2" fill="none" />
// //                   <path d="M35 25 L35 15 Q35 10 40 10 L60 10 Q65 10 65 15 L65 25" stroke="#3d6060" strokeWidth="2" fill="none" />
// //                   <line x1="15" y1="50" x2="85" y2="50" stroke="#3d6060" strokeWidth="1.5" />
// //                   <rect x="40" y="43" width="20" height="14" rx="3" stroke="#3d6060" strokeWidth="1.5" fill="none" />
// //                 </svg>
// //               </div>
// //               <div className="flex items-center gap-2 pt-5 px-5 text-[0.82rem] text-[#666]">
// //                 <div className="w-7 h-7 rounded-full bg-[#c8a882] flex items-center justify-center text-[0.65rem] text-white font-semibold shrink-0">AI</div>
// //                 <span>System</span><span className="mx-0.5">·</span>
// //                 <span>Step 1</span><span className="mx-0.5">·</span><span>2 min</span>
// //               </div>
// //               <div className="p-5 pb-6">
// //                 <div className="text-base font-semibold text-[#5c1a1a] mb-2.5 leading-[1.35]">Upload Your Resume — PDF or DOCX Accepted</div>
// //                 <p className="text-[0.83rem] text-[#555] leading-[1.55] line-clamp-3">Drop your resume and our AI will instantly extract your skills, experience, education, and accomplishments into a structured profile ready for matching.</p>
// //               </div>
// //             </div>

// //             <div className="bg-white border border-black/5 cursor-pointer overflow-hidden transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)]">
// //               <div className="w-full aspect-[4/3] flex items-center justify-center text-5xl bg-[#d9c76e]">
// //                 <svg width="100" height="100" viewBox="0 0 100 100" fill="none">
// //                   <circle cx="50" cy="45" r="28" stroke="#5c1a1a" strokeWidth="2" fill="none" />
// //                   <line x1="70" y1="65" x2="85" y2="80" stroke="#5c1a1a" strokeWidth="3" strokeLinecap="round" />
// //                   <line x1="38" y1="45" x2="62" y2="45" stroke="#5c1a1a" strokeWidth="1.5" />
// //                   <line x1="50" y1="33" x2="50" y2="57" stroke="#5c1a1a" strokeWidth="1.5" />
// //                 </svg>
// //               </div>
// //               <div className="flex items-center gap-2 pt-5 px-5 text-[0.82rem] text-[#666]">
// //                 <div className="w-7 h-7 rounded-full bg-[#c8a882] flex items-center justify-center text-[0.65rem] text-white font-semibold shrink-0">AI</div>
// //                 <span>System</span><span className="mx-0.5">·</span>
// //                 <span>Step 2</span><span className="mx-0.5">·</span><span>instant</span>
// //               </div>
// //               <div className="p-5 pb-6">
// //                 <div className="text-base font-semibold text-[#5c1a1a] mb-2.5 leading-[1.35]">AI Scans Live Jobs and Scores Your Match</div>
// //                 <p className="text-[0.83rem] text-[#555] leading-[1.55] line-clamp-3">We query thousands of active job listings and rank them by how well your skills, experience, and goals align — giving you a match score for every opportunity.</p>
// //               </div>
// //             </div>

// //             <div className="bg-white border border-black/5 cursor-pointer overflow-hidden transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)]">
// //               <div className="w-full aspect-[4/3] flex items-center justify-center text-5xl bg-[#5a82b0]">
// //                 <svg width="100" height="100" viewBox="0 0 100 100" fill="none">
// //                   <rect x="15" y="20" width="70" height="60" rx="5" stroke="white" strokeWidth="1.5" fill="none" />
// //                   <line x1="25" y1="38" x2="75" y2="38" stroke="white" strokeWidth="1" />
// //                   <line x1="25" y1="50" x2="65" y2="50" stroke="white" strokeWidth="1" />
// //                   <line x1="25" y1="62" x2="55" y2="62" stroke="white" strokeWidth="1" />
// //                   <circle cx="72" cy="65" r="12" fill="rgba(255,255,255,0.15)" stroke="white" strokeWidth="1.5" />
// //                   <polyline points="66,65 71,70 78,61" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round" />
// //                 </svg>
// //               </div>
// //               <div className="flex items-center gap-2 pt-5 px-5 text-[0.82rem] text-[#666]">
// //                 <div className="w-7 h-7 rounded-full bg-[#c8a882] flex items-center justify-center text-[0.65rem] text-white font-semibold shrink-0">AI</div>
// //                 <span>System</span><span className="mx-0.5">·</span>
// //                 <span>Step 3</span><span className="mx-0.5">·</span><span>tailored</span>
// //               </div>
// //               <div className="p-5 pb-6">
// //                 <div className="text-base font-semibold text-[#5c1a1a] mb-2.5 leading-[1.35]">Get a Tailored Profile That Beats the ATS</div>
// //                 <p className="text-[0.83rem] text-[#555] leading-[1.55] line-clamp-3">For every job you apply to, we generate a tailored resume and cover letter optimized for that company's ATS filters — dramatically boosting your callback rate.</p>
// //               </div>
// //             </div>
// //           </div>

// //           <a href="#upload" onClick={(e) => { e.preventDefault(); scrollToSection('upload'); }} className="inline-block bg-[#b8dede] border-2 border-[#5c1a1a] rounded-full p-4 px-14 font-['DM_Sans',sans-serif] text-base font-medium text-[#2a1a1a] cursor-pointer no-underline transition-all hover:bg-[#9fcece] hover:-translate-y-[2px]">Upload My Resume</a>
// //         </section>

// //         {/* ─── NEWSLETTER / CONTACT ─── */}
// //         <section className="bg-[#b8dede] py-20 px-16 text-center relative overflow-hidden before:content-[''] before:absolute before:inset-0 before:bg-[linear-gradient(rgba(90,130,130,0.18)_1px,transparent_1px),linear-gradient(90deg,rgba(90,130,130,0.18)_1px,transparent_1px)] before:bg-[size:40px_40px] before:pointer-events-none" id="contact">
// //           <div className="relative z-10">
// //             <span className="inline-block border-[1.5px] border-[#5c1a1a] rounded-full py-[0.4rem] px-[1.2rem] text-[0.9rem] font-medium text-[#5c1a1a] mb-[1.8rem] bg-transparent">Stay Updated</span>
// //             <h2 className="font-['Anton',sans-serif] text-[clamp(2.5rem,7vw,5.5rem)] text-[#5c1a1a] uppercase mb-[1.2rem]">Join the Expedition</h2>
// //             <p className="text-[1.1rem] font-medium text-[#6b2020] mb-10 leading-[1.55]">Get new job matches and curated career tips<br />delivered straight to your inbox.</p>

// //             <div className="max-w-[520px] mx-auto text-left">
// //               <label className="block text-[0.9rem] font-medium text-[#2a1a1a] mb-2" htmlFor="emailInput">Email</label>
// //               <input className="w-full p-[0.85rem] px-5 border-[1.5px] border-black/15 rounded font-['DM_Sans',sans-serif] text-[0.95rem] bg-white mb-4 outline-none transition-colors focus:border-[#5c1a1a]" type="email" id="emailInput" placeholder="you@email.com" />
// //               <div className="flex items-center gap-2.5 mb-5 text-[0.88rem] text-[#444]">
// //                 <input type="checkbox" id="consent" className="w-4 h-4 accent-[#5c1a1a] cursor-pointer" />
// //                 <label htmlFor="consent">Yes, subscribe me to job alerts and updates.</label>
// //               </div>
// //               <button className="w-full bg-[#5c1a1a] text-white border-none rounded-full p-[0.95rem] font-['DM_Sans',sans-serif] text-base font-medium cursor-pointer transition-all hover:bg-[#4a1414] hover:-translate-y-[1px]">Subscribe →</button>
// //             </div>
// //           </div>
// //         </section>

// //         {/* ─── FOOTER ─── */}
// //         <footer className="bg-[#5c1a1a] text-white py-12 px-16 flex items-center justify-between flex-wrap gap-6">
// //           <div className="font-['Anton',sans-serif] text-[1.6rem] text-[#d4be6a] tracking-[0.03em]">HireMe</div>
// //           <ul className="flex gap-8 list-none">
// //             <li><a href="#" className="text-white/75 no-underline text-[0.9rem] transition-colors hover:text-white" onClick={(e) => e.preventDefault()}>Home</a></li>
// //             <li><a href="#jobs" className="text-white/75 no-underline text-[0.9rem] transition-colors hover:text-white" onClick={(e) => { e.preventDefault(); scrollToSection('jobs'); }}>Jobs</a></li>
// //             <li><a href="#" className="text-white/75 no-underline text-[0.9rem] transition-colors hover:text-white">About</a></li>
// //             <li><a href="#contact" className="text-white/75 no-underline text-[0.9rem] transition-colors hover:text-white" onClick={(e) => { e.preventDefault(); scrollToSection('contact'); }}>Contact</a></li>
// //           </ul>
// //           <span className="text-[0.8rem] text-white/50">© 2025 HireMe. All rights reserved.</span>
// //         </footer>
// //       </div>
// //     </>
// //   );
// // };

// // export default UploadPage;

// import React, { useState, useRef } from 'react';
// import { useNavigate } from 'react-router-dom';
// import { useApp } from '../context/AppContext';
// import api from '../api/client';

// const UploadPage = () => {
//   // --- UPLOAD STATE & LOGIC ---
//   const [file, setFile] = useState(null);
//   const [isDragging, setIsDragging] = useState(false);
//   const [isUploading, setIsUploading] = useState(false);
//   const [error, setError] = useState(null);
  
//   const { setProfileId, user, isAuthenticated, setIsAuthModalOpen, logout } = useApp();
//   const navigate = useNavigate();
//   const fileInputRef = useRef(null);

//   const handleDragOver = (e) => {
//     e.preventDefault();
//     setIsDragging(true);
//   };

//   const handleDragLeave = (e) => {
//     e.preventDefault();
//     setIsDragging(false);
//   };

//   const handleDrop = (e) => {
//     e.preventDefault();
//     setIsDragging(false);
//     const droppedFile = e.dataTransfer.files[0];
//     if (droppedFile) validateAndSetFile(droppedFile);
//   };

//   const handleFileChange = (e) => {
//     const selectedFile = e.target.files[0];
//     if (selectedFile) validateAndSetFile(selectedFile);
//   };

//   const validateAndSetFile = (selectedFile) => {
//     setError(null);
//     const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
//     if (!validTypes.includes(selectedFile.type)) {
//       setError('Please upload a PDF or DOCX file.');
//       return;
//     }
//     if (selectedFile.size > 10 * 1024 * 1024) {
//       setError('File is too large. Maximum size is 10MB.');
//       return;
//     }
//     setFile(selectedFile);
//   };

//   const handleUpload = async () => {
//     if (!file || isUploading) return;
    
//     setIsUploading(true);
//     setError(null);

//     const formData = new FormData();
//     formData.append('file', file);

//     const tempUserId = "123e4567-e89b-12d3-a456-426614174004";

//     try {
//       const response = await api.post(`/resume/upload?user_id=${tempUserId}`, formData, {
//         headers: {
//           'Content-Type': 'multipart/form-data',
//         },
//       });

//       setProfileId(response.data.profile_id);
//       navigate('/jobs');
      
//     } catch (err) {
//       console.error(err);
//       setError(err.response?.data?.detail || 'Failed to parse resume. Please try again.');
//     } finally {
//       setIsUploading(false);
//     }
//   };

//   const scrollToSection = (id) => {
//     document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
//   };

//   return (
//     <>
//       {/* Inline styles for fonts and custom keyframes to avoid touching tailwind.config.js */}
//       <style>{`
//         @import url('https://fonts.googleapis.com/css2?family=Anton&family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');
//         @keyframes fadeUp { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }
//         @keyframes marquee { from { transform: translateX(0); } to { transform: translateX(-50%); } }
//         .animate-fadeUp-1 { animation: fadeUp 0.7s ease both; }
//         .animate-fadeUp-2 { animation: fadeUp 0.7s 0.2s ease both; }
//         .animate-fadeUp-3 { animation: fadeUp 0.6s 0.35s ease both; }
//         .animate-marquee { animation: marquee 18s linear infinite; }
//       `}</style>

//       {/* Breakout Wrapper */}
//       <div className="absolute top-0 left-0 w-screen min-h-screen z-[100] overflow-x-hidden font-['DM_Sans',sans-serif] bg-[#f5f0d8] text-[#2a1a1a]">
        
//         {/* ─── NAV ─── */}
//         <nav className="sticky top-0 z-[200] bg-white flex items-center justify-between px-12 h-[72px] border-b border-black/5">
//           <div className="w-[46px] h-[46px] bg-[#5c1a1a] rounded-full flex items-center justify-center font-['Anton',sans-serif] text-white text-[1.3rem] cursor-pointer shrink-0">
//             H
//           </div>
//           <ul className="flex gap-10 list-none absolute left-1/2 -translate-x-1/2">
//             <li><a href="#" className="text-base font-normal text-[#2a1a1a] no-underline hover:text-[#5c1a1a] transition-colors underline" onClick={(e) => e.preventDefault()}>Home</a></li>
//             <li><a href="#upload" className="text-base font-normal text-[#2a1a1a] no-underline hover:text-[#5c1a1a] transition-colors" onClick={(e) => { e.preventDefault(); scrollToSection('upload'); }}>Upload</a></li>
//             <li><a href="#jobs" className="text-base font-normal text-[#2a1a1a] no-underline hover:text-[#5c1a1a] transition-colors" onClick={(e) => { e.preventDefault(); scrollToSection('jobs'); }}>Jobs</a></li>
//             <li><a href="#contact" className="text-base font-normal text-[#2a1a1a] no-underline hover:text-[#5c1a1a] transition-colors" onClick={(e) => { e.preventDefault(); scrollToSection('contact'); }}>Contact</a></li>
//           </ul>
//           <button className="bg-[#d4be6a] border-2 border-[#5c1a1a] rounded-full py-[0.6rem] px-[1.8rem] font-['DM_Sans',sans-serif] text-[0.95rem] font-medium text-[#2a1a1a] cursor-pointer hover:bg-[#c8b05e] hover:-translate-y-[1px] transition-all" onClick={() => scrollToSection('upload')}>
//             Start Exploring
//           </button>
//         </nav>

//         {/* ─── HERO (Section 1) ─── */}
//         <section className="bg-[#b8dede] min-h-[88vh] relative overflow-hidden flex flex-col before:content-[''] before:absolute before:inset-0 before:bg-[linear-gradient(rgba(90,130,130,0.18)_1px,transparent_1px),linear-gradient(90deg,rgba(90,130,130,0.18)_1px,transparent_1px)] before:bg-[size:40px_40px] before:pointer-events-none">
//           <svg className="absolute left-[-10px] top-[60px] w-[260px] opacity-50 pointer-events-none" viewBox="0 0 260 300" fill="none" xmlns="http://www.w3.org/2000/svg">
//             <rect x="20" y="90" width="220" height="160" rx="12" stroke="#3d6060" strokeWidth="1.5" fill="none" />
//             <path d="M85 90 L85 65 Q85 50 100 50 L160 50 Q175 50 175 65 L175 90" stroke="#3d6060" strokeWidth="1.5" fill="none" />
//             <line x1="20" y1="155" x2="240" y2="155" stroke="#3d6060" strokeWidth="1.5" />
//             <rect x="110" y="140" width="40" height="30" rx="5" stroke="#3d6060" strokeWidth="1.5" fill="none" />
//             <rect x="55" y="30" width="70" height="90" rx="4" stroke="#3d6060" strokeWidth="1" fill="none" transform="rotate(-12 90 75)" />
//             <line x1="65" y1="55" x2="108" y2="48" stroke="#3d6060" strokeWidth="0.8" transform="rotate(-12 90 75)" />
//             <line x1="65" y1="65" x2="108" y2="58" stroke="#3d6060" strokeWidth="0.8" transform="rotate(-12 90 75)" />
//             <line x1="65" y1="75" x2="108" y2="68" stroke="#3d6060" strokeWidth="0.8" transform="rotate(-12 90 75)" />
//             <circle cx="210" cy="50" r="3" fill="#3d6060" opacity="0.5" />
//             <circle cx="230" cy="70" r="2" fill="#3d6060" opacity="0.4" />
//             <line x1="195" y1="35" x2="195" y2="25" stroke="#3d6060" strokeWidth="1" opacity="0.5" />
//             <line x1="190" y1="30" x2="200" y2="30" stroke="#3d6060" strokeWidth="1" opacity="0.5" />
//           </svg>

//           <svg className="absolute right-[-20px] top-[50px] w-[300px] opacity-50 pointer-events-none" viewBox="0 0 300 360" fill="none" xmlns="http://www.w3.org/2000/svg">
//             <rect x="30" y="20" width="200" height="270" rx="6" stroke="#3d6060" strokeWidth="1.5" fill="none" />
//             <rect x="35" y="25" width="190" height="260" rx="5" stroke="#3d6060" strokeWidth="0.5" fill="none" opacity="0.4" />
//             <rect x="50" y="40" width="60" height="60" rx="30" stroke="#3d6060" strokeWidth="1" fill="none" />
//             <rect x="125" y="50" width="85" height="8" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" />
//             <rect x="125" y="65" width="65" height="6" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" />
//             <rect x="125" y="78" width="75" height="5" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" opacity="0.6" />
//             <line x1="50" y1="115" x2="210" y2="115" stroke="#3d6060" strokeWidth="1" />
//             <rect x="50" y="128" width="50" height="7" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" />
//             <rect x="50" y="143" width="150" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
//             <rect x="50" y="153" width="140" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
//             <rect x="50" y="163" width="130" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
//             <rect x="50" y="180" width="55" height="7" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" />
//             <rect x="50" y="195" width="145" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
//             <rect x="50" y="205" width="155" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
//             <rect x="50" y="215" width="120" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
//             <rect x="50" y="232" width="45" height="7" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" />
//             <rect x="50" y="247" width="130" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
//             <rect x="50" y="257" width="110" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
//             <rect x="50" y="35" width="200" height="270" rx="6" stroke="#3d6060" strokeWidth="1" fill="none" opacity="0.25" transform="rotate(6 150 170)" />
//             <circle cx="250" cy="40" r="3" fill="#3d6060" opacity="0.4" />
//             <line x1="265" y1="60" x2="265" y2="50" stroke="#3d6060" strokeWidth="1" opacity="0.5" />
//             <line x1="260" y1="55" x2="270" y2="55" stroke="#3d6060" strokeWidth="1" opacity="0.5" />
//           </svg>

//           {/* Hero Content (Centered) */}
//           <div className="relative z-10 pt-16 pb-12 px-4 flex-1 flex flex-col items-center justify-center text-center w-full">
//             <h1 className="font-['Anton',sans-serif] text-[clamp(5rem,13vw,12rem)] text-[#5c1a1a] leading-[1.1] tracking-[0.02em] uppercase w-full animate-fadeUp-1">
//               Let's get hired!
//             </h1>
//             <p className="font-['DM_Sans',sans-serif] text-[clamp(1.1rem,2vw,1.45rem)] font-normal text-[#6b2020] pt-4 max-w-[600px] leading-[1.5] mx-auto animate-fadeUp-2">
//               Shit that works — AI parses your resume, matches real jobs, and tailors your profile to beat the ATS.
//             </p>
//           </div>

//           {/* Tag Pills (Aligned Horizontally) */}
//           <div className="absolute z-20 bottom-[180px] left-[5%] md:left-[15%]">
//             <div className="inline-flex items-center gap-[0.6rem] bg-[#d4be6a] border-[1.5px] border-black/10 rounded-full py-[0.55rem] px-[1.4rem] text-[0.95rem] font-medium text-[#2a1a1a] cursor-pointer hover:scale-[1.03] transition-transform animate-fadeUp-3">
//               <span className="w-2.5 h-2.5 bg-[#5c1a1a] rounded-full shrink-0"></span> ATS Optimization
//             </div>
//           </div>
          
//           <div className="absolute z-20 bottom-[180px] right-[5%] md:right-[15%]">
//             <div className="inline-flex items-center gap-[0.6rem] bg-[#d4be6a] border-[1.5px] border-black/10 rounded-full py-[0.55rem] px-[1.4rem] text-[0.95rem] font-medium text-[#2a1a1a] cursor-pointer hover:scale-[1.03] transition-transform animate-fadeUp-3">
//               <span className="w-2.5 h-2.5 bg-[#5c1a1a] rounded-full shrink-0"></span> Smart Job Match
//             </div>
//           </div>

//           {/* Scroll Down Button */}
//           <div className="absolute bottom-8 right-10 z-10 w-[52px] h-[52px] bg-[#d4be6a] border-2 border-[#5c1a1a] rounded-full flex items-center justify-center cursor-pointer hover:translate-y-[2px] transition-transform" onClick={() => scrollToSection('marquee')}>
//             <svg viewBox="0 0 24 24" fill="none" stroke="#5c1a1a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
//               <line x1="12" y1="5" x2="12" y2="19" /><polyline points="19 12 12 19 5 12" />
//             </svg>
//           </div>
//         </section>

//         {/* ─── MARQUEE ─── */}
//         <div className="bg-white border-y-2 border-[#5c1a1a] overflow-hidden py-[0.65rem] whitespace-nowrap" id="marquee">
//           <div className="inline-flex gap-0 animate-marquee">
//             {[...Array(10)].map((_, i) => (
//               <span key={i} className="font-['DM_Sans',sans-serif] text-base font-medium text-[#5c1a1a] px-8 inline-flex items-center gap-6">
//                 Upload. Parse. Get Hired. <span className="text-[#6b2020]">→</span>
//               </span>
//             ))}
//           </div>
//         </div>

//         {/* ─── UPLOAD SECTION ─── */}
//         <section className="grid grid-cols-1 md:grid-cols-2 min-h-[75vh] relative" id="upload">
//           {/* LEFT PANEL */}
//           <div className="bg-[#d9c76e] py-16 px-[3.5rem] pl-[4rem] flex flex-col justify-center relative before:content-[''] before:absolute before:inset-0 before:bg-[linear-gradient(rgba(140,110,0,0.12)_1px,transparent_1px),linear-gradient(90deg,rgba(140,110,0,0.12)_1px,transparent_1px)] before:bg-[size:40px_40px] before:pointer-events-none">
//             <div className="relative z-10">
//               <span className="inline-block border-[1.5px] border-[#5c1a1a] rounded-full py-[0.4rem] px-[1.2rem] text-[0.9rem] font-medium text-[#5c1a1a] mb-[1.8rem] w-fit">Resume Upload</span>
//               <h2 className="font-['Anton',sans-serif] text-[clamp(2.8rem,5vw,5rem)] text-[#5c1a1a] leading-[0.95] uppercase mb-6">Drop your<br />resume<br />here</h2>
//               <p className="text-[1.1rem] font-normal text-[#6b2020] leading-[1.5] max-w-[380px] mb-10">Our AI will parse your skills, find matching jobs, and tailor your profile to beat the ATS.</p>

//               <button className="inline-flex items-center gap-3 bg-[#5c1a1a] border-2 border-[#5c1a1a] rounded-full py-[0.85rem] px-8 font-['DM_Sans',sans-serif] text-base font-semibold text-white cursor-pointer hover:bg-[#4a1414] hover:-translate-y-[2px] transition-all w-fit" id="leftUploadBtn" onClick={handleInitiateUpload}>
//                 <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
//                   <polyline points="16 16 12 12 8 16" /><line x1="12" y1="12" x2="12" y2="21" />
//                   <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
//                 </svg>
//                 Upload Resume
//               </button>
//             </div>
//           </div>

//           {/* ARROW CIRCLE (Centered between panels) */}
//           <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 w-[120px] h-[120px] bg-white border-[2.5px] border-[#5c1a1a] rounded-full flex items-center justify-center cursor-pointer hover:bg-[#f5f0d8] hover:scale-105 transition-all duration-200" onClick={() => scrollToSection('upload')}>
//             <svg viewBox="0 0 24 24" fill="none" stroke="#5c1a1a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-[38px] h-[38px]">
//               <line x1="5" y1="12" x2="19" y2="12" />
//               <polyline points="12 5 19 12 12 19" />
//             </svg>
//           </div>

//           {/* RIGHT PANEL */}
//           <div className="bg-[#ede6c3] relative flex items-center justify-center py-12 px-14 before:content-[''] before:absolute before:inset-0 before:bg-[linear-gradient(rgba(0,0,0,0.07)_1px,transparent_1px),linear-gradient(90deg,rgba(0,0,0,0.07)_1px,transparent_1px)] before:bg-[size:40px_40px] before:pointer-events-none">
//             <div className="relative z-10 bg-white border-2 border-[#5c1a1a] rounded-2xl p-10 w-full max-w-[440px] shadow-[6px_6px_0_#5c1a1a]">
//               {/* Hidden file input */}
//               <input 
//                 type="file" 
//                 id="fileInput" 
//                 accept=".pdf,.docx" 
//                 className="hidden" 
//                 ref={fileInputRef}
//                 onChange={handleFileChange}
//               />

//               {/* Drop zone */}
//               <div 
//                 className={`border-2 border-dashed rounded-xl py-10 px-6 flex flex-col items-center justify-center text-center cursor-pointer transition-all bg-[#f5f0d8] min-h-[200px] ${isDragging || file ? 'border-[#5c1a1a] bg-[#5c1a1a]/[0.06]' : 'border-[#c0a060] hover:border-[#5c1a1a] hover:bg-[#5c1a1a]/[0.04]'}`}
//                 id="dropZone"
//                 onDragOver={handleDragOver}
//                 onDragLeave={handleDragLeave}
//                 onDrop={handleDrop}
//                 onClick={() => fileInputRef.current?.click()}
//               >
//                 <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 transition-colors ${file ? 'bg-[#5c1a1a]/15' : 'bg-[#5c1a1a]/10'}`} id="dropIcon">
//                   {file ? (
//                     <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#5c1a1a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
//                       <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
//                       <polyline points="14 2 14 8 20 8" />
//                       <line x1="16" y1="13" x2="8" y2="13" />
//                       <line x1="16" y1="17" x2="8" y2="17" />
//                       <polyline points="10 9 9 9 8 9" />
//                     </svg>
//                   ) : (
//                     <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#5c1a1a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
//                       <polyline points="16 16 12 12 8 16" /><line x1="12" y1="12" x2="12" y2="21" />
//                       <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
//                     </svg>
//                   )}
//                 </div>
//                 <div id="dropContent">
//                   {file ? (
//                     <>
//                       <p className="text-base font-semibold text-[#5c1a1a] mb-1">{file.name}</p>
//                       <p className="text-[0.82rem] text-[#888]">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
//                     </>
//                   ) : (
//                     <>
//                       <p className="text-base font-semibold text-[#2a1a1a] mb-1">Click to upload or drag and drop</p>
//                       <p className="text-[0.82rem] text-[#888]">PDF or DOCX (Max 10MB)</p>
//                     </>
//                   )}
//                 </div>
//               </div>

//               {/* Error */}
//               {error && (
//                 <div className="mt-4 py-3 px-4 bg-red-600/[0.08] border border-red-600/35 rounded-lg flex items-center gap-2.5 text-[0.85rem] text-[#b91c1c]" id="errorBox">
//                   <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
//                     <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
//                   </svg>
//                   <span id="errorMsg">{error}</span>
//                 </div>
//               )}

//               {/* Submit */}
//               <button 
//                 className={`w-full mt-6 p-4 rounded-full font-['DM_Sans',sans-serif] text-base font-semibold border-none flex items-center justify-center gap-2 transition-all ${!file ? 'bg-[#e8e0c8] text-[#a0907a] cursor-not-allowed' : 'bg-[#5c1a1a] text-white cursor-pointer hover:bg-[#4a1414] hover:-translate-y-[2px] hover:shadow-[0_6px_20px_rgba(92,26,26,0.25)]'} ${isUploading ? '!bg-[#7a3030] !text-white !cursor-not-allowed' : ''}`} 
//                 id="parseBtn" 
//                 disabled={!file || isUploading}
//                 onClick={handleUpload}
//               >
//                 {isUploading ? (
//                   <>
//                     <div className="w-5 h-5 border-[2.5px] border-white/30 border-t-white rounded-full animate-spin"></div> AI is analyzing your profile...
//                   </>
//                 ) : (
//                   'Parse Resume & Find Jobs ✨'
//                 )}
//               </button>
//             </div>
//           </div>
//         </section>

//         {/* ─── BLOG / FEATURES ─── */}
//         <section className="bg-[#f5f0d8] py-20 px-16 text-center" id="jobs">
//           <span className="inline-block border-[1.5px] border-[#5c1a1a] rounded-full py-[0.4rem] px-[1.2rem] text-[0.9rem] font-medium text-[#5c1a1a] mb-[1.8rem] bg-transparent">How It Works</span>
//           <h2 className="font-['Anton',sans-serif] text-[clamp(2.8rem,7vw,6rem)] text-[#5c1a1a] uppercase leading-[0.95] mb-[1.2rem]">From the Dashboard</h2>
//           <p className="text-[1.1rem] font-medium text-[#6b2020] mb-12 leading-[1.5]">Dive into our latest job matches and career discoveries</p>

//           <div className="grid grid-cols-1 md:grid-cols-3 gap-0 text-left mb-12">
//             <div className="bg-white border border-black/5 cursor-pointer overflow-hidden transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)]">
//               <div className="w-full aspect-[4/3] flex items-center justify-center text-5xl bg-[#acd8d8]">
//                 <svg width="100" height="100" viewBox="0 0 100 100" fill="none">
//                   <rect x="15" y="25" width="70" height="55" rx="5" stroke="#3d6060" strokeWidth="2" fill="none" />
//                   <path d="M35 25 L35 15 Q35 10 40 10 L60 10 Q65 10 65 15 L65 25" stroke="#3d6060" strokeWidth="2" fill="none" />
//                   <line x1="15" y1="50" x2="85" y2="50" stroke="#3d6060" strokeWidth="1.5" />
//                   <rect x="40" y="43" width="20" height="14" rx="3" stroke="#3d6060" strokeWidth="1.5" fill="none" />
//                 </svg>
//               </div>
//               <div className="flex items-center gap-2 pt-5 px-5 text-[0.82rem] text-[#666]">
//                 <div className="w-7 h-7 rounded-full bg-[#c8a882] flex items-center justify-center text-[0.65rem] text-white font-semibold shrink-0">AI</div>
//                 <span>System</span><span className="mx-0.5">·</span>
//                 <span>Step 1</span><span className="mx-0.5">·</span><span>2 min</span>
//               </div>
//               <div className="p-5 pb-6">
//                 <div className="text-base font-semibold text-[#5c1a1a] mb-2.5 leading-[1.35]">Upload Your Resume — PDF or DOCX Accepted</div>
//                 <p className="text-[0.83rem] text-[#555] leading-[1.55] line-clamp-3">Drop your resume and our AI will instantly extract your skills, experience, education, and accomplishments into a structured profile ready for matching.</p>
//               </div>
//             </div>

//             <div className="bg-white border border-black/5 cursor-pointer overflow-hidden transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)]">
//               <div className="w-full aspect-[4/3] flex items-center justify-center text-5xl bg-[#d9c76e]">
//                 <svg width="100" height="100" viewBox="0 0 100 100" fill="none">
//                   <circle cx="50" cy="45" r="28" stroke="#5c1a1a" strokeWidth="2" fill="none" />
//                   <line x1="70" y1="65" x2="85" y2="80" stroke="#5c1a1a" strokeWidth="3" strokeLinecap="round" />
//                   <line x1="38" y1="45" x2="62" y2="45" stroke="#5c1a1a" strokeWidth="1.5" />
//                   <line x1="50" y1="33" x2="50" y2="57" stroke="#5c1a1a" strokeWidth="1.5" />
//                 </svg>
//               </div>
//               <div className="flex items-center gap-2 pt-5 px-5 text-[0.82rem] text-[#666]">
//                 <div className="w-7 h-7 rounded-full bg-[#c8a882] flex items-center justify-center text-[0.65rem] text-white font-semibold shrink-0">AI</div>
//                 <span>System</span><span className="mx-0.5">·</span>
//                 <span>Step 2</span><span className="mx-0.5">·</span><span>instant</span>
//               </div>
//               <div className="p-5 pb-6">
//                 <div className="text-base font-semibold text-[#5c1a1a] mb-2.5 leading-[1.35]">AI Scans Live Jobs and Scores Your Match</div>
//                 <p className="text-[0.83rem] text-[#555] leading-[1.55] line-clamp-3">We query thousands of active job listings and rank them by how well your skills, experience, and goals align — giving you a match score for every opportunity.</p>
//               </div>
//             </div>

//             <div className="bg-white border border-black/5 cursor-pointer overflow-hidden transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)]">
//               <div className="w-full aspect-[4/3] flex items-center justify-center text-5xl bg-[#5a82b0]">
//                 <svg width="100" height="100" viewBox="0 0 100 100" fill="none">
//                   <rect x="15" y="20" width="70" height="60" rx="5" stroke="white" strokeWidth="1.5" fill="none" />
//                   <line x1="25" y1="38" x2="75" y2="38" stroke="white" strokeWidth="1" />
//                   <line x1="25" y1="50" x2="65" y2="50" stroke="white" strokeWidth="1" />
//                   <line x1="25" y1="62" x2="55" y2="62" stroke="white" strokeWidth="1" />
//                   <circle cx="72" cy="65" r="12" fill="rgba(255,255,255,0.15)" stroke="white" strokeWidth="1.5" />
//                   <polyline points="66,65 71,70 78,61" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round" />
//                 </svg>
//               </div>
//               <div className="flex items-center gap-2 pt-5 px-5 text-[0.82rem] text-[#666]">
//                 <div className="w-7 h-7 rounded-full bg-[#c8a882] flex items-center justify-center text-[0.65rem] text-white font-semibold shrink-0">AI</div>
//                 <span>System</span><span className="mx-0.5">·</span>
//                 <span>Step 3</span><span className="mx-0.5">·</span><span>tailored</span>
//               </div>
//               <div className="p-5 pb-6">
//                 <div className="text-base font-semibold text-[#5c1a1a] mb-2.5 leading-[1.35]">Get a Tailored Profile That Beats the ATS</div>
//                 <p className="text-[0.83rem] text-[#555] leading-[1.55] line-clamp-3">For every job you apply to, we generate a tailored resume and cover letter optimized for that company's ATS filters — dramatically boosting your callback rate.</p>
//               </div>
//             </div>
//           </div>

//           <a href="#upload" onClick={(e) => { e.preventDefault(); scrollToSection('upload'); }} className="inline-block bg-[#b8dede] border-2 border-[#5c1a1a] rounded-full p-4 px-14 font-['DM_Sans',sans-serif] text-base font-medium text-[#2a1a1a] cursor-pointer no-underline transition-all hover:bg-[#9fcece] hover:-translate-y-[2px]">Upload My Resume</a>
//         </section>

//         {/* ─── NEWSLETTER / CONTACT ─── */}
//         <section className="bg-[#b8dede] py-20 px-16 text-center relative overflow-hidden before:content-[''] before:absolute before:inset-0 before:bg-[linear-gradient(rgba(90,130,130,0.18)_1px,transparent_1px),linear-gradient(90deg,rgba(90,130,130,0.18)_1px,transparent_1px)] before:bg-[size:40px_40px] before:pointer-events-none" id="contact">
//           <div className="relative z-10">
//             <span className="inline-block border-[1.5px] border-[#5c1a1a] rounded-full py-[0.4rem] px-[1.2rem] text-[0.9rem] font-medium text-[#5c1a1a] mb-[1.8rem] bg-transparent">Stay Updated</span>
//             <h2 className="font-['Anton',sans-serif] text-[clamp(2.5rem,7vw,5.5rem)] text-[#5c1a1a] uppercase mb-[1.2rem]">Join the Expedition</h2>
//             <p className="text-[1.1rem] font-medium text-[#6b2020] mb-10 leading-[1.55]">Get new job matches and curated career tips<br />delivered straight to your inbox.</p>

//             <div className="max-w-[520px] mx-auto text-left">
//               <label className="block text-[0.9rem] font-medium text-[#2a1a1a] mb-2" htmlFor="emailInput">Email</label>
//               <input className="w-full p-[0.85rem] px-5 border-[1.5px] border-black/15 rounded font-['DM_Sans',sans-serif] text-[0.95rem] bg-white mb-4 outline-none transition-colors focus:border-[#5c1a1a]" type="email" id="emailInput" placeholder="you@email.com" />
//               <div className="flex items-center gap-2.5 mb-5 text-[0.88rem] text-[#444]">
//                 <input type="checkbox" id="consent" className="w-4 h-4 accent-[#5c1a1a] cursor-pointer" />
//                 <label htmlFor="consent">Yes, subscribe me to job alerts and updates.</label>
//               </div>
//               <button className="w-full bg-[#5c1a1a] text-white border-none rounded-full p-[0.95rem] font-['DM_Sans',sans-serif] text-base font-medium cursor-pointer transition-all hover:bg-[#4a1414] hover:-translate-y-[1px]">Subscribe →</button>
//             </div>
//           </div>
//         </section>

//         {/* ─── FOOTER ─── */}
//         <footer className="bg-[#5c1a1a] text-white py-12 px-16 flex items-center justify-between flex-wrap gap-6">
//           <div className="font-['Anton',sans-serif] text-[1.6rem] text-[#d4be6a] tracking-[0.03em]">HireMe</div>
//           <ul className="flex gap-8 list-none">
//             <li><a href="#" className="text-white/75 no-underline text-[0.9rem] transition-colors hover:text-white" onClick={(e) => e.preventDefault()}>Home</a></li>
//             <li><a href="#jobs" className="text-white/75 no-underline text-[0.9rem] transition-colors hover:text-white" onClick={(e) => { e.preventDefault(); scrollToSection('jobs'); }}>Jobs</a></li>
//             <li><a href="#" className="text-white/75 no-underline text-[0.9rem] transition-colors hover:text-white">About</a></li>
//             <li><a href="#contact" className="text-white/75 no-underline text-[0.9rem] transition-colors hover:text-white" onClick={(e) => { e.preventDefault(); scrollToSection('contact'); }}>Contact</a></li>
//           </ul>
//           <span className="text-[0.8rem] text-white/50">© 2025 HireMe. All rights reserved.</span>
//         </footer>
//       </div>
//     </>
//   );
// };

// export default UploadPage;

import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import api from '../api/client';
import fempicc from '../assets/fempicc.png';
import GuestUploadModal from '../components/GuestUploadModal';

const UploadPage = () => {
  // --- UPLOAD STATE & LOGIC ---
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  
  const { setProfileId, user, isAuthenticated, setIsAuthModalOpen, logout, enterDemoMode } = useApp();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // Guest Upload Interception State
  const [isGuestModalOpen, setIsGuestModalOpen] = useState(false);
  const [pendingFile, setPendingFile] = useState(null);

  const handleLaunchDemo = () => {
    enterDemoMode();
    navigate('/jobs');
  };

  const handleInitiateUpload = () => {
    if (!isAuthenticated) {
      setIsGuestModalOpen(true);
      return;
    }
    fileInputRef.current?.click();
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (!droppedFile) return;

    if (!isAuthenticated) {
      setPendingFile(droppedFile);
      setIsGuestModalOpen(true);
      return;
    }

    validateAndSetFile(droppedFile);
  };

  const handleAuthenticatedWithFile = (authedFile) => {
    if (authedFile) {
      validateAndSetFile(authedFile);
      setPendingFile(null);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) validateAndSetFile(selectedFile);
  };

  const validateAndSetFile = (selectedFile) => {
    setError(null);
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!validTypes.includes(selectedFile.type)) {
      setError('Please upload a PDF or DOCX file.');
      return;
    }
    if (selectedFile.size > 10 * 1024 * 1024) {
      setError('File is too large. Maximum size is 10MB.');
      return;
    }
    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file || isUploading) return;

    if (!isAuthenticated) {
      setPendingFile(file);
      setIsGuestModalOpen(true);
      return;
    }
    
    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    const targetUserId = user?.id || "123e4567-e89b-12d3-a456-426614174004";

    try {
      const response = await api.post(`/resume/upload?user_id=${targetUserId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setProfileId(response.data.profile_id);
      navigate('/jobs');
      
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to parse resume. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const scrollToSection = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <>
      {/* Inline styles for fonts and custom keyframes */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Anton&family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');
        @keyframes fadeUp { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes marquee { from { transform: translateX(0); } to { transform: translateX(-50%); } }
        .animate-fadeUp-1 { animation: fadeUp 0.7s ease both; }
        .animate-fadeUp-2 { animation: fadeUp 0.7s 0.2s ease both; }
        .animate-fadeUp-3 { animation: fadeUp 0.6s 0.35s ease both; }
        .animate-marquee { animation: marquee 18s linear infinite; }
      `}</style>

      {/* Breakout Wrapper */}
      <div className="absolute top-0 left-0 w-screen min-h-screen z-[100] overflow-x-hidden font-['DM_Sans',sans-serif] bg-[#f5f0d8] text-[#2a1a1a]">
        
        {/* ─── NAV ─── */}
        <nav className="sticky top-0 z-[200] bg-white flex items-center justify-between px-12 h-[72px] border-b border-black/5">
          <div className="flex items-center gap-3 cursor-pointer shrink-0" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <div className="w-[42px] h-[42px] bg-[#5c1a1a] rounded-xl flex items-center justify-center font-['Anton',sans-serif] text-white text-[1.3rem] shadow-sm relative overflow-hidden">
              <span className="relative z-10">H</span>
              <div className="absolute top-0 right-0 w-3 h-3 bg-[#d4be6a] rounded-bl-lg"></div>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1 font-['Anton',sans-serif] text-[1.45rem] text-[#5c1a1a] tracking-[0.02em] leading-none">
                <span>HIREME</span>
                <span className="text-[0.75rem] font-['DM_Sans',sans-serif] font-bold bg-[#5c1a1a] text-[#d4be6a] px-1.5 py-0.5 rounded ml-0.5 tracking-wider">AI</span>
              </div>
              <span className="text-[0.68rem] font-medium text-[#6b2020]/75 tracking-wider uppercase">Career &amp; Resume Accelerator</span>
            </div>
          </div>
          <ul className="flex gap-10 list-none absolute left-1/2 -translate-x-1/2">
            <li><a href="#" className="text-base font-normal text-[#2a1a1a] no-underline hover:text-[#5c1a1a] transition-colors underline" onClick={(e) => e.preventDefault()}>Home</a></li>
            <li><a href="#upload" className="text-base font-normal text-[#2a1a1a] no-underline hover:text-[#5c1a1a] transition-colors" onClick={(e) => { e.preventDefault(); scrollToSection('upload'); }}>Upload</a></li>
            <li><a href="#jobs" className="text-base font-normal text-[#2a1a1a] no-underline hover:text-[#5c1a1a] transition-colors" onClick={(e) => { e.preventDefault(); scrollToSection('jobs'); }}>Jobs</a></li>
            <li><a href="#contact" className="text-base font-normal text-[#2a1a1a] no-underline hover:text-[#5c1a1a] transition-colors" onClick={(e) => { e.preventDefault(); scrollToSection('contact'); }}>Contact</a></li>
          </ul>
          <div className="flex items-center gap-3 relative z-30">
            {isAuthenticated ? (
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-[#5c1a1a] bg-white/80 border border-[#5c1a1a]/20 px-3 py-1.5 rounded-full">
                  {user?.full_name || user?.email}
                </span>
                <button
                  type="button"
                  onClick={logout}
                  className="text-xs font-medium text-[#5c1a1a] hover:underline cursor-pointer"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setIsAuthModalOpen(true)}
                className="text-sm font-bold text-[#5c1a1a] hover:text-[#2a1a1a] transition-colors cursor-pointer px-2 py-1"
              >
                Sign In
              </button>
            )}
            <button
              type="button"
              onClick={handleLaunchDemo}
              className="hidden sm:inline-flex items-center gap-1.5 bg-[#5c1a1a] text-[#f5f0d8] border-2 border-[#5c1a1a] rounded-full py-[0.55rem] px-4 font-['DM_Sans',sans-serif] text-xs font-bold hover:bg-[#431212] hover:-translate-y-[1px] transition-all shadow-sm cursor-pointer"
            >
              <span>⚡ Try Instant Demo</span>
            </button>
            <button className="bg-[#d4be6a] border-2 border-[#5c1a1a] rounded-full py-[0.6rem] px-[1.8rem] font-['DM_Sans',sans-serif] text-[0.95rem] font-medium text-[#2a1a1a] cursor-pointer hover:bg-[#c8b05e] hover:-translate-y-[1px] transition-all" onClick={() => scrollToSection('upload')}>
              Start Exploring
            </button>
          </div>
        </nav>

        {/* ─── HERO (Section 1) ─── */}
        <section className="bg-[#b8dede] min-h-[88vh] relative overflow-hidden flex flex-col before:content-[''] before:absolute before:inset-0 before:bg-[linear-gradient(rgba(90,130,130,0.18)_1px,transparent_1px),linear-gradient(90deg,rgba(90,130,130,0.18)_1px,transparent_1px)] before:bg-[size:40px_40px] before:pointer-events-none">
          
          {/* Decorative Briefcase & Resume Layout */}
          <svg className="absolute left-[-10px] top-[60px] w-[260px] opacity-50 pointer-events-none" viewBox="0 0 260 300" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="20" y="90" width="220" height="160" rx="12" stroke="#3d6060" strokeWidth="1.5" fill="none" />
            <path d="M85 90 L85 65 Q85 50 100 50 L160 50 Q175 50 175 65 L175 90" stroke="#3d6060" strokeWidth="1.5" fill="none" />
            <line x1="20" y1="155" x2="240" y2="155" stroke="#3d6060" strokeWidth="1.5" />
            <rect x="110" y="140" width="40" height="30" rx="5" stroke="#3d6060" strokeWidth="1.5" fill="none" />
            <rect x="55" y="30" width="70" height="90" rx="4" stroke="#3d6060" strokeWidth="1" fill="none" transform="rotate(-12 90 75)" />
            <line x1="65" y1="55" x2="108" y2="48" stroke="#3d6060" strokeWidth="0.8" transform="rotate(-12 90 75)" />
            <line x1="65" y1="65" x2="108" y2="58" stroke="#3d6060" strokeWidth="0.8" transform="rotate(-12 90 75)" />
            <line x1="65" y1="75" x2="108" y2="68" stroke="#3d6060" strokeWidth="0.8" transform="rotate(-12 90 75)" />
            <circle cx="210" cy="50" r="3" fill="#3d6060" opacity="0.5" />
            <circle cx="230" cy="70" r="2" fill="#3d6060" opacity="0.4" />
            <line x1="195" y1="35" x2="195" y2="25" stroke="#3d6060" strokeWidth="1" opacity="0.5" />
            <line x1="190" y1="30" x2="200" y2="30" stroke="#3d6060" strokeWidth="1" opacity="0.5" />
          </svg>

          <svg className="absolute right-[-20px] top-[50px] w-[300px] opacity-50 pointer-events-none" viewBox="0 0 300 360" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="30" y="20" width="200" height="270" rx="6" stroke="#3d6060" strokeWidth="1.5" fill="none" />
            <rect x="35" y="25" width="190" height="260" rx="5" stroke="#3d6060" strokeWidth="0.5" fill="none" opacity="0.4" />
            <rect x="50" y="40" width="60" height="60" rx="30" stroke="#3d6060" strokeWidth="1" fill="none" />
            <rect x="125" y="50" width="85" height="8" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" />
            <rect x="125" y="65" width="65" height="6" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" />
            <rect x="125" y="78" width="75" height="5" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" opacity="0.6" />
            <line x1="50" y1="115" x2="210" y2="115" stroke="#3d6060" strokeWidth="1" />
            <rect x="50" y="128" width="50" height="7" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" />
            <rect x="50" y="143" width="150" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
            <rect x="50" y="153" width="140" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
            <rect x="50" y="163" width="130" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
            <rect x="50" y="180" width="55" height="7" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" />
            <rect x="50" y="195" width="145" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
            <rect x="50" y="205" width="155" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
            <rect x="50" y="215" width="120" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
            <rect x="50" y="232" width="45" height="7" rx="2" stroke="#3d6060" strokeWidth="0.8" fill="none" />
            <rect x="50" y="247" width="130" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
            <rect x="50" y="257" width="110" height="5" rx="2" stroke="#3d6060" strokeWidth="0.7" fill="none" opacity="0.7" />
            <rect x="50" y="35" width="200" height="270" rx="6" stroke="#3d6060" strokeWidth="1" fill="none" opacity="0.25" transform="rotate(6 150 170)" />
            <circle cx="250" cy="40" r="3" fill="#3d6060" opacity="0.4" />
            <line x1="265" y1="60" x2="265" y2="50" stroke="#3d6060" strokeWidth="1" opacity="0.5" />
            <line x1="260" y1="55" x2="270" y2="55" stroke="#3d6060" strokeWidth="1" opacity="0.5" />
          </svg>

          {/* Hero Content (Pushed down & flex-col layout changed) */}
          <div className="relative z-10 flex-1 w-full flex flex-col items-center justify-between pt-[18vh] md:pt-[20vh] px-4 pb-0">
            
            {/* Text & Doodles Wrapper */}
            <div className="relative inline-flex flex-col items-center text-center max-w-[100vw] z-20">
              
              {/* DOODLE 1: Top Left Sparkle/Burst */}
              {/* <svg className="absolute -top-8 -left-6 md:-top-16 md:-left-24 w-12 h-12 md:w-20 md:h-20 text-[#d4be6a] opacity-90 animate-fadeUp-3 pointer-events-none" viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round">
                <line x1="50" y1="10" x2="50" y2="30"/>
                <line x1="50" y1="70" x2="50" y2="90"/>
                <line x1="10" y1="50" x2="30" y2="50"/>
                <line x1="70" y1="50" x2="90" y2="50"/>
                <line x1="25" y1="25" x2="35" y2="35"/>
                <line x1="65" y1="65" x2="75" y2="75"/>
                <line x1="25" y1="75" x2="35" y2="65"/>
                <line x1="65" y1="35" x2="75" y2="25"/>
              </svg> */}

              {/* DOODLE 2: Top Right Curly Arrow */}
              {/* <svg className="absolute -top-8 -right-2 md:-top-12 md:-right-20 w-16 h-16 md:w-24 md:h-24 text-[#5c1a1a] opacity-50 animate-fadeUp-2 hidden sm:block pointer-events-none" viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round">
                <path d="M80 15 Q 90 50, 30 75" />
                <path d="M45 60 L 30 75 L 35 95" />
              </svg> */}

              {/* DOODLE 3: Bottom Left Crosses */}
              {/* <svg className="absolute bottom-4 -left-10 md:bottom-8 md:-left-24 w-8 h-8 md:w-12 md:h-12 text-[#5c1a1a] opacity-40 animate-fadeUp-3 hidden sm:block pointer-events-none" viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="6" strokeLinecap="round">
                <line x1="50" y1="10" x2="50" y2="90"/>
                <line x1="10" y1="50" x2="90" y2="50"/>
              </svg> */}

              {/* DOODLE 4: Bottom Right Loopy Circle (Pushed further out) */}
              {/* <svg className="absolute -bottom-10 -right-8 md:-bottom-12 md:-right-28 w-12 h-12 md:w-20 md:h-20 text-[#d4be6a] opacity-70 animate-fadeUp-3 hidden sm:block pointer-events-none z-0" viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round">
                <path d="M50 15 C 80 15, 90 40, 70 70 C 40 100, 15 70, 25 40 C 35 10, 70 20, 80 50" />
              </svg> */}

              {/* DOODLE 5: Squiggly Line under the H1 */}
              {/* <svg className="absolute top-[40%] md:top-[-20%] left-1/2 -translate-x-1/2 w-[70%] h-6 md:h-10 text-[#5c1a1a] opacity-20 animate-fadeUp-3 pointer-events-none" viewBox="0 0 300 40" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round">
                <path d="M10,20 C 50,-10, 100,50, 150,20 C 200,-10, 250,50, 290,20" />
              </svg> */}

              {/* DOODLE 6: Small Dot Cluster near the subtext */}
              {/* <svg className="absolute -bottom-12 right-[5%] w-10 h-10 text-[#5c1a1a] opacity-30 animate-fadeUp-3 hidden md:block pointer-events-none" viewBox="0 0 100 100" fill="currentColor">
                <circle cx="20" cy="30" r="6"/>
                <circle cx="70" cy="50" r="4"/>
                <circle cx="40" cy="80" r="8"/>
              </svg> */}

              {/* Main Heading (Larger & Bolder) */}
              <h1 className="relative z-10 font-['Anton',sans-serif] text-[clamp(3.5rem,10vw,13rem)] sm:whitespace-nowrap text-[#5c1a1a] leading-[1] tracking-[0.02em] uppercase animate-fadeUp-1 text-center mx-auto mb-2 drop-shadow-sm">
                Let's get hired!
              </h1>
              
              {/* Subheading */}
              <p className="relative z-10 font-['DM_Sans',sans-serif] text-[clamp(1rem,1.8vw,1.45rem)] font-medium text-[#6b2020] mt-4 max-w-[640px] leading-[1.6] animate-fadeUp-2 text-center mx-auto px-4">
                Shit that works — AI parses your resume, matches real jobs, and tailors your profile to beat the ATS.
              </p>

              {/* Instant Demo Hero Action Buttons */}
              <div className="relative z-20 mt-6 flex flex-wrap items-center justify-center gap-3 animate-fadeUp-3">
                <button
                  type="button"
                  onClick={handleLaunchDemo}
                  className="bg-[#5c1a1a] text-white border-2 border-[#5c1a1a] rounded-full py-3 px-6 font-['DM_Sans',sans-serif] text-sm font-bold shadow-lg hover:bg-[#431212] hover:-translate-y-0.5 transition-all flex items-center gap-2 cursor-pointer"
                >
                  <span>⚡ Launch Instant Demo (No Signup)</span>
                  <span className="text-[#d4be6a] text-base">→</span>
                </button>
                <button
                  type="button"
                  onClick={() => scrollToSection('upload')}
                  className="bg-white/80 backdrop-blur-sm text-[#5c1a1a] border-2 border-[#5c1a1a]/30 rounded-full py-3 px-6 font-['DM_Sans',sans-serif] text-sm font-semibold hover:border-[#5c1a1a] hover:bg-white transition-all cursor-pointer"
                >
                  Upload Your PDF
                </button>
              </div>
            </div>

            {/* Downward Illustration Image (Pushed to bottom, just above marquee) */}
            <div className="relative z-10 mt-auto mb-12 w-[240px] sm:w-[320px] md:w-[380px] animate-fadeUp-3">
              <img src={fempicc} alt="AI Assistant" className="w-full h-auto object-contain drop-shadow-xl" />
            </div>

          </div>

          {/* Tag Pills (Aligned Horizontally on the exact same axis) */}
          <div className="absolute z-20 bottom-[18%] left-[5%] md:left-[10%] xl:left-[15%] hidden lg:block">
            <div className="inline-flex items-center gap-[0.6rem] bg-[#d4be6a] border-[1.5px] border-black/10 rounded-full py-[0.55rem] px-[1.4rem] text-[0.95rem] font-medium text-[#2a1a1a] cursor-pointer hover:scale-[1.03] transition-transform animate-fadeUp-3 shadow-sm">
              <span className="w-2.5 h-2.5 bg-[#5c1a1a] rounded-full shrink-0"></span> ATS Optimization
            </div>
          </div>
          
          <div className="absolute z-20 bottom-[18%] right-[5%] md:right-[10%] xl:right-[15%] hidden lg:block">
            <div className="inline-flex items-center gap-[0.6rem] bg-[#d4be6a] border-[1.5px] border-black/10 rounded-full py-[0.55rem] px-[1.4rem] text-[0.95rem] font-medium text-[#2a1a1a] cursor-pointer hover:scale-[1.03] transition-transform animate-fadeUp-3 shadow-sm">
              <span className="w-2.5 h-2.5 bg-[#5c1a1a] rounded-full shrink-0"></span> Smart Job Match
            </div>
          </div>

          {/* Scroll Down Button */}
          <div className="absolute bottom-8 right-10 z-30 w-[52px] h-[52px] bg-[#d4be6a] border-2 border-[#5c1a1a] rounded-full flex items-center justify-center cursor-pointer hover:translate-y-[2px] transition-transform shadow-sm" onClick={() => scrollToSection('marquee')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="#5c1a1a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
              <line x1="12" y1="5" x2="12" y2="19" /><polyline points="19 12 12 19 5 12" />
            </svg>
          </div>
        </section>

        {/* ─── MARQUEE ─── */}
        <div className="bg-white border-y-2 border-[#5c1a1a] overflow-hidden py-[0.65rem] whitespace-nowrap relative z-20" id="marquee">
          <div className="inline-flex gap-0 animate-marquee">
            {[...Array(10)].map((_, i) => (
              <span key={i} className="font-['DM_Sans',sans-serif] text-base font-medium text-[#5c1a1a] px-8 inline-flex items-center gap-6">
                Upload. Submit. Get Interview Calls. <span className="text-[#6b2020]">→</span>
              </span>
            ))}
          </div>
        </div>

        {/* ─── UPLOAD SECTION ─── */}
        <section className="grid grid-cols-1 md:grid-cols-2 min-h-[75vh] relative" id="upload">
          {/* LEFT PANEL */}
          <div className="bg-[#d9c76e] py-16 px-[3.5rem] pl-[4rem] flex flex-col justify-center relative before:content-[''] before:absolute before:inset-0 before:bg-[linear-gradient(rgba(140,110,0,0.12)_1px,transparent_1px),linear-gradient(90deg,rgba(140,110,0,0.12)_1px,transparent_1px)] before:bg-[size:40px_40px] before:pointer-events-none">
            <div className="relative z-10">
              <span className="inline-block border-[1.5px] border-[#5c1a1a] rounded-full py-[0.4rem] px-[1.2rem] text-[0.9rem] font-medium text-[#5c1a1a] mb-[1.8rem] w-fit">Resume Upload</span>
              <h2 className="font-['Anton',sans-serif] text-[clamp(2.8rem,5vw,5rem)] text-[#5c1a1a] leading-[0.95] uppercase mb-6">Drop your<br />resume<br />here</h2>
              <p className="text-[1.1rem] font-normal text-[#6b2020] leading-[1.5] max-w-[380px] mb-10">Our AI will parse your skills, find matching jobs, and tailor your profile to beat the ATS.</p>

              <button className="inline-flex items-center gap-3 bg-[#5c1a1a] border-2 border-[#5c1a1a] rounded-full py-[0.85rem] px-8 font-['DM_Sans',sans-serif] text-base font-semibold text-white cursor-pointer hover:bg-[#4a1414] hover:-translate-y-[2px] transition-all w-fit" id="leftUploadBtn" onClick={handleInitiateUpload}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
                  <polyline points="16 16 12 12 8 16" /><line x1="12" y1="12" x2="12" y2="21" />
                  <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
                </svg>
                Upload Resume
              </button>
            </div>
          </div>

          {/* ARROW CIRCLE (Centered between panels) */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 w-[120px] h-[120px] bg-white border-[2.5px] border-[#5c1a1a] rounded-full flex items-center justify-center cursor-pointer hover:bg-[#f5f0d8] hover:scale-105 transition-all duration-200" onClick={() => scrollToSection('upload')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="#5c1a1a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-[38px] h-[38px]">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </div>

          {/* RIGHT PANEL */}
          <div className="bg-[#ede6c3] relative flex items-center justify-center py-12 px-14 before:content-[''] before:absolute before:inset-0 before:bg-[linear-gradient(rgba(0,0,0,0.07)_1px,transparent_1px),linear-gradient(90deg,rgba(0,0,0,0.07)_1px,transparent_1px)] before:bg-[size:40px_40px] before:pointer-events-none">
            <div className="relative z-10 bg-white border-2 border-[#5c1a1a] rounded-2xl p-10 w-full max-w-[440px] shadow-[6px_6px_0_#5c1a1a]">
              {/* Hidden file input */}
              <input 
                type="file" 
                id="fileInput" 
                accept=".pdf,.docx" 
                className="hidden" 
                ref={fileInputRef}
                onChange={handleFileChange}
              />

              {/* Drop zone */}
              <div 
                className={`border-2 border-dashed rounded-xl py-10 px-6 flex flex-col items-center justify-center text-center cursor-pointer transition-all bg-[#f5f0d8] min-h-[200px] ${isDragging || file ? 'border-[#5c1a1a] bg-[#5c1a1a]/[0.06]' : 'border-[#c0a060] hover:border-[#5c1a1a] hover:bg-[#5c1a1a]/[0.04]'}`}
                id="dropZone"
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={handleInitiateUpload}
              >
                <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 transition-colors ${file ? 'bg-[#5c1a1a]/15' : 'bg-[#5c1a1a]/10'}`} id="dropIcon">
                  {file ? (
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#5c1a1a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="16" y1="13" x2="8" y2="13" />
                      <line x1="16" y1="17" x2="8" y2="17" />
                      <polyline points="10 9 9 9 8 9" />
                    </svg>
                  ) : (
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#5c1a1a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="16 16 12 12 8 16" /><line x1="12" y1="12" x2="12" y2="21" />
                      <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
                    </svg>
                  )}
                </div>
                <div id="dropContent">
                  {file ? (
                    <>
                      <p className="text-base font-semibold text-[#5c1a1a] mb-1">{file.name}</p>
                      <p className="text-[0.82rem] text-[#888]">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    </>
                  ) : (
                    <>
                      <p className="text-base font-semibold text-[#2a1a1a] mb-1">Click to upload or drag and drop</p>
                      <p className="text-[0.82rem] text-[#888]">PDF or DOCX (Max 10MB)</p>
                    </>
                  )}
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="mt-4 py-3 px-4 bg-red-600/[0.08] border border-red-600/35 rounded-lg flex items-center gap-2.5 text-[0.85rem] text-[#b91c1c]" id="errorBox">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
                    <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                  <span id="errorMsg">{error}</span>
                </div>
              )}

              {/* Submit */}
              <button 
                className={`w-full mt-6 p-4 rounded-full font-['DM_Sans',sans-serif] text-base font-semibold border-none flex items-center justify-center gap-2 transition-all ${!file ? 'bg-[#e8e0c8] text-[#a0907a] cursor-not-allowed' : 'bg-[#5c1a1a] text-white cursor-pointer hover:bg-[#4a1414] hover:-translate-y-[2px] hover:shadow-[0_6px_20px_rgba(92,26,26,0.25)]'} ${isUploading ? '!bg-[#7a3030] !text-white !cursor-not-allowed' : ''}`} 
                id="parseBtn" 
                disabled={!file || isUploading}
                onClick={handleUpload}
              >
                {isUploading ? (
                  <>
                    <div className="w-5 h-5 border-[2.5px] border-white/30 border-t-white rounded-full animate-spin"></div> AI is analyzing your profile...
                  </>
                ) : (
                  'Parse Resume & Find Jobs ✨'
                )}
              </button>

              {/* Instant Demo Alternative */}
              <div className="mt-4 pt-3 border-t border-[#5c1a1a]/15 text-center">
                <button
                  type="button"
                  onClick={handleLaunchDemo}
                  className="text-xs font-bold text-[#5c1a1a] hover:text-[#2a1a1a] underline decoration-[#5c1a1a]/40 hover:decoration-[#5c1a1a] transition-colors cursor-pointer"
                >
                  ⚡ Don't have a resume handy? Try Instant Demo (1-Click) →
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* ─── BLOG / FEATURES ─── */}
        <section className="bg-[#f5f0d8] py-20 px-16 text-center" id="jobs">
          <span className="inline-block border-[1.5px] border-[#5c1a1a] rounded-full py-[0.4rem] px-[1.2rem] text-[0.9rem] font-medium text-[#5c1a1a] mb-[1.8rem] bg-transparent">How It Works</span>
          <h2 className="font-['Anton',sans-serif] text-[clamp(2.8rem,7vw,6rem)] text-[#5c1a1a] uppercase leading-[0.95] mb-[1.2rem]">From the Dashboard</h2>
          <p className="text-[1.1rem] font-medium text-[#6b2020] mb-12 leading-[1.5]">Dive into our latest job matches and career discoveries</p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-0 text-left mb-12">
            <div className="bg-white border border-black/5 cursor-pointer overflow-hidden transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)]">
              <div className="w-full aspect-[4/3] flex items-center justify-center text-5xl bg-[#acd8d8]">
                <svg width="100" height="100" viewBox="0 0 100 100" fill="none">
                  <rect x="15" y="25" width="70" height="55" rx="5" stroke="#3d6060" strokeWidth="2" fill="none" />
                  <path d="M35 25 L35 15 Q35 10 40 10 L60 10 Q65 10 65 15 L65 25" stroke="#3d6060" strokeWidth="2" fill="none" />
                  <line x1="15" y1="50" x2="85" y2="50" stroke="#3d6060" strokeWidth="1.5" />
                  <rect x="40" y="43" width="20" height="14" rx="3" stroke="#3d6060" strokeWidth="1.5" fill="none" />
                </svg>
              </div>
              <div className="flex items-center gap-2 pt-5 px-5 text-[0.82rem] text-[#666]">
                <div className="w-7 h-7 rounded-full bg-[#c8a882] flex items-center justify-center text-[0.65rem] text-white font-semibold shrink-0">AI</div>
                <span>System</span><span className="mx-0.5">·</span>
                <span>Step 1</span><span className="mx-0.5">·</span><span>2 min</span>
              </div>
              <div className="p-5 pb-6">
                <div className="text-base font-semibold text-[#5c1a1a] mb-2.5 leading-[1.35]">Upload Your Resume — PDF or DOCX Accepted</div>
                <p className="text-[0.83rem] text-[#555] leading-[1.55] line-clamp-3">Drop your resume and our AI will instantly extract your skills, experience, education, and accomplishments into a structured profile ready for matching.</p>
              </div>
            </div>

            <div className="bg-white border border-black/5 cursor-pointer overflow-hidden transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)]">
              <div className="w-full aspect-[4/3] flex items-center justify-center text-5xl bg-[#d9c76e]">
                <svg width="100" height="100" viewBox="0 0 100 100" fill="none">
                  <circle cx="50" cy="45" r="28" stroke="#5c1a1a" strokeWidth="2" fill="none" />
                  <line x1="70" y1="65" x2="85" y2="80" stroke="#5c1a1a" strokeWidth="3" strokeLinecap="round" />
                  <line x1="38" y1="45" x2="62" y2="45" stroke="#5c1a1a" strokeWidth="1.5" />
                  <line x1="50" y1="33" x2="50" y2="57" stroke="#5c1a1a" strokeWidth="1.5" />
                </svg>
              </div>
              <div className="flex items-center gap-2 pt-5 px-5 text-[0.82rem] text-[#666]">
                <div className="w-7 h-7 rounded-full bg-[#c8a882] flex items-center justify-center text-[0.65rem] text-white font-semibold shrink-0">AI</div>
                <span>System</span><span className="mx-0.5">·</span>
                <span>Step 2</span><span className="mx-0.5">·</span><span>instant</span>
              </div>
              <div className="p-5 pb-6">
                <div className="text-base font-semibold text-[#5c1a1a] mb-2.5 leading-[1.35]">AI Scans Live Jobs and Scores Your Match</div>
                <p className="text-[0.83rem] text-[#555] leading-[1.55] line-clamp-3">We query thousands of active job listings and rank them by how well your skills, experience, and goals align — giving you a match score for every opportunity.</p>
              </div>
            </div>

            <div className="bg-white border border-black/5 cursor-pointer overflow-hidden transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(0,0,0,0.1)]">
              <div className="w-full aspect-[4/3] flex items-center justify-center text-5xl bg-[#5a82b0]">
                <svg width="100" height="100" viewBox="0 0 100 100" fill="none">
                  <rect x="15" y="20" width="70" height="60" rx="5" stroke="white" strokeWidth="1.5" fill="none" />
                  <line x1="25" y1="38" x2="75" y2="38" stroke="white" strokeWidth="1" />
                  <line x1="25" y1="50" x2="65" y2="50" stroke="white" strokeWidth="1" />
                  <line x1="25" y1="62" x2="55" y2="62" stroke="white" strokeWidth="1" />
                  <circle cx="72" cy="65" r="12" fill="rgba(255,255,255,0.15)" stroke="white" strokeWidth="1.5" />
                  <polyline points="66,65 71,70 78,61" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round" />
                </svg>
              </div>
              <div className="flex items-center gap-2 pt-5 px-5 text-[0.82rem] text-[#666]">
                <div className="w-7 h-7 rounded-full bg-[#c8a882] flex items-center justify-center text-[0.65rem] text-white font-semibold shrink-0">AI</div>
                <span>System</span><span className="mx-0.5">·</span>
                <span>Step 3</span><span className="mx-0.5">·</span><span>tailored</span>
              </div>
              <div className="p-5 pb-6">
                <div className="text-base font-semibold text-[#5c1a1a] mb-2.5 leading-[1.35]">Get a Tailored Profile That Beats the ATS</div>
                <p className="text-[0.83rem] text-[#555] leading-[1.55] line-clamp-3">For every job you apply to, we generate a tailored resume and cover letter optimized for that company's ATS filters — dramatically boosting your callback rate.</p>
              </div>
            </div>
          </div>

          <a href="#upload" onClick={(e) => { e.preventDefault(); scrollToSection('upload'); }} className="inline-block bg-[#b8dede] border-2 border-[#5c1a1a] rounded-full p-4 px-14 font-['DM_Sans',sans-serif] text-base font-medium text-[#2a1a1a] cursor-pointer no-underline transition-all hover:bg-[#9fcece] hover:-translate-y-[2px]">Upload My Resume</a>
        </section>

        {/* ─── NEWSLETTER / CONTACT ─── */}
        <section className="bg-[#b8dede] py-20 px-16 text-center relative overflow-hidden before:content-[''] before:absolute before:inset-0 before:bg-[linear-gradient(rgba(90,130,130,0.18)_1px,transparent_1px),linear-gradient(90deg,rgba(90,130,130,0.18)_1px,transparent_1px)] before:bg-[size:40px_40px] before:pointer-events-none" id="contact">
          <div className="relative z-10">
            <span className="inline-block border-[1.5px] border-[#5c1a1a] rounded-full py-[0.4rem] px-[1.2rem] text-[0.9rem] font-medium text-[#5c1a1a] mb-[1.8rem] bg-transparent">Stay Updated</span>
            <h2 className="font-['Anton',sans-serif] text-[clamp(2.5rem,7vw,5.5rem)] text-[#5c1a1a] uppercase mb-[1.2rem]">Join the Expedition</h2>
            <p className="text-[1.1rem] font-medium text-[#6b2020] mb-10 leading-[1.55]">Get new job matches and curated career tips<br />delivered straight to your inbox.</p>

            <div className="max-w-[520px] mx-auto text-left">
              <label className="block text-[0.9rem] font-medium text-[#2a1a1a] mb-2" htmlFor="emailInput">Email</label>
              <input className="w-full p-[0.85rem] px-5 border-[1.5px] border-black/15 rounded font-['DM_Sans',sans-serif] text-[0.95rem] bg-white mb-4 outline-none transition-colors focus:border-[#5c1a1a]" type="email" id="emailInput" placeholder="you@email.com" />
              <div className="flex items-center gap-2.5 mb-5 text-[0.88rem] text-[#444]">
                <input type="checkbox" id="consent" className="w-4 h-4 accent-[#5c1a1a] cursor-pointer" />
                <label htmlFor="consent">Yes, subscribe me to job alerts and updates.</label>
              </div>
              <button className="w-full bg-[#5c1a1a] text-white border-none rounded-full p-[0.95rem] font-['DM_Sans',sans-serif] text-base font-medium cursor-pointer transition-all hover:bg-[#4a1414] hover:-translate-y-[1px]">Subscribe →</button>
            </div>
          </div>
        </section>

        {/* ─── FOOTER ─── */}
        <footer className="bg-[#5c1a1a] text-white py-12 px-16 flex items-center justify-between flex-wrap gap-6">
          <div className="flex items-center gap-2">
            <span className="font-['Anton',sans-serif] text-[1.7rem] text-[#d4be6a] tracking-[0.03em]">HireMe</span>
            <span className="text-[0.8rem] font-bold bg-[#d4be6a] text-[#5c1a1a] px-1.5 py-0.5 rounded">AI</span>
          </div>
          <ul className="flex gap-8 list-none">
            <li><a href="#" className="text-white/75 no-underline text-[0.9rem] transition-colors hover:text-white" onClick={(e) => e.preventDefault()}>Home</a></li>
            <li><a href="#jobs" className="text-white/75 no-underline text-[0.9rem] transition-colors hover:text-white" onClick={(e) => { e.preventDefault(); scrollToSection('jobs'); }}>Jobs</a></li>
            <li><a href="#" className="text-white/75 no-underline text-[0.9rem] transition-colors hover:text-white">About</a></li>
            <li><a href="#contact" className="text-white/75 no-underline text-[0.9rem] transition-colors hover:text-white" onClick={(e) => { e.preventDefault(); scrollToSection('contact'); }}>Contact</a></li>
          </ul>
          <span className="text-[0.8rem] text-white/50">© 2026 HireMe AI. All rights reserved.</span>
        </footer>

        {/* Guest Upload Interception Modal */}
        <GuestUploadModal
          isOpen={isGuestModalOpen}
          onClose={() => setIsGuestModalOpen(false)}
          pendingFile={pendingFile}
          onAuthenticatedWithFile={handleAuthenticatedWithFile}
        />
      </div>
    </>
  );
};

export default UploadPage;