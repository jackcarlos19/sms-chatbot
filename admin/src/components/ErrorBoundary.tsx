import { Component, type ReactNode } from 'react'
import { Card, CardContent } from './ui/Card'
import { Button } from './ui/Button'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: string
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: '' }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error: error.message }
  }

  render() {
    if (this.state.hasError) {
      return (
        <Card className="m-8">
          <CardContent className="p-8 text-center">
            <h2 className="mb-2 text-lg font-semibold text-destructive">Something went wrong</h2>
            <p className="mb-4 text-sm text-muted-foreground">{this.state.error}</p>
            <Button
              onClick={() => {
                this.setState({ hasError: false })
                window.location.reload()
              }}
            >
              Reload
            </Button>
          </CardContent>
        </Card>
      )
    }
    return this.props.children
  }
}
