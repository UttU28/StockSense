import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ResponsiveContainer, AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import { ChartResponse } from "@/lib/api";

interface PriceChartProps {
  chartData: ChartResponse;
  chartType: "price" | "ohlc";
  onChartTypeChange: (type: "price" | "ohlc") => void;
}

export function PriceChart({ chartData, chartType, onChartTypeChange }: PriceChartProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          {chartType === "price" ? `${chartData.symbol} Price Chart (30 Days)` : "OHLC Chart (Open, High, Low, Close)"}
        </h3>
        <div className="flex gap-2">
          <Button
            variant={chartType === "price" ? "default" : "outline"}
            size="sm"
            onClick={() => onChartTypeChange("price")}
          >
            Price Chart
          </Button>
          <Button
            variant={chartType === "ohlc" ? "default" : "outline"}
            size="sm"
            onClick={() => onChartTypeChange("ohlc")}
          >
            OHLC Chart
          </Button>
        </div>
      </div>
      <div className="bg-muted/30 rounded-lg p-4">
        {chartType === "price" ? (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={chartData.data}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8884d8" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="date" 
                stroke="#9ca3af"
                tick={{ fill: '#9ca3af' }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                stroke="#9ca3af"
                tick={{ fill: '#9ca3af' }}
                domain={['dataMin - 5', 'dataMax + 5']}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#f3f4f6'
                }}
                formatter={(value: number) => [`$${value.toFixed(2)}`, 'Price']}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Area
                type="monotone"
                dataKey="close"
                stroke="#8884d8"
                fillOpacity={1}
                fill="url(#colorPrice)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData.data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey="date" 
                  stroke="#9ca3af"
                  tick={{ fill: '#9ca3af' }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis 
                  stroke="#9ca3af"
                  tick={{ fill: '#9ca3af' }}
                  domain={['dataMin - 5', 'dataMax + 5']}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#f3f4f6'
                  }}
                  formatter={(value: number) => `$${value.toFixed(2)}`}
                  labelStyle={{ color: '#9ca3af' }}
                />
                <Line type="monotone" dataKey="open" stroke="#3b82f6" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="high" stroke="#10b981" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="low" stroke="#ef4444" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="close" stroke="#8884d8" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
            <div className="flex gap-4 mt-4 justify-center">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-blue-500"></div>
                <span className="text-sm text-muted-foreground">Open</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-green-500"></div>
                <span className="text-sm text-muted-foreground">High</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-red-500"></div>
                <span className="text-sm text-muted-foreground">Low</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-purple-500"></div>
                <span className="text-sm text-muted-foreground">Close</span>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
