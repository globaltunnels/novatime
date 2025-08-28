import React from 'react'

function App() {
  return (
    <div className="min-h-screen bg-bg text-text">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-primary mb-4">
            NovaTime
          </h1>
          <p className="text-lg text-text-muted">
            AI-first time tracking and project management platform
          </p>
        </header>
        
        <main className="max-w-4xl mx-auto">
          <div className="card">
            <h2 className="text-2xl font-semibold mb-4">Welcome to NovaTime</h2>
            <p className="text-text-muted mb-6">
              Your unified platform for time tracking, task management, and team collaboration.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="card">
                <h3 className="text-lg font-semibold mb-2 text-time-active">
                  ⏱️ Time Tracking
                </h3>
                <p className="text-sm text-text-muted">
                  Smart timers with AI-powered timesheet generation
                </p>
              </div>
              
              <div className="card">
                <h3 className="text-lg font-semibold mb-2 text-primary">
                  📋 Task Management
                </h3>
                <p className="text-sm text-text-muted">
                  Kanban boards and project timelines with AI insights
                </p>
              </div>
              
              <div className="card">
                <h3 className="text-lg font-semibold mb-2 text-success">
                  🤖 AI Assistant
                </h3>
                <p className="text-sm text-text-muted">
                  Chat with @ai for smart suggestions and automation
                </p>
              </div>
            </div>
            
            <div className="mt-8 flex gap-4 justify-center">
              <button className="btn btn-primary">
                Get Started
              </button>
              <button className="btn btn-secondary">
                Learn More
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App