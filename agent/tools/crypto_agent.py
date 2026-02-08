"""
GLTCH Crypto Agent
Advanced crypto/blockchain capabilities beyond basic wallet
"""

import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from decimal import Decimal
from enum import Enum


class NetworkType(Enum):
    """Supported blockchain networks"""
    ETHEREUM = "ethereum"
    BASE = "base"
    OPTIMISM = "optimism"
    ARBITRUM = "arbitrum"
    POLYGON = "polygon"
    SOLANA = "solana"


class TradeType(Enum):
    """Trade types"""
    SWAP = "swap"
    LIMIT_ORDER = "limit_order"
    DCA = "dca"  # Dollar-cost averaging
    STOP_LOSS = "stop_loss"


@dataclass
class TokenInfo:
    """Token information"""
    address: str
    symbol: str
    name: str
    decimals: int
    network: NetworkType
    price_usd: Optional[Decimal] = None
    market_cap: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None
    change_24h: Optional[float] = None
    logo_url: Optional[str] = None


@dataclass
class WalletPosition:
    """Wallet position in a token"""
    token: TokenInfo
    balance: Decimal
    value_usd: Decimal
    allocation_pct: float
    avg_cost: Optional[Decimal] = None
    pnl_usd: Optional[Decimal] = None
    pnl_pct: Optional[float] = None


@dataclass
class TradeOrder:
    """Trade order"""
    id: str
    type: TradeType
    token_in: str
    token_out: str
    amount_in: Decimal
    network: NetworkType
    
    # For limit orders
    target_price: Optional[Decimal] = None
    
    # For DCA
    interval_hours: Optional[int] = None
    remaining_iterations: Optional[int] = None
    
    # Status
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    tx_hash: Optional[str] = None
    amount_out: Optional[Decimal] = None
    error: Optional[str] = None


class CryptoAgent:
    """
    Advanced crypto capabilities for GLTCH
    
    Features:
    - Portfolio tracking across chains
    - Token swaps via DEX aggregators
    - Limit orders and DCA
    - Price alerts
    - Gas optimization
    - Airdrop hunting
    - NFT operations
    """
    
    def __init__(self, private_key: Optional[str] = None):
        self.private_key = private_key or os.getenv('GLTCH_WALLET_KEY')
        self._positions: Dict[str, WalletPosition] = {}
        self._orders: Dict[str, TradeOrder] = {}
        self._price_alerts: Dict[str, dict] = {}
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize crypto agent"""
        if not self.private_key:
            print("⚠ Crypto Agent: No wallet key configured")
            return False
        
        try:
            from web3 import Web3
            from eth_account import Account
            
            self.account = Account.from_key(self.private_key)
            self.address = self.account.address
            
            # Initialize Web3 providers for each network
            self._providers = {
                NetworkType.ETHEREUM: Web3(Web3.HTTPProvider(
                    os.getenv('ETH_RPC_URL', 'https://eth.llamarpc.com')
                )),
                NetworkType.BASE: Web3(Web3.HTTPProvider(
                    os.getenv('BASE_RPC_URL', 'https://mainnet.base.org')
                )),
            }
            
            self._initialized = True
            print(f"✓ Crypto Agent initialized: {self.address}")
            return True
            
        except Exception as e:
            print(f"✗ Crypto Agent initialization failed: {e}")
            return False
    
    async def get_portfolio(self) -> Dict[str, Any]:
        """Get complete portfolio overview"""
        if not self._initialized:
            return {"error": "Not initialized"}
        
        positions = []
        total_value = Decimal('0')
        
        for network in NetworkType:
            if network in self._providers:
                network_positions = await self._get_network_positions(network)
                positions.extend(network_positions)
                for pos in network_positions:
                    total_value += pos.value_usd
        
        # Calculate allocations
        for pos in positions:
            pos.allocation_pct = float(pos.value_usd / total_value * 100) if total_value > 0 else 0
        
        return {
            "address": self.address,
            "total_value_usd": float(total_value),
            "positions": [
                {
                    "symbol": p.token.symbol,
                    "balance": str(p.balance),
                    "value_usd": float(p.value_usd),
                    "allocation_pct": round(p.allocation_pct, 2),
                    "network": p.token.network.value,
                }
                for p in sorted(positions, key=lambda x: x.value_usd, reverse=True)
            ]
        }
    
    async def _get_network_positions(self, network: NetworkType) -> List[WalletPosition]:
        """Get positions on a specific network"""
        positions = []
        web3 = self._providers.get(network)
        if not web3:
            return positions
        
        try:
            # Get native balance
            balance_wei = web3.eth.get_balance(self.address)
            balance = Decimal(str(balance_wei)) / Decimal('1e18')
            
            # Get ETH price (simplified)
            eth_price = await self._get_token_price("ETH")
            value_usd = balance * eth_price if eth_price else Decimal('0')
            
            if balance > 0:
                positions.append(WalletPosition(
                    token=TokenInfo(
                        address="0x0",
                        symbol="ETH",
                        name="Ethereum",
                        decimals=18,
                        network=network,
                        price_usd=eth_price
                    ),
                    balance=balance,
                    value_usd=value_usd,
                    allocation_pct=0
                ))
            
        except Exception as e:
            print(f"Error getting {network.value} positions: {e}")
        
        return positions
    
    async def _get_token_price(self, symbol: str) -> Optional[Decimal]:
        """Get token price from price feed"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.coingecko.com/api/v3/simple/price",
                    params={"ids": symbol.lower(), "vs_currencies": "usd"}
                )
                if response.status_code == 200:
                    data = response.json()
                    if symbol.lower() in data:
                        return Decimal(str(data[symbol.lower()]["usd"]))
        except Exception:
            pass
        return None
    
    async def swap_tokens(
        self,
        token_in: str,
        token_out: str,
        amount: str,
        network: NetworkType = NetworkType.BASE,
        slippage: float = 0.5
    ) -> Dict[str, Any]:
        """
        Swap tokens using DEX aggregator
        
        Args:
            token_in: Input token symbol or address
            token_out: Output token symbol or address  
            amount: Amount of input token
            network: Network to use
            slippage: Slippage tolerance (percentage)
        """
        if not self._initialized:
            return {"success": False, "error": "Not initialized"}
        
        try:
            # In production, would use 0x, 1inch, or ParaSwap API
            # This is a simplified implementation
            
            order = TradeOrder(
                id=f"swap_{datetime.now().timestamp()}",
                type=TradeType.SWAP,
                token_in=token_in,
                token_out=token_out,
                amount_in=Decimal(amount),
                network=network,
                status="pending"
            )
            
            self._orders[order.id] = order
            
            # Would execute actual swap here
            return {
                "success": True,
                "order_id": order.id,
                "status": "pending",
                "message": f"Swapping {amount} {token_in} for {token_out}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_limit_order(
        self,
        token_in: str,
        token_out: str,
        amount: str,
        target_price: str,
        network: NetworkType = NetworkType.BASE
    ) -> Dict[str, Any]:
        """Create a limit order"""
        if not self._initialized:
            return {"success": False, "error": "Not initialized"}
        
        order = TradeOrder(
            id=f"limit_{datetime.now().timestamp()}",
            type=TradeType.LIMIT_ORDER,
            token_in=token_in,
            token_out=token_out,
            amount_in=Decimal(amount),
            network=network,
            target_price=Decimal(target_price)
        )
        
        self._orders[order.id] = order
        
        return {
            "success": True,
            "order_id": order.id,
            "message": f"Limit order created: Buy {token_out} at ${target_price}"
        }
    
    async def create_dca(
        self,
        token_in: str,
        token_out: str,
        amount_per_buy: str,
        interval_hours: int,
        num_buys: int,
        network: NetworkType = NetworkType.BASE
    ) -> Dict[str, Any]:
        """Create a DCA (dollar-cost averaging) strategy"""
        if not self._initialized:
            return {"success": False, "error": "Not initialized"}
        
        order = TradeOrder(
            id=f"dca_{datetime.now().timestamp()}",
            type=TradeType.DCA,
            token_in=token_in,
            token_out=token_out,
            amount_in=Decimal(amount_per_buy),
            network=network,
            interval_hours=interval_hours,
            remaining_iterations=num_buys
        )
        
        self._orders[order.id] = order
        
        total_amount = Decimal(amount_per_buy) * num_buys
        duration_days = (interval_hours * num_buys) / 24
        
        return {
            "success": True,
            "order_id": order.id,
            "message": f"DCA created: ${amount_per_buy} of {token_out} every {interval_hours}h for {duration_days:.1f} days (${total_amount} total)"
        }
    
    async def set_price_alert(
        self,
        token: str,
        target_price: str,
        condition: str = "above"  # "above" or "below"
    ) -> Dict[str, Any]:
        """Set a price alert"""
        alert_id = f"alert_{token}_{condition}_{target_price}"
        
        self._price_alerts[alert_id] = {
            "token": token,
            "target_price": Decimal(target_price),
            "condition": condition,
            "created_at": datetime.now(),
            "triggered": False
        }
        
        return {
            "success": True,
            "alert_id": alert_id,
            "message": f"Alert set: Notify when {token} is {condition} ${target_price}"
        }
    
    async def check_gas_prices(self) -> Dict[str, Any]:
        """Get current gas prices across networks"""
        gas_prices = {}
        
        for network, web3 in self._providers.items():
            try:
                gas_wei = web3.eth.gas_price
                gas_gwei = gas_wei / 1e9
                gas_prices[network.value] = {
                    "gwei": round(gas_gwei, 2),
                    "estimated_swap_cost_usd": round(gas_gwei * 150000 / 1e9 * 2000, 2)  # Rough estimate
                }
            except Exception:
                pass
        
        return gas_prices
    
    async def find_airdrops(self) -> List[Dict[str, Any]]:
        """Find potential airdrop opportunities"""
        # In production, would check various protocols for airdrop eligibility
        return [
            {
                "protocol": "Example Protocol",
                "action": "Bridge to L2 and swap",
                "estimated_value": "Unknown",
                "difficulty": "Easy"
            }
        ]
    
    def get_orders(self) -> List[Dict[str, Any]]:
        """Get all orders"""
        return [
            {
                "id": o.id,
                "type": o.type.value,
                "token_in": o.token_in,
                "token_out": o.token_out,
                "amount_in": str(o.amount_in),
                "status": o.status,
                "created_at": o.created_at.isoformat()
            }
            for o in self._orders.values()
        ]
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if order_id in self._orders:
            self._orders[order_id].status = "cancelled"
            return True
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get crypto agent status"""
        return {
            "initialized": self._initialized,
            "address": getattr(self, 'address', None),
            "networks": [n.value for n in self._providers.keys()] if self._initialized else [],
            "pending_orders": sum(1 for o in self._orders.values() if o.status == "pending"),
            "active_alerts": sum(1 for a in self._price_alerts.values() if not a["triggered"])
        }
