#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Basic Usage Examples

Demonstrates how to use the USB Relay Controller programmatically.
"""

from relay.controllers.recovery import DeviceRecoveryController
from relay.controllers.initializer import DeviceInitializer
from relay.core.config import ConfigManager


def example_recovery():
    """Example: Recover a lost ADB connection."""
    serial_number = 'ABC123456'
    
    print(f'Recovering device: {serial_number}')
    
    # Use context manager for automatic cleanup
    with DeviceRecoveryController(serial_number) as controller:
        # Configure recovery settings
        controller.config.adb_timeout = 15
        controller.config.max_recovery_attempts = 5
        
        # Execute recovery
        success = controller.execute()
        
        if success:
            print('✓ Device recovered successfully!')
        else:
            print('✗ Recovery failed')


def example_initialization():
    """Example: Initialize and bind a device."""
    serial_number = 'ABC123456'
    
    print(f'Initializing device: {serial_number}')
    
    # Use context manager
    with DeviceInitializer(serial_number) as initializer:
        # Auto-bind to available port
        success = initializer.bind_device()
        
        if success:
            print('✓ Device bound successfully!')
        else:
            print('✗ Binding failed')
        
        # Or bind to specific port
        # success = initializer.bind_device(port=3, force=True)


def example_configuration():
    """Example: Configure the system."""
    # Get configuration manager (singleton)
    config_manager = ConfigManager()
    config = config_manager.config
    
    # Access configuration
    print(f'Database host: {config.database.host}')
    print(f'Server port: {config.server.port}')
    print(f'ADB timeout: {config.adb_timeout}')
    
    # Update configuration
    config_manager.update_config(
        adb_timeout=20,
        max_recovery_attempts=10
    )
    
    print(f'Updated ADB timeout: {config.adb_timeout}')


if __name__ == '__main__':
    print('=' * 60)
    print('USB Relay Controller - Basic Usage Examples')
    print('=' * 60)
    print()
    
    # Example 1: Configuration
    print('Example 1: Configuration')
    print('-' * 60)
    example_configuration()
    print()
    
    # Example 2: Initialization
    print('Example 2: Device Initialization')
    print('-' * 60)
    # example_initialization()  # Uncomment to run
    print('(Skipped - requires hardware)')
    print()
    
    # Example 3: Recovery
    print('Example 3: Device Recovery')
    print('-' * 60)
    # example_recovery()  # Uncomment to run
    print('(Skipped - requires hardware)')
    print()
    
    print('=' * 60)
    print('For more examples, see docs/USER_GUIDE.md')
    print('=' * 60)

