import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/navigation';
import { Logo } from '@/components/logo';
import { Button } from '@/components/button';

export default function NotFound() {
  const t = useTranslations('common');

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-4">
      <div className="text-center">
        <div className="mb-6 flex justify-center">
          <Logo size="lg" variant="icon" />
        </div>
        <h1 className="text-6xl font-[var(--font-display)] font-bold text-primary-600">404</h1>
        <h2 className="mt-4 text-2xl font-[var(--font-display)] font-semibold text-text-primary">
          {t('notFoundTitle')}
        </h2>
        <p className="mt-2 text-text-secondary">
          {t('notFoundDescription')}
        </p>
        <div className="mt-6">
          <Link href="/">
            <Button variant="primary" size="md">
              {t('goHome')}
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
