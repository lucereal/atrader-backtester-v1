import json
import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from run_backtester import TestRunner


class TestTestRunner(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""

        # Mock the MassiveClient
        self.massive_client_patcher = patch('run_backtester.MassiveClient')
        self.mock_massive_client_class = self.massive_client_patcher.start()
        self.mock_massive_client = Mock()
        self.mock_massive_client_class.return_value = self.mock_massive_client
        
        # Create the TestRunner instance
        self.run_backtester = TestRunner()
    
    def tearDown(self):
        """Clean up after each test method."""
        self.massive_client_patcher.stop()
    
    def test_init(self):
        """Test that TestRunner initializes correctly."""
        self.assertIsNotNone(self.run_backtester.massive_client)
        self.mock_massive_client_class.assert_called_once()

    def load_mock_data(self, filename):
        """Load mock data from JSON file."""
        # Get the parent directory (project root)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_file_path = os.path.join(project_root, 'contract_examples', filename)
        
        with open(json_file_path, 'r') as f:
            return json.load(f)

    def create_mock_contract(self, contract_data):
        """Create a mock contract that behaves like OptionsContract."""
        mock_contract = Mock()
        
        # Set all attributes from the JSON data
        for key, value in contract_data.items():
            setattr(mock_contract, key, value)
        
        # Mock the __dict__ property to return the contract data
        mock_contract.__dict__ = contract_data
        
        # Mock Pydantic methods if they exist
        mock_contract.model_dump.return_value = contract_data
        mock_contract.model_dump_json.return_value = json.dumps(contract_data, indent=2)
        
        return mock_contract

    def create_mock_agg(self, agg_data):
        """Create a mock aggregate that behaves like the library's Agg class."""
        mock_agg = Mock()
        
        # Set all attributes from the JSON data
        for key, value in agg_data.items():
            setattr(mock_agg, key, value)
        
        # Mock the __dict__ property to return the agg data
        mock_agg.__dict__ = agg_data
        
        return mock_agg
   self.
    @patch('builtins.print')
    def test_run_options_test(self, mock_print):
        """Test the run_options_test method."""
        # Create mock contract from JSON data
        mock_contract = Mock()

        mock_data = self.load_mock_data(filename='0-SPY241202C00600000.json')
        contract_data = mock_data["contract"]
        mock_contract = self.create_mock_contract(contract_data)

        mock_contracts = [mock_contract]
        
        # Create mock aggs from JSON data
        mock_aggs = []
        for agg_data in mock_data["aggs"]["aggs"]:
            if len(agg_data) > 1:  # More than just "otc" key
                mock_agg = self.create_mock_agg(agg_data)
                mock_aggs.append(mock_agg)
        
        # Setup mock returns
        self.mock_massive_client.list_options_contracts_by_ticker.return_value = mock_contracts
        self.mock_massive_client.list_aggs.return_value = mock_aggs
        
        # Call the method
        self.run_backtester.run_options_test()
        
        # Verify the calls
        self.mock_massive_client.list_options_contracts_by_ticker.assert_called_once_with(
            "SPY", 
            contract_type="call", 
            expiration_date="2024-12-02", 
            as_of="2024-12-02", 
            strike_price=600, 
            limit=10
        )
        self.mock_massive_client.list_aggs.assert_called_once_with(
            mock_contract.ticker, 
            multiplier=1, 
            timespan="hour", 
            from_date="2024-12-02", 
            to_date="2024-12-02", 
            limit=5000
        )
        
        # Verify print was called
        mock_print.assert_called()


if __name__ == '__main__':
    unittest.main()
