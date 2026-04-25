import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import DemoApp from './DemoApp'
import './index.css'

const isDemo = window.location.hash === '#demo';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {isDemo ? <DemoApp /> : <App />}
  </React.StrictMode>,
)
