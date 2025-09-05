import os
import requests
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Get the HubSpot API token from the environment
HUBSPOT_ACCESS_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")

def update_hubspot_contact_and_deal(email, interest):
    """
    Creates or updates a deal and associates it with a contact, then updates the contact.
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

        # Step 2: Search for an existing deal
        print(f"STEP 2: Searching for deal with name: '{deal_name}'...")
        search_deal_url = "https://api.hubapi.com/crm/v3/objects/deals/search"
        search_payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "dealname",
                            "operator": "EQ",
                            "value": deal_name
                        }
                    ]
                }
            ],
            "limit": 1
        }
        search_response = requests.post(search_deal_url, headers=headers, json=search_payload)
        search_response.raise_for_status()
        search_results = search_response.json().get("results", [])
        
        deal_id = None
        if search_results:
            deal_id = search_results[0]["id"]
            print(f"SUCCESS: Found existing deal with ID: {deal_id}")
            
            # Update the existing deal's properties and associate it with the contact
            print(f"STEP 2A: Updating existing deal with ID: {deal_id}...")
            update_deal_url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}"
            update_deal_payload = {
                "properties": {
                    "dealstage": "appointmentscheduled",
                    "service_category": service_category_value
                }
            }
            requests.patch(update_deal_url, headers=headers, json=update_deal_payload).raise_for_status()
            print("SUCCESS: Deal properties updated.")

            # Associate the existing deal with the contact
            print("STEP 2B: Associating existing deal with contact...")
            associate_url = "https://api.hubapi.com/crm/v3/associations/deals/contacts/batch/create"
            association_payload = {
                "inputs": [
                    {
                        "from": { "id": deal_id },
                        "to": { "id": contact_id },
                        "type": "deal_to_contact"
                    }
                ]
            }
            requests.post(associate_url, headers=headers, json=association_payload).raise_for_status()
            print("SUCCESS: Existing deal associated with contact.")
            
            # Step 3: Update the contact's interest property
            print("STEP 3: Updating contact's interest property...")
            update_contact_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
            contact_payload = {"properties": {"interest": interest}}
            requests.patch(update_contact_url, headers=headers, json=contact_payload).raise_for_status()
            print("SUCCESS: Contact interest property updated.")

            return True, f"Contact updated and existing deal (ID: {deal_id}) updated and associated."

        else:
            print("INFO: No existing deal found. Creating a new one...")
            # If no deal is found, create a new one
            create_deal_url = "https://api.hubapi.com/crm/v3/objects/deals"
            create_deal_payload = {
                "properties": {
                    "dealname": deal_name,
                    "dealstage": "appointmentscheduled",
                    "service_category": service_category_value
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

            # Update the contact's interest property
            print("STEP 3: Updating contact's interest property...")
            update_contact_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
            contact_payload = {"properties": {"interest": interest}}
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