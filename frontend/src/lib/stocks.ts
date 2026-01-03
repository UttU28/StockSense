// Comprehensive list of popular stocks organized by category

export interface Stock {
  symbol: string;
  name: string;
  category: string;
}

export const STOCKS: Stock[] = [
  // Tech Giants
  { symbol: "AAPL", name: "Apple Inc.", category: "Technology" },
  { symbol: "MSFT", name: "Microsoft Corporation", category: "Technology" },
  { symbol: "GOOGL", name: "Alphabet Inc.", category: "Technology" },
  { symbol: "AMZN", name: "Amazon.com Inc.", category: "Technology" },
  { symbol: "META", name: "Meta Platforms Inc.", category: "Technology" },
  { symbol: "NVDA", name: "NVIDIA Corporation", category: "Technology" },
  { symbol: "TSLA", name: "Tesla, Inc.", category: "Technology" },
  { symbol: "AMD", name: "Advanced Micro Devices", category: "Technology" },
  { symbol: "INTC", name: "Intel Corporation", category: "Technology" },
  { symbol: "ORCL", name: "Oracle Corporation", category: "Technology" },
  { symbol: "CRM", name: "Salesforce, Inc.", category: "Technology" },
  { symbol: "ADBE", name: "Adobe Inc.", category: "Technology" },
  { symbol: "NFLX", name: "Netflix, Inc.", category: "Technology" },
  { symbol: "UBER", name: "Uber Technologies Inc.", category: "Technology" },
  { symbol: "SNOW", name: "Snowflake Inc.", category: "Technology" },
  { symbol: "MDB", name: "MongoDB, Inc.", category: "Technology" },
  { symbol: "PANW", name: "Palo Alto Networks", category: "Technology" },
  { symbol: "ASML", name: "ASML Holding N.V.", category: "Technology" },
  
  // Finance
  { symbol: "JPM", name: "JPMorgan Chase & Co.", category: "Finance" },
  { symbol: "BAC", name: "Bank of America Corp.", category: "Finance" },
  { symbol: "WFC", name: "Wells Fargo & Company", category: "Finance" },
  { symbol: "GS", name: "Goldman Sachs Group Inc.", category: "Finance" },
  { symbol: "MS", name: "Morgan Stanley", category: "Finance" },
  { symbol: "C", name: "Citigroup Inc.", category: "Finance" },
  { symbol: "BLK", name: "BlackRock, Inc.", category: "Finance" },
  { symbol: "V", name: "Visa Inc.", category: "Finance" },
  { symbol: "MA", name: "Mastercard Incorporated", category: "Finance" },
  { symbol: "AXP", name: "American Express Company", category: "Finance" },
  
  // Healthcare
  { symbol: "JNJ", name: "Johnson & Johnson", category: "Healthcare" },
  { symbol: "UNH", name: "UnitedHealth Group Inc.", category: "Healthcare" },
  { symbol: "PFE", name: "Pfizer Inc.", category: "Healthcare" },
  { symbol: "ABBV", name: "AbbVie Inc.", category: "Healthcare" },
  { symbol: "TMO", name: "Thermo Fisher Scientific Inc.", category: "Healthcare" },
  { symbol: "ABT", name: "Abbott Laboratories", category: "Healthcare" },
  { symbol: "DHR", name: "Danaher Corporation", category: "Healthcare" },
  { symbol: "BMY", name: "Bristol-Myers Squibb Company", category: "Healthcare" },
  { symbol: "AMGN", name: "Amgen Inc.", category: "Healthcare" },
  { symbol: "GILD", name: "Gilead Sciences, Inc.", category: "Healthcare" },
  
  // Consumer
  { symbol: "WMT", name: "Walmart Inc.", category: "Consumer" },
  { symbol: "HD", name: "The Home Depot, Inc.", category: "Consumer" },
  { symbol: "MCD", name: "McDonald's Corporation", category: "Consumer" },
  { symbol: "NKE", name: "Nike, Inc.", category: "Consumer" },
  { symbol: "SBUX", name: "Starbucks Corporation", category: "Consumer" },
  { symbol: "TGT", name: "Target Corporation", category: "Consumer" },
  { symbol: "COST", name: "Costco Wholesale Corporation", category: "Consumer" },
  { symbol: "LOW", name: "Lowe's Companies, Inc.", category: "Consumer" },
  { symbol: "DIS", name: "The Walt Disney Company", category: "Consumer" },
  { symbol: "NFLX", name: "Netflix, Inc.", category: "Consumer" },
  
  // Energy
  { symbol: "XOM", name: "Exxon Mobil Corporation", category: "Energy" },
  { symbol: "CVX", name: "Chevron Corporation", category: "Energy" },
  { symbol: "COP", name: "ConocoPhillips", category: "Energy" },
  { symbol: "SLB", name: "Schlumberger Limited", category: "Energy" },
  { symbol: "EOG", name: "EOG Resources, Inc.", category: "Energy" },
  
  // Industrial
  { symbol: "BA", name: "The Boeing Company", category: "Industrial" },
  { symbol: "CAT", name: "Caterpillar Inc.", category: "Industrial" },
  { symbol: "GE", name: "General Electric Company", category: "Industrial" },
  { symbol: "HON", name: "Honeywell International Inc.", category: "Industrial" },
  { symbol: "RTX", name: "Raytheon Technologies Corporation", category: "Industrial" },
  { symbol: "LMT", name: "Lockheed Martin Corporation", category: "Industrial" },
  
  // Crypto/Blockchain Related
  { symbol: "COIN", name: "Coinbase Global, Inc.", category: "Crypto" },
  { symbol: "MSTR", name: "MicroStrategy Incorporated", category: "Crypto" },
  { symbol: "RIOT", name: "Riot Platforms, Inc.", category: "Crypto" },
  { symbol: "MARA", name: "Marathon Digital Holdings", category: "Crypto" },
  
  // Other Popular
  { symbol: "AVGO", name: "Broadcom Inc.", category: "Technology" },
  { symbol: "RH", name: "RH (Restoration Hardware)", category: "Consumer" },
  { symbol: "SPY", name: "SPDR S&P 500 ETF", category: "ETF" },
  { symbol: "QQQ", name: "Invesco QQQ Trust", category: "ETF" },
];

// Get stocks by category
export const getStocksByCategory = (): Record<string, Stock[]> => {
  return STOCKS.reduce((acc, stock) => {
    if (!acc[stock.category]) {
      acc[stock.category] = [];
    }
    acc[stock.category].push(stock);
    return acc;
  }, {} as Record<string, Stock[]>);
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
  tech: ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"],
  finance: ["JPM", "BAC", "GS", "MS", "V", "MA"],
  healthcare: ["JNJ", "UNH", "PFE", "ABBV", "TMO"],
  popular: ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "AMD"],
  crypto: ["COIN", "MSTR", "RIOT", "MARA"],
};

