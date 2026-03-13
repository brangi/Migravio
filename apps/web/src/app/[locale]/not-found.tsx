import { Link } from '@/i18n/navigation';

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-blue-700">404</h1>
        <h2 className="mt-4 text-2xl font-semibold text-gray-900">
          Page not found
        </h2>
        <p className="mt-2 text-gray-600">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link
          href="/"
          className="mt-6 inline-block rounded-lg bg-blue-700 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-800"
        >
          Go back home
        </Link>
      </div>
    </div>
  );
}
