'use client';

import Twin from '@/components/twin';
import { LargeAvatar } from '@/components/avatar';
import { ThemeToggle } from '@/components/theme-toggle';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 transition-colors duration-200">
      <ThemeToggle />
      <div className="container mx-auto px-4 py-12 sm:py-16">
        <div className="max-w-4xl mx-auto">
          {/* Header with Avatar */}
          <div className="flex flex-col items-center mb-12">
            <div className="mb-6">
              <LargeAvatar src="/avatar.png" alt="Diletta" fallbackText="DC" />
            </div>
            <h1 className="text-5xl sm:text-6xl font-bold text-center text-gray-900 dark:text-gray-50 mb-3 bg-gradient-to-r from-teal-600 via-emerald-600 to-cyan-600 dark:from-teal-400 dark:via-emerald-400 dark:to-cyan-400 bg-clip-text text-transparent">
              Talk to Luna
            </h1>
            <p className="text-center text-gray-700 dark:text-gray-300 text-xl font-medium mb-2">
              Diletta&apos;s Professional Digital Twin
            </p>
            <p className="text-center text-gray-600 dark:text-gray-400 text-base max-w-2xl">
              Chat with Luna to learn about Diletta&apos;s professional background, experience, and expertise
            </p>
          </div>

          {/* Chat Interface */}
          <div className="h-[650px] sm:h-[700px]">
            <Twin />
          </div>

          {/* Footer */}
          <footer className="mt-12 text-center text-sm text-gray-500 dark:text-gray-400">
            <p>&copy; {new Date().getFullYear()} Diletta Calussi. All rights reserved.</p>
          </footer>
        </div>
      </div>
    </main>
  );
}