import Link from 'next/link';
import { Database, MessageSquare, Zap, Shield, Code, Brain, ArrowRight, Github, Star } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">CodeBase QA</span>
              <Badge variant="secondary" className="ml-2">v1.0</Badge>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" asChild>
                <a href="https://github.com/alakhanpal23/CodeBase-QA-Agent" target="_blank" rel="noopener noreferrer">
                  <Github className="w-4 h-4 mr-2" />
                  GitHub
                </a>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <div className="inline-flex items-center px-4 py-2 bg-blue-100 text-blue-800 rounded-full text-sm font-medium mb-6">
            <Zap className="w-4 h-4 mr-2" />
            AI-Powered Code Intelligence
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
            Ask Questions About
            <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent block">
              Your Codebase
            </span>
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8 leading-relaxed">
            Get intelligent answers with code snippets, citations, and context. 
            Transform how you understand and navigate your repositories.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" asChild className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700">
              <Link href="/chat">
                Start Asking Questions
                <ArrowRight className="w-4 h-4 ml-2" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/repos">
                <Database className="w-4 h-4 mr-2" />
                Manage Repositories
              </Link>
            </Button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <Brain className="w-6 h-6 text-blue-600" />
              </div>
              <CardTitle>Intelligent Search</CardTitle>
              <CardDescription>
                Vector-based semantic search through your entire codebase with AI-powered understanding.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                <Code className="w-6 h-6 text-green-600" />
              </div>
              <CardTitle>Code Snippets</CardTitle>
              <CardDescription>
                Get relevant code snippets with syntax highlighting and surrounding context for better understanding.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                <Shield className="w-6 h-6 text-purple-600" />
              </div>
              <CardTitle>Secure & Fast</CardTitle>
              <CardDescription>
                Enterprise-grade security with blazing-fast performance. Your code stays private and secure.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>

        {/* Main Actions */}
        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <Card className="group border-0 shadow-lg hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100">
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="p-3 bg-blue-100 rounded-lg group-hover:bg-blue-200 transition-colors">
                    <Database className="w-6 h-6 text-blue-600" />
                  </div>
                  <CardTitle className="ml-4 text-xl">Repository Management</CardTitle>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors" />
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-base mb-4">
                Add repositories from GitHub URLs, monitor ingestion status, and manage your codebase collection with ease.
              </CardDescription>
              <div className="flex flex-wrap gap-2 mb-4">
                <Badge variant="secondary">GitHub Integration</Badge>
                <Badge variant="secondary">Auto-Indexing</Badge>
                <Badge variant="secondary">Real-time Status</Badge>
              </div>
              <Button asChild className="w-full">
                <Link href="/repos">
                  Manage Repositories
                  <Database className="w-4 h-4 ml-2" />
                </Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="group border-0 shadow-lg hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-green-50 to-emerald-50 hover:from-green-100 hover:to-emerald-100">
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="p-3 bg-green-100 rounded-lg group-hover:bg-green-200 transition-colors">
                    <MessageSquare className="w-6 h-6 text-green-600" />
                  </div>
                  <CardTitle className="ml-4 text-xl">AI-Powered Chat</CardTitle>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-green-600 transition-colors" />
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-base mb-4">
                Ask natural language questions about your codebase and get intelligent answers with code snippets and citations.
              </CardDescription>
              <div className="flex flex-wrap gap-2 mb-4">
                <Badge variant="secondary">Natural Language</Badge>
                <Badge variant="secondary">Code Citations</Badge>
                <Badge variant="secondary">Context Aware</Badge>
              </div>
              <Button asChild className="w-full">
                <Link href="/chat">
                  Start Chatting
                  <MessageSquare className="w-4 h-4 ml-2" />
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-white/80 backdrop-blur-sm mt-20">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="flex items-center space-x-2 mb-4 md:mb-0">
              <div className="w-6 h-6 bg-gradient-to-br from-blue-600 to-indigo-600 rounded flex items-center justify-center">
                <Brain className="w-4 h-4 text-white" />
              </div>
              <span className="font-semibold text-gray-900">CodeBase QA Agent</span>
            </div>
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span>Built with ❤️ for developers</span>
              <div className="flex items-center space-x-1">
                <Star className="w-4 h-4 text-yellow-500" />
                <span>Open Source</span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}