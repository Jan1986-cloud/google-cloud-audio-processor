import functions_framework

# Dit is de standaard manier om een functie te registreren voor een GCS event.
@functions_framework.cloud_event
def hello_gcs(cloud_event):
    """
    Een standaard CloudEvent functie die reageert op een GCS event.
    """
    data = cloud_event.data

    event_id = cloud_event["id"]
    event_type = cloud_event["type"]

    bucket = data["bucket"]
    name = data["name"]
    metageneration = data["metageneration"]
    timeCreated = data["timeCreated"]
    updated = data["updated"]

    print(f"--- GOOGLE TEMPLATE EXECUTED ---")
    print(f"Event ID: {event_id}")
    print(f"Event Type: {event_type}")
    print(f"Bucket: {bucket}")
    print(f"File: {name}")
    print(f"--- Als je dit ziet, is het probleem opgelost en lag het aan onze vorige code/configuratie. ---")
