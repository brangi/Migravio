import { Link } from '@/i18n/navigation';
import { Logo } from '@/components/logo';
import { Button } from '@/components/button';

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-4">
      <div className="text-center">
        <div className="mb-6 flex justify-center">
          <Logo size="lg" variant="icon" />
        </div>
        <h1 className="text-6xl font-[var(--font-display)] font-bold text-primary-600">404</h1>
        <h2 className="mt-4 text-2xl font-[var(--font-display)] font-semibold text-text-primary">
          Page not found
        </h2>
        <p className="mt-2 text-text-secondary">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="mt-6">
          <Link href="/">
            <Button variant="primary" size="md">
              Go back home
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
