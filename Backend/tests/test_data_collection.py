import sys
from pathlib import Path
import pandas as pd
import pytest
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

# Add the parent directory to system path
sys.path.append(str(Path(__file__).parent.parent))

from app.data.data_collector import DataCollector
from app.data.data_integrator import DataIntegrator

# Test player IDs from different sources
TEST_PLAYERS = {
    'haaland': {
        'transfermarkt': '418560',
        'fbref': '1f44ac21',
        'sofifa': '239085'
    },
    'mbappe': {
        'transfermarkt': '342229',
        'fbref': '5eae500a',
        'sofifa': '231747'
    }
}

@pytest.fixture
def collector():
    return DataCollector()

@pytest.fixture
def integrator():
    return DataIntegrator()

async def test_transfermarkt_data_collection(collector):
    """Test collecting data from Transfermarkt"""
    print("\nTesting Transfermarkt data collection...")
    
    try:
        data = await collector.get_player_data(
            TEST_PLAYERS['haaland']['transfermarkt'], 
            'transfermarkt'
        )
        
        print("Transfermarkt data retrieved:")
        print(json.dumps(data, indent=2))
        
        assert data is not None
        assert isinstance(data, dict)
        assert 'name' in data
        assert 'current_value' in data
        assert 'age' in data
        
        print("✓ Transfermarkt data collection test passed")
        
    except Exception as e:
        print(f"✗ Transfermarkt test failed: {str(e)}")
        raise

async def test_fbref_data_collection(collector):
    """Test collecting data from FBref"""
    print("\nTesting FBref data collection...")
    
    try:
        data = await collector.get_player_data(
            TEST_PLAYERS['mbappe']['fbref'], 
            'fbref'
        )
        
        print("FBref data retrieved:")
        print(json.dumps(data, indent=2))
        
        assert data is not None
        assert isinstance(data, dict)
        assert 'matches' in data
        assert 'goals' in data
        assert 'assists' in data
        
        print("✓ FBref data collection test passed")
        
    except Exception as e:
        print(f"✗ FBref test failed: {str(e)}")
        raise

async def test_data_integration(integrator):
    """Test data integration from multiple sources"""
    print("\nTesting data integration...")
    
    try:
        player_ids = {
            'transfermarkt': TEST_PLAYERS['haaland']['transfermarkt'],
            'fbref': TEST_PLAYERS['haaland']['fbref']
        }
        
        integrated_data = await integrator.get_integrated_player_data(player_ids)
        
        print("Integrated data:")
        print(json.dumps(integrated_data, indent=2))
        
        assert integrated_data is not None
        assert isinstance(integrated_data, dict)
        assert 'name' in integrated_data
        assert 'performance' in integrated_data
        assert 'market_value' in integrated_data
        assert 'advanced_stats' in integrated_data['performance']
        
        print("✓ Integration test passed")
        
    except Exception as e:
        print(f"✗ Integration test failed: {str(e)}")
        raise

def test_cache_mechanism(integrator):
    """Test cache mechanism"""
    print("\nTesting cache mechanism...")
    
    try:
        # Test cache creation and reading
        test_data = {'test': 'data'}
        integrator._cache_data('test_key', test_data)
        
        cached_data = integrator._check_cache('test_key')
        assert cached_data is not None
        
        print("✓ Cache mechanism test passed")
        
    except Exception as e:
        print(f"✗ Cache test failed: {str(e)}")
        raise

async def test_error_handling(collector):
    """Test error handling with invalid data"""
    print("\nTesting error handling...")
    
    try:
        # Test with invalid player ID
        data = await collector.get_player_data('invalid_id', 'transfermarkt')
        assert data == {}
        print("✓ Invalid player ID test passed")
        
        # Test with invalid source
        try:
            await collector.get_player_data('123', 'invalid_source')
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert str(e).startswith("Invalid source")
            print("✓ Invalid source test passed")
        
        print("✓ Error handling test passed")
        
    except Exception as e:
        print(f"✗ Error handling test failed: {str(e)}")
        raise

async def run_async_tests():
    """Run all async tests"""
    collector = DataCollector()
    integrator = DataIntegrator()
    
    # Run all tests
    await test_transfermarkt_data_collection(collector)
    await test_fbref_data_collection(collector)
    await test_data_integration(integrator)
    test_cache_mechanism(integrator)
    await test_error_handling(collector)
    
    print("\n✓ All tests completed successfully!")

def run_all_tests():
    """Run all tests"""
    print("\nRunning all data collection and integration tests...")
    
    try:
        asyncio.run(run_async_tests())
        print("\n✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Tests failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_all_tests()