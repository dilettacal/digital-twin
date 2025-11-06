import Twin from '@/components/twin';
import { LargeAvatar } from '@/components/avatar';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header with Avatar */}
          <div className="flex flex-col items-center mb-8">
            <div className="mb-4">
              <LargeAvatar src="/avatar.png" alt="Diletta" fallbackText="DC" />
            </div>
            <h1 className="text-5xl font-bold text-center text-gray-800 mb-2 bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Talk to Luna
            </h1>
            <p className="text-center text-gray-600 text-lg mb-2">
             Diletta's Professional Digital Twin
            </p>
            <p className="text-center text-gray-500 text-sm">
              Chat with Luna to learn about Diletta's professional background and experience
            </p>
          </div>

          <div className="h-[600px]">
            <Twin />
          </div>

          <footer className="mt-8 text-center text-sm text-gray-500">
            <p>&copy; {new Date().getFullYear()} Diletta Calussi. All rights reserved.</p>
          </footer>
        </div>
      </div>
    </main>
  );
}