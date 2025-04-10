# **NPC Assignment - Custom Market Making Strategy**

This repository contains the implementation of a custom market-making strategy developed as part of the NPC assignment for BITS Goa.

## **Overview**
The strategy is designed to work with Hummingbot, an open-source framework for algorithmic trading. It leverages technical indicators like volatility, trend analysis, and inventory management to dynamically place bid and ask orders on a centralized exchange.

The strategy operates in **paper trading mode** for testing purposes, ensuring no real funds are used during development.

---

## **Features**
1. **Volatility-Based Spread Adjustment**:
   - Uses Bollinger Bands to calculate market volatility.
   - Dynamically adjusts bid and ask spreads based on volatility levels.

2. **Trend Detection**:
   - Implements moving average crossovers to detect uptrends or downtrends.
   - Adjusts spreads accordingly to align with market direction.

3. **Inventory Management**:
   - Maintains a balanced portfolio (50% BTC, 50% USDT).
   - Dynamically adjusts spreads to rebalance inventory when needed.

4. **Paper Trading Compatible**:
   - Fully tested in paper trading mode for safe experimentation.

---

## **How It Works**
1. The bot calculates key indicators:
   - **Volatility**: Measures market fluctuations using Bollinger Bands.
   - **Trend**: Determines market direction using moving averages.
   - **Inventory Skew**: Tracks portfolio imbalance to adjust order placement.
   
2. Based on these indicators, the bot:
   - Places bid and ask orders around the mid-price with calculated spreads.
   - Refreshes orders periodically to adapt to changing market conditions.

3. All trades are simulated in paper trading mode, ensuring no real funds are used.

---

## **Setup Instructions**
1. Clone this repository:
git clone https://github.com/Divyanshomer-io/npc_assignment.git

2. Navigate to the `scripts` directory of your Hummingbot installation:
cd ~/hummingbot/scripts

3. Copy the strategy file from this repository:
cp ~/npc_assignment/custom_mm_strategy.py .

4. Start Hummingbot and run the strategy:
./start
start --script custom_mm_strategy.py


---

## **Parameters**
| Parameter              | Description                                       | Default Value |
|------------------------|---------------------------------------------------|---------------|
| `order_amount`         | Size of each order                                | `0.01 BTC`    |
| `base_spread`          | Base spread for bid/ask orders                    | `0.05%`       |
| `order_refresh_time`   | Time interval (in seconds) between order refreshes | `300 seconds` |
| `target_base_pct`      | Target portfolio allocation for base asset         | `50%`         |
| `max_skew`             | Maximum inventory skew allowed                    | `0.5`         |

---

## **Example Output**
When running the bot, you can expect logs like this:

Volatility: 0.0276 | Trend: 1 | Skew: 0
Bid Spread: 0.0008 | Ask Spread: 0.0001
Active orders: 2

---

## **Acknowledgments**
- This project was developed as part of the NPC assignment for BITS Goa.
- Special thanks to the Hummingbot community for their open-source framework.
