import { Logo } from '@/components/logo';

export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface">
      <div className="text-center">
        <div className="mb-4 flex justify-center">
          <Logo size="md" variant="icon" className="animate-pulse" />
        </div>
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent"></div>
      </div>
    </div>
  );
}
