export default function DashboardLoading() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header skeleton */}
        <div className="mb-8">
          <div className="h-8 w-48 animate-pulse rounded bg-gray-200"></div>
          <div className="mt-2 h-4 w-64 animate-pulse rounded bg-gray-200"></div>
        </div>

        {/* Grid skeleton */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* Visa status card */}
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <div className="h-6 w-32 animate-pulse rounded bg-gray-200"></div>
            <div className="mt-4 h-4 w-full animate-pulse rounded bg-gray-200"></div>
            <div className="mt-2 h-4 w-3/4 animate-pulse rounded bg-gray-200"></div>
            <div className="mt-4 h-24 w-full animate-pulse rounded bg-gray-200"></div>
          </div>

          {/* Subscription card */}
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <div className="h-6 w-32 animate-pulse rounded bg-gray-200"></div>
            <div className="mt-4 h-4 w-full animate-pulse rounded bg-gray-200"></div>
            <div className="mt-2 h-4 w-2/3 animate-pulse rounded bg-gray-200"></div>
            <div className="mt-4 h-10 w-full animate-pulse rounded bg-gray-200"></div>
          </div>

          {/* Recent chats card */}
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <div className="h-6 w-32 animate-pulse rounded bg-gray-200"></div>
            <div className="mt-4 space-y-3">
              <div className="h-4 w-full animate-pulse rounded bg-gray-200"></div>
              <div className="h-4 w-5/6 animate-pulse rounded bg-gray-200"></div>
              <div className="h-4 w-4/6 animate-pulse rounded bg-gray-200"></div>
            </div>
          </div>
        </div>

        {/* Action items skeleton */}
        <div className="mt-8 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div className="h-6 w-40 animate-pulse rounded bg-gray-200"></div>
          <div className="mt-4 space-y-3">
            <div className="h-4 w-full animate-pulse rounded bg-gray-200"></div>
            <div className="h-4 w-4/5 animate-pulse rounded bg-gray-200"></div>
            <div className="h-4 w-3/5 animate-pulse rounded bg-gray-200"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
