import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { AppInitProvider } from './contexts/AppInitContext';
import './index.css';

const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);
root.render(
  <React.StrictMode>
    <AppInitProvider>
      <App />
    </AppInitProvider>
  </React.StrictMode>
);
