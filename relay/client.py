# -*- coding: utf-8 -*-
"""
Relay Client

Client for sending relay control requests to the server.
"""

import socket
import pickle
from typing import Optional, Any

from relay.utils.relay_utils import Task
from relay.core.config import ConfigManager


class RelayClient:
    """
    Client for communicating with relay server.
    
    Provides a high-level interface for sending relay control commands
    to the server and receiving responses.
    """
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        """
        Initialize relay client.
        
        Args:
            host: Server host address (default: from config)
            port: Server port number (default: from config)
        """
        config = ConfigManager().config
        
        self.host = host or config.server.host
        self.port = port or config.server.port
        self.timeout = 5.0
    
    def send_request(self, task: Task, timeout: Optional[float] = None) -> Optional[Any]:
        """
        Send relay control request to server.
        
        Args:
            task: Task to send
            timeout: Connection timeout (default: 5.0 seconds)
        
        Returns:
            Response from server or None if failed
        """
        connection = None
        
        try:
            connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connection.settimeout(timeout or self.timeout)
            connection.connect((self.host, self.port))
            
            # Send task
            data = pickle.dumps(task)
            connection.send(data)
            
            # Receive response
            response_data = connection.recv(4096)
            response = pickle.loads(response_data)
            
            return response
            
        except socket.timeout:
            return None
        except (socket.error, pickle.PickleError) as e:
            return None
        finally:
            if connection:
                connection.close()
    
    def __repr__(self):
        """String representation."""
        return f'RelayClient(host={self.host}, port={self.port})'

