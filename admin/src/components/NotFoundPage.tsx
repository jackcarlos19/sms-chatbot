import { Link } from '@tanstack/react-router'

export function NotFoundPage() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-6 bg-background px-4">
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold tracking-tight text-foreground">404</h1>
        <p className="text-muted-foreground">
          This page doesn’t exist or you don’t have access to it.
        </p>
      </div>
      <Link
        to="/"
        className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90"
      >
        Go to Dashboard
      </Link>
    </div>
  )
}
