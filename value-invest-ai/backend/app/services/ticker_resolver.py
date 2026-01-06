"""
Ticker Resolver Service.

Handles ticker format normalization between:
- Internal format (AAPL, PTT.BK)
- Provider formats (FMP, EOD)
- Display format for UI

Market Detection:
- US stocks: No suffix (AAPL, MSFT, GOOGL)
- Thai stocks: .BK suffix (PTT.BK, CPALL.BK, AOT.BK)
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import re


@dataclass
class TickerInfo:
    """Resolved ticker information."""
    base_ticker: str  # Base symbol without suffix (e.g., "PTT")
    display_ticker: str  # User-friendly display (e.g., "PTT")
    internal_ticker: str  # Internal format (e.g., "PTT.BK")
    market: str  # "US" or "SET"
    currency: str  # "USD" or "THB"


class TickerResolver:
    """
    Handles ticker format differences between markets and providers.

    Ticker Format Examples:
    - US: AAPL, MSFT, GOOGL (1-5 uppercase letters, sometimes with dots like BRK.A)
    - Thai: PTT.BK, SCB.BK, KBANK.BK (letters + .BK suffix)

    Provider-specific formats:
    - FMP: AAPL (US), PTT.BK (Thai)
    - EOD: AAPL.US (US), PTT.BK (Thai)
    """

    # Market identifiers
    MARKET_US = "US"
    MARKET_SET = "SET"

    # Market suffixes for internal storage
    MARKET_SUFFIXES = {
        MARKET_US: "",  # No suffix for US stocks
        MARKET_SET: ".BK",  # .BK suffix for Thai stocks
    }

    # Currency by market
    MARKET_CURRENCIES = {
        MARKET_US: "USD",
        MARKET_SET: "THB",
    }

    # Provider-specific ticker formats
    PROVIDER_FORMATS = {
        "fmp": {
            MARKET_US: "{ticker}",  # AAPL
            MARKET_SET: "{ticker}.BK",  # PTT.BK
        },
        "eod": {
            MARKET_US: "{ticker}.US",  # AAPL.US
            MARKET_SET: "{ticker}.BK",  # PTT.BK
        }
    }

    # Validation patterns
    US_TICKER_PATTERN = re.compile(r'^[A-Z]{1,5}$')
    US_TICKER_WITH_CLASS_PATTERN = re.compile(r'^[A-Z]{1,5}\.[A-Z]$')  # BRK.A, BRK.B
    THAI_TICKER_PATTERN = re.compile(r'^[A-Z0-9]{1,10}$')

    @classmethod
    def detect_market(cls, ticker: str) -> str:
        """
        Auto-detect market from ticker format.

        Args:
            ticker: Stock ticker symbol (any format)

        Returns:
            'SET' if ticker ends with .BK, 'US' otherwise
        """
        ticker = ticker.upper().strip()
        if ticker.endswith(".BK"):
            return cls.MARKET_SET
        return cls.MARKET_US

    @classmethod
    def get_base_ticker(cls, ticker: str) -> str:
        """
        Extract base ticker without any suffix.

        Args:
            ticker: Stock ticker (e.g., "PTT.BK", "AAPL.US", "AAPL")

        Returns:
            Base ticker (e.g., "PTT", "AAPL")
        """
        ticker = ticker.upper().strip()
        # Remove common suffixes
        for suffix in [".BK", ".US", ".NYSE", ".NASDAQ"]:
            if ticker.endswith(suffix):
                return ticker[:-len(suffix)]
        return ticker

    @classmethod
    def resolve(cls, ticker: str, market: Optional[str] = None) -> TickerInfo:
        """
        Resolve ticker to full information.

        Args:
            ticker: User-provided ticker (e.g., "AAPL", "PTT", "PTT.BK")
            market: Optional market override ("US" or "SET")

        Returns:
            TickerInfo with all resolved information
        """
        ticker = ticker.upper().strip()

        # Auto-detect market if not provided
        if market is None:
            market = cls.detect_market(ticker)
        else:
            market = market.upper()

        # Get base ticker
        base_ticker = cls.get_base_ticker(ticker)

        # Build internal ticker format
        suffix = cls.MARKET_SUFFIXES.get(market, "")
        internal_ticker = f"{base_ticker}{suffix}"

        # Get currency
        currency = cls.MARKET_CURRENCIES.get(market, "USD")

        return TickerInfo(
            base_ticker=base_ticker,
            display_ticker=base_ticker,
            internal_ticker=internal_ticker,
            market=market,
            currency=currency,
        )

    @classmethod
    def to_provider_format(cls, ticker: str, provider: str, market: str) -> str:
        """
        Convert ticker to provider-specific format.

        Args:
            ticker: Base ticker or internal ticker
            provider: Provider name ("fmp", "eod")
            market: Market identifier ("US" or "SET")

        Returns:
            Provider-formatted ticker
        """
        provider = provider.lower()
        market = market.upper()

        base_ticker = cls.get_base_ticker(ticker)

        if provider not in cls.PROVIDER_FORMATS:
            raise ValueError(f"Unknown provider: {provider}")

        if market not in cls.PROVIDER_FORMATS[provider]:
            raise ValueError(f"Unknown market for provider {provider}: {market}")

        template = cls.PROVIDER_FORMATS[provider][market]
        return template.format(ticker=base_ticker)

    @classmethod
    def to_internal_format(cls, ticker: str, market: str) -> str:
        """
        Convert any ticker format to internal format.

        Args:
            ticker: Ticker in any format
            market: Market identifier

        Returns:
            Internal ticker format (e.g., "AAPL", "PTT.BK")
        """
        base_ticker = cls.get_base_ticker(ticker)
        suffix = cls.MARKET_SUFFIXES.get(market.upper(), "")
        return f"{base_ticker}{suffix}"

    @classmethod
    def validate_ticker(cls, ticker: str, market: str) -> Tuple[bool, str]:
        """
        Validate ticker format for a given market.

        Args:
            ticker: Base ticker to validate
            market: Market identifier

        Returns:
            Tuple of (is_valid, error_message)
        """
        base_ticker = cls.get_base_ticker(ticker)
        market = market.upper()

        if market == cls.MARKET_US:
            if cls.US_TICKER_PATTERN.match(base_ticker):
                return True, ""
            if cls.US_TICKER_WITH_CLASS_PATTERN.match(base_ticker):
                return True, ""
            return False, f"Invalid US ticker format: {base_ticker}. Expected 1-5 uppercase letters."

        elif market == cls.MARKET_SET:
            if cls.THAI_TICKER_PATTERN.match(base_ticker):
                return True, ""
            return False, f"Invalid Thai ticker format: {base_ticker}. Expected 1-10 uppercase letters/numbers."

        return False, f"Unknown market: {market}"

    @classmethod
    def parse_user_input(cls, user_input: str) -> Tuple[str, str]:
        """
        Parse user input to extract ticker and market.

        Handles various input formats:
        - "AAPL" -> ("AAPL", "US")
        - "PTT" -> ("PTT", "US")  # Assumes US if no suffix
        - "PTT.BK" -> ("PTT", "SET")
        - "AAPL US" -> ("AAPL", "US")
        - "PTT SET" -> ("PTT", "SET")

        Args:
            user_input: User-provided string

        Returns:
            Tuple of (base_ticker, market)
        """
        parts = user_input.upper().strip().split()

        if len(parts) >= 2:
            ticker = parts[0]
            market_hint = parts[1]
            if market_hint in ["SET", "TH", "THAI", "BK"]:
                market = cls.MARKET_SET
            else:
                market = cls.MARKET_US
        else:
            ticker = parts[0] if parts else ""
            market = cls.detect_market(ticker)

        base_ticker = cls.get_base_ticker(ticker)
        return base_ticker, market
