# -*- coding: utf-8 -*-
"""
Relay Server CLI

Command-line interface for starting the relay server.
"""

import sys
import argparse
import signal
from typing import Optional

from relay.server.task_manager import RelayTaskManager
from relay.core.config import LoggerFactory


def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    logger = LoggerFactory.get_server_logger()
    logger.info(f'Received signal {signum}, shutting down...')
    sys.exit(0)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog='relay-server',
        description='USB Relay Server - Controls USB relay hardware',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    Start server with default settings
  %(prog)s --port 12345       Start server on custom port
  %(prog)s --host 0.0.0.0     Listen on all interfaces
  %(prog)s --log-level DEBUG  Enable debug logging

For more information, visit: https://github.com/yourusername/UsbRelay
        """
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='Server host address (default: localhost)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=11222,
        help='Server port number (default: 11222)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    return parser.parse_args()


def run_server(
    host: Optional[str] = None,
    port: Optional[int] = None,
    log_level: str = 'INFO'
) -> int:
    """
    Start the relay server.
    
    Args:
        host: Server host address
        port: Server port number
        log_level: Logging level
    
    Returns:
        Exit code (0 for success)
    """
    # Setup signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    logger = LoggerFactory.get_server_logger()
    logger.info('=' * 60)
    logger.info('USB Relay Server Starting'.center(60))
    logger.info('=' * 60)
    
    try:
        # Create and start task manager
        task_manager = RelayTaskManager(host=host, port=port)
        
        logger.info(f'Server listening on {task_manager.host}:{task_manager.port}')
        logger.info('Press Ctrl+C to stop server')
        logger.info('-' * 60)
        
        # Start server
        task_manager.start()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info('Server stopped by user')
        return 0
        
    except Exception as e:
        logger.error(f'Server error: {e}', exc_info=True)
        return 1


def main():
    """Main entry point for relay-server command."""
    args = parse_arguments()
    
    sys.exit(run_server(
        host=args.host,
        port=args.port,
        log_level=args.log_level
    ))


if __name__ == '__main__':
    main()

