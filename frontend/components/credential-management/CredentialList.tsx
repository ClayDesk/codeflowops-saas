/**
 * Credential List Component
 * Displays and manages AWS credentials with security controls
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '@/components/ui/dropdown-menu';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Shield, 
  Key, 
  MoreVertical, 
  Eye, 
  Edit, 
  Trash2, 
  Clock, 
  AlertTriangle,
  CheckCircle,
  Copy,
  RefreshCw,
  Download
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface Credential {
  credential_id: string;
  credential_name: string;
  credential_type: string;
  aws_region?: string;
  aws_account_id?: string;
  created_at: string;
  last_rotated?: string;
  expires_at?: string;
  is_active: boolean;
  is_validated: boolean;
  last_validated?: string;
  mfa_required: boolean;
  rotation_schedule?: string;
}

interface AWSSession {
  session_id: string;
  access_key_id: string;
  secret_access_key: string;
  session_token: string;
  expires_at: string;
  region: string;
}

interface CredentialListProps {
  onSetupNew: () => void;
  onEdit: (credentialId: string) => void;
}

const CredentialList: React.FC<CredentialListProps> = ({ onSetupNew, onEdit }) => {
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeSession, setActiveSession] = useState<AWSSession | null>(null);
  const [showAccessDialog, setShowAccessDialog] = useState(false);
  const [selectedCredential, setSelectedCredential] = useState<string | null>(null);
  const [mfaToken, setMfaToken] = useState('');
  const [accessLoading, setAccessLoading] = useState(false);

  useEffect(() => {
    loadCredentials();
  }, []);

  const loadCredentials = async () => {
    try {
      const response = await fetch('/api/v1/credentials/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setCredentials(data);
      }
    } catch (error) {
      console.error('Failed to load credentials:', error);
    } finally {
      setLoading(false);
    }
  };

  const accessCredential = async (credentialId: string) => {
    setAccessLoading(true);
    try {
      const response = await fetch('/api/v1/credentials/access', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          credential_id: credentialId,
          mfa_token: mfaToken || undefined,
          session_duration: 3600
        })
      });

      if (response.ok) {
        const session = await response.json();
        setActiveSession(session);
        setShowAccessDialog(false);
        setMfaToken('');
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to access credential');
      }
    } catch (error) {
      console.error('Failed to access credential:', error);
      alert('Failed to access credential');
    } finally {
      setAccessLoading(false);
    }
  };

  const deleteCredential = async (credentialId: string) => {
    if (!confirm('Are you sure you want to delete this credential?')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/credentials/${credentialId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        await loadCredentials();
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to delete credential');
      }
    } catch (error) {
      console.error('Failed to delete credential:', error);
      alert('Failed to delete credential');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  };

  const exportSession = () => {
    if (!activeSession) return;

    const exportData = {
      AWS_ACCESS_KEY_ID: activeSession.access_key_id,
      AWS_SECRET_ACCESS_KEY: activeSession.secret_access_key,
      AWS_SESSION_TOKEN: activeSession.session_token,
      AWS_DEFAULT_REGION: activeSession.region
    };

    const dataStr = Object.entries(exportData)
      .map(([key, value]) => `export ${key}="${value}"`)
      .join('\n');

    const element = document.createElement('a');
    const file = new Blob([dataStr], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = 'aws-credentials.sh';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const getStatusBadge = (credential: Credential) => {
    if (!credential.is_active) {
      return <Badge variant="secondary">Inactive</Badge>;
    }
    
    if (credential.expires_at && new Date(credential.expires_at) < new Date()) {
      return <Badge variant="destructive">Expired</Badge>;
    }
    
    if (!credential.is_validated) {
      return <Badge variant="outline">Unvalidated</Badge>;
    }
    
    return <Badge variant="default" className="bg-green-600">Active</Badge>;
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'access_key':
        return <Key className="w-4 h-4" />;
      case 'role_arn':
        return <Shield className="w-4 h-4" />;
      default:
        return <Key className="w-4 h-4" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">AWS Credentials</h1>
          <p className="text-gray-600">Manage your secure AWS credentials</p>
        </div>
        <Button onClick={onSetupNew}>
          <Key className="w-4 h-4 mr-2" />
          Add Credential
        </Button>
      </div>

      {/* Active Session */}
      {activeSession && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-800">
              <CheckCircle className="w-5 h-5" />
              Active AWS Session
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-sm font-medium text-green-700">Access Key ID</Label>
                <div className="flex items-center gap-2 mt-1">
                  <code className="bg-white px-2 py-1 rounded text-sm">{activeSession.access_key_id}</code>
                  <Button 
                    size="sm" 
                    variant="ghost" 
                    onClick={() => copyToClipboard(activeSession.access_key_id)}
                  >
                    <Copy className="w-3 h-3" />
                  </Button>
                </div>
              </div>
              <div>
                <Label className="text-sm font-medium text-green-700">Region</Label>
                <div className="mt-1">
                  <code className="bg-white px-2 py-1 rounded text-sm">{activeSession.region}</code>
                </div>
              </div>
              <div>
                <Label className="text-sm font-medium text-green-700">Expires</Label>
                <div className="mt-1 text-sm">
                  {formatDistanceToNow(new Date(activeSession.expires_at), { addSuffix: true })}
                </div>
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={exportSession}>
                  <Download className="w-3 h-3 mr-1" />
                  Export
                </Button>
                <Button size="sm" variant="outline" onClick={() => setActiveSession(null)}>
                  Clear Session
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Credentials Table */}
      <Card>
        <CardContent className="p-0">
          {credentials.length === 0 ? (
            <div className="text-center py-12">
              <Key className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No credentials found</h3>
              <p className="text-gray-500 mb-6">Get started by adding your first AWS credential</p>
              <Button onClick={onSetupNew}>
                Add AWS Credential
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Region</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Security</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {credentials.map((credential) => (
                  <TableRow key={credential.credential_id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getTypeIcon(credential.credential_type)}
                        <div>
                          <div className="font-medium">{credential.credential_name}</div>
                          {credential.aws_account_id && (
                            <div className="text-sm text-gray-500">
                              Account: {credential.aws_account_id}
                            </div>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {credential.credential_type.replace('_', ' ').toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell>{credential.aws_region || 'N/A'}</TableCell>
                    <TableCell>{getStatusBadge(credential)}</TableCell>
                    <TableCell>
                      {formatDistanceToNow(new Date(credential.created_at), { addSuffix: true })}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {credential.mfa_required && (
                          <Badge variant="secondary" className="text-xs">
                            MFA
                          </Badge>
                        )}
                        {credential.expires_at && (
                          <Badge variant="outline" className="text-xs">
                            <Clock className="w-3 h-3 mr-1" />
                            Expires
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => {
                              setSelectedCredential(credential.credential_id);
                              setShowAccessDialog(true);
                            }}
                          >
                            <Eye className="w-4 h-4 mr-2" />
                            Access
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => onEdit(credential.credential_id)}>
                            <Edit className="w-4 h-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => deleteCredential(credential.credential_id)}
                            className="text-red-600"
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Access Credential Dialog */}
      <Dialog open={showAccessDialog} onOpenChange={setShowAccessDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Access AWS Credential</DialogTitle>
            <DialogDescription>
              This will create a temporary AWS session with the selected credentials.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {selectedCredential && (
              <div>
                <Label className="text-sm font-medium">Credential</Label>
                <div className="mt-1">
                  {credentials.find(c => c.credential_id === selectedCredential)?.credential_name}
                </div>
              </div>
            )}

            {selectedCredential && 
             credentials.find(c => c.credential_id === selectedCredential)?.mfa_required && (
              <div>
                <Label htmlFor="mfa_token">MFA Token</Label>
                <Input
                  id="mfa_token"
                  value={mfaToken}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMfaToken(e.target.value)}
                  placeholder="Enter your MFA token"
                  className="mt-1"
                />
              </div>
            )}

            <Alert>
              <Shield className="w-4 h-4" />
              <AlertDescription>
                This session will be valid for 1 hour and will be logged for security purposes.
              </AlertDescription>
            </Alert>

            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setShowAccessDialog(false)}>
                Cancel
              </Button>
              <Button 
                onClick={() => selectedCredential && accessCredential(selectedCredential)}
                disabled={accessLoading}
              >
                {accessLoading ? 'Creating Session...' : 'Create Session'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CredentialList;
