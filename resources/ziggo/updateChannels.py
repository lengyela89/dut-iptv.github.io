import requests, json


def determine_asset_id(videoStreams, protectionScheme="widevine"):
    for vs in videoStreams:
        if (protectionScheme in vs["protectionSchemes"]):
            return vs["streamingUrl"] + "&%%&" + vs["contentLocator"]
            
    return ""

def determine_icon_url(images, width=110):
    for img in images:
        if (width == img["width"]):
            return img["url"]
    
    return ""

def update_channel_list():
    channel_list_input = download_hgo_channel_list()
    channel_list_output = transform_channel_list(channel_list_input)
    
    # Write output to file
    with open("channels.json", "w") as json_output:
        json.dump(channel_list_output, json_output)


# Transforms channel list from HorizonGo format for Kodi IPTV plugin
def transform_channel_list(input):
    output = {}

    for c in input["channels"]:
        if (len(c["stationSchedules"]) != 1 or len(c["stationSchedules"][0]["station"]["videoStreams"]) == 0):
            continue
            
        # TODO: Is always the first element needed?
        station = c["stationSchedules"][0]["station"]
        
        id = station["id"]
    
        output[id] = {
            "id": id,
            "assetid": determine_asset_id(station["videoStreams"]),
            "name": station["title"],
            "icon": determine_icon_url(station["images"]),
            "description": "",
            "channelno": str(c["channelNumber"]),
            "erotica": "0",
            "minimal": "1",
            "replay": "1" if station["replayTvEnabled"] == True else "0",
            "regional": "0",
            "home_only": "0"
        }

    return output


def download_hgo_channel_list():
    CHANNEL_URL = "https://web-api-pepper.horizon.tv/oesp/v2/HU/hun/web/channels"
    
    r = requests.get(CHANNEL_URL, allow_redirects=True)
    
    if not(r.ok):
        raise Exception("Channel list cannot be downloaded! Status code: " + str(r.status_code))
    
    return r.json()


def main():
    print("Update channel list...")
    
    try:
        update_channel_list()
    except Exception as e:
        print(str(e))
        print("Failed.")
    else:
        print("Done.")
    

if __name__ == "__main__":
    # execute only if run as a script
    main()