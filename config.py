import os
import dotenv

# Load environment variables
dotenv.load_dotenv()

# HubSpot API Key
HUBSPOT_API_KEY = os.environ.get('HUBSPOT_API_KEY')
