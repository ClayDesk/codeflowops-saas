// Repository Upload - File upload component for project repositories
'use client';

import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  Upload, 
  FileText, 
  FolderOpen, 
  CheckCircle, 
  AlertCircle,
  X,
  Github,
  Download,
  Zap
} from 'lucide-react';
import { useDropzone } from 'react-dropzone';

interface UploadedFile {
  name: string;
  size: number;
  type: string;
  lastModified: number;
}

interface AnalysisResult {
  project_type: string;
  framework: string;
  languages: string[];
  dependencies: string[];
  recommendations: string[];
}

interface RepositoryUploadProps {
  onUploadComplete: () => void;
}

export function RepositoryUpload({ onUploadComplete }: RepositoryUploadProps) {
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tempPath, setTempPath] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      if (file.type !== 'application/zip' && !file.name.endsWith('.zip')) {
        setError('Please upload a ZIP file containing your project');
        return;
      }

      if (file.size > 100 * 1024 * 1024) { // 100MB limit
        setError('File size must be less than 100MB');
        return;
      }

      setError(null);
      setUploadedFile({
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified
      });
      
      uploadFile(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/zip': ['.zip']
    },
    maxFiles: 1,
    disabled: isUploading || isAnalyzing
  });

  const uploadFile = async (file: File) => {
    setIsUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await fetch('/api/v1/smart-deploy/upload-repository', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (response.ok) {
        const result = await response.json();
        setTempPath(result.temp_path);
        
        // Start analysis after successful upload
        setTimeout(() => {
          analyzeRepository(result.temp_path);
        }, 500);
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      setError('Failed to upload file. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const analyzeRepository = async (tempPath: string) => {
    setIsAnalyzing(true);
    
    try {
      // Simulate AI analysis - in production this would call the actual API
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Mock analysis result
      const mockResult: AnalysisResult = {
        project_type: 'spa',
        framework: 'React',
        languages: ['TypeScript', 'JavaScript', 'CSS'],
        dependencies: ['react', 'next.js', 'tailwindcss', 'axios'],
        recommendations: [
          'Enable SSL/TLS for security',
          'Use CDN for global performance',
          'Implement auto-scaling for high traffic',
          'Add monitoring and alerting',
          'Set up automated backups'
        ]
      };
      
      setAnalysisResult(mockResult);
    } catch (error) {
      console.error('Analysis error:', error);
      setError('Failed to analyze repository. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const handleCreateDeployment = () => {
    if (analysisResult && uploadedFile) {
      // This would typically open the create deployment modal with pre-filled data
      onUploadComplete();
    }
  };

  const resetUpload = () => {
    setUploadedFile(null);
    setUploadProgress(0);
    setIsUploading(false);
    setIsAnalyzing(false);
    setAnalysisResult(null);
    setError(null);
    setTempPath(null);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5 text-blue-500" />
            Repository Upload
          </CardTitle>
          <CardDescription>
            Upload your project repository as a ZIP file for AI-powered analysis and infrastructure generation
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!uploadedFile ? (
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-300 hover:border-gray-400'
              } ${isUploading || isAnalyzing ? 'pointer-events-none opacity-50' : ''}`}
            >
              <input {...getInputProps()} />
              <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {isDragActive ? 'Drop your ZIP file here' : 'Upload Repository'}
              </h3>
              <p className="text-gray-600 mb-4">
                Drag and drop your project ZIP file, or click to browse
              </p>
              <Button variant="outline">
                Choose File
              </Button>
              <p className="text-sm text-gray-500 mt-3">
                Maximum file size: 100MB. ZIP files only.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* File Info */}
              <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                <FolderOpen className="h-8 w-8 text-blue-500" />
                <div className="flex-1">
                  <h4 className="font-medium">{uploadedFile.name}</h4>
                  <p className="text-sm text-gray-600">
                    {formatFileSize(uploadedFile.size)} • {formatDate(uploadedFile.lastModified)}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={resetUpload}
                  disabled={isUploading || isAnalyzing}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {/* Upload Progress */}
              {isUploading && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Uploading...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <Progress value={uploadProgress} className="h-2" />
                </div>
              )}

              {/* Analysis Progress */}
              {isAnalyzing && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-blue-500 animate-pulse" />
                    <span className="text-sm font-medium">Analyzing repository structure...</span>
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-2 bg-blue-500 rounded-full animate-pulse" />
                        <span>Detecting project type and framework</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-2 bg-purple-500 rounded-full animate-pulse" />
                        <span>Analyzing dependencies and architecture</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-2 bg-purple-500 rounded-full animate-pulse" />
                        <span>Generating infrastructure recommendations</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Analysis Results */}
              {analysisResult && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="h-5 w-5" />
                    <span className="font-medium">Analysis Complete!</span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-lg">Project Details</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div>
                          <p className="text-sm font-medium text-gray-600">Project Type</p>
                          <p className="text-lg font-semibold capitalize">
                            {analysisResult.project_type.replace('_', ' ')}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-600">Framework</p>
                          <p className="text-lg font-semibold">{analysisResult.framework}</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-600">Languages</p>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {analysisResult.languages.map(lang => (
                              <span
                                key={lang}
                                className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                              >
                                {lang}
                              </span>
                            ))}
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-lg">Key Dependencies</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {analysisResult.dependencies.slice(0, 6).map(dep => (
                            <div key={dep} className="flex items-center gap-2">
                              <FileText className="h-4 w-4 text-gray-400" />
                              <span className="text-sm">{dep}</span>
                            </div>
                          ))}
                          {analysisResult.dependencies.length > 6 && (
                            <p className="text-sm text-gray-500">
                              +{analysisResult.dependencies.length - 6} more dependencies
                            </p>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-lg">Template Recommendations</CardTitle>
                      <CardDescription>
                        Smart Deploy suggests these infrastructure optimizations for your project
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {analysisResult.recommendations.map((rec, index) => (
                          <div key={index} className="flex items-start gap-2">
                            <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                            <span className="text-sm">{rec}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <div className="flex gap-3">
                    <Button onClick={handleCreateDeployment} className="flex items-center gap-2">
                      <Zap className="h-4 w-4" />
                      Create Smart Deployment
                    </Button>
                    <Button variant="outline" onClick={resetUpload}>
                      Upload Different Project
                    </Button>
                  </div>
                </div>
              )}

              {/* Error State */}
              {error && (
                <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                  <AlertCircle className="h-5 w-5" />
                  <span>{error}</span>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* GitHub Integration Option */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Github className="h-8 w-8 text-gray-700" />
              <div>
                <h3 className="font-medium">Connect GitHub Repository</h3>
                <p className="text-sm text-gray-600">
                  Or connect directly to a GitHub repository for automatic updates
                </p>
              </div>
            </div>
            <Button variant="outline" disabled>
              Connect GitHub
              <span className="ml-2 text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded">
                Coming Soon
              </span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
