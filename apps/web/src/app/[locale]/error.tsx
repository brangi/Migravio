'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/navigation';
import { useEffect } from 'react';
import { Button } from '@/components/button';
import { AlertTriangle } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const t = useTranslations('common');

  useEffect(() => {
    // Log the error to an error reporting service
    console.error('Error boundary caught:', error);
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-4">
      <div className="text-center">
        <div className="mb-6 flex justify-center">
          <AlertTriangle className="h-16 w-16 text-danger" strokeWidth={1.5} />
        </div>
        <h1 className="text-3xl font-[var(--font-display)] font-bold text-text-primary">
          {t('error')}
        </h1>
        <p className="mt-2 text-text-secondary">
          {t('errorDescription')}
        </p>
        <div className="mt-6 flex items-center justify-center gap-4">
          <Button
            onClick={reset}
            variant="primary"
            size="md"
          >
            {t('tryAgain')}
          </Button>
          <Link href="/">
            <Button
              variant="secondary"
              size="md"
            >
              {t('goHome')}
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
