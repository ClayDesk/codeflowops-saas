import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Eye, EyeOff, Key, AlertTriangle, CheckCircle } from 'lucide-react';

interface SimpleCredentialInputProps {
  onCredentialsValidated: (credentials: {
    access_key_id: string;
    secret_access_key: string;
    region: string;
  }) => void;
  onCancel?: () => void;
}

const SimpleCredentialInput: React.FC<SimpleCredentialInputProps> = ({ 
  onCredentialsValidated, 
  onCancel 
}) => {
  const [credentials, setCredentials] = useState({
    access_key_id: '',
    secret_access_key: '',
    region: 'us-east-1'
  });
  
  const [showSecret, setShowSecret] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    error?: string;
    permissions?: string[];
  } | null>(null);

  const handleInputChange = (field: string, value: string) => {
    setCredentials(prev => ({
      ...prev,
      [field]: value
    }));
    // Clear validation when user changes input
    if (validationResult) {
      setValidationResult(null);
    }
  };

  const validateAndProceed = async () => {
    if (!credentials.access_key_id || !credentials.secret_access_key) {
      setValidationResult({
        valid: false,
        error: 'Please provide both Access Key ID and Secret Access Key'
      });
      return;
    }

    setIsValidating(true);
    try {
      const response = await fetch('http://localhost:8000/api/validate-credentials', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          aws_access_key: credentials.access_key_id,
          aws_secret_key: credentials.secret_access_key,
          aws_region: credentials.region || 'us-east-1'
        })
      });

      const result = await response.json();
      
      if (result.valid) {
        setValidationResult({
          valid: true,
          permissions: result.permissions || []
        });
        
        // Immediately pass validated credentials to parent
        onCredentialsValidated(credentials);
      } else {
        setValidationResult({
          valid: false,
          error: result.error || 'Credential validation failed'
        });
      }
    } catch (error) {
      console.error('Validation failed:', error);
      setValidationResult({
        valid: false,
        error: 'Failed to validate credentials - please check your network connection'
      });
    } finally {
      setIsValidating(false);
    }
  };

  const isFormValid = credentials.access_key_id && credentials.secret_access_key;

  return (
    <div className="max-w-2xl mx-auto p-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="w-5 h-5" />
            AWS Credentials
          </CardTitle>
          <p className="text-gray-600 text-sm">
            Enter your AWS credentials for deployment. They will be used immediately and not stored.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="access_key_id">AWS Access Key ID</Label>
            <Input
              id="access_key_id"
              value={credentials.access_key_id}
              onChange={(e) => handleInputChange('access_key_id', e.target.value)}
              placeholder="AKIA..."
              className="mt-1"
            />
          </div>

          <div>
            <div className="flex items-center justify-between">
              <Label htmlFor="secret_access_key">AWS Secret Access Key</Label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setShowSecret(!showSecret)}
              >
                {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                {showSecret ? 'Hide' : 'Show'}
              </Button>
            </div>
            <Input
              id="secret_access_key"
              type={showSecret ? 'text' : 'password'}
              value={credentials.secret_access_key}
              onChange={(e) => handleInputChange('secret_access_key', e.target.value)}
              placeholder="Enter secret access key"
              className="mt-1"
            />
          </div>

          <div>
            <Label htmlFor="region">AWS Region</Label>
            <select
              id="region"
              value={credentials.region}
              onChange={(e) => handleInputChange('region', e.target.value)}
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="us-east-1">US East (N. Virginia)</option>
              <option value="us-west-2">US West (Oregon)</option>
              <option value="eu-west-1">Europe (Ireland)</option>
              <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
              <option value="ap-northeast-1">Asia Pacific (Tokyo)</option>
            </select>
          </div>

          {validationResult && (
            <Alert className={validationResult.valid ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
              {validationResult.valid ? (
                <CheckCircle className="w-4 h-4 text-green-600" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-red-600" />
              )}
              <AlertDescription className={validationResult.valid ? 'text-green-800' : 'text-red-800'}>
                {validationResult.valid ? (
                  <>
                    <strong>Credentials Valid!</strong> Proceeding with deployment...
                    {validationResult.permissions && validationResult.permissions.length > 0 && (
                      <div className="mt-2 text-sm">
                        Detected permissions: {validationResult.permissions.slice(0, 3).join(', ')}
                        {validationResult.permissions.length > 3 && ` and ${validationResult.permissions.length - 3} more`}
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <strong>Validation Failed:</strong> {validationResult.error}
                  </>
                )}
              </AlertDescription>
            </Alert>
          )}

          <Alert>
            <Key className="w-4 h-4" />
            <AlertDescription>
              Your credentials are used immediately for deployment and are not stored permanently.
            </AlertDescription>
          </Alert>

          <div className="flex justify-between pt-4">
            {onCancel && (
              <Button variant="outline" onClick={onCancel}>
                Cancel
              </Button>
            )}
            <Button 
              onClick={validateAndProceed}
              disabled={!isFormValid || isValidating}
              className="ml-auto"
            >
              {isValidating ? 'Validating...' : 'Validate & Deploy'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SimpleCredentialInput;
