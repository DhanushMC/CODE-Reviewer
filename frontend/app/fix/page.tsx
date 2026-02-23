'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { Wrench, ArrowRight, Loader2 } from 'lucide-react';

// BUG FIX: Wrap in Suspense for useSearchParams
function FixContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const sessionId = searchParams.get('session');

    const [original, setOriginal] = useState('');
    const [fixed, setFixed] = useState('');
    const [explanation, setExplanation] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchFix = async () => {
            if (!sessionId) return;
            try {
                const code = sessionStorage.getItem('code') || '';
                setOriginal(code);
                const result = await apiClient.generateFix(sessionId);
                setFixed(result.fixed_code);
                setExplanation(result.explanation);
                // BUG FIX: store fixed code so tests page can access it if needed
                sessionStorage.setItem('fixedCode', result.fixed_code);
            } catch (err: any) {
                setError(err.message || 'Failed to generate fix');
            } finally {
                setLoading(false);
            }
        };
        fetchFix();
    }, [sessionId]);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-indigo-400" />
                    <p className="text-xl">Generating intent-aware fix...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="glass rounded-2xl p-8 max-w-md text-center">
                    <p className="text-red-400 text-lg mb-4">{error}</p>
                    <button onClick={() => router.back()} className="btn-secondary">Go Back</button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen p-8">
            <div className="max-w-7xl mx-auto">
                <h1 className="text-4xl font-bold mb-8 gradient-text flex items-center gap-3">
                    <Wrench className="w-10 h-10" />
                    Code Fix Preview
                </h1>

                <div className="glass rounded-2xl p-6 mb-6">
                    <h2 className="text-xl font-bold mb-3">What Changed</h2>
                    <p className="text-slate-300 whitespace-pre-wrap">{explanation}</p>
                </div>

                <div className="grid md:grid-cols-2 gap-6 mb-6">
                    <div className="glass rounded-2xl p-6">
                        <h3 className="text-lg font-semibold mb-4 text-red-400">Vulnerable Code</h3>
                        <pre className="code-block overflow-x-auto text-sm">{original}</pre>
                    </div>
                    <div className="glass rounded-2xl p-6">
                        <h3 className="text-lg font-semibold mb-4 text-green-400">Fixed Code</h3>
                        <pre className="code-block overflow-x-auto text-sm">{fixed}</pre>
                    </div>
                </div>

                <div className="flex gap-4">
                    <button
                        onClick={() => router.push(`/tests?session=${sessionId}`)}
                        className="btn-primary flex items-center gap-2"
                    >
                        Generate Tests <ArrowRight className="w-5 h-5" />
                    </button>
                    <button onClick={() => router.back()} className="btn-secondary">Back</button>
                </div>
            </div>
        </div>
    );
}

export default function FixPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
            </div>
        }>
            <FixContent />
        </Suspense>
    );
}
