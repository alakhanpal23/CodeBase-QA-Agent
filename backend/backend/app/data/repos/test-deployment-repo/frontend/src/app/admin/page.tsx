'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Activity, 
  Database, 
  Clock, 
  Users, 
  Zap, 
  AlertTriangle, 
  CheckCircle, 
  TrendingUp,
  Server,
  Brain,
  Shield,
  RefreshCw
} from 'lucide-react';

interface SystemStats {
  status: 'healthy' | 'warning' | 'error';
  uptime: number;
  totalRepositories: number;
  totalFiles: number;
  totalChunks: number;
  avgQueryLatency: number;
  embeddingMode: string;
  memoryUsage: number;
  diskUsage: number;
  requestsPerMinute: number;
  errorRate: number;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchStats = async () => {
    try {
      setLoading(true);
      
      // Fetch health status
      const healthResponse = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/health`);
      const healthData = await healthResponse.json();
      
      // Fetch system stats
      const statsResponse = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/stats`);
      const statsData = await statsResponse.json();
      
      // Mock additional system metrics (in production, these would come from monitoring)
      const systemStats: SystemStats = {
        status: healthData.ok ? 'healthy' : 'error',
        uptime: Date.now() - (healthData.timestamp * 1000),
        totalRepositories: statsData.total_repositories || 0,
        totalFiles: statsData.total_files || 0,
        totalChunks: statsData.total_chunks || 0,
        avgQueryLatency: Math.random() * 500 + 100,
        embeddingMode: 'auto',
        memoryUsage: Math.random() * 80 + 10,
        diskUsage: Math.random() * 60 + 20,
        requestsPerMinute: Math.floor(Math.random() * 100 + 10),
        errorRate: Math.random() * 5
      };
      
      setStats(systemStats);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      setStats({
        status: 'error',
        uptime: 0,
        totalRepositories: 0,
        totalFiles: 0,
        totalChunks: 0,
        avgQueryLatency: 0,
        embeddingMode: 'unknown',
        memoryUsage: 0,
        diskUsage: 0,
        requestsPerMinute: 0,
        errorRate: 100
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-5 h-5" />;
      case 'warning': return <AlertTriangle className="w-5 h-5" />;
      case 'error': return <AlertTriangle className="w-5 h-5" />;
      default: return <Activity className="w-5 h-5" />;
    }
  };

  const formatUptime = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ${hours % 24}h`;
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  if (loading && !stats) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading system dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">System Dashboard</h1>
              <p className="text-gray-600 mt-1">Monitor system health and performance</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-sm text-gray-500">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </div>
              <Button onClick={fetchStats} disabled={loading} size="sm">
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <Card className="border-l-4 border-l-blue-500">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {getStatusIcon(stats?.status || 'error')}
                  <div>
                    <CardTitle>System Status</CardTitle>
                    <CardDescription>Overall system health and availability</CardDescription>
                  </div>
                </div>
                <Badge className={getStatusColor(stats?.status || 'error')}>
                  {stats?.status?.toUpperCase() || 'UNKNOWN'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {stats ? formatUptime(stats.uptime) : '0s'}
                  </div>
                  <div className="text-sm text-gray-600">Uptime</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {stats?.requestsPerMinute || 0}
                  </div>
                  <div className="text-sm text-gray-600">Requests/min</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {stats?.avgQueryLatency.toFixed(0) || 0}ms
                  </div>
                  <div className="text-sm text-gray-600">Avg Latency</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {stats?.errorRate.toFixed(1) || 0}%
                  </div>
                  <div className="text-sm text-gray-600">Error Rate</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Repository Data</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Repositories</span>
                  <span className="font-semibold">{stats?.totalRepositories || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Files Indexed</span>
                  <span className="font-semibold">{stats?.totalFiles.toLocaleString() || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Code Chunks</span>
                  <span className="font-semibold">{stats?.totalChunks.toLocaleString() || 0}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Performance</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Query Latency</span>
                  <span className="font-semibold">{stats?.avgQueryLatency.toFixed(0) || 0}ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Memory Usage</span>
                  <span className="font-semibold">{stats?.memoryUsage.toFixed(1) || 0}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Disk Usage</span>
                  <span className="font-semibold">{stats?.diskUsage.toFixed(1) || 0}%</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">AI System</CardTitle>
              <Brain className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Embedding Mode</span>
                  <Badge variant="secondary">{stats?.embeddingMode || 'unknown'}</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Model Status</span>
                  <Badge className="bg-green-100 text-green-800">Active</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Vector Index</span>
                  <Badge className="bg-blue-100 text-blue-800">Optimized</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}