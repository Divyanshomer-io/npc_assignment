from decimal import Decimal
import pandas as pd
import numpy as np
import random
import asyncio
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
from hummingbot.core.data_type.common import OrderType, TradeType

class CustomMarketMaker(ScriptStrategyBase):
    """
    BITS GOA Assignment - Custom Market Making Strategy
    Features:
    - Volatility-adjusted spreads using Bollinger Bands
    - Trend detection with moving averages
    - Inventory management system
    - Paper trading compatible
    """
    
    markets = {"binance_paper_trade": {"BTC-USDT"}}
    
    order_amount = Decimal("0.01")  
    base_spread = Decimal("0.0005")   
    min_spread = Decimal("0.0001")    
    max_spread = Decimal("0.01")     
    order_refresh_time = 150          
    
    
    bb_length = 20        # Bollinger band period
    bb_std = 2.0         
    fast_ma = 10         
    slow_ma = 50          
    
    
    target_base_pct = Decimal("0.5")  
    max_skew = Decimal("0.5")         
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.price_data = []  
        self.last_refresh = 0 
        self.active_orders = {}  
        self.trade_count = 0
        
        
        self._init_price_data()
        
        
        self.debug_mode = True  
    
    def _init_price_data(self):
        """Seed initial price data for indicator calculation"""
        
        base = 80000
        for i in range(100):
            # Add some randomness that looks like real price movement
            noise = random.uniform(-0.002, 0.002)
            drift = 0.0001 * (i - 50)
            self.price_data.append(float(base * (1 + noise + drift)))
    
    def on_tick(self):
        """Main strategy logic - called on each tick"""
        try:
            now = self.current_timestamp
            
            
            if now - self.last_refresh < self.order_refresh_time:
                return
                
            self.last_refresh = now
            
            
            exchange = list(self.markets.keys())[0]  
            pair = list(self.markets[exchange])[0]   
            connector = self.connectors[exchange]    
            
            
            if not connector.ready:
                if self.debug_mode:
                    self.logger().info("Connector not ready")
                return
            
            
            mid_price = connector.get_mid_price(pair)
            if not mid_price:  
                return
                
            
            self.price_data.append(float(mid_price))
            
            if len(self.price_data) > 100:
                self.price_data.pop(0)
            
            
            vol = self._calc_volatility()
            trend = self._calc_trend()
            skew = self._calc_inventory_skew(exchange, pair)
            
            
            self.logger().info(f"Volatility: {vol:.4f} | Trend: {trend} | Skew: {skew:.4f}")
            
            
            bid_spread = self._calc_bid_spread(vol, trend, skew)
            ask_spread = self._calc_ask_spread(vol, trend, skew)
            
            self.logger().info(f"Bid Spread: {bid_spread:.4f} | Ask Spread: {ask_spread:.4f}")
            
            
            if self._check_balance(exchange, pair):
                
                asyncio.create_task(self._refresh_orders(exchange, pair, mid_price, bid_spread, ask_spread))
            else:
                self.logger().warning("Insufficient balance for orders")
                
        except Exception as e:
            
            self.logger().error(f"Error in on_tick: {str(e)}")
    
    def _calc_volatility(self):
        """Calculate market volatility using Bollinger Bands width"""
        
        if len(self.price_data) < self.bb_length:
            return Decimal("0.005")
            
        
        prices = pd.Series(self.price_data[-self.bb_length:])
        
        
        mean = prices.mean()
        stdev = prices.std()
        
        upper = mean + (stdev * self.bb_std)
        lower = mean - (stdev * self.bb_std)
        
        
        bandwidth = (upper - lower) / mean
        
       
        return Decimal(str(bandwidth)).quantize(Decimal("0.0001"))
    
    def _calc_trend(self):
        """Detect market trend using moving average crossover"""
        
        if len(self.price_data) < self.slow_ma:
            return 0 
        
        prices = np.array(self.price_data)
        
        fast_ma_val = np.mean(prices[-self.fast_ma:])
        slow_ma_val = np.mean(prices[-self.slow_ma:])
        
        if fast_ma_val > slow_ma_val * 1.002:
            return 1  # Uptrend
        elif fast_ma_val < slow_ma_val * 0.998:
            return -1  # Downtrend
        else:
            return 0  # Sideways/neutral
    
    def _calc_inventory_skew(self, exchange, trading_pair):
        """Calculate inventory skew factor based on asset balance"""
        connector = self.connectors[exchange]
        base, quote = trading_pair.split("-")
        
        base_bal = connector.get_balance(base)
        quote_bal = connector.get_balance(quote)
        mid_price = connector.get_mid_price(trading_pair)
        
        total_value = (base_bal * mid_price) + quote_bal
        
        if total_value == Decimal("0"):
            return Decimal("0")
        
        current_ratio = (base_bal * mid_price) / total_value
        
        raw_skew = (current_ratio - self.target_base_pct) / self.max_skew
        
        capped_skew = max(min(raw_skew, Decimal("1")), Decimal("-1"))
        
        return capped_skew.quantize(Decimal("0.0001"))
    
    def _calc_bid_spread(self, volatility, trend, inventory_skew):
        """Calculate optimal bid spread based on market conditions"""
        spread = self.base_spread
        
        volatility_factor = Decimal("1") + volatility
        spread *= volatility_factor
        
        if trend > 0:
            spread *= Decimal("0.8")  
        elif trend < 0:
            spread *= Decimal("1.2")  
        
        spread *= (Decimal("1") + inventory_skew)
        
        spread = max(spread, self.min_spread)
        spread = min(spread, self.max_spread)
        
        return spread.quantize(Decimal("0.0001"))
    
    def _calc_ask_spread(self, volatility, trend, inventory_skew):
        """Calculate optimal ask spread based on market conditions"""
        spread = self.base_spread
        
        volatility_factor = Decimal("1") + volatility
        spread *= volatility_factor
        
        if trend > 0:
            spread *= Decimal("1.2") 
        elif trend < 0:
            spread *= Decimal("0.8")  
        
        spread *= (Decimal("1") - inventory_skew)
        
        spread = max(spread, self.min_spread)
        spread = min(spread, self.max_spread)
        
        return spread.quantize(Decimal("0.0001"))
    
    def _check_balance(self, exchange, trading_pair):
        """Check if we have sufficient balance to place orders"""
        connector = self.connectors[exchange]
        base, quote = trading_pair.split("-")
        
        base_avail = connector.get_available_balance(base)
        quote_avail = connector.get_available_balance(quote)
        
        mid_price = connector.get_mid_price(trading_pair)
        
        if base_avail < self.order_amount:
            return False
        
        quote_needed = self.order_amount * mid_price
        if quote_avail < quote_needed:
            return False
        
        return True
    
    async def _refresh_orders(self, exchange, trading_pair, mid_price, bid_spread, ask_spread):
        """Place new orders after canceling existing ones"""
        try:
            connector = self.connectors[exchange]
            
            bid_price = (mid_price * (Decimal("1") - bid_spread)).quantize(Decimal("0.01"))
            ask_price = (mid_price * (Decimal("1") + ask_spread)).quantize(Decimal("0.01"))
            
            try:
                await connector.cancel_all(trading_pair)
                self.active_orders = {}  
            except Exception as e:
                self.logger().error(f"Error canceling orders: {str(e)}")
            
            
            bid_id = connector.buy(
                trading_pair=trading_pair,
                amount=self.order_amount,
                order_type=OrderType.LIMIT,
                price=bid_price
            )
            
            ask_id = connector.sell(
                trading_pair=trading_pair,
                amount=self.order_amount,
                order_type=OrderType.LIMIT,
                price=ask_price
            )
            
            self.active_orders[bid_id] = {
                "side": "buy",
                "price": bid_price,
                "amount": self.order_amount,
                "time": self.current_timestamp
            }
            
            self.active_orders[ask_id] = {
                "side": "sell",
                "price": ask_price,
                "amount": self.order_amount,
                "time": self.current_timestamp
            }
            
            self.logger().info(f"Active orders: {len(self.active_orders)}")
            
        except Exception as e:
            self.logger().error(f"Order refresh error: {str(e)}")
