'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { TestTube, Play, Loader2, CheckCircle, XCircle } from 'lucide-react';

// BUG FIX: Wrap in Suspense for useSearchParams
function TestsContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const sessionId = searchParams.get('session');

    const [tests, setTests] = useState('');
    const [descriptions, setDescriptions] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);
    const [running, setRunning] = useState(false);
    const [results, setResults] = useState<any>(null);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchTests = async () => {
            if (!sessionId) return;
            try {
                const result = await apiClient.generateTests(sessionId);
                setTests(result.tests);
                setDescriptions(result.test_descriptions);
            } catch (err: any) {
                setError(err.message || 'Failed to generate tests');
            } finally {
                setLoading(false);
            }
        };
        fetchTests();
    }, [sessionId]);

    const handleRunTests = async () => {
        if (!sessionId) return;
        setRunning(true);
        setError('');
        try {
            const result = await apiClient.runTests(sessionId);
            setResults(result);
            sessionStorage.setItem('testResults', JSON.stringify(result));
        } catch (err: any) {
            setError(err.message || 'Failed to run tests');
        } finally {
            setRunning(false);
        }
    };

    const handleNext = () => {
        if (results?.all_tests_passed) {
            router.push(`/approve?session=${sessionId}`);
        } else {
            setError('All tests must pass before proceeding to approval.');
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-indigo-400" />
                    <p className="text-xl">Generating intent-aware tests...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen p-8">
            <div className="max-w-6xl mx-auto">
                <h1 className="text-4xl font-bold mb-8 gradient-text flex items-center gap-3">
                    <TestTube className="w-10 h-10" />
                    Generated Tests
                </h1>

                <div className="glass rounded-2xl p-6 mb-6">
                    <h2 className="text-xl font-bold mb-4">Test Coverage</h2>
                    <ul className="space-y-2">
                        {descriptions.map((desc, i) => (
                            <li key={i} className="flex items-start gap-2">
                                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                                <span>{desc}</span>
                            </li>
                        ))}
                    </ul>
                </div>

                <div className="glass rounded-2xl p-6 mb-6">
                    <h2 className="text-xl font-bold mb-4">Test Code</h2>
                    <pre className="code-block overflow-x-auto text-sm max-h-96">{tests}</pre>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
                        {error}
                    </div>
                )}

                {!results && (
                    <button
                        onClick={handleRunTests}
                        disabled={running}
                        className="btn-primary w-full flex items-center justify-center gap-2 mb-6"
                    >
                        {running ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Running Tests in Sandbox...
                            </>
                        ) : (
                            <>
                                <Play className="w-5 h-5" />
                                Run Tests in Sandbox
                            </>
                        )}
                    </button>
                )}

                {results && (
                    <div className="glass rounded-2xl p-6 mb-6">
                        <div className="flex items-center gap-3 mb-4">
                            {results.all_tests_passed ? (
                                <>
                                    <CheckCircle className="w-8 h-8 text-green-400" />
                                    <h2 className="text-2xl font-bold text-green-400">All Tests Passed!</h2>
                                </>
                            ) : (
                                <>
                                    <XCircle className="w-8 h-8 text-red-400" />
                                    <h2 className="text-2xl font-bold text-red-400">Tests Failed</h2>
                                </>
                            )}
                        </div>

                        <div className="mb-4">
                            <h3 className="text-lg font-semibold mb-2">Execution Logs</h3>
                            <pre className="code-block overflow-x-auto text-xs max-h-64">{results.logs}</pre>
                        </div>

                        {results.individual_results?.length > 0 && (
                            <div>
                                <h3 className="text-lg font-semibold mb-2">Individual Results</h3>
                                <div className="space-y-2">
                                    {results.individual_results.map((r: any, i: number) => (
                                        <div
                                            key={i}
                                            className={`p-3 rounded-lg flex items-center gap-2 ${r.passed ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}
                                        >
                                            {r.passed ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
                                            <span className="font-mono text-sm">{r.name}</span>
                                            {r.error_message && <span className="text-xs ml-2">— {r.error_message}</span>}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                <div className="flex gap-4">
                    {results?.all_tests_passed && (
                        <button onClick={handleNext} className="btn-primary flex-1">
                            Proceed to Final Approval
                        </button>
                    )}
                    <button onClick={() => router.back()} className="btn-secondary">Back</button>
                </div>
            </div>
        </div>
    );
}

export default function TestsPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
            </div>
        }>
            <TestsContent />
        </Suspense>
    );
}
