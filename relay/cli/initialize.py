# -*- coding: utf-8 -*-
"""
Device Initialization CLI

Command-line interface for initializing and binding devices to relay ports.
"""

import sys
import argparse
from typing import Optional

from relay.controllers.initializer import DeviceInitializer
from relay.core.config import LoggerFactory


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog='relay-init',
        description='Initialize and bind devices to relay ports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s bind ABC123456           Bind device to available relay port
  %(prog)s release ABC123456        Release device from relay port
  %(prog)s list                     List all bound devices
  %(prog)s status                   Show relay port status

For more information, visit: https://github.com/yourusername/UsbRelay
        """
    )
    
    parser.add_argument(
        'action',
        type=str,
        choices=['bind', 'release', 'list', 'status'],
        help='Action to perform'
    )
    
    parser.add_argument(
        'serial',
        type=str,
        nargs='?',
        help='Device serial number (required for bind/release)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        metavar='N',
        help='Specific relay port to use (1-based index)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force binding even if port is occupied'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    return parser.parse_args()


def run_initialization(action: str, serial_number: Optional[str] = None, **kwargs) -> int:
    """
    Run device initialization/management.
    
    Args:
        action: Action to perform (bind, release, list, status)
        serial_number: Device serial number (required for bind/release)
        **kwargs: Additional options
    
    Returns:
        Exit code (0 for success)
    """
    if action in ['bind', 'release'] and not serial_number:
        print(f'Error: Serial number required for {action} action')
        return 1
    
    logger = LoggerFactory.get_logger('InitCLI', serial_number)
    
    logger.info('=' * 60)
    logger.info(f'Device Initialization - {action.upper()}'.center(60))
    logger.info('=' * 60)
    
    try:
        if action == 'bind':
            with DeviceInitializer(serial_number) as initializer:
                success = initializer.bind_device(
                    port=kwargs.get('port'),
                    force=kwargs.get('force', False)
                )
                return 0 if success else 1
                
        elif action == 'release':
            with DeviceInitializer(serial_number) as initializer:
                success = initializer.release_device()
                return 0 if success else 1
                
        elif action == 'list':
            # List bound devices
            logger.info('Listing bound devices...')
            # Implementation needed
            return 0
            
        elif action == 'status':
            # Show relay port status
            logger.info('Relay port status:')
            # Implementation needed
            return 0
            
    except Exception as e:
        logger.error(f'Initialization error: {e}', exc_info=True)
        return 1


def main():
    """Main entry point for relay-init command."""
    args = parse_arguments()
    
    sys.exit(run_initialization(
        action=args.action,
        serial_number=args.serial,
        port=args.port,
        force=args.force
    ))


if __name__ == '__main__':
    main()

