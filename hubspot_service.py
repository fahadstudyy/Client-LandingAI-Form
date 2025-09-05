import os
import requests
from dotenv import load_dotenv

load_dotenv()

HUBSPOT_ACCESS_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")

def update_hubspot_contact_and_deal(email, interest):
    """
    Creates or updates a deal and associates it with a contact, then updates the contact.
    """
    if not HUBSPOT_ACCESS_TOKEN:
        return False, "HubSpot API token not found."

    headers = {
        "Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:

        get_contact_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{email}?idProperty=email&properties=firstname,lastname"
        contact_response = requests.get(get_contact_url, headers=headers)
        contact_response.raise_for_status()
        contact_data = contact_response.json()
        contact_id = contact_data["id"]

        first_name = contact_data["properties"].get("firstname", "")
        
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
            raise ValueError(f"Invalid interest value: '{interest}'. It must be one of {list(service_category_map.keys())}")


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

            update_deal_url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}"
            update_deal_payload = {
                "properties": {
                    "dealstage": "appointmentscheduled",
                    "service_category": service_category_value
                }
            }
            requests.patch(update_deal_url, headers=headers, json=update_deal_payload).raise_for_status()

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
            
            update_contact_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
            contact_payload = {"properties": {"interest": interest}}
            requests.patch(update_contact_url, headers=headers, json=contact_payload).raise_for_status()

            return True, f"Contact updated and existing deal (ID: {deal_id}) updated and associated."

        else:

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

            update_contact_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
            contact_payload = {"properties": {"interest": interest}}
            requests.patch(update_contact_url, headers=headers, json=contact_payload).raise_for_status()

            return True, f"Contact updated and new deal created (ID: {new_deal_id}) and associated."

    except requests.exceptions.RequestException as e:
        error_message = e.response.text if e.response else str(e)
        print(f"An error occurred with the HTTP API request: {error_message}")
        return False, f"An error occurred while updating HubSpot: {error_message}"
    except ValueError as e:
        return False, str(e)