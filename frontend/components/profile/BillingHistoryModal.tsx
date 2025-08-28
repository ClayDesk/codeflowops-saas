'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Loader2, Download, Eye, CreditCard, Calendar, DollarSign } from 'lucide-react'

interface Invoice {
  id: string
  number: string
  amount_paid: number
  amount_due: number
  currency: string
  status: string
  created: number
  period_start: number
  period_end: number
  invoice_pdf: string
  hosted_invoice_url: string
  description: string
  payment_intent: string
}

interface BillingHistoryModalProps {
  onFetchBillingHistory: () => Promise<Invoice[]>
  children: React.ReactNode
}

export function BillingHistoryModal({ onFetchBillingHistory, children }: BillingHistoryModalProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleOpen = async () => {
    setIsOpen(true)
    setLoading(true)
    setError(null)
    
    try {
      const billingData = await onFetchBillingHistory()
      setInvoices(billingData)
    } catch (err) {
      setError('Failed to load billing history')
      console.error('Error fetching billing history:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase()
    }).format(amount / 100)
  }

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      paid: { variant: 'default' as const, label: 'Paid' },
      open: { variant: 'secondary' as const, label: 'Open' },
      void: { variant: 'destructive' as const, label: 'Void' },
      draft: { variant: 'outline' as const, label: 'Draft' }
    }
    
    const config = statusConfig[status as keyof typeof statusConfig] || { variant: 'outline' as const, label: status }
    
    return (
      <Badge variant={config.variant}>
        {config.label}
      </Badge>
    )
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild onClick={handleOpen}>
        {children}
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Billing History
          </DialogTitle>
          <DialogDescription>
            View and download your past invoices and payment history
          </DialogDescription>
        </DialogHeader>
        
        <div className="flex-1 overflow-auto">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              <span>Loading billing history...</span>
            </div>
          ) : error ? (
            <div className="text-center py-8 text-red-600">
              <p>{error}</p>
              <Button variant="outline" onClick={handleOpen} className="mt-4">
                Try Again
              </Button>
            </div>
          ) : invoices.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <CreditCard className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No billing history found</p>
              <p className="text-sm">Your invoices will appear here after your first payment</p>
            </div>
          ) : (
            <div className="space-y-4">
              {invoices.map((invoice) => (
                <Card key={invoice.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-medium">
                            {invoice.number || `Invoice ${invoice.id.slice(-8)}`}
                          </h3>
                          {getStatusBadge(invoice.status)}
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <DollarSign className="h-3 w-3" />
                            <span>{formatCurrency(invoice.amount_paid, invoice.currency)}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            <span>{formatDate(invoice.created)}</span>
                          </div>
                        </div>
                        
                        {invoice.description && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {invoice.description}
                          </p>
                        )}
                        
                        <div className="text-xs text-muted-foreground mt-1">
                          Period: {formatDate(invoice.period_start)} - {formatDate(invoice.period_end)}
                        </div>
                      </div>
                      
                      <div className="flex gap-2 ml-4">
                        {invoice.hosted_invoice_url && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => window.open(invoice.hosted_invoice_url, '_blank')}
                          >
                            <Eye className="h-3 w-3 mr-1" />
                            View
                          </Button>
                        )}
                        {invoice.invoice_pdf && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => window.open(invoice.invoice_pdf, '_blank')}
                          >
                            <Download className="h-3 w-3 mr-1" />
                            PDF
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
