"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Package, Bell, Clock, Download, BarChart3, ShoppingBot } from "lucide-react"

export default function LandingPage() {
  const features = [
    {
      icon: Package,
      title: "Multi-Store Tracking",
      description: "Track inventory across multiple Blinkit dark stores by coordinates or store ID",
      color: "bg-green-500/20 text-green-400",
    },
    {
      icon: Bell,
      title: "Low Stock Alerts",
      description: "Get instant notifications when items fall below threshold",
      color: "bg-red-500/20 text-red-400",
    },
    {
      icon: Clock,
      title: "Scheduled Monitoring",
      description: "Set up automatic inventory checks at configurable intervals",
      color: "bg-blue-500/20 text-blue-400",
    },
    {
      icon: Download,
      title: "Export Data",
      description: "Export inventory to CSV or JSON with historical tracking",
      color: "bg-purple-500/20 text-purple-400",
    },
    {
      icon: BarChart3,
      title: "Analytics Dashboard",
      description: "Visualize inventory trends and store performance",
      color: "bg-yellow-500/20 text-yellow-400",
    },
    {
      icon: ShoppingBot,
      title: "WhatsApp Ordering",
      description: "Order groceries via WhatsApp using AI-powered bot",
      color: "bg-cyan-500/20 text-cyan-400",
    },
  ]

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b bg-background/80 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">Z</span>
            </div>
            <span className="text-xl font-bold">Zyvro</span>
          </div>
          <div className="flex gap-4 items-center">
            <Link href="/inventory" className="hover:text-green-400 transition">
              Inventory
            </Link>
            <Link href="/inventory">
              <Button className="bg-green-500 hover:bg-green-600">
                Open Dashboard
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="min-h-screen flex items-center justify-center pt-20">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-green-500/10 border border-green-500/20 mb-8">
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
            <span className="text-sm">Live Grocery Monitoring</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            Smart Grocery<br />
            <span className="text-green-400">Inventory Tracker</span>
          </h1>

          <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto">
            Track real-time inventory across multiple Blinkit stores.
            Get alerts for low stock, schedule monitoring, and export data seamlessly.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/inventory">
              <Button size="lg" className="bg-green-500 hover:bg-green-600 gap-2">
                <BarChart3 className="w-5 h-5" />
                Open Dashboard
              </Button>
            </Link>
          </div>

          {/* Quick Demo Card */}
          <Card className="mt-16 max-w-3xl mx-auto">
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold mb-4">Quick Stats</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-lg bg-muted">
                  <div className="text-2xl font-bold text-green-400">15</div>
                  <div className="text-sm text-muted-foreground">Products</div>
                </div>
                <div className="p-4 rounded-lg bg-muted">
                  <div className="text-2xl font-bold text-red-400">3</div>
                  <div className="text-sm text-muted-foreground">Low Stock</div>
                </div>
                <div className="p-4 rounded-lg bg-muted">
                  <div className="text-2xl font-bold">343</div>
                  <div className="text-sm text-muted-foreground">Total Units</div>
                </div>
                <div className="p-4 rounded-lg bg-muted">
                  <div className="text-2xl font-bold">22</div>
                  <div className="text-sm text-muted-foreground">Avg Stock</div>
                </div>
              </div>
              <p className="text-sm text-muted-foreground mt-4">
                Visit the dashboard to search products and see real-time inventory
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 border-t">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-4xl font-bold text-center mb-16">Features</h2>

          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, idx) => (
              <Card key={idx} className="hover:scale-105 transition-transform">
                <CardContent className="p-8">
                  <div className={`w-14 h-14 rounded-xl flex items-center justify-center mb-6 ${feature.color}`}>
                    <feature.icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-muted/50 border-t">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-4xl font-bold text-center mb-16">How It Works</h2>

          <div className="grid md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">1</div>
              <h3 className="font-semibold mb-2">Set Location</h3>
              <p className="text-muted-foreground text-sm">Choose store by coordinates or ID</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">2</div>
              <h3 className="font-semibold mb-2">Search Products</h3>
              <p className="text-muted-foreground text-sm">Enter product name to search</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">3</div>
              <h3 className="font-semibold mb-2">View Inventory</h3>
              <p className="text-muted-foreground text-sm">See real-time stock levels</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">4</div>
              <h3 className="font-semibold mb-2">Get Alerts</h3>
              <p className="text-muted-foreground text-sm">Monitored automatically</p>
            </div>
          </div>

          <div className="mt-16 text-center">
            <Link href="/inventory">
              <Button size="lg" className="bg-green-500 hover:bg-green-600">
                Open Full Dashboard
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t">
        <div className="max-w-7xl mx-auto px-6 text-center text-muted-foreground">
          <p>&copy; 2026 Zyvro. Smart Grocery Automation.</p>
        </div>
      </footer>
    </div>
  )
}