import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Get the HubSpot API token from the environment
HUBSPOT_ACCESS_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")

def update_hubspot_contact_and_deal(email, interest, postcode):
    """
    Creates a new deal and associates it with a contact, then updates the contact.
    """
    if not HUBSPOT_ACCESS_TOKEN:
        print("ERROR: HubSpot API token not found.")
        return False, "HubSpot API token not found."

    headers = {
        "Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        # Step 1: Find the contact by email and get their ID and names
        print("STEP 1: Attempting to find contact by email...")
        get_contact_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{email}?idProperty=email&properties=firstname,lastname"
        contact_response = requests.get(get_contact_url, headers=headers)
        contact_response.raise_for_status()
        contact_data = contact_response.json()
        contact_id = contact_data["id"]
        print(f"SUCCESS: Found contact with ID: {contact_id}")

        first_name = contact_data["properties"].get("firstname", "")
        last_name = contact_data["properties"].get("lastname", "")
        
        full_name = f"{first_name}".strip()
        if not full_name:
            deal_name = email
        else:
            deal_name = full_name

        service_category_map = {
            "Solar & Battery": "Solar & Battery",
            "Solar": "Solar Only",
            "Battery": "Battery Only"
        }
        
        service_category_value = service_category_map.get(interest, None)
        
        if not service_category_value:
            print(f"ERROR: Invalid interest value '{interest}'.")
            raise ValueError(f"Invalid interest value: '{interest}'. It must be one of {list(service_category_map.keys())}")

        # Step 2: Create a new deal and associate it with the contact
        print("STEP 2: Creating a new deal...")
        create_deal_url = "https://api.hubapi.com/crm/v3/objects/deals"
        create_deal_payload = {
            "properties": {
                "dealname": deal_name,
                "dealstage": "appointmentscheduled",
                "service_category": service_category_value,
                "enquiry_notes": f"Postcode (form entry): {postcode}",
                "master__deal_source": "Google Ads"
            },
            "associations": [
                {
                    "to": {"id": contact_id, "type": "contact"},
                    "types": [
                        {"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}
                    ]
                }
            ]
        }
        create_deal_response = requests.post(create_deal_url, headers=headers, json=create_deal_payload)
        create_deal_response.raise_for_status()
        new_deal_id = create_deal_response.json()["id"]
        print(f"SUCCESS: New deal created with ID: {new_deal_id}")

        # Step 3: Update the contact's interest property
        print("STEP 3: Updating contact's interest property...")
        update_contact_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
        contact_payload = {"properties": {"form_submission_interest": interest}}
        requests.patch(update_contact_url, headers=headers, json=contact_payload).raise_for_status()
        print("SUCCESS: Contact interest property updated.")

        return True, f"Contact updated and new deal created (ID: {new_deal_id}) and associated."

    except requests.exceptions.RequestException as e:
        error_message = e.response.text if e.response else str(e)
        print(f"ERROR: An error occurred with the HTTP API request: {error_message}")
        return False, f"An error occurred while updating HubSpot: {error_message}"
    except ValueError as e:
        print(f"ERROR: A ValueError occurred: {e}")
        return False, str(e)
