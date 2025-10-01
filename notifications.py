"""
Notification system for arbitrage opportunities
Supports: Console, Discord, Telegram
"""
import requests
import json
from datetime import datetime
from typing import Dict, Any
import config


class NotificationService:
    """Handles sending alerts about arbitrage opportunities"""
    
    def __init__(self):
        self.alert_method = config.ALERT_METHOD
        self.discord_webhook = config.DISCORD_WEBHOOK_URL
        self.telegram_token = config.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = config.TELEGRAM_CHAT_ID
    
    def send_alert(self, opportunity: Dict[str, Any]) -> bool:
        """
        Send alert about an arbitrage opportunity
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            bool: True if alert sent successfully
        """
        message = self._format_message(opportunity)
        
        if self.alert_method == "discord":
            return self._send_discord(message, opportunity)
        elif self.alert_method == "telegram":
            return self._send_telegram(message)
        else:  # console
            return self._send_console(message)
    
    def _format_message(self, opp: Dict[str, Any]) -> str:
        """Format opportunity data into readable message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""
🚨 ARBITRAGE OPPORTUNITY DETECTED 🚨
Time: {timestamp}

📊 Market Details:
Polymarket: {opp.get('polymarket_question', 'N/A')}
Kalshi: {opp.get('kalshi_title', 'N/A')}

💰 Opportunity Type: {opp.get('type', 'N/A')}

💵 Prices:
  • Polymarket {opp.get('type', '').split('-')[0]}: ${opp.get('poly_price', 0):.4f}
  • Kalshi {opp.get('type', '').split('-')[1] if '-' in opp.get('type', '') else ''}: ${opp.get('kalshi_price', 0):.4f}

📈 Profit Margin (Gross): {opp.get('profit_margin', 0)*100:.2f}%
💸 Profit Margin (Net): {opp.get('net_profit_margin', 0)*100:.2f}%

⚠️ Risk Score: {opp.get('risk_score', 'N/A')}/10
📍 Similarity Score: {opp.get('similarity_score', 0)*100:.1f}%

💡 Example Trade ($1000):
  • Expected Net Profit: ${opp.get('expected_profit_1k', 0):.2f}
  • ROI: {opp.get('roi_1k', 0)*100:.2f}%
"""
        return message.strip()
    
    def _send_console(self, message: str) -> bool:
        """Print to console"""
        print("\n" + "="*60)
        print(message)
        print("="*60 + "\n")
        return True
    
    def _send_discord(self, message: str, opp: Dict[str, Any]) -> bool:
        """Send alert via Discord webhook"""
        if not self.discord_webhook:
            print("⚠️  Discord webhook not configured")
            return False
        
        try:
            # Create rich embed for Discord
            embed = {
                "title": "🚨 Arbitrage Opportunity",
                "description": f"**{opp.get('type', 'Unknown')} Opportunity**",
                "color": 3066993 if opp.get('net_profit_margin', 0) > 0.05 else 15844367,
                "fields": [
                    {
                        "name": "📊 Polymarket",
                        "value": opp.get('polymarket_question', 'N/A')[:100],
                        "inline": False
                    },
                    {
                        "name": "📊 Kalshi",
                        "value": opp.get('kalshi_title', 'N/A')[:100],
                        "inline": False
                    },
                    {
                        "name": "💵 Prices",
                        "value": f"Poly: ${opp.get('poly_price', 0):.4f} | Kalshi: ${opp.get('kalshi_price', 0):.4f}",
                        "inline": True
                    },
                    {
                        "name": "📈 Net Profit",
                        "value": f"{opp.get('net_profit_margin', 0)*100:.2f}%",
                        "inline": True
                    },
                    {
                        "name": "⚠️ Risk Score",
                        "value": f"{opp.get('risk_score', 'N/A')}/10",
                        "inline": True
                    },
                    {
                        "name": "💡 $1k Trade Profit",
                        "value": f"${opp.get('expected_profit_1k', 0):.2f}",
                        "inline": True
                    }
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": f"Similarity: {opp.get('similarity_score', 0)*100:.1f}%"
                }
            }
            
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(
                self.discord_webhook,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 204:
                print("✅ Discord alert sent successfully")
                return True
            else:
                print(f"❌ Discord alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending Discord alert: {e}")
            return False
    
    def _send_telegram(self, message: str) -> bool:
        """Send alert via Telegram bot"""
        if not self.telegram_token or not self.telegram_chat_id:
            print("⚠️  Telegram not configured")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                print("✅ Telegram alert sent successfully")
                return True
            else:
                print(f"❌ Telegram alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending Telegram alert: {e}")
            return False
    
    def send_system_message(self, message: str, level: str = "info"):
        """Send system status message"""
        prefix = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅"
        }.get(level, "ℹ️")
        
        formatted = f"{prefix} {message}"
        
        if self.alert_method == "console":
            print(formatted)
        # Could extend to send system messages to Discord/Telegram as well


# Global instance
notifier = NotificationService()
