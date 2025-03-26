import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';

// Components
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import SearchBar from './components/SearchBar';
import PropertyList from './components/PropertyList';
import PropertyMap from './components/PropertyMap';
import PropertyDetails from './components/PropertyDetails';
import SavedSearches from './components/SavedSearches';
import Analytics from './components/Analytics';

// Theme
import { ThemeProvider } from './contexts/ThemeContext';

const queryClient = new QueryClient();

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [view, setView] = useState('list'); // 'list' or 'map'
  
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <Router>
          <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            {/* Top Navigation */}
            <Navbar 
              onMenuClick={() => setSidebarOpen(!sidebarOpen)}
              onViewChange={setView}
              currentView={view}
            />
            
            {/* Main Layout */}
            <div className="flex h-[calc(100vh-64px)]">
              {/* Sidebar */}
              <Sidebar 
                isOpen={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
              />
              
              {/* Main Content */}
              <main className="flex-1 overflow-auto">
                <Routes>
                  <Route 
                    path="/" 
                    element={
                      <div className="p-4">
                        {/* Global Search */}
                        <SearchBar 
                          className="mb-4"
                          placeholder="Search properties, areas, or features..."
                        />
                        
                        {/* View Toggle */}
                        {view === 'list' ? (
                          <PropertyList />
                        ) : (
                          <PropertyMap />
                        )}
                      </div>
                    } 
                  />
                  
                  <Route 
                    path="/property/:id" 
                    element={<PropertyDetails />} 
                  />
                  
                  <Route 
                    path="/saved" 
                    element={<SavedSearches />} 
                  />
                  
                  <Route 
                    path="/analytics" 
                    element={<Analytics />} 
                  />
                </Routes>
              </main>
            </div>
          </div>
          
          {/* Toast Notifications */}
          <Toaster position="bottom-right" />
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
