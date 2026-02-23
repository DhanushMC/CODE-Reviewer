'use client';

import { useRouter } from 'next/navigation';
import { CheckCircle, Download, Home } from 'lucide-react';

export default function SuccessPage() {
    const router = useRouter();
    const finalCode = typeof window !== 'undefined' ? sessionStorage.getItem('finalCode') : '';

    const handleDownload = () => {
        if (finalCode) {
            const blob = new Blob([finalCode], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'fixed_code.txt';
            a.click();
            URL.revokeObjectURL(url);
        }
    };

    return (
        <div className="min-h-screen p-8 flex items-center justify-center">
            <div className="max-w-3xl w-full text-center">
                <div className="inline-block glass rounded-full p-8 mb-8 animate-float">
                    <CheckCircle className="w-24 h-24 text-green-400" />
                </div>

                <h1 className="text-5xl font-bold mb-4 gradient-text">Success!</h1>
                <p className="text-2xl text-slate-300 mb-8">
                    Your code has been securely fixed and validated
                </p>

                <div className="glass rounded-2xl p-8 mb-8">
                    <p className="text-lg text-slate-300 mb-6">
                        The vulnerability has been successfully patched using intent-aware fixing.
                        All tests passed in the isolated sandbox environment.
                    </p>

                    {finalCode && (
                        <div className="mb-6">
                            <h3 className="text-xl font-bold mb-4">Fixed Code</h3>
                            <pre className="code-block text-left overflow-x-auto text-sm max-h-64">{finalCode}</pre>
                        </div>
                    )}

                    <button
                        onClick={handleDownload}
                        className="btn-primary flex items-center gap-2 mx-auto"
                    >
                        <Download className="w-5 h-5" />
                        Download Fixed Code
                    </button>
                </div>

                <button
                    onClick={() => router.push('/')}
                    className="btn-secondary flex items-center gap-2 mx-auto"
                >
                    <Home className="w-5 h-5" />
                    Return Home
                </button>
            </div>
        </div>
    );
}
