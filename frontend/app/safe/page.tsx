'use client';

import { useRouter } from 'next/navigation';
import { ShieldCheck, Home } from 'lucide-react';

export default function SafePage() {
    const router = useRouter();

    return (
        <div className="min-h-screen p-8 flex items-center justify-center">
            <div className="max-w-3xl w-full text-center">
                <div className="inline-block glass rounded-full p-8 mb-8 animate-float">
                    <ShieldCheck className="w-24 h-24 text-green-400" />
                </div>

                <h1 className="text-5xl font-bold mb-4 gradient-text">No Vulnerabilities Found!</h1>
                <p className="text-2xl text-slate-300 mb-8">
                    Your code passed all security checks
                </p>

                <div className="glass rounded-2xl p-8 mb-8">
                    <p className="text-lg text-slate-300">
                        Our ML-based analysis (CodeBERT + rule-based detection) found no security vulnerabilities
                        in your code. Your implementation follows secure coding practices!
                    </p>
                </div>

                <button
                    onClick={() => router.push('/')}
                    className="btn-primary flex items-center gap-2 mx-auto"
                >
                    <Home className="w-5 h-5" />
                    Return Home
                </button>
            </div>
        </div>
    );
}
