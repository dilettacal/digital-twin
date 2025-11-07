'use client';

import Twin from '@/components/twin';
import { LargeAvatar } from '@/components/avatar';
import { ThemeToggle } from '@/components/theme-toggle';
import { SignInButton, SignUpButton, UserButton, useUser } from '@clerk/nextjs';

export default function Home() {
  const { isSignedIn, user } = useUser();

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 transition-colors duration-200 relative">
      {/* UI chrome */}
      <div className="absolute top-4 left-4 right-4 sm:left-8 sm:right-8 z-20 flex items-center justify-between gap-3">
        <ThemeToggle />
        {isSignedIn ? (
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-700 dark:text-gray-300">
              {user?.firstName || user?.emailAddresses[0]?.emailAddress}
            </span>
            <UserButton afterSignOutUrl="/" />
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <SignInButton mode="modal">
              <button className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors">
                Sign In
              </button>
            </SignInButton>
            <SignUpButton mode="modal">
              <button className="px-4 py-2 text-sm font-medium bg-gradient-to-r from-teal-600 to-emerald-600 text-white rounded-lg hover:from-teal-700 hover:to-emerald-700 transition-all shadow-sm">
                Sign Up
              </button>
            </SignUpButton>
          </div>
        )}
      </div>
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
            {isSignedIn ? (
              <Twin />
            ) : (
              <div className="h-full w-full rounded-3xl border border-dashed border-slate-300 dark:border-slate-700 bg-white/70 dark:bg-gray-900/40 backdrop-blur flex flex-col items-center justify-center text-center px-8">
                <h2 className="text-2xl font-semibold text-slate-800 dark:text-slate-100 mb-3">
                  Sign in to chat with Luna
                </h2>
                <p className="text-slate-600 dark:text-slate-300 mb-6 max-w-md">
                  Create an account or sign in to start a conversation. We use Clerk authentication to keep your sessions secure and personalised.
                </p>
                <div className="flex flex-col sm:flex-row gap-3">
                  <SignInButton mode="modal">
                    <button className="px-5 py-2.5 text-sm font-medium text-white bg-slate-900 dark:bg-slate-100 dark:text-slate-900 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                      Sign In
                    </button>
                  </SignInButton>
                  <SignUpButton mode="modal">
                    <button className="px-5 py-2.5 text-sm font-medium bg-gradient-to-r from-teal-600 to-emerald-600 text-white rounded-lg shadow-sm hover:shadow-md transition-shadow">
                      Create Account
                    </button>
                  </SignUpButton>
                </div>
              </div>
            )}
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