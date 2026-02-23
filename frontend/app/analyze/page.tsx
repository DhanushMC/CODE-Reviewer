'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import {
    Loader2, Upload, Code2, FolderArchive, GitBranch,
    CheckCircle, X, FileCode, ChevronDown, Cpu, Database,
    Shield, Globe, Package, Zap, AlertCircle, RefreshCw
} from 'lucide-react';

type InputMode = 'paste' | 'zip' | 'git';

interface DetectionResult {
    language: string;
    language_confidence: number;
    framework: string | null;
    project_type: string | null;
    api_endpoints: { method: string; path: string }[];
    dependencies: string[];
    database: string | null;
    auth_mechanisms: string[];
    summary: string;
}

const METHOD_COLORS: Record<string, string> = {
    GET:    'bg-green-500/20 text-green-300 border-green-500/40',
    POST:   'bg-blue-500/20 text-blue-300 border-blue-500/40',
    PUT:    'bg-yellow-500/20 text-yellow-300 border-yellow-500/40',
    PATCH:  'bg-orange-500/20 text-orange-300 border-orange-500/40',
    DELETE: 'bg-red-500/20 text-red-300 border-red-500/40',
    ANY:    'bg-purple-500/20 text-purple-300 border-purple-500/40',
};

const LANG_ICONS: Record<string, string> = {
    python: '🐍', javascript: '🟨', typescript: '🔷',
    java: '☕', cpp: '⚙️', csharp: '💜', go: '🐹', php: '🐘', ruby: '💎', rust: '🦀',
};

export default function AnalyzePage() {
    const router = useRouter();

    const [mode, setMode] = useState<InputMode>('paste');

    // Paste
    const [code, setCode]         = useState('');
    // ZIP
    const [zipFile, setZipFile]   = useState<File | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    // Git
    const [repoUrl, setRepoUrl]   = useState('');
    const [branch, setBranch]     = useState('main');

    // Auto-detection
    const [detection, setDetection]         = useState<DetectionResult | null>(null);
    const [detecting, setDetecting]         = useState(false);
    const [detectionError, setDetectionError] = useState('');
    const detectTimer = useRef<NodeJS.Timeout | null>(null);

    // Analysis
    const [loading, setLoading]   = useState(false);
    const [loadingMsg, setLoadingMsg] = useState('Analyzing...');
    const [error, setError]       = useState('');

    // ── Auto-detect as user types (debounced 800ms) ──────────────────────────
    useEffect(() => {
        if (mode !== 'paste' || code.length < 50) {
            setDetection(null);
            return;
        }
        if (detectTimer.current) clearTimeout(detectTimer.current);
        detectTimer.current = setTimeout(() => runDetection(code), 800);
        return () => { if (detectTimer.current) clearTimeout(detectTimer.current); };
    }, [code, mode]);

    const runDetection = async (codeToDetect: string, filename?: string) => {
        if (!codeToDetect.trim() || codeToDetect.length < 50) return;
        setDetecting(true);
        setDetectionError('');
        try {
            const result = await apiClient.detectCode(codeToDetect, filename);
            setDetection(result);
        } catch (e: any) {
            setDetectionError('Detection failed: ' + e.message);
        } finally {
            setDetecting(false);
        }
    };

    // ── Drag & drop ──────────────────────────────────────────────────────────
    const onDragOver  = useCallback((e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); }, []);
    const onDragLeave = useCallback(() => setIsDragging(false), []);
    const onDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault(); setIsDragging(false);
        const file = e.dataTransfer.files[0];
        if (file?.name.endsWith('.zip')) { setZipFile(file); setError(''); }
        else setError('Please drop a .zip file');
    }, []);

    // ── Extract ZIP client-side using JSZip ──────────────────────────────────
    const extractZipCode = async (file: File, lang: string): Promise<string> => {
        if (!(window as any).JSZip) {
            await new Promise<void>((res, rej) => {
                const s = document.createElement('script');
                s.src = 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js';
                s.onload = () => res(); s.onerror = () => rej(new Error('Failed to load JSZip'));
                document.head.appendChild(s);
            });
        }
        const extMap: Record<string, string[]> = {
            python: ['.py'], javascript: ['.js','.ts','.jsx','.tsx'],
            typescript: ['.ts','.tsx'], java: ['.java'], cpp: ['.cpp','.cc','.h','.c'],
            csharp: ['.cs'], go: ['.go'], php: ['.php'], ruby: ['.rb'], rust: ['.rs'],
        };
        const exts = extMap[lang] || ['.py','.js','.java','.cpp','.go','.php','.cs','.ts','.rb','.rs'];
        const ignored = ['node_modules/','__pycache__/','.git/','vendor/','dist/','build/','venv/','.next/'];

        const JSZip = (window as any).JSZip;
        const zip = await JSZip.loadAsync(file);
        const parts: string[] = [];
        const promises: Promise<void>[] = [];

        zip.forEach((path: string, entry: any) => {
            if (entry.dir) return;
            if (!exts.some(e => path.toLowerCase().endsWith(e))) return;
            if (ignored.some(i => path.includes(i))) return;
            if (parts.length >= 20) return;
            promises.push(
                entry.async('string').then((c: string) => {
                    parts.push(`// ===== FILE: ${path} =====\n${c}`);
                })
            );
        });
        await Promise.all(promises);
        if (!parts.length) throw new Error(`No files found for language "${lang}". Check language selection.`);
        return parts.join('\n\n');
    };

    // ── Main analyze handler ─────────────────────────────────────────────────
    const handleAnalyze = async () => {
        setError('');
        let finalCode = '';
        let detectedLang = detection?.language || 'python';

        if (mode === 'paste') {
            if (!code.trim()) { setError('Please paste your code'); return; }
            finalCode = code;
        } else if (mode === 'zip') {
            if (!zipFile) { setError('Please select a ZIP file'); return; }
        } else {
            if (!repoUrl.trim()) { setError('Please enter a repository URL'); return; }
            if (!repoUrl.startsWith('http')) { setError('Enter a valid URL starting with https://'); return; }
        }

        setLoading(true);
        try {
            if (mode === 'zip') {
                setLoadingMsg('Extracting ZIP...');
                // First extract a sample to detect language
                const sample = await extractZipCode(zipFile!, 'python'); // extract all common
                setLoadingMsg('Detecting language & framework...');
                const det = await apiClient.detectCode(sample, zipFile!.name);
                setDetection(det);
                detectedLang = det.language;
                finalCode = await extractZipCode(zipFile!, detectedLang);
            } else if (mode === 'git') {
                setLoadingMsg('Cloning repository...');
                const gitResult = await apiClient.fetchGitRepo(repoUrl, branch, 'python');
                setLoadingMsg('Detecting language & framework...');
                const det = await apiClient.detectCode(gitResult.code);
                setDetection(det);
                detectedLang = det.language;
                finalCode = gitResult.code;
            }

            setLoadingMsg('Running security analysis...');
            const result = await apiClient.analyze({ code: finalCode, language: detectedLang });

            sessionStorage.setItem('analysisResult', JSON.stringify(result));
            sessionStorage.setItem('code', finalCode);
            sessionStorage.setItem('language', detectedLang);
            sessionStorage.setItem('detection', JSON.stringify(detection));

            router.push(result.is_vulnerable ? `/results?session=${result.session_id}` : '/safe');
        } catch (err: any) {
            setError(err.message || 'Analysis failed');
        } finally {
            setLoading(false);
            setLoadingMsg('Analyzing...');
        }
    };

    const fmt = (bytes: number) =>
        bytes < 1024*1024 ? `${(bytes/1024).toFixed(1)} KB` : `${(bytes/(1024*1024)).toFixed(1)} MB`;

    const confColor = (c: number) =>
        c > 0.8 ? 'text-green-400' : c > 0.5 ? 'text-yellow-400' : 'text-orange-400';

    return (
        <div className="min-h-screen p-8">
            <div className="max-w-5xl mx-auto">

                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold mb-2 gradient-text">Code Analysis</h1>
                    <p className="text-slate-400">Language, framework & endpoints are detected automatically</p>
                </div>

                <div className="grid lg:grid-cols-5 gap-6">

                    {/* ── Left: Input panel (3/5) ── */}
                    <div className="lg:col-span-3 glass rounded-2xl p-6">

                        {/* Mode tabs */}
                        <div className="flex gap-1.5 mb-6 p-1 bg-slate-800/60 rounded-xl">
                            {([
                                { id: 'paste', icon: Code2,         label: 'Paste Code' },
                                { id: 'zip',   icon: FolderArchive,  label: 'Upload ZIP' },
                                { id: 'git',   icon: GitBranch,      label: 'Git Repo'   },
                            ] as const).map(({ id, icon: Icon, label }) => (
                                <button key={id}
                                    onClick={() => { setMode(id); setError(''); setDetection(null); }}
                                    className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-lg font-semibold text-sm transition-all duration-200 ${
                                        mode === id
                                            ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/30'
                                            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
                                    }`}
                                >
                                    <Icon className="w-4 h-4" />{label}
                                </button>
                            ))}
                        </div>

                        {/* PASTE */}
                        {mode === 'paste' && (
                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <label className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                                        <Code2 className="w-4 h-4" /> Code Input
                                    </label>
                                    {code.length > 0 && (
                                        <span className="text-xs text-slate-500">
                                            {code.split('\n').length} lines · {code.length} chars
                                        </span>
                                    )}
                                </div>
                                <textarea
                                    value={code}
                                    onChange={e => setCode(e.target.value)}
                                    placeholder="Paste your code here — language & framework will be detected automatically..."
                                    className="w-full h-80 font-mono text-sm"
                                    spellCheck={false}
                                />
                                {detecting && (
                                    <div className="flex items-center gap-2 mt-2 text-xs text-indigo-400">
                                        <Loader2 className="w-3 h-3 animate-spin" /> Detecting...
                                    </div>
                                )}
                            </div>
                        )}

                        {/* ZIP */}
                        {mode === 'zip' && (
                            <div>
                                <label className="block text-sm font-semibold mb-3 text-slate-300 flex items-center gap-2">
                                    <FolderArchive className="w-4 h-4" /> Upload Project ZIP
                                </label>
                                <div
                                    onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop}
                                    onClick={() => !zipFile && fileInputRef.current?.click()}
                                    className={`relative border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-200 ${
                                        isDragging ? 'border-indigo-400 bg-indigo-500/10 scale-[1.01]'
                                        : zipFile  ? 'border-green-500/60 bg-green-500/5 cursor-default'
                                        : 'border-slate-600 bg-slate-800/30 hover:border-indigo-500/60 hover:bg-indigo-500/5'
                                    }`}
                                >
                                    {!zipFile ? (
                                        <>
                                            <FolderArchive className={`w-12 h-12 mx-auto mb-3 ${isDragging ? 'text-indigo-400' : 'text-slate-500'}`} />
                                            <p className="font-semibold text-slate-300 mb-1">
                                                {isDragging ? 'Drop it!' : 'Drag & drop your ZIP'}
                                            </p>
                                            <p className="text-slate-500 text-sm">or click to browse</p>
                                        </>
                                    ) : (
                                        <div className="flex items-center justify-center gap-4">
                                            <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                                                <FileCode className="w-5 h-5 text-green-400" />
                                            </div>
                                            <div className="text-left">
                                                <p className="font-semibold text-green-300 text-sm">{zipFile.name}</p>
                                                <p className="text-xs text-slate-400">{fmt(zipFile.size)}</p>
                                            </div>
                                            <button onClick={e => { e.stopPropagation(); setZipFile(null); setDetection(null); if (fileInputRef.current) fileInputRef.current.value = ''; }}
                                                className="p-1.5 rounded-lg hover:bg-red-500/20 text-slate-400 hover:text-red-400">
                                                <X className="w-4 h-4" />
                                            </button>
                                        </div>
                                    )}
                                </div>
                                <input ref={fileInputRef} type="file" accept=".zip" onChange={e => { setZipFile(e.target.files?.[0] || null); setDetection(null); }} className="hidden" />
                                <p className="text-xs text-slate-500 mt-3">
                                    Language is auto-detected from your files. node_modules, __pycache__, .git are skipped.
                                </p>
                            </div>
                        )}

                        {/* GIT */}
                        {mode === 'git' && (
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-semibold mb-2 text-slate-300 flex items-center gap-2">
                                        <GitBranch className="w-4 h-4" /> Repository URL
                                    </label>
                                    <input type="text" value={repoUrl}
                                        onChange={e => { setRepoUrl(e.target.value); setDetection(null); }}
                                        placeholder="https://github.com/username/repository"
                                        className="w-full font-mono text-sm" />
                                </div>
                                <div>
                                    <label className="block text-sm font-semibold mb-2 text-slate-300">Branch</label>
                                    <input type="text" value={branch}
                                        onChange={e => setBranch(e.target.value)}
                                        placeholder="main" className="w-full max-w-xs" />
                                </div>
                                <div className="p-4 bg-blue-500/8 rounded-lg border border-blue-500/20 text-xs text-slate-400 leading-relaxed">
                                    <strong className="text-blue-300">Public repos only.</strong> The backend clones your repo,
                                    auto-detects the language and framework, then scans all source files. For private repos, use ZIP upload.
                                </div>
                            </div>
                        )}

                        {/* Error */}
                        {error && (
                            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/40 rounded-xl flex items-start gap-2 text-red-400 text-sm">
                                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />{error}
                            </div>
                        )}

                        {/* Submit */}
                        <div className="flex gap-3 mt-6">
                            <button onClick={handleAnalyze} disabled={loading}
                                className="btn-primary flex items-center gap-2 px-8">
                                {loading
                                    ? <><Loader2 className="w-4 h-4 animate-spin" />{loadingMsg}</>
                                    : <><Zap className="w-4 h-4" />Analyze Code</>
                                }
                            </button>
                            <button onClick={() => router.push('/')} className="btn-secondary">Cancel</button>
                        </div>
                    </div>

                    {/* ── Right: Detection panel (2/5) ── */}
                    <div className="lg:col-span-2 space-y-4">

                        {/* Detection card */}
                        <div className="glass rounded-2xl p-5">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="font-bold text-slate-200 flex items-center gap-2">
                                    <Cpu className="w-4 h-4 text-indigo-400" /> Auto-Detection
                                </h2>
                                {detection && !detecting && (
                                    <button onClick={() => runDetection(code)}
                                        className="text-slate-500 hover:text-indigo-400 transition-colors">
                                        <RefreshCw className="w-3.5 h-3.5" />
                                    </button>
                                )}
                            </div>

                            {detecting && (
                                <div className="flex flex-col items-center justify-center py-8 gap-3">
                                    <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
                                    <p className="text-sm text-slate-400">Analyzing code structure...</p>
                                </div>
                            )}

                            {!detecting && !detection && (
                                <div className="text-center py-8">
                                    <Cpu className="w-10 h-10 mx-auto mb-3 text-slate-600" />
                                    <p className="text-sm text-slate-500">
                                        {mode === 'paste'
                                            ? 'Paste 50+ characters to auto-detect'
                                            : 'Detection runs after loading your code'}
                                    </p>
                                </div>
                            )}

                            {!detecting && detection && (
                                <div className="space-y-4">

                                    {/* Language */}
                                    <div className="p-3 bg-slate-800/60 rounded-xl">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <span className="text-xl">{LANG_ICONS[detection.language] || '📄'}</span>
                                                <div>
                                                    <p className="font-semibold text-slate-100 capitalize">{detection.language}</p>
                                                    <p className="text-xs text-slate-500">Language</p>
                                                </div>
                                            </div>
                                            <span className={`text-sm font-bold ${confColor(detection.language_confidence)}`}>
                                                {(detection.language_confidence * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                    </div>

                                    {/* Framework */}
                                    {detection.framework && (
                                        <div className="p-3 bg-slate-800/60 rounded-xl flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center flex-shrink-0">
                                                <Globe className="w-4 h-4 text-purple-400" />
                                            </div>
                                            <div>
                                                <p className="font-semibold text-slate-100">{detection.framework}</p>
                                                <p className="text-xs text-slate-500">Framework</p>
                                            </div>
                                        </div>
                                    )}

                                    {/* Project type */}
                                    {detection.project_type && (
                                        <div className="p-3 bg-slate-800/60 rounded-xl flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                                                <Zap className="w-4 h-4 text-blue-400" />
                                            </div>
                                            <div>
                                                <p className="font-semibold text-slate-100">{detection.project_type}</p>
                                                <p className="text-xs text-slate-500">Project Type</p>
                                            </div>
                                        </div>
                                    )}

                                    {/* Database */}
                                    {detection.database && (
                                        <div className="p-3 bg-slate-800/60 rounded-xl flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center flex-shrink-0">
                                                <Database className="w-4 h-4 text-green-400" />
                                            </div>
                                            <div>
                                                <p className="font-semibold text-slate-100">{detection.database}</p>
                                                <p className="text-xs text-slate-500">Database</p>
                                            </div>
                                        </div>
                                    )}

                                    {/* Auth */}
                                    {detection.auth_mechanisms.length > 0 && (
                                        <div className="p-3 bg-slate-800/60 rounded-xl">
                                            <div className="flex items-center gap-2 mb-2">
                                                <Shield className="w-4 h-4 text-yellow-400" />
                                                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Auth</p>
                                            </div>
                                            <div className="flex flex-wrap gap-1.5">
                                                {detection.auth_mechanisms.map(a => (
                                                    <span key={a} className="px-2 py-0.5 rounded-md bg-yellow-500/15 border border-yellow-500/30 text-yellow-300 text-xs">
                                                        {a}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* API Endpoints card */}
                        {detection?.api_endpoints && detection.api_endpoints.length > 0 && (
                            <div className="glass rounded-2xl p-5">
                                <h3 className="font-bold text-slate-200 flex items-center gap-2 mb-3">
                                    <Globe className="w-4 h-4 text-green-400" />
                                    API Endpoints
                                    <span className="ml-auto text-xs text-slate-500 font-normal">
                                        {detection.api_endpoints.length} found
                                    </span>
                                </h3>
                                <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
                                    {detection.api_endpoints.map((ep, i) => (
                                        <div key={i} className="flex items-center gap-2">
                                            <span className={`px-1.5 py-0.5 rounded text-xs font-bold border flex-shrink-0 w-14 text-center ${METHOD_COLORS[ep.method] || METHOD_COLORS['ANY']}`}>
                                                {ep.method}
                                            </span>
                                            <code className="text-xs text-slate-300 font-mono truncate">{ep.path}</code>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Dependencies card */}
                        {detection?.dependencies && detection.dependencies.length > 0 && (
                            <div className="glass rounded-2xl p-5">
                                <h3 className="font-bold text-slate-200 flex items-center gap-2 mb-3">
                                    <Package className="w-4 h-4 text-blue-400" />
                                    Dependencies
                                    <span className="ml-auto text-xs text-slate-500 font-normal">
                                        {detection.dependencies.length} found
                                    </span>
                                </h3>
                                <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
                                    {detection.dependencies.map(dep => (
                                        <span key={dep} className="px-2 py-0.5 rounded-md bg-slate-700/60 border border-slate-600 text-slate-300 text-xs font-mono">
                                            {dep}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {detectionError && (
                            <div className="p-3 bg-orange-500/10 border border-orange-500/30 rounded-xl text-orange-400 text-xs flex gap-2">
                                <AlertCircle className="w-4 h-4 flex-shrink-0" />{detectionError}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
