"use client"

import React, { useState, useEffect } from "react"
import { DashboardLayout } from "@/components/dashboard/dashboard-layout"
import { GlanceCard } from "@/components/dashboard/glance-card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Package, AlertTriangle, RefreshCw, Search } from "lucide-react"

const FLASK_API = "http://localhost:5000/api"

interface Product {
  product_id: string
  name: string
  variant: string
  price: number
  inventory: number
  brand: string
  eta: string
  merchant_id: string
}

interface Alert {
  type: string
  name: string
  variant: string
  inventory: number
}

export default function InventoryDashboard() {
  const [products, setProducts] = useState<Product[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState("milk")
  const [selectedLocation, setSelectedLocation] = useState("store_43939")
  const [error, setError] = useState("")

  // Fetch inventory data directly from Flask
  const fetchInventory = async (doSearch = false) => {
    setLoading(true)
    setError("")
    try {
      let endpoint = doSearch ? "inventory/search" : "inventory"
      const storeId = selectedLocation.startsWith("store_") ? selectedLocation.replace("store_", "") : null
      const url = doSearch 
        ? `${FLASK_API}/${endpoint}?q=${searchQuery}&limit=20${storeId ? `&store_id=${storeId}` : ''}`
        : `${FLASK_API}/${endpoint}`
      
      const res = await fetch(url)
      const data = await res.json()
      setProducts(data.products || [])
    } catch (e) {
      setError("Failed to connect to API. Make sure Flask server is running on port 5000")
      console.error("Failed to fetch inventory:", e)
    }
    setLoading(false)
  }

  // Fetch alerts
  const fetchAlerts = async () => {
    try {
      const res = await fetch(`${FLASK_API}/alerts`)
      const data = await res.json()
      setAlerts(data.alerts || [])
    } catch (e) {
      console.error("Failed to fetch alerts:", e)
    }
  }

  useEffect(() => {
    fetchInventory(false)
    fetchAlerts()
  }, [])

  // Calculate metrics
  const totalProducts = products.length
  const lowStockItems = products.filter(p => p.inventory < 5).length
  const totalInventory = products.reduce((sum, p) => sum + p.inventory, 0)
  const avgStock = totalProducts > 0 ? Math.round(totalInventory / totalProducts) : 0

  const glanceCards = [
    { title: "Total Products", value: totalProducts, suffix: "", change: 0, sparklineData: [10, 15, 12, 18, 20] },
    { title: "Low Stock Items", value: lowStockItems, suffix: "", change: lowStockItems > 0 ? 100 : 0, sparklineData: [2, 3, 1, 4, 2] },
    { title: "Total Stock", value: totalInventory, suffix: "units", change: 0, sparklineData: [500, 550, 520, 600, 580] },
    { title: "Avg Stock/Item", value: avgStock, suffix: "", change: 0, sparklineData: [45, 50, 48, 55, 52] },
  ]

  return (
    <DashboardLayout>
      <div className="p-4 md:p-6 lg:p-8">
        {/* Header */}
        <div className="mb-6 md:mb-8">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="w-2 h-2 bg-green-500 pulse" />
                <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
                  Live Inventory
                </span>
              </div>
              <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">
                Inventory Dashboard
              </h1>
              <p className="text-sm md:text-base text-muted-foreground mt-1">
                Track real-time stock across Blinkit dark stores
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => fetchInventory(true)} className="gap-2">
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                <span className="hidden sm:inline">Refresh</span>
              </Button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <Card className="mb-6 border-red-500">
            <CardContent className="p-4 text-red-400">
              {error}
            </CardContent>
          </Card>
        )}

        {/* Search Bar */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex gap-4">
              <div className="flex-1 flex gap-2">
                <Input
                  placeholder="Search products..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && fetchInventory(true)}
                  className="flex-1"
                />
                <Select value={selectedLocation} onValueChange={setSelectedLocation}>
                  <SelectTrigger className="w-56">
                    <SelectValue placeholder="Store" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="store_43939">Express Store 1 (ID: 43939)</SelectItem>
                    <SelectItem value="store_44001">Express Store 2 (ID: 44001)</SelectItem>
                    <SelectItem value="store_43939">Dwarka (43939)</SelectItem>
                    <SelectItem value="store_44001">Rajouri (44001)</SelectItem>
                  </SelectContent>
                </Select>
                <Button onClick={() => fetchInventory(true)}>
                  <Search className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Glance Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6 md:mb-8">
          {glanceCards.map((card) => (
            <GlanceCard
              key={card.title}
              title={card.title}
              value={card.value}
              suffix={card.suffix}
              change={card.change}
              sparklineData={card.sparklineData}
            />
          ))}
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Products Table */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Package className="w-5 h-5" />
                  Products ({products.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center justify-center p-8">
                    <RefreshCw className="w-6 h-6 animate-spin" />
                  </div>
                ) : products.length > 0 ? (
                  <div className="space-y-2">
                    {products.map((product, idx) => (
                      <div
                        key={idx}
                        className={`flex items-center justify-between p-3 rounded-lg border ${
                          product.inventory < 5 ? "border-red-500/50 bg-red-500/10" : "border-border"
                        }`}
                      >
                        <div className="flex-1 min-w-0">
                          <div className="font-medium truncate">{product.name}</div>
                          <div className="text-sm text-muted-foreground">
                            {product.variant} - {product.brand} - Store: {product.merchant_id}
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <div className="font-mono font-bold">Rs.{product.price}</div>
                            <div className="text-xs text-muted-foreground">{product.eta}</div>
                          </div>
                          <div
                            className={`px-3 py-1 rounded-full text-center min-w-[60px] ${
                              product.inventory < 5
                                ? "bg-red-500 text-white"
                                : product.inventory < 20
                                ? "bg-yellow-500 text-white"
                                : "bg-green-500 text-white"
                            }`}
                          >
                            <span className="font-bold">{product.inventory}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center p-8 text-muted-foreground">
                    <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No products found</p>
                    <p className="text-sm">Search for a product to see inventory</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Alerts & Stats */}
          <div className="flex flex-col gap-6">
            {/* Low Stock Alerts */}
            <Card className={alerts.length > 0 ? "border-red-500" : ""}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-400">
                  <AlertTriangle className="w-5 h-5" />
                  Low Stock Alerts ({alerts.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {alerts.length > 0 ? (
                  <div className="space-y-2">
                    {alerts.slice(0, 5).map((alert, idx) => (
                      <div key={idx} className="p-3 bg-red-500/10 rounded-lg border border-red-500/30">
                        <div className="font-medium text-sm">{alert.name}</div>
                        <div className="text-xs text-muted-foreground">{alert.variant}</div>
                        <div className="mt-1 text-red-400 font-bold">Only {alert.inventory} left!</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center p-4 text-muted-foreground">
                    <p className="text-sm">All stock levels OK</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Stock Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Stock Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Critical (0-5)</span>
                    <Badge variant="destructive">{products.filter(p => p.inventory <= 5).length}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Low (6-20)</span>
                    <Badge variant="warning">{products.filter(p => p.inventory > 5 && p.inventory <= 20).length}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Good (21+)</span>
                    <Badge variant="outline" className="bg-green-500/20">{products.filter(p => p.inventory > 20).length}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}