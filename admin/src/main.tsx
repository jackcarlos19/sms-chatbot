import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createRouter, RouterProvider } from '@tanstack/react-router'
import { setRedirectOnUnauthorized } from './lib/api'
import { routeTree } from './routeTree.gen'
import './index.css'

const router = createRouter({
  routeTree,
  basepath: '/admin',
})

setRedirectOnUnauthorized(() => {
  router.navigate({ to: '/sign-in' })
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
)
