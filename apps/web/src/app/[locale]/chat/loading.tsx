export default function ChatLoading() {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar skeleton */}
      <div className="hidden w-64 border-r border-gray-200 bg-white p-4 md:block">
        <div className="h-10 w-full animate-pulse rounded bg-gray-200"></div>
        <div className="mt-4 space-y-2">
          <div className="h-16 w-full animate-pulse rounded bg-gray-200"></div>
          <div className="h-16 w-full animate-pulse rounded bg-gray-200"></div>
          <div className="h-16 w-full animate-pulse rounded bg-gray-200"></div>
        </div>
      </div>

      {/* Main chat area skeleton */}
      <div className="flex flex-1 flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 bg-white p-4">
          <div className="h-6 w-48 animate-pulse rounded bg-gray-200"></div>
        </div>

        {/* Messages area */}
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          <div className="flex justify-start">
            <div className="h-20 w-3/4 animate-pulse rounded-lg bg-gray-200"></div>
          </div>
          <div className="flex justify-end">
            <div className="h-16 w-2/3 animate-pulse rounded-lg bg-gray-200"></div>
          </div>
          <div className="flex justify-start">
            <div className="h-24 w-4/5 animate-pulse rounded-lg bg-gray-200"></div>
          </div>
        </div>

        {/* Input area */}
        <div className="border-t border-gray-200 bg-white p-4">
          <div className="h-12 w-full animate-pulse rounded-lg bg-gray-200"></div>
        </div>
      </div>
    </div>
  );
}
