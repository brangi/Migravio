import { Skeleton, SkeletonAvatar } from "@/components/skeleton";

export default function AttorneysLoading() {
  return (
    <div className="min-h-screen bg-surface py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header skeleton */}
        <div className="mb-8">
          <Skeleton className="h-8 w-56 mb-2" />
          <Skeleton className="h-4 w-96" />
        </div>

        {/* Attorney cards skeleton */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="rounded-lg border border-border bg-surface p-6 shadow-sm"
            >
              {/* Avatar */}
              <div className="flex justify-center mb-4">
                <SkeletonAvatar size="lg" />
              </div>

              {/* Name */}
              <Skeleton className="h-6 w-3/4 mx-auto mb-2" />

              {/* Specialty */}
              <Skeleton className="h-4 w-1/2 mx-auto mb-4" />

              {/* Languages */}
              <div className="flex justify-center gap-2 mb-3">
                <Skeleton className="h-6 w-16 rounded-full" />
                <Skeleton className="h-6 w-16 rounded-full" />
              </div>

              {/* States */}
              <Skeleton className="h-4 w-2/3 mx-auto mb-6" />

              {/* Button */}
              <Skeleton className="h-10 w-full rounded-lg" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
