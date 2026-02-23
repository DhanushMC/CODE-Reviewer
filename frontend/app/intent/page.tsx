'use client';

import { Suspense } from 'react';
import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { Brain, Plus, X, Loader2 } from 'lucide-react';

// BUG FIX: Wrap in Suspense to fix useSearchParams build error in Next.js 13+
function IntentContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const sessionId = searchParams.get('session');

    const [purpose, setPurpose] = useState('');
    const [validCases, setValidCases] = useState([{ input: '', expected: '' }]);
    const [invalidCases, setInvalidCases] = useState([{ input: '', expected: '' }]);
    const [constraints, setConstraints] = useState<string[]>([]);
    const [sideEffects, setSideEffects] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const constraintOptions = [
        'no_sql_injection',
        'no_xss',
        'no_command_injection',
        'input_validation',
        'output_encoding'
    ];

    const sideEffectOptions = [
        'read_only',
        'write_data',
        'network_call',
        'file_system',
        'database_write'
    ];

    const addValidCase = () => setValidCases([...validCases, { input: '', expected: '' }]);
    const removeValidCase = (i: number) => setValidCases(validCases.filter((_, idx) => idx !== i));
    const addInvalidCase = () => setInvalidCases([...invalidCases, { input: '', expected: '' }]);
    const removeInvalidCase = (i: number) => setInvalidCases(invalidCases.filter((_, idx) => idx !== i));

    const handleSubmit = async () => {
        if (!purpose.trim()) {
            setError('Please provide the function purpose');
            return;
        }
        setLoading(true);
        setError('');
        try {
            await apiClient.captureIntent({
                session_id: sessionId!,
                purpose,
                valid_cases: validCases.filter(c => c.input || c.expected),
                invalid_cases: invalidCases.filter(c => c.input || c.expected),
                security_constraints: constraints,
                side_effects: sideEffects,
            });
            router.push(`/fix?session=${sessionId}`);
        } catch (err: any) {
            setError(err.message || 'Failed to capture intent');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen p-8">
            <div className="max-w-4xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-4xl font-bold mb-2 gradient-text flex items-center gap-3">
                        <Brain className="w-10 h-10" />
                        Intent Capture
                    </h1>
                    <p className="text-slate-400">Describe what your code should do (SEM-8 Novelty)</p>
                </div>

                <div className="glass rounded-2xl p-8 space-y-8">
                    <div>
                        <label className="block text-sm font-semibold mb-2">Function Purpose *</label>
                        <textarea
                            value={purpose}
                            onChange={(e) => setPurpose(e.target.value)}
                            placeholder="e.g., Fetch user data from database by ID"
                            className="w-full h-20"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-semibold mb-2">Valid Input Cases</label>
                        {validCases.map((c, i) => (
                            <div key={i} className="flex gap-3 mb-3">
                                <input
                                    type="text"
                                    placeholder="Input"
                                    value={c.input}
                                    onChange={(e) => {
                                        const updated = [...validCases];
                                        updated[i].input = e.target.value;
                                        setValidCases(updated);
                                    }}
                                    className="flex-1"
                                />
                                <input
                                    type="text"
                                    placeholder="Expected behavior"
                                    value={c.expected}
                                    onChange={(e) => {
                                        const updated = [...validCases];
                                        updated[i].expected = e.target.value;
                                        setValidCases(updated);
                                    }}
                                    className="flex-1"
                                />
                                {validCases.length > 1 && (
                                    <button onClick={() => removeValidCase(i)} className="text-red-400 hover:text-red-300">
                                        <X className="w-5 h-5" />
                                    </button>
                                )}
                            </div>
                        ))}
                        <button onClick={addValidCase} className="btn-secondary text-sm flex items-center gap-2">
                            <Plus className="w-4 h-4" /> Add Valid Case
                        </button>
                    </div>

                    <div>
                        <label className="block text-sm font-semibold mb-2">Invalid Input Cases</label>
                        {invalidCases.map((c, i) => (
                            <div key={i} className="flex gap-3 mb-3">
                                <input
                                    type="text"
                                    placeholder="Invalid input"
                                    value={c.input}
                                    onChange={(e) => {
                                        const updated = [...invalidCases];
                                        updated[i].input = e.target.value;
                                        setInvalidCases(updated);
                                    }}
                                    className="flex-1"
                                />
                                <input
                                    type="text"
                                    placeholder="Expected behavior (e.g., raise error)"
                                    value={c.expected}
                                    onChange={(e) => {
                                        const updated = [...invalidCases];
                                        updated[i].expected = e.target.value;
                                        setInvalidCases(updated);
                                    }}
                                    className="flex-1"
                                />
                                {invalidCases.length > 1 && (
                                    <button onClick={() => removeInvalidCase(i)} className="text-red-400 hover:text-red-300">
                                        <X className="w-5 h-5" />
                                    </button>
                                )}
                            </div>
                        ))}
                        <button onClick={addInvalidCase} className="btn-secondary text-sm flex items-center gap-2">
                            <Plus className="w-4 h-4" /> Add Invalid Case
                        </button>
                    </div>

                    <div>
                        <label className="block text-sm font-semibold mb-2">Security Constraints</label>
                        <div className="flex flex-wrap gap-4">
                            {constraintOptions.map((opt) => (
                                <label key={opt} className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={constraints.includes(opt)}
                                        onChange={(e) => {
                                            setConstraints(e.target.checked
                                                ? [...constraints, opt]
                                                : constraints.filter(c => c !== opt)
                                            );
                                        }}
                                        className="w-4 h-4"
                                    />
                                    <span className="text-sm">{opt.replace(/_/g, ' ')}</span>
                                </label>
                            ))}
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-semibold mb-2">Side Effects</label>
                        <div className="flex flex-wrap gap-4">
                            {sideEffectOptions.map((opt) => (
                                <label key={opt} className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={sideEffects.includes(opt)}
                                        onChange={(e) => {
                                            setSideEffects(e.target.checked
                                                ? [...sideEffects, opt]
                                                : sideEffects.filter(s => s !== opt)
                                            );
                                        }}
                                        className="w-4 h-4"
                                    />
                                    <span className="text-sm">{opt.replace(/_/g, ' ')}</span>
                                </label>
                            ))}
                        </div>
                    </div>

                    {error && (
                        <div className="p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    <div className="flex gap-4">
                        <button
                            onClick={handleSubmit}
                            disabled={loading || !purpose}
                            className="btn-primary flex-1 flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Submitting...
                                </>
                            ) : (
                                'Submit Intent & Generate Fix'
                            )}
                        </button>
                        <button onClick={() => router.back()} className="btn-secondary">
                            Back
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function IntentPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
            </div>
        }>
            <IntentContent />
        </Suspense>
    );
}
