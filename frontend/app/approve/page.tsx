'use client';

import { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { CheckCircle, Loader2 } from 'lucide-react';

// BUG FIX: Wrap in Suspense for useSearchParams
function ApproveContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const sessionId = searchParams.get('session');

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleApprove = async (approved: boolean) => {
        if (!sessionId) return;
        setLoading(true);
        setError('');
        try {
            const result = await apiClient.finalApproval(sessionId, approved);
            if (approved && result.final_code) {
                sessionStorage.setItem('finalCode', result.final_code);
                router.push('/success');
            } else {
                router.push('/');
            }
        } catch (err: any) {
            setError(err.message || 'Approval failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen p-8 flex items-center justify-center">
            <div className="max-w-3xl w-full">
                <div className="text-center mb-8">
                    <div className="inline-block glass rounded-full p-6 mb-6">
                        <CheckCircle className="w-16 h-16 text-green-400" />
                    </div>
                    <h1 className="text-4xl font-bold mb-4 gradient-text">Final Approval</h1>
                    <p className="text-xl text-slate-300">All tests passed! Ready to apply the fix?</p>
                </div>

                <div className="glass rounded-2xl p-8 mb-6">
                    <h2 className="text-2xl font-bold mb-6">Summary</h2>
                    <div className="space-y-4">
                        {['Vulnerability Detected', 'Intent Captured', 'Fix Generated', 'Tests Passed'].map((step) => (
                            <div key={step} className="flex justify-between items-center p-4 bg-slate-800/50 rounded-lg">
                                <span className="text-slate-400">{step}</span>
                                <CheckCircle className="w-5 h-5 text-green-400" />
                            </div>
                        ))}
                    </div>

                    <div className="mt-8 p-4 bg-blue-500/10 border border-blue-500/50 rounded-lg">
                        <p className="text-blue-300">
                            <strong>Note:</strong> Approving will finalize the fix. The secure code will be available for download.
                        </p>
                    </div>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
                        {error}
                    </div>
                )}

                <div className="flex gap-4">
                    <button
                        onClick={() => handleApprove(true)}
                        disabled={loading}
                        className="btn-primary flex-1 text-lg py-4 flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-6 h-6 animate-spin" />
                                Processing...
                            </>
                        ) : (
                            <>
                                <CheckCircle className="w-6 h-6" />
                                Apply Fix
                            </>
                        )}
                    </button>
                    <button
                        onClick={() => handleApprove(false)}
                        disabled={loading}
                        className="btn-secondary flex-1 text-lg py-4"
                    >
                        Reject Fix
                    </button>
                </div>
            </div>
        </div>
    );
}

export default function ApprovePage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
            </div>
        }>
            <ApproveContent />
        </Suspense>
    );
}
