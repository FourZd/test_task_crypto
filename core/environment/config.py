import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings using Pydantic Settings.
    
    Attributes
    ----------
    rpc_base_url : str
        Base RPC URL (network path will be added automatically)
    redis_host : str
        Redis host for caching
    redis_port : int
        Redis port
    redis_db : int
        Redis database number
    redis_password : str
        Redis password (optional)
    snowtrace_api_key : str
        Snowtrace API key for fetching ABIs (optional)
    etherscan_api_key : str
        Etherscan API key for fetching ABIs (optional)
    ankr_api_key : str
        Ankr API key for RPC access
    """
    
    rpc_base_url: str = "https://rpc.ankr.com"
    
    redis_host: str
    redis_port: int
    redis_db: int
    redis_password: str
    
    snowtrace_api_key: str
    etherscan_api_key: str
    ankr_api_key: str

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    def get_rpc_url(self, network: str) -> str:
        """
        Get RPC URL for specific network.
        
        Parameters
        ----------
        network : str
            Network name (avalanche, ethereum, etc.)
            
        Returns
        -------
        str
            Full RPC URL with API key
        """
        network_paths = {
            "avalanche": "avalanche",
            "ethereum": "eth"
        }
        network_path = network_paths.get(network, network)
        return f"{self.rpc_base_url}/{network_path}/{self.ankr_api_key}"
