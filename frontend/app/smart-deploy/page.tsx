'use client';

import { SmartDeployDashboard } from '@/components/smart-deploy/SmartDeployDashboard';
import { useAuthGuard } from '@/hooks/use-auth-guard';
import { Skeleton } from '@/components/ui/skeleton';

export default function SmartDeployPage() {
  const { isAuthenticated, loading } = useAuthGuard('/login');

  // Show loading skeleton while checking authentication
  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="space-y-6">
          <Skeleton className="w-64 h-8" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Skeleton className="h-48" />
            <Skeleton className="h-48" />
            <Skeleton className="h-48" />
          </div>
          <Skeleton className="w-full h-96" />
        </div>
      </div>
    );
  }

  // Don't render content if not authenticated (guard will redirect)
  if (!isAuthenticated) {
    return null;
  }

  return <SmartDeployDashboard />;
}
