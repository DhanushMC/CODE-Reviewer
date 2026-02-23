'use client';

import { Suspense } from 'react';
import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { AlertTriangle, Info, Loader2 } from 'lucide-react';

// BUG FIX: useSearchParams() requires a Suspense boundary in Next.js 13+
// Wrap the actual page content in a separate component so Suspense can wrap it

function ResultsContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const sessionId = searchParams.get('session');

    const [result, setResult] = useState<any>(null);
    const [explanation, setExplanation] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [showModal, setShowModal] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        const stored = sessionStorage.getItem('analysisResult');
        if (stored) {
            setResult(JSON.parse(stored));
        }
    }, []);

    const handleExplain = async () => {
        if (!sessionId || !result) return;
        setLoading(true);
        setError('');
        try {
            const code = sessionStorage.getItem('code') || '';
            const explanationResult = await apiClient.explain(
                sessionId,
                code,
                result.vulnerability_type,
                result.evidence
            );
            setExplanation(explanationResult);
            sessionStorage.setItem('explanation', JSON.stringify(explanationResult));
            setShowModal(true);
        } catch (err: any) {
            setError(err.message || 'Failed to generate explanation');
        } finally {
            setLoading(false);
        }
    };

    const handleProceed = () => {
        router.push(`/intent?session=${sessionId}`);
    };

    const handleCancel = () => {
        router.push('/');
    };

    if (!result) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
            </div>
        );
    }

    const severityColors: Record<string, string> = {
        HIGH: 'text-red-400 bg-red-500/10 border-red-500/50',
        MEDIUM: 'text-orange-400 bg-orange-500/10 border-orange-500/50',
        LOW: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/50',
    };

    return (
        <div className="min-h-screen p-8">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-4xl font-bold mb-8 gradient-text">Vulnerability Detected</h1>

                <div className="glass rounded-2xl p-8 mb-6">
                    <div className="flex items-center gap-4 mb-6">
                        <AlertTriangle className="w-12 h-12 text-red-400" />
                        <div>
                            <h2 className="text-2xl font-bold">{result.vulnerability_type.replace(/_/g, ' ')}</h2>
                            <p className="text-slate-400">Security vulnerability found in your code</p>
                        </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6 mb-6">
                        <div className={`p-4 rounded-lg border ${severityColors[result.severity] || 'text-slate-400 bg-slate-800/50 border-slate-600'}`}>
                            <div className="text-sm font-semibold mb-1">Severity</div>
                            <div className="text-2xl font-bold">{result.severity ?? 'N/A'}</div>
                        </div>

                        <div className="p-4 rounded-lg border border-slate-600 bg-slate-800/50">
                            <div className="text-sm font-semibold mb-1 text-slate-400">Confidence</div>
                            <div className="text-2xl font-bold">{(result.confidence * 100).toFixed(1)}%</div>
                        </div>
                    </div>

                    <div className="mb-6">
                        <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                            <Info className="w-5 h-5" />
                            Evidence
                        </h3>
                        <div className="code-block">{result.evidence}</div>
                        {result.line_numbers?.length > 0 && (
                            <p className="text-sm text-slate-400 mt-2">
                                Lines: {result.line_numbers.join(', ')}
                            </p>
                        )}
                    </div>

                    {error && (
                        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    {!explanation && (
                        <button
                            onClick={handleExplain}
                            disabled={loading}
                            className="btn-primary w-full flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Generating Explanation...
                                </>
                            ) : (
                                'Get Detailed Explanation'
                            )}
                        </button>
                    )}

                    {explanation && (
                        <div className="mt-6 p-6 bg-slate-800/50 rounded-lg border border-slate-700">
                            <h3 className="text-xl font-bold mb-4">Explanation</h3>
                            <div className="mb-6">
                                <p className="whitespace-pre-wrap text-slate-300">{explanation.explanation}</p>
                            </div>

                            {explanation.similar_examples?.length > 0 && (
                                <div>
                                    <h4 className="text-lg font-semibold mb-3">Similar Examples</h4>
                                    <div className="space-y-4">
                                        {explanation.similar_examples.map((ex: any, i: number) => (
                                            <div key={i} className="p-4 bg-slate-900/50 rounded-lg">
                                                <p className="text-sm text-slate-400 mb-2">{ex.description}</p>
                                                <div className="grid md:grid-cols-2 gap-4">
                                                    <div>
                                                        <div className="text-xs text-red-400 mb-1">Vulnerable:</div>
                                                        <pre className="text-xs bg-black/50 p-2 rounded overflow-x-auto">{ex.vulnerable_code}</pre>
                                                    </div>
                                                    <div>
                                                        <div className="text-xs text-green-400 mb-1">Secure:</div>
                                                        <pre className="text-xs bg-black/50 p-2 rounded overflow-x-auto">{ex.secure_code}</pre>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {showModal && (
                    <div className="glass rounded-2xl p-8">
                        <h3 className="text-2xl font-bold mb-4">Proceed with Fix?</h3>
                        <p className="text-slate-300 mb-6">
                            A vulnerability was detected. Would you like to proceed with fixing it?
                            This will require you to specify your intent for the code.
                        </p>
                        <div className="flex gap-4">
                            <button onClick={handleProceed} className="btn-primary flex-1">
                                Yes, Fix It
                            </button>
                            <button onClick={handleCancel} className="btn-secondary flex-1">
                                No, Cancel
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default function ResultsPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
            </div>
        }>
            <ResultsContent />
        </Suspense>
    );
}
