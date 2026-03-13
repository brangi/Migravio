export default function AttorneysLoading() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header skeleton */}
        <div className="mb-8">
          <div className="h-8 w-56 animate-pulse rounded bg-gray-200"></div>
          <div className="mt-2 h-4 w-96 animate-pulse rounded bg-gray-200"></div>
        </div>

        {/* Attorney cards skeleton */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
            >
              {/* Avatar */}
              <div className="mx-auto h-20 w-20 animate-pulse rounded-full bg-gray-200"></div>

              {/* Name */}
              <div className="mt-4 h-6 w-3/4 animate-pulse rounded bg-gray-200 mx-auto"></div>

              {/* Specialty */}
              <div className="mt-2 h-4 w-1/2 animate-pulse rounded bg-gray-200 mx-auto"></div>

              {/* Languages */}
              <div className="mt-4 flex justify-center gap-2">
                <div className="h-6 w-16 animate-pulse rounded-full bg-gray-200"></div>
                <div className="h-6 w-16 animate-pulse rounded-full bg-gray-200"></div>
              </div>

              {/* States */}
              <div className="mt-3 h-4 w-2/3 animate-pulse rounded bg-gray-200 mx-auto"></div>

              {/* Button */}
              <div className="mt-6 h-10 w-full animate-pulse rounded-lg bg-gray-200"></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
