// Test modal to debug the framework selector
'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Server, Zap, Cloud } from 'lucide-react';

export function TestFrameworkModal() {
  const [framework, setFramework] = useState('auto-detect');

  return (
    <div className="p-4 border rounded-lg bg-white">
      <h3 className="text-lg font-semibold mb-4">Framework Selector Test</h3>
      
      <div className="space-y-2 max-w-md">
        <Label htmlFor="framework_type" className="flex items-center gap-2">
          <Server className="h-4 w-4" />
          Framework Type
        </Label>
        <Select value={framework} onValueChange={setFramework}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="auto-detect">
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4" />
                Auto-detect from repository
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
        
        <p className="text-sm text-gray-600 mt-2">
          Selected: {framework}
        </p>
        
        <p className="text-sm text-gray-600">
          {framework === 'auto-detect' 
            ? 'Framework will be detected from your GitHub repository' 
            : '☁️ Static/SPA frameworks deploy to CloudFront + S3'
          }
        </p>
      </div>
    </div>
  );
}
