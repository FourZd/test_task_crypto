from dishka import Provider, Scope, provide
from core.environment.config import Settings


class EnvironmentProvider(Provider):
    """
    Provider for environment configuration.
    """
    
    component = "environment"
    scope = Scope.APP

    @provide
    def get_environment(self) -> Settings:
        """
        Provide application settings.
        
        Returns
        -------
        Settings
            Application settings instance
        """
        return Settings()

