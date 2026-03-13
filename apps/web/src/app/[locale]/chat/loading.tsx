import { Skeleton } from "@/components/skeleton";

export default function ChatLoading() {
  return (
    <div className="flex h-screen bg-surface">
      {/* Sidebar skeleton */}
      <div className="hidden w-64 border-r border-border bg-surface p-4 md:block">
        <Skeleton className="h-10 w-full mb-4" />
        <div className="space-y-2">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      </div>

      {/* Main chat area skeleton */}
      <div className="flex flex-1 flex-col">
        {/* Header */}
        <div className="border-b border-border bg-surface p-4">
          <Skeleton className="h-6 w-48" />
        </div>

        {/* Messages area */}
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          <div className="flex justify-start">
            <Skeleton className="h-20 w-3/4 rounded-lg" />
          </div>
          <div className="flex justify-end">
            <Skeleton className="h-16 w-2/3 rounded-lg" />
          </div>
          <div className="flex justify-start">
            <Skeleton className="h-24 w-4/5 rounded-lg" />
          </div>
        </div>

        {/* Input area */}
        <div className="border-t border-border bg-surface p-4">
          <Skeleton className="h-12 w-full rounded-lg" />
        </div>
      </div>
    </div>
  );
}
