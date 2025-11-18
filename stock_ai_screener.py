# stock_ai_screener.py
import yfinance as yf
import pandas as pd
import numpy as np
import time
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

class AIStockScreener:
    def __init__(self):
        # Screening Criteria
        self.criteria = {
            # Fundamental Analysis
            'max_pe': 25,
            'max_debt_equity': 0.5,
            'min_roe': 0.15,
            'min_market_cap': 2e9,
            'min_revenue_growth': 0.05,
            'min_profit_margin': 0.10,
            
            # Technical Analysis  
            'min_price_sma50': 0.95,
            'min_volume_ratio': 0.8,
            
            # Investment Parameters
            'investment_amount': 1000,
            'stop_loss_percentage': 0.08,    # 8% stop loss
            'take_profit_percentage': 0.20,  # 20% take profit
            'max_position_risk': 0.02,       # Risk max 2% of portfolio
        }
        
        self.results = []
    
    def get_stock_data(self, ticker: str) -> Dict:
        """Fetch comprehensive stock data from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1y")
            
            # Fundamental data
            data = {
                'ticker': ticker,
                'company_name': info.get('longName', 'N/A'),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'debt_to_equity': info.get('debtToEquity'),
                'roe': info.get('returnOnEquity'),
                'market_cap': info.get('marketCap'),
                'revenue_growth': info.get('revenueGrowth'),
                'profit_margin': info.get('profitMargins'),
                'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'beta': info.get('beta', 1.0),
                'dividend_yield': info.get('dividendYield', 0),
            }
            
            # Technical data
            if not hist.empty:
                data['price_50_sma'] = hist['Close'].tail(50).mean()
                data['price_200_sma'] = hist['Close'].tail(200).mean()
                data['current_price'] = hist['Close'][-1] if data['current_price'] is None else data['current_price']
                data['volume_avg'] = hist['Volume'].tail(50).mean()
                data['volume_recent'] = hist['Volume'].tail(10).mean()
                
                # Calculate volatility
                returns = hist['Close'].pct_change().dropna()
                data['volatility'] = returns.std() * np.sqrt(252)
                
                # Support and resistance
                data['resistance'] = hist['High'].tail(50).max()
                data['support'] = hist['Low'].tail(50).min()
            else:
                data.update({
                    'price_50_sma': None,
                    'price_200_sma': None,
                    'volume_avg': None,
                    'volume_recent': None,
                    'volatility': 0.3,
                    'resistance': None,
                    'support': None
                })
            
            return data
            
        except Exception as e:
            print(f"Error fetching data for {ticker}: {str(e)}")
            return None
    
    def calculate_investment_scenario(self, data: Dict) -> Dict:
        """Calculate $1000 investment scenario with projections"""
        if not data or data['current_price'] is None:
            return {}
        
        current_price = data['current_price']
        investment = self.criteria['investment_amount']
        stop_loss_pct = self.criteria['stop_loss_percentage']
        take_profit_pct = self.criteria['take_profit_percentage']
        volatility = data.get('volatility', 0.3)
        
        # Calculate position sizing
        shares = investment / current_price
        total_cost = shares * current_price
        
        # Risk management
        stop_loss_price = current_price * (1 - stop_loss_pct)
        take_profit_price = current_price * (1 + take_profit_pct)
        risk_per_share = current_price - stop_loss_price
        total_risk = risk_per_share * shares
        
        # Projection scenarios
        conservative_return = 0.08
        moderate_return = 0.15  
        aggressive_return = 0.25
        
        # Monte Carlo simulation
        projections = self.monte_carlo_projection(current_price, volatility, shares)
        
        scenario = {
            'investment_amount': investment,
            'current_price': current_price,
            'shares': round(shares, 2),
            'total_cost': round(total_cost, 2),
            'stop_loss_price': round(stop_loss_price, 2),
            'take_profit_price': round(take_profit_price, 2),
            'risk_per_share': round(risk_per_share, 2),
            'total_risk': round(total_risk, 2),
            'risk_reward_ratio': round(take_profit_pct / stop_loss_pct, 2),
            
            # Projections
            'conservative_value': round(total_cost * (1 + conservative_return), 2),
            'moderate_value': round(total_cost * (1 + moderate_return), 2),
            'aggressive_value': round(total_cost * (1 + aggressive_return), 2),
            
            # Monte Carlo results
            'mc_avg_projection': round(projections['average'], 2),
            'mc_best_case': round(projections['best_case'], 2),
            'mc_worst_case': round(projections['worst_case'], 2),
            'mc_probability_profit': projections['probability_profit'],
        }
        
        return scenario
    
    def monte_carlo_projection(self, current_price: float, volatility: float, shares: float, 
                             days: int = 252, simulations: int = 1000) -> Dict:
        """Monte Carlo simulation for price projections"""
        try:
            final_prices = []
            
            for _ in range(simulations):
                price = current_price
                for _ in range(days):
                    drift = 0.0004
                    shock = np.random.normal(0, volatility / np.sqrt(252))
                    price *= (1 + drift + shock)
                final_prices.append(price)
            
            final_values = [price * shares for price in final_prices]
            
            return {
                'average': np.mean(final_values),
                'best_case': np.percentile(final_values, 90),
                'worst_case': np.percentile(final_values, 10),
                'probability_profit': sum(1 for v in final_values if v > 1000) / len(final_values)
            }
        except:
            return {
                'average': 1000 * 1.15,
                'best_case': 1000 * 1.3,
                'worst_case': 1000 * 0.85,
                'probability_profit': 0.65
            }
    
    def calculate_score(self, data: Dict) -> Tuple[bool, int, List[str]]:
        """Calculate screening score"""
        if not data:
            return False, 0, ["No data available"]
        
        score = 0
        reasons = []
        passes = True
        
        # Fundamental Scoring (70 points)
        fundamental_score = 0
        
        # P/E Ratio (20 points)
        if data['pe_ratio'] and data['pe_ratio'] > 0:
            if data['pe_ratio'] <= 15:
                fundamental_score += 20
            elif data['pe_ratio'] <= 25:
                fundamental_score += 15
            elif data['pe_ratio'] <= 35:
                fundamental_score += 10
            else:
                reasons.append(f"High P/E: {data['pe_ratio']:.1f}")
                passes = False
        else:
            reasons.append("No P/E data")
        
        # ROE (20 points)
        if data['roe']:
            if data['roe'] >= 0.20:
                fundamental_score += 20
            elif data['roe'] >= 0.15:
                fundamental_score += 15
            elif data['roe'] >= 0.10:
                fundamental_score += 10
            else:
                reasons.append(f"Low ROE: {data['roe']:.1%}")
                passes = False
        else:
            reasons.append("No ROE data")
        
        # Debt-to-Equity (15 points)
        if data['debt_to_equity']:
            if data['debt_to_equity'] <= 0.3:
                fundamental_score += 15
            elif data['debt_to_equity'] <= 0.5:
                fundamental_score += 10
            elif data['debt_to_equity'] <= 0.7:
                fundamental_score += 5
            else:
                reasons.append(f"High Debt/Equity: {data['debt_to_equity']:.2f}")
                passes = False
        
        # Revenue Growth (15 points)
        if data['revenue_growth']:
            if data['revenue_growth'] >= 0.15:
                fundamental_score += 15
            elif data['revenue_growth'] >= 0.10:
                fundamental_score += 12
            elif data['revenue_growth'] >= 0.05:
                fundamental_score += 8
            else:
                reasons.append(f"Low revenue growth: {data['revenue_growth']:.1%}")
        
        # Technical Scoring (30 points)
        technical_score = 0
        
        if data['price_50_sma'] and data['current_price']:
            price_ratio = data['current_price'] / data['price_50_sma']
            if price_ratio >= 1.0:
                technical_score += 15
            elif price_ratio >= 0.95:
                technical_score += 10
            elif price_ratio >= 0.90:
                technical_score += 5
            else:
                reasons.append(f"Price below 50-day SMA: {price_ratio:.2f}")
        else:
            reasons.append("No technical data")
        
        if data['volume_avg'] and data['volume_recent'] and data['volume_avg'] > 0:
            volume_ratio = data['volume_recent'] / data['volume_avg']
            if volume_ratio >= 1.2:
                technical_score += 15
            elif volume_ratio >= 0.8:
                technical_score += 10
            elif volume_ratio >= 0.5:
                technical_score += 5
        
        total_score = fundamental_score + technical_score
        
        if total_score < 60:
            passes = False
            reasons.append(f"Low overall score: {total_score}/100")
        
        return passes, total_score, reasons
    
    def screen_stock(self, ticker: str):
        """Screen individual stock"""
        print(f"Analyzing {ticker}...")
        
        data = self.get_stock_data(ticker)
        if not data:
            return
        
        passes, score, reasons = self.calculate_score(data)
        
        investment_scenario = {}
        if passes and data['current_price']:
            investment_scenario = self.calculate_investment_scenario(data)
        
        result = {
            'ticker': ticker,
            'company_name': data['company_name'],
            'sector': data['sector'],
            'current_price': data['current_price'],
            'pe_ratio': data['pe_ratio'],
            'roe': data['roe'],
            'debt_to_equity': data['debt_to_equity'],
            'revenue_growth': data['revenue_growth'],
            'market_cap': data['market_cap'],
            'score': score,
            'passes': passes,
            'reasons': reasons,
            'investment_scenario': investment_scenario
        }
        
        self.results.append(result)
        
        status = "✓ PASS" if passes else "✗ FAIL"
        print(f"  {status} - Score: {score}/100")
        
        if reasons and not passes:
            print(f"    Reasons: {', '.join(reasons[:2])}")
    
    def screen_multiple_stocks(self, tickers: List[str], delay: float = 0.5):
        """Screen multiple stocks"""
        print("🧠 AI STOCK SCREENER WITH $1000 INVESTMENT PLANS")
        print("=" * 70)
        print(f"Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        for ticker in tickers:
            self.screen_stock(ticker)
            time.sleep(delay)
        
        self.display_results()
    
    def display_results(self):
        """Display results with investment plans"""
        print("\n" + "=" * 70)
        print("📊 FINAL ANALYSIS RESULTS")
        print("=" * 70)
        
        passed_stocks = [r for r in self.results if r['passes']]
        failed_stocks = [r for r in self.results if not r['passes']]
        
        print(f"✅ Stocks Passed: {len(passed_stocks)}")
        print(f"❌ Stocks Failed: {len(failed_stocks)}")
        print(f"📈 Total Analyzed: {len(self.results)}")
        
        if passed_stocks:
            print("\n🎯 RECOMMENDED INVESTMENTS:")
            print("=" * 70)
            
            passed_stocks.sort(key=lambda x: x['score'], reverse=True)
            
            for i, stock in enumerate(passed_stocks[:5], 1):
                scenario = stock['investment_scenario']
                print(f"\n#{i} {stock['ticker']} - {stock['company_name'][:20]}...")
                print(f"  📊 Score: {stock['score']}/100 | Sector: {stock['sector']}")
                print(f"  💰 Current: ${scenario['current_price']:.2f} | Shares: {scenario['shares']:.1f}")
                print(f"  🛡️  Stop Loss: ${scenario['stop_loss_price']:.2f} (-8%)")
                print(f"  🎯 Take Profit: ${scenario['take_profit_price']:.2f} (+20%)")
                print(f"  ⚖️  Risk/Reward: 1:{scenario['risk_reward_ratio']:.1f}")
                print(f"  📈 Projections:")
                print(f"     • 1-Year Conservative: ${scenario['conservative_value']:.2f}")
                print(f"     • 1-Year Moderate: ${scenario['moderate_value']:.2f}") 
                print(f"     • 1-Year Aggressive: ${scenario['aggressive_value']:.2f}")
                print(f"     • Monte Carlo Avg: ${scenario['mc_avg_projection']:.2f}")
                print(f"     • Profit Probability: {scenario['mc_probability_profit']:.1%}")
        
        if failed_stocks:
            print(f"\n⏳ STOCKS TO WATCH (Need Improvement):")
            print("-" * 50)
            failed_stocks.sort(key=lambda x: x['score'], reverse=True)
            for stock in failed_stocks[:3]:
                print(f"⏳ {stock['ticker']} - Score: {stock['score']}/100 | Issues: {', '.join(stock['reasons'][:1])}")

def main():
    """Main function - RUN THIS PROGRAM"""
    
    print("🚀 WELCOME TO AI STOCK SCREENER!")
    print("This program will analyze stocks and create $1000 investment plans.")
    print("=" * 60)
    
    # STOCK LIST - MODIFY THIS WITH YOUR FAVORITE STOCKS!
    stock_tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 
        'JPM', 'JNJ', 'WMT', 'NVDA', 'DIS',
        'V', 'PG', 'HD', 'PYPL', 'NFLX',
        'COST', 'MCD', 'KO', 'PEP', 'ABBV'
    ]
    
    print(f"📈 Analyzing {len(stock_tickers)} popular stocks...")
    print("💡 Pro tip: Edit the 'stock_tickers' list to analyze your preferred stocks!")
    print("=" * 60)
    
    # Create screener instance
    screener = AIStockScreener()
    
    # Optional: Customize your investment parameters
    screener.criteria.update({
        'investment_amount': 1000,      # Change to $500, $2000, etc.
        'stop_loss_percentage': 0.08,   # 8% stop loss
        'take_profit_percentage': 0.20, # 20% take profit
    })
    
    # Run the analysis
    screener.screen_multiple_stocks(stock_tickers)
    
    # Investment strategy guidelines
    print("\n" + "=" * 70)
    print("💡 SMART INVESTING STRATEGY:")
    print("=" * 70)
    print("1. 🛡️  ALWAYS USE STOP-LOSS: Protects your capital from big losses")
    print("2. ⚖️  DIVERSIFY: Don't put all $1000 in one stock")
    print("3. 📊  POSITION SIZE: Risk only 1-2% of total portfolio per trade") 
    print("4. 🎯  TAKE PROFITS: Sell partial positions at 20-25% gains")
    print("5. 📈  REBALANCE: Review and adjust your portfolio monthly")
    print("6. 🔍  DO YOUR RESEARCH: This is AI analysis - verify with your own research!")
    print("=" * 70)
    print(f"✅ Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🚀 Happy Investing!")

if __name__ == "__main__":
    main()