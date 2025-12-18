# -*- coding: utf-8 -*-
"""
Relay Task Manager

Server implementation for handling relay control requests via socket.
"""

import socket
import pickle
import time
import sys
from typing import Optional, Generator, Any
from contextlib import contextmanager

from relay.hardware.serial_comm import SerialCommunicator
from relay.utils.relay_utils import Task, Device
from relay.constants import (
    RELAY_DISCONNECT_MSG,
    RELAY_CONNECT_MSG,
    RELAY_DISCONNECT_MSG_SEC,
    RELAY_CONNECT_MSG_SEC,
    RELAY_GET_STATE_MSG,
    RELAY_SET_STATE_MSG,
)
from relay.core.config import ConfigManager, LoggerFactory


class RelayTaskManager:
    """
    Task manager for relay control server.
    
    Handles incoming socket connections and processes relay control tasks
    using a generator-based task queue.
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        backlog: int = 5
    ):
        """
        Initialize task manager.
        
        Args:
            host: Server host address (default: from config)
            port: Server port number (default: from config)
            backlog: Maximum queued connections
        """
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        
        self.host = host or self.config.server.host
        self.port = port or self.config.server.port
        self.backlog = backlog
        
        self.logger = LoggerFactory.get_server_logger()
        
        # Initialize serial communicator
        try:
            self.serial = SerialCommunicator('server')
        except ValueError as e:
            self.logger.error(f'Failed to initialize serial: {e}')
            raise
        
        # Initialize socket
        self.socket: Optional[socket.socket] = None
        self._task_generator: Optional[Generator[str, Task, None]] = None
        self._running = False
        
        self._setup_socket()
    
    def _setup_socket(self) -> None:
        """Setup server socket."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(self.backlog)
            self.logger.info(f'Socket server initialized on {self.host}:{self.port}')
        except socket.error as e:
            self.logger.error(f'Socket setup failed: {e}')
            raise
    
    def _task_handler(self) -> Generator[str, Task, None]:
        """
        Task handler generator.
        
        Yields:
            Response string ('OK' or 'KO')
        
        Receives:
            Task objects to process
        """
        response = 'KO'
        
        while self.serial.is_open:
            task = yield response
            try:
                response = self._process_task(task)
                self.logger.info(f'[OUT_TASK] - Finished task "{task}"')
            except Exception as e:
                self.logger.error(f'[OUT_TASK] - Task failed: {e}', exc_info=True)
                response = 'KO'
    
    def _process_task(self, task: Task) -> str:
        """
        Process a relay control task.
        
        Args:
            task: Task to process
        
        Returns:
            Response string ('OK' or state data)
        """
        message = task.message
        index = task.index
        value = task.value
        
        self.logger.debug(f'Processing task: message={message}, index={index}, value={value}')
        
        # Handle different message types
        if message == RELAY_DISCONNECT_MSG:
            self.serial.usb_off(index)
            return 'OK'
        
        elif message == RELAY_CONNECT_MSG:
            self.serial.usb_on(index)
            return 'OK'
        
        elif message == RELAY_SET_STATE_MSG:
            self.serial.set_port_state(index, value)
            return 'OK'
        
        elif message == RELAY_GET_STATE_MSG:
            states = self.serial.get_all_port_states()
            return str(states)
        
        elif message == RELAY_DISCONNECT_MSG_SEC:
            self.serial.usb_off_by_value(value)
            return 'OK'
        
        elif message == RELAY_CONNECT_MSG_SEC:
            self.serial.usb_on_by_value(value)
            return 'OK'
        
        else:
            self.logger.warning(f'Unknown message type: {message}')
            return 'KO'
    
    def _handle_connection(self, connection: socket.socket, address: tuple) -> None:
        """
        Handle a client connection.
        
        Args:
            connection: Client socket connection
            address: Client address tuple
        """
        self.logger.info(f'[IN_TASK] - Connection from {address}')
        
        try:
            # Receive task data
            data = connection.recv(4096)
            if not data:
                return
            
            # Deserialize task
            task = pickle.loads(data)
            self.logger.info(f'[IN_TASK] - Received task: {task}')
            
            # Process task through generator
            if self._task_generator is None:
                self._task_generator = self._task_handler()
                next(self._task_generator)  # Initialize generator
            
            # Send task and get response
            response = self._task_generator.send(task)
            
            # Send response back to client
            response_data = pickle.dumps(response)
            connection.send(response_data)
            
            self.logger.info(f'[IN_TASK] - Sent response: {response}')
            
        except pickle.PickleError as e:
            self.logger.error(f'Pickle error: {e}')
        except Exception as e:
            self.logger.error(f'Connection handling error: {e}', exc_info=True)
        finally:
            connection.close()
    
    def start(self) -> None:
        """Start the server and begin accepting connections."""
        if self._running:
            self.logger.warning('Server is already running')
            return
        
        self._running = True
        self.logger.info('=' * 60)
        self.logger.info('USB Relay Server Started'.center(60))
        self.logger.info('=' * 60)
        self.logger.info(f'Listening on {self.host}:{self.port}')
        self.logger.info('Press Ctrl+C to stop')
        self.logger.info('-' * 60)
        
        try:
            while self._running:
                self.logger.info('[IN_TASK] - Waiting for connection...')
                
                try:
                    connection, address = self.socket.accept()
                    self._handle_connection(connection, address)
                except socket.error as e:
                    if self._running:
                        self.logger.error(f'Socket error: {e}')
                        break
                        
        except KeyboardInterrupt:
            self.logger.info('Received interrupt signal')
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the server and cleanup resources."""
        self._running = False
        
        if self._task_generator:
            try:
                self._task_generator.close()
            except Exception:
                pass
            self._task_generator = None
        
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
        
        if self.serial:
            self.serial.close()
        
        self.logger.info('Server stopped')
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
    
    def __del__(self):
        """Cleanup on deletion."""
        self.stop()


def main():
    """Main entry point for server."""
    import argparse
    
    parser = argparse.ArgumentParser(description='USB Relay Server')
    parser.add_argument('--host', type=str, help='Server host')
    parser.add_argument('--port', type=int, help='Server port')
    parser.add_argument('--log-level', type=str, default='INFO')
    
    args = parser.parse_args()
    
    try:
        with RelayTaskManager(host=args.host, port=args.port) as manager:
            manager.start()
    except Exception as e:
        print(f'Server error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()

