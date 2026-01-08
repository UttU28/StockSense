// Comprehensive list of popular stocks organized by category

export interface Stock {
  symbol: string;
  name: string;
  category: string;
}

export const STOCKS: Stock[] = [
  // Technology
  { symbol: "AAPL", name: "Apple Inc.", category: "Technology" },
  { symbol: "NVDA", name: "NVIDIA Corporation", category: "Technology" },
  { symbol: "PANW", name: "Palo Alto Networks", category: "Technology" },
  { symbol: "AVGO", name: "Broadcom Inc.", category: "Technology" },
  { symbol: "ADBE", name: "Adobe Inc.", category: "Technology" },
  { symbol: "MDB", name: "MongoDB, Inc.", category: "Technology" },
  { symbol: "ASML", name: "ASML Holding N.V.", category: "Technology" },
  { symbol: "TSLA", name: "Tesla, Inc.", category: "Technology" },
  
  // Finance
  { symbol: "BLK", name: "BlackRock, Inc.", category: "Finance" },
  
  // Consumer
  { symbol: "RH", name: "RH (Restoration Hardware)", category: "Consumer" },
  
  // Crypto
  { symbol: "MSTR", name: "MicroStrategy Incorporated", category: "Crypto" },
  { symbol: "COIN", name: "Coinbase Global, Inc.", category: "Crypto" },
];

// Get stocks by category with sequential numbering
export const getStocksByCategory = (): Record<string, Array<Stock & { index: number }>> => {
  let globalIndex = 1;
  return STOCKS.reduce((acc, stock) => {
    if (!acc[stock.category]) {
      acc[stock.category] = [];
    }
    acc[stock.category].push({ ...stock, index: globalIndex++ });
    return acc;
  }, {} as Record<string, Array<Stock & { index: number }>>);
};

// Get all symbols
export const getAllSymbols = (): string[] => {
  return STOCKS.map(stock => stock.symbol);
};

// Get stock by symbol
export const getStockBySymbol = (symbol: string): Stock | undefined => {
  return STOCKS.find(stock => stock.symbol === symbol.toUpperCase());
};

// Popular watchlists
export const WATCHLISTS = {
  all: ["AAPL", "NVDA", "PANW", "RH", "AVGO", "MSTR", "COIN", "BLK", "ADBE", "MDB", "ASML", "TSLA"],
  tech: ["AAPL", "NVDA", "PANW", "AVGO", "ADBE", "MDB", "ASML", "TSLA"],
  finance: ["BLK"],
  consumer: ["RH"],
  crypto: ["COIN", "MSTR"],
};

