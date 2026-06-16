import json

def get_weather(location: str, unit: str = "celsius"):
    dummy_data = {
        "Vancouver": {"celsius": "8°C", "fahrenheit": "46°F"},
        "Paris": {"celsius": "12°C", "fahrenheit": "54°F"}
    }
    return dummy_data.get(location, {"celsius": "N/A", "fahrenheit": "N/A"})[unit]

result = get_weather("Vancouver", "celsius")
print(json.dumps({"celsius": result}))