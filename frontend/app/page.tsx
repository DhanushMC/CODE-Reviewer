'use client';

import Link from 'next/link';
import { Shield, Lock, CheckCircle, Zap, Code, TestTube } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Hero Section */}
      <main className="flex-1 flex items-center justify-center px-4 py-20">
        <div className="max-w-6xl mx-auto text-center">
          {/* Animated Icon */}
          <div className="mb-8 flex justify-center">
            <div className="glass rounded-full p-6 animate-float">
              <Shield className="w-20 h-20 text-indigo-400" />
            </div>
          </div>

          {/* Title */}
          <h1 className="text-6xl font-bold mb-6">
            <span className="gradient-text">Secure Code Reviewer</span>
          </h1>

          <p className="text-2xl text-slate-300 mb-4">
            Intent-Aware AI-Driven Vulnerability Detection & Correction
          </p>

          <p className="text-lg text-slate-400 max-w-3xl mx-auto mb-12">
            Professional ML-based code security analysis using CodeBERT, with intelligent
            vulnerability detection, RAG-enhanced explanations, and intent-aware automated fixing.
          </p>

          {/* CTA Button */}
          <Link href="/analyze">
            <button className="btn-primary text-xl px-10 py-4">
              Start Code Review →
            </button>
          </Link>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-8 mt-20">
            <div className="glass rounded-2xl p-8 hover:scale-105 transition-transform duration-300">
              <div className="mb-4 flex justify-center">
                <Code className="w-12 h-12 text-indigo-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">ML-Based Detection</h3>
              <p className="text-slate-400">
                CodeBERT neural network with rule-based refinement for accurate vulnerability detection
              </p>
            </div>

            <div className="glass rounded-2xl p-8 hover:scale-105 transition-transform duration-300">
              <div className="mb-4 flex justify-center">
                <Lock className="w-12 h-12 text-purple-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Intent-Aware Fixing</h3>
              <p className="text-slate-400">
                Captures developer intent to generate fixes that preserve logic and behavior
              </p>
            </div>

            <div className="glass rounded-2xl p-8 hover:scale-105 transition-transform duration-300">
              <div className="mb-4 flex justify-center">
                <TestTube className="w-12 h-12 text-pink-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Sandbox Validation</h3>
              <p className="text-slate-400">
                Docker-isolated test execution ensures fixes work correctly and securely
              </p>
            </div>
          </div>

          {/* Supported Vulnerabilities */}
          <div className="mt-20">
            <h2 className="text-3xl font-bold mb-8 gradient-text">Detects 7+ Vulnerability Types</h2>
            <div className="flex flex-wrap justify-center gap-4">
              {[
                'SQL Injection',
                'XSS',
                'Command Injection',
                'Path Traversal',
                'Hardcoded Secrets',
                'Weak Cryptography',
                'XXE'
              ].map((vuln) => (
                <div key={vuln} className="glass rounded-full px-6 py-3 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span className="font-medium">{vuln}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Supported Languages */}
          <div className="mt-16">
            <h3 className="text-2xl font-bold mb-6">Supports Top 7 Languages</h3>
            <div className="flex flex-wrap justify-center gap-3">
              {['Python', 'JavaScript', 'Java', 'C++', 'C#', 'Go', 'PHP'].map((lang) => (
                <span key={lang} className="bg-slate-700/50 rounded-lg px-5 py-2 font-mono text-sm">
                  {lang}
                </span>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center py-8 text-slate-500">
        <p>Intent-Aware AI Secure Code Reviewer | SEM-8 Final Year Project</p>
      </footer>
    </div>
  );
}
