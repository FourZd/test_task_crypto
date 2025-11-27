import logging
import sys
from dishka import Provider, provide, Scope


class LoggerProvider(Provider):
    """
    Provider for logging configuration and logger instances.
    
    Configures logging to output to console (stdout) with INFO level.
    """
    component = "logger"
    @provide(scope=Scope.APP)
    def get_logger(self) -> logging.Logger:
        """
        Provide configured logger instance.
        
        Returns
        -------
        logging.Logger
            Configured logger that writes to console
        """
        if not logging.getLogger().handlers:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(sys.stdout)
                ]
            )
        
        return logging.getLogger("blockchain_api")

