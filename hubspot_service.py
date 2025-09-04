import requests
from config import HUBSPOT_API_KEY

def update_hubspot_contact_and_deal(email, interest):
    service_category_map = {
        "Solar & Battery": "Solar & Battery",
        "Solar": "Solar Only",
        "Battery": "Battery Only"
    }
    deal_service_category = service_category_map.get(interest, "Uncategorized")
    contact_id = None
    
    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # 1. Upsert/Update the Contact 
        upsert_url = "https://api.hubapi.com/crm/v3/objects/contacts?idProperty=email"
        upsert_payload = {
            "properties": {
                "email": email,
                "interest": interest
            }
        }
        upsert_response = requests.post(upsert_url, headers=headers, json=upsert_payload)

        if upsert_response.status_code == 409:
            error_data = upsert_response.json()
            if 'message' in error_data and 'Existing ID:' in error_data['message']:
                contact_id = error_data['message'].split('Existing ID: ')[-1]
                print(f"Contact already exists. Updating contact ID: {contact_id}")
                
                # Update logic for existing contact, note the 'interest' property is updated here
                update_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
                update_payload = {"properties": {"interest": interest}}
                update_response = requests.patch(update_url, headers=headers, json=update_payload)
                update_response.raise_for_status()
                print(f"Successfully updated interest for contact ID: {contact_id}")
        
        elif upsert_response.status_code in [200, 201]:
            contact_data = upsert_response.json()
            contact_id = contact_data['id']
            print(f"Contact upserted successfully. ID: {contact_id}")
        
        else:
            upsert_response.raise_for_status()

        # 2. Check and Update the Associated Deal (This part is now moved outside the conditional)
        if not contact_id:
            return False, "Failed to get contact ID."

        associations_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}/associations/deal"
        associations_response = requests.get(associations_url, headers=headers)
        associations_response.raise_for_status()
        associations_data = associations_response.json()

        if not associations_data.get('results'):
            print(f"No associated deals for contact {contact_id}. Skipping deal update.")
            return True, "Contact upserted, but no deal was updated."

        deal_id = associations_data['results'][0]['id']
        update_deal_url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}"
        update_deal_payload = {"properties": {"service_category": deal_service_category}}

        update_deal_response = requests.patch(update_deal_url, headers=headers, json=update_deal_payload)
        update_deal_response.raise_for_status()

        print(f"Updated 'service_category' to '{deal_service_category}' for deal ID {deal_id}.")
        return True, "Contact and associated deal updated successfully."
        
    except requests.exceptions.HTTPError as err:
        error_message = f"HubSpot API error: {err.response.text}"
        print(f"HTTP Error {err.response.status_code}: {error_message}")
        return False, error_message
    except Exception as e:
        error_message = f"Unexpected error: {e}"
        print(error_message)
        return False, error_message