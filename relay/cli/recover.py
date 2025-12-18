# -*- coding: utf-8 -*-
"""
Device Recovery CLI

Command-line interface for recovering lost ADB connections.
"""

import sys
import argparse
from typing import Optional

from relay.controllers.recovery import DeviceRecoveryController
from relay.core.config import LoggerFactory


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog='relay-recover',
        description='Recover lost ADB connection using USB relay',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --serial ABC123456         Recover device ABC123456
  %(prog)s -s ABC123456 --attempts 5  Try recovery up to 5 times
  %(prog)s -s ABC123456 --force       Force recovery even if ADB is connected

For more information, visit: https://github.com/yourusername/UsbRelay
        """
    )
    
    parser.add_argument(
        '-s', '--serial',
        type=str,
        required=True,
        metavar='SERIAL',
        help='Device serial number (required)'
    )
    
    parser.add_argument(
        '--attempts',
        type=int,
        default=3,
        metavar='N',
        help='Maximum recovery attempts (default: 3)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force recovery even if device appears connected'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        metavar='SECONDS',
        help='ADB connection timeout in seconds (default: 10)'
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


def run_recovery(
    serial_number: str,
    max_attempts: int = 3,
    timeout: int = 10,
    force: bool = False
) -> int:
    """
    Run device recovery procedure.
    
    Args:
        serial_number: Device serial number
        max_attempts: Maximum recovery attempts
        timeout: ADB connection timeout
        force: Force recovery even if connected
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger = LoggerFactory.get_logger('RecoveryCLI', serial_number)
    
    logger.info('=' * 60)
    logger.info(f'Device Recovery for {serial_number}'.center(60))
    logger.info('=' * 60)
    
    try:
        with DeviceRecoveryController(serial_number) as controller:
            controller.config.adb_timeout = timeout
            controller.config.max_recovery_attempts = max_attempts
            
            if not force and controller.is_adb_connected():
                logger.info('Device is already connected via ADB')
                logger.info('Use --force to force recovery anyway')
                return 0
            
            success = controller.execute()
            
            if success:
                logger.info('=' * 60)
                logger.info('Recovery Successful'.center(60))
                logger.info('=' * 60)
                return 0
            else:
                logger.error('=' * 60)
                logger.error('Recovery Failed'.center(60))
                logger.error('=' * 60)
                return 1
                
    except Exception as e:
        logger.error(f'Recovery error: {e}', exc_info=True)
        return 1


def main():
    """Main entry point for relay-recover command."""
    args = parse_arguments()
    
    sys.exit(run_recovery(
        serial_number=args.serial,
        max_attempts=args.attempts,
        timeout=args.timeout,
        force=args.force
    ))


if __name__ == '__main__':
    main()

